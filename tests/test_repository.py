from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SKILLS = sorted(path.name for path in (ROOT / "skills").iterdir() if path.is_dir())


def frontmatter(skill: str) -> dict[str, str]:
    text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, f"{skill}: missing frontmatter"
    fields: dict[str, str] = {}
    current = None
    for line in match.group(1).splitlines():
        if re.match(r"^[a-z_-]+:", line):
            key, _, value = line.partition(":")
            current = key.strip()
            fields[current] = value.strip()
        elif current:
            fields[current] = (fields[current] + " " + line.strip()).strip()
    if fields.get("description", "").startswith(">-"):
        fields["description"] = fields["description"][2:].strip()
    return fields


class ManifestTests(unittest.TestCase):
    def test_json_manifests_parse(self) -> None:
        for relative in (
            ".claude-plugin/plugin.json",
            ".claude-plugin/marketplace.json",
            ".cursor-plugin/plugin.json",
            "package.json",
        ):
            with self.subTest(relative):
                json.loads((ROOT / relative).read_text(encoding="utf-8"))

    def test_plugin_lists_every_skill(self) -> None:
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(Path(p).name for p in plugin["skills"]), SKILLS)
        for path in plugin["skills"]:
            self.assertTrue((ROOT / path / "SKILL.md").is_file(), path)

    def test_package_and_cursor_list_every_skill(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(Path(p).name for p in package["pi"]["skills"]), SKILLS)
        cursor = json.loads((ROOT / ".cursor-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(Path(p).name for p in cursor["skills"]), SKILLS)

    def test_versions_agree(self) -> None:
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        cursor = json.loads((ROOT / ".cursor-plugin/plugin.json").read_text(encoding="utf-8"))
        entry = next(p for p in marketplace["plugins"] if p["name"] == plugin["name"])
        self.assertEqual(entry["version"], plugin["version"])
        self.assertEqual(cursor["version"], plugin["version"])
        openai = (ROOT / "agents/openai.yaml").read_text(encoding="utf-8")
        self.assertIn(f'version: "{plugin["version"]}"', openai)
        for skill in SKILLS:
            self.assertIn(f"  - {skill}\n", openai)


class SkillTests(unittest.TestCase):
    def test_frontmatter(self) -> None:
        for skill in SKILLS:
            with self.subTest(skill):
                fields = frontmatter(skill)
                self.assertEqual(fields.get("name"), skill)
                description = fields.get("description", "")
                self.assertGreater(len(description), 200)
                self.assertLessEqual(len(description), 1024)

    def test_referenced_files_exist(self) -> None:
        pattern = re.compile(r"`((?:references|scripts)/[\w./-]+\.(?:md|py))")
        for skill in SKILLS:
            directory = ROOT / "skills" / skill
            sources = [directory / "SKILL.md", *(directory / "references").glob("*.md")]
            for source in sources:
                if source.name == "sources.md":
                    continue  # the chapter map spans every skill; ChapterCoverageTests checks it
                text = source.read_text(encoding="utf-8")
                for relative in set(pattern.findall(text)):
                    with self.subTest(skill=skill, file=relative, source=source.name):
                        self.assertTrue((directory / relative).is_file())

    def test_skill_names_referenced_in_docs_exist(self) -> None:
        pattern = re.compile(r"\bsystem-design-[a-z-]+[a-z]\b")
        plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["name"]
        for path in [*(ROOT / "skills").rglob("*.md"), *(ROOT / "references").glob("*.md"), ROOT / "README.md", ROOT / "AGENTS.md", ROOT / "CONTRIBUTING.md", ROOT / "DESIGN-CHECKS.md"]:
            text = re.sub(r"https?://\S+", "", path.read_text(encoding="utf-8"))
            for name in set(pattern.findall(text)) - {plugin, "system-design-agent-skill", "system-design-notes"}:
                with self.subTest(file=str(path.relative_to(ROOT)), name=name):
                    self.assertIn(name, SKILLS)

    def test_copies_in_sync(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/sync_skill_copies.py"), "--check"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout)


class ChapterCoverageTests(unittest.TestCase):
    ROW = re.compile(r"^\| (Vol\. \d ch\. \d+) \| (.+?) \| `([\w-]+)` \| `(references/[\w-]+\.md)` \|$")

    def rows(self) -> list[tuple[str, str, str, str]]:
        text = (ROOT / "references/sources.md").read_text(encoding="utf-8")
        return [match.groups() for line in text.splitlines() if (match := self.ROW.match(line))]

    def test_all_twenty_eight_chapters_are_mapped(self) -> None:
        rows = self.rows()
        self.assertEqual(len(rows), 28)
        self.assertEqual(len({chapter for chapter, *_ in rows}), 28)

    def test_every_chapter_reference_exists_in_its_skill(self) -> None:
        for chapter, title, skill, reference in self.rows():
            with self.subTest(chapter=chapter):
                self.assertIn(skill, SKILLS)
                path = ROOT / "skills" / skill / reference
                self.assertTrue(path.is_file(), f"{chapter} ({title}): {path}")

    def test_every_case_study_reference_is_mapped(self) -> None:
        mapped = {(skill, reference) for _, _, skill, reference in self.rows()}
        shared = {p.name for p in (ROOT / "references").glob("*.md")}
        for skill in SKILLS:
            for path in (ROOT / "skills" / skill / "references").glob("*.md"):
                if path.name in shared:
                    continue
                with self.subTest(skill=skill, reference=path.name):
                    self.assertIn((skill, f"references/{path.name}"), mapped)

    def test_specialists_are_listed_in_the_orchestrator(self) -> None:
        text = (ROOT / "skills/system-design-advisor/SKILL.md").read_text(encoding="utf-8")
        for skill in SKILLS:
            if skill != "system-design-advisor":
                self.assertIn(f"`{skill}`", text)

    def test_design_checks_list_every_scanner_rule(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        import arch_scan  # noqa: WPS433

        text = (ROOT / "DESIGN-CHECKS.md").read_text(encoding="utf-8")
        for rule in arch_scan.RULES:
            with self.subTest(rule.id):
                self.assertIn(f"| {rule.id} |", text)

    def test_checklist_ids_are_unique(self) -> None:
        text = (ROOT / "references/review-checklist.md").read_text(encoding="utf-8")
        ids = re.findall(r"^\| (RC-\d+\.\d+) \|", text, re.M)
        self.assertGreaterEqual(len(ids), 40)
        self.assertEqual(len(ids), len(set(ids)))


class EvalTests(unittest.TestCase):
    def test_every_skill_has_skill_creator_evals(self) -> None:
        for skill in SKILLS:
            with self.subTest(skill):
                directory = ROOT / "skills" / skill / "evals"
                evals = json.loads((directory / "evals.json").read_text(encoding="utf-8"))
                self.assertEqual(evals["skill_name"], skill)
                ids = [item["id"] for item in evals["evals"]]
                self.assertEqual(len(ids), len(set(ids)))
                for item in evals["evals"]:
                    self.assertTrue(item["expectations"])
                    for relative in item["files"]:
                        self.assertTrue((ROOT / "skills" / skill / relative).exists(), relative)

    def test_trigger_evals_mix_positive_and_negative(self) -> None:
        for skill in SKILLS:
            with self.subTest(skill):
                path = ROOT / "skills" / skill / "evals" / "trigger-evals.json"
                items = json.loads(path.read_text(encoding="utf-8"))
                self.assertGreaterEqual(len(items), 16)
                positives = sum(item["should_trigger"] for item in items)
                self.assertGreaterEqual(positives, 6)
                self.assertGreaterEqual(len(items) - positives, 6)


if __name__ == "__main__":
    unittest.main()
