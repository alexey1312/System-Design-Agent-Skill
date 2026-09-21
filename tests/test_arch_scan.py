from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import arch_scan  # noqa: E402


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_project(root: Path) -> None:
    write(root, "package.json", '{"dependencies": {"ioredis": "^5", "kafkajs": "^2", "express": "^4"}}')
    write(root, "docker-compose.yml", "services:\n  db:\n    image: postgres:16\n  cache:\n    image: redis:7\n  search:\n    image: elasticsearch:8\n")
    write(root, "requirements.txt", "stripe==7.0\nflask\n")
    write(
        root,
        "app/checkout.py",
        "\n".join(
            [
                "import stripe",
                "from geohash import encode",
                "def charge(amount: float, currency: str):",
                "    total_price = float(amount)",
                "    row = db.execute('SELECT balance FROM wallets WHERE id = ? FOR UPDATE', (1,))",
                "    shard = hash(user_id) % len(servers)",
                "    label: str = 'amount'",
                "    bucket = value % 100",
                "    ranked = db.execute('SELECT COUNT(*) FROM leaderboard WHERE score >= ?', (s,))",
            ]
        ),
    )
    write(root, "db/migrate/001.sql", "CREATE TABLE orders (id INT, amount FLOAT, note TEXT);\n")
    write(root, "node_modules/leftpad/index.js", "const cassandra = require('cassandra-driver');\n")
    write(root, ".hidden/secret.py", "import dynamodb\n")
    write(root, "build.gradle.kts", 'dependencies {\n    "app.pillion.server.*",  // Ktor dash server (device-bound)\n    implementation("io.ktor:ktor-server-core")\n}\n')


class ScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_project(self.root)
        self.result = arch_scan.scan(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def names(self) -> set[str]:
        return {item["name"] for item in self.result["inventory"]}

    def test_inventory_from_manifests_and_imports(self) -> None:
        self.assertIn("Redis", self.names())
        self.assertIn("Kafka", self.names())
        self.assertIn("PostgreSQL", self.names())
        self.assertIn("Elasticsearch / OpenSearch", self.names())
        self.assertIn("Payments provider", self.names())
        self.assertIn("Geospatial", self.names())

    def test_evidence_points_at_a_file_and_line(self) -> None:
        redis = next(item for item in self.result["inventory"] if item["name"] == "Redis")
        self.assertEqual(redis["evidence"][0]["file"], "docker-compose.yml")
        self.assertEqual(redis["evidence"][0]["line"], 5)

    def test_dependencies_and_hidden_directories_are_skipped(self) -> None:
        self.assertNotIn("Cassandra / Scylla", self.names())
        self.assertNotIn("DynamoDB", self.names())
        with_deps = arch_scan.scan(self.root, include_dependencies=True)
        self.assertIn("Cassandra / Scylla", {item["name"] for item in with_deps["inventory"]})

    def test_findings(self) -> None:
        by_id = {}
        for finding in self.result["findings"]:
            by_id.setdefault(finding["id"], []).append(finding)
        self.assertEqual(len(by_id["SD001"]), 1, by_id.get("SD001"))
        self.assertEqual(by_id["SD001"][0]["line"], 3)
        self.assertEqual(by_id["SD002"][0]["file"], "app/checkout.py")
        self.assertEqual(by_id["SD003"][0]["line"], 6)
        self.assertEqual(by_id["SD004"][0]["file"], "db/migrate/001.sql")
        self.assertEqual(by_id["SD007"][0]["line"], 9)
        self.assertNotIn("SD005", by_id)
        self.assertNotIn("SD006", by_id)

    def test_generic_words_in_comments_are_not_technologies(self) -> None:
        self.assertNotIn("Media processing", self.names())
        self.assertNotIn("Serverless", self.names())

    def test_negative_lines_do_not_match(self) -> None:
        lines = {(f["id"], f["line"]) for f in self.result["findings"]}
        self.assertNotIn(("SD001", 7), lines)  # label: str = 'amount'
        self.assertNotIn(("SD003", 8), lines)  # value % 100

    def test_every_rule_cites_a_source_and_reference(self) -> None:
        for rule in arch_scan.RULES:
            self.assertRegex(rule.id, r"^SD\d{3}$")
            self.assertTrue(rule.source.startswith("Vol.") or rule.source.startswith("inference"), rule.id)
            for skill, file in rule.references:
                self.assertTrue((ROOT / "skills" / skill / file).is_file(), f"{rule.id}: {skill}/{file}")

    def test_every_technology_reference_exists(self) -> None:
        for tech in arch_scan.TECHNOLOGIES:
            for skill, file in tech.references:
                self.assertTrue((ROOT / "skills" / skill / file).is_file(), f"{tech.name}: {skill}/{file}")

    def test_questions_follow_the_categories(self) -> None:
        self.assertIn("cache", self.result["categories"])
        self.assertTrue(any("TTL" in q for q in self.result["questions"]))
        self.assertTrue(any("idempotency key reaches the provider" in q for q in self.result["questions"]))

    def test_references_group_by_skill(self) -> None:
        refs = self.result["references"]
        self.assertIn("references/consistent-hashing.md", refs["system-design-infrastructure"])
        self.assertIn("references/payment-system.md", refs["system-design-transactions"])

    def test_scan_does_not_modify_files(self) -> None:
        def digest() -> dict[str, str]:
            return {
                p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(self.root.rglob("*"))
                if p.is_file()
            }

        before = digest()
        arch_scan.scan(self.root, include_dependencies=True)
        self.assertEqual(before, digest())

    def test_cli_json_and_markdown(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = arch_scan.main([str(self.root), "--format", "json"])
        self.assertEqual(code, 0)
        data = json.loads(buffer.getvalue())
        self.assertEqual(data["scanner"]["name"], "arch_scan")
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            arch_scan.main([str(self.root)])
        text = buffer.getvalue()
        self.assertIn("## Inventory", text)
        self.assertIn("SD001", text)
        self.assertIn("## Questions for the owners", text)

    def test_empty_project(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            result = arch_scan.scan(Path(empty))
        self.assertEqual(result["inventory"], [])
        self.assertEqual(result["findings"], [])
        self.assertIn("Nothing recognised", arch_scan.render_markdown(result))


if __name__ == "__main__":
    unittest.main()
