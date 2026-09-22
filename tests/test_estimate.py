from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import estimate  # noqa: E402


class ParsingTests(unittest.TestCase):
    def test_counts(self) -> None:
        self.assertEqual(estimate.parse_count("150M"), 150e6)
        self.assertEqual(estimate.parse_count("2.5k"), 2500)
        self.assertEqual(estimate.parse_count("1,000"), 1000)
        self.assertEqual(estimate.parse_count("1B"), 1e9)
        self.assertEqual(estimate.parse_count("42"), 42)

    def test_sizes_are_decimal(self) -> None:
        self.assertEqual(estimate.parse_size("300B"), 300)
        self.assertEqual(estimate.parse_size("1KB"), 1000)
        self.assertEqual(estimate.parse_size("1MB"), 1e6)
        self.assertEqual(estimate.parse_size("2.5 GB"), 2.5e9)
        self.assertEqual(estimate.parse_size("140 bytes"), 140)
        self.assertEqual(estimate.parse_size("0"), 0)

    def test_durations(self) -> None:
        self.assertEqual(estimate.parse_duration_days("5y"), 1825)
        self.assertEqual(estimate.parse_duration_days("30d"), 30)
        self.assertEqual(estimate.parse_duration_days("12h"), 0.5)
        self.assertEqual(estimate.parse_duration_days("2w"), 14)
        self.assertEqual(estimate.parse_duration_days("2mo"), 60)

    def test_ratios(self) -> None:
        self.assertEqual(estimate.parse_ratio("10"), 10)
        self.assertEqual(estimate.parse_ratio("10:1"), 10)
        self.assertAlmostEqual(estimate.parse_ratio("1:5"), 0.2)
        self.assertEqual(estimate.parse_ratio("50%"), 0.5)

    def test_bad_input_raises(self) -> None:
        with self.assertRaises(estimate.ParseError):
            estimate.parse_count("lots")
        with self.assertRaises(estimate.ParseError):
            estimate.parse_size("3 parsecs")
        with self.assertRaises(estimate.ParseError):
            estimate.parse_duration_days("5 fortnights")


class TrafficTests(unittest.TestCase):
    """The Twitter example from Vol. 1 ch. 2."""

    def setUp(self) -> None:
        self.result = estimate.traffic(
            dau=150e6,
            actions_per_day=2,
            payload=204,
            media_share=0.1,
            media_size=1e6,
            retention_days=1825,
        )

    def test_qps_matches_the_chapter(self) -> None:
        self.assertAlmostEqual(self.result["write_qps"], 3472, delta=1)
        self.assertAlmostEqual(self.result["peak_write_qps"], 6944, delta=1)

    def test_storage_matches_the_chapter(self) -> None:
        self.assertAlmostEqual(self.result["storage_per_day_bytes"] / 1e12, 30, delta=0.2)
        self.assertAlmostEqual(self.result["storage_retained_bytes"] / 1e15, 55, delta=0.5)

    def test_human_strings(self) -> None:
        human = self.result["human"]
        self.assertEqual(human["write_qps"], "3.47K")
        self.assertEqual(human["storage_per_day"], "30.1 TB")
        self.assertEqual(human["storage_retained"], "54.9 PB")

    def test_qps_and_events_inputs(self) -> None:
        by_qps = estimate.traffic(qps=5000, payload=100, read_write_ratio=0)
        self.assertAlmostEqual(by_qps["writes_per_day"], 5000 * 86_400)
        self.assertAlmostEqual(by_qps["write_qps"], 5000)
        by_events = estimate.traffic(events_per_day=240_000, payload=500)
        self.assertAlmostEqual(by_events["write_qps"], 2.78, delta=0.01)
        self.assertIsNone(by_events["assumptions"]["dau"])
        with self.assertRaises(estimate.ParseError):
            estimate.traffic(dau=1e6, qps=10, payload=1)

    def test_served_size_rows_and_egress_cost(self) -> None:
        result = estimate.traffic(
            dau=2e6, actions_per_day=3, payload=0, media_share=1, media_size=2e6,
            served_size=300e3, read_write_ratio=20, peak_factor=3, retention_days=3 * 365,
            row_bytes=500, egress_cost_per_gb=0.02,
        )
        self.assertAlmostEqual(result["egress_bytes_per_second"], 6e6 * 20 / 86_400 * 300e3, delta=1)
        self.assertAlmostEqual(result["peak_egress_bytes_per_second"], result["egress_bytes_per_second"] * 3)
        self.assertAlmostEqual(result["rows_retained"], 6e6 * 1095)
        self.assertAlmostEqual(result["metadata_retained_bytes"], 6e6 * 1095 * 500)
        self.assertAlmostEqual(result["egress_cost_per_day"], 6e6 * 20 * 300e3 / 1e9 * 0.02)

    def test_size(self) -> None:
        result = estimate.size(count=73e6, bytes_each=1000, replication=3)
        self.assertAlmostEqual(result["bytes"], 219e9)
        grown = estimate.size(count=1e6, bytes_each=100, growth_per_day=1000, retention_days=365)
        self.assertAlmostEqual(grown["count_after_retention"], 1_365_000)

    def test_replication_and_servers(self) -> None:
        result = estimate.traffic(dau=1e6, actions_per_day=1, payload=1000, replication=3, server_qps=1)
        self.assertAlmostEqual(result["storage_retained_bytes"], 1e6 * 1000 * 365 * 3)
        self.assertEqual(result["servers_at_peak"], 255)


class AvailabilityTests(unittest.TestCase):
    def test_four_nines(self) -> None:
        result = estimate.availability(99.99)
        self.assertAlmostEqual(result["downtime_seconds_per_day"], 8.64, places=2)
        self.assertAlmostEqual(result["downtime_seconds_per_year"] / 60, 52.56, places=1)
        self.assertEqual(result["nines"], 4)

    def test_three_nines(self) -> None:
        result = estimate.availability(99.9)
        self.assertAlmostEqual(result["downtime_seconds_per_year"] / 3600, 8.76, places=2)

    def test_out_of_range(self) -> None:
        with self.assertRaises(estimate.ParseError):
            estimate.availability(100)


class FormattingTests(unittest.TestCase):
    def test_human_count(self) -> None:
        self.assertEqual(estimate.human_count(950), "950")
        self.assertEqual(estimate.human_count(1_500), "1.5K")
        self.assertEqual(estimate.human_count(24_000), "24K")
        self.assertEqual(estimate.human_count(1.2e9), "1.2B")

    def test_human_size(self) -> None:
        self.assertEqual(estimate.human_size(500), "500 B")
        self.assertEqual(estimate.human_size(36.5e12), "36.5 TB")
        self.assertEqual(estimate.human_size(1e15), "1 PB")

    def test_human_duration(self) -> None:
        self.assertEqual(estimate.human_duration(0.5e-9), "0.5 ns")
        self.assertEqual(estimate.human_duration(150e-3), "150 ms")
        self.assertEqual(estimate.human_duration(3600 * 8.76), "8.76 h")


class CliTests(unittest.TestCase):
    def run_cli(self, *argv: str) -> str:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = estimate.main(list(argv))
        self.assertEqual(code, 0)
        return buffer.getvalue()

    def test_traffic_json(self) -> None:
        output = self.run_cli("--format", "json", "traffic", "--mau", "300M", "--dau-ratio", "50%", "--actions-per-day", "2", "--payload", "204B", "--media-share", "10%", "--media-size", "1MB", "--retention", "5y")
        data = json.loads(output)
        self.assertEqual(data["assumptions"]["dau"], 150e6)
        self.assertEqual(data["human"]["storage_retained"], "54.9 PB")

    def test_traffic_markdown_has_derivations(self) -> None:
        output = self.run_cli("traffic", "--dau", "10M", "--actions-per-day", "1", "--payload", "1KB")
        self.assertIn("| Write QPS (avg / peak) |", output)
        self.assertIn("Units: decimal", output)

    def test_size_cli(self) -> None:
        self.assertIn("73M × 1 KB × 3 replicas = 219 GB", self.run_cli("size", "--count", "73M", "--bytes-each", "1KB", "--replication", "3"))
        self.assertIn("| Write QPS (avg / peak) | 5K / 10K |", self.run_cli("traffic", "--qps", "5000", "--payload", "100B"))

    def test_latency_and_powers(self) -> None:
        self.assertIn("Disk seek", self.run_cli("latency"))
        self.assertIn("2^30", self.run_cli("powers"))
        self.assertIn("52.6 min per year", self.run_cli("availability", "99.99"))

    def test_dau_and_mau_are_exclusive(self) -> None:
        with self.assertRaises(SystemExit):
            with redirect_stdout(io.StringIO()):
                estimate.main(["traffic", "--dau", "1M", "--mau", "2M"])


if __name__ == "__main__":
    unittest.main()
