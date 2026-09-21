#!/usr/bin/env python3
"""Back-of-the-envelope calculator for system design estimates.

Deterministic arithmetic for the numbers an interview answer or design
review needs, so the agent reasons over a table instead of doing mental
math in prose. Reads nothing and writes nothing.

Subcommands:
  traffic       QPS, storage, bandwidth, cache and server counts from DAU
  availability  downtime allowed by an availability percentage
  latency       the "latency numbers every programmer should know" table
  powers        powers of two with their approximate decimal names

Storage uses decimal units (1 KB = 1000 B), as interview estimates do.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from typing import Any

SECONDS_PER_DAY = 86_400
DAYS_PER_YEAR = 365

COUNT_SUFFIXES = {"": 1, "k": 1e3, "m": 1e6, "b": 1e9, "t": 1e12}
SIZE_SUFFIXES = {
    "b": 1,
    "byte": 1,
    "bytes": 1,
    "kb": 1e3,
    "mb": 1e6,
    "gb": 1e9,
    "tb": 1e12,
    "pb": 1e15,
    "eb": 1e18,
}
DURATION_DAYS = {
    "s": 1 / SECONDS_PER_DAY,
    "sec": 1 / SECONDS_PER_DAY,
    "min": 1 / 1440,
    "h": 1 / 24,
    "hr": 1 / 24,
    "d": 1,
    "day": 1,
    "days": 1,
    "w": 7,
    "wk": 7,
    "mo": 30,
    "month": 30,
    "months": 30,
    "y": DAYS_PER_YEAR,
    "yr": DAYS_PER_YEAR,
    "year": DAYS_PER_YEAR,
    "years": DAYS_PER_YEAR,
}

LATENCY_NUMBERS = [
    ("L1 cache reference", 0.5e-9),
    ("Branch mispredict", 5e-9),
    ("L2 cache reference", 7e-9),
    ("Mutex lock/unlock", 25e-9),
    ("Main memory reference", 100e-9),
    ("Compress 1 KB with Zippy", 10e-6),
    ("Send 2 KB over 1 Gbps network", 20e-6),
    ("Read 1 MB sequentially from memory", 250e-6),
    ("Round trip within the same data center", 500e-6),
    ("Read 1 MB sequentially from SSD", 1e-3),
    ("Disk seek", 10e-3),
    ("Read 1 MB sequentially from disk", 30e-3),
    ("Send a packet CA -> Netherlands -> CA", 150e-3),
]

_NUMBER = re.compile(r"^\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*([a-zA-Z]*)\s*$")


class ParseError(ValueError):
    pass


def _split(text: str) -> tuple[float, str]:
    match = _NUMBER.match(str(text))
    if not match:
        raise ParseError(f"cannot parse {text!r}")
    return float(match.group(1).replace(",", "")), match.group(2).lower()


def parse_count(text: str) -> float:
    """'150M' -> 150e6, '2.5k' -> 2500, '1,000' -> 1000."""
    value, suffix = _split(text)
    if suffix not in COUNT_SUFFIXES:
        raise ParseError(f"unknown count suffix {suffix!r} in {text!r}")
    return value * COUNT_SUFFIXES[suffix]


def parse_size(text: str) -> float:
    """'300B' -> 300, '1MB' -> 1e6, '2.5 GB' -> 2.5e9 (decimal units)."""
    value, suffix = _split(text)
    if suffix not in SIZE_SUFFIXES:
        raise ParseError(f"unknown size suffix {suffix!r} in {text!r}")
    return value * SIZE_SUFFIXES[suffix]


def parse_duration_days(text: str) -> float:
    """'5y' -> 1825, '30d' -> 30, '12h' -> 0.5, '2mo' -> 60."""
    value, suffix = _split(text)
    if suffix not in DURATION_DAYS:
        raise ParseError(f"unknown duration suffix {suffix!r} in {text!r}")
    return value * DURATION_DAYS[suffix]


def parse_ratio(text: str) -> float:
    """'10' -> 10, '10:1' -> 10, '1:5' -> 0.2, '50%' -> 0.5."""
    text = str(text).strip()
    if text.endswith("%"):
        return float(text[:-1]) / 100
    if ":" in text:
        left, right = text.split(":", 1)
        return float(left) / float(right)
    return float(text)


def human_count(value: float, unit: str = "") -> str:
    for suffix, factor in (("T", 1e12), ("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(value) >= factor:
            return f"{_sig(value / factor)}{suffix}{unit}"
    return f"{_sig(value)}{unit}"


def human_size(value: float) -> str:
    for suffix, factor in (
        ("EB", 1e18),
        ("PB", 1e15),
        ("TB", 1e12),
        ("GB", 1e9),
        ("MB", 1e6),
        ("KB", 1e3),
    ):
        if abs(value) >= factor:
            return f"{_sig(value / factor)} {suffix}"
    return f"{_sig(value)} B"


def human_duration(seconds: float) -> str:
    for suffix, factor in (
        ("days", SECONDS_PER_DAY),
        ("h", 3600),
        ("min", 60),
        ("s", 1),
        ("ms", 1e-3),
        ("µs", 1e-6),
        ("ns", 1e-9),
    ):
        if abs(seconds) >= factor:
            return f"{_sig(seconds / factor)} {suffix}"
    return f"{_sig(seconds / 1e-9)} ns"


def _sig(value: float, digits: int = 3) -> str:
    if value == 0:
        return "0"
    magnitude = math.floor(math.log10(abs(value)))
    rounded = round(value, max(0, digits - 1 - magnitude))
    if rounded == int(rounded):
        return f"{int(rounded):,}"
    return f"{rounded:,.{max(0, digits - 1 - magnitude)}f}".rstrip("0").rstrip(".")


def traffic(
    *,
    dau: float,
    actions_per_day: float,
    payload: float,
    read_write_ratio: float = 10.0,
    peak_factor: float = 2.0,
    media_share: float = 0.0,
    media_size: float = 0.0,
    retention_days: float = DAYS_PER_YEAR,
    replication: float = 1.0,
    cache_share: float = 0.2,
    server_qps: float | None = None,
) -> dict[str, Any]:
    writes_per_day = dau * actions_per_day
    write_qps = writes_per_day / SECONDS_PER_DAY
    read_qps = write_qps * read_write_ratio
    reads_per_day = writes_per_day * read_write_ratio
    average_object = payload + media_share * media_size
    storage_per_day = writes_per_day * average_object
    storage_retained = storage_per_day * retention_days * replication
    ingress = storage_per_day / SECONDS_PER_DAY
    egress = read_qps * average_object
    cache_bytes = reads_per_day * cache_share * average_object
    result: dict[str, Any] = {
        "assumptions": {
            "dau": dau,
            "actions_per_day": actions_per_day,
            "payload_bytes": payload,
            "media_share": media_share,
            "media_size_bytes": media_size,
            "read_write_ratio": read_write_ratio,
            "peak_factor": peak_factor,
            "retention_days": retention_days,
            "replication": replication,
            "cache_share": cache_share,
            "units": "decimal (1 KB = 1000 B); day = 86,400 s; year = 365 days",
        },
        "writes_per_day": writes_per_day,
        "write_qps": write_qps,
        "peak_write_qps": write_qps * peak_factor,
        "read_qps": read_qps,
        "peak_read_qps": read_qps * peak_factor,
        "average_object_bytes": average_object,
        "storage_per_day_bytes": storage_per_day,
        "storage_retained_bytes": storage_retained,
        "ingress_bytes_per_second": ingress,
        "egress_bytes_per_second": egress,
        "cache_bytes": cache_bytes,
    }
    if server_qps:
        result["servers_at_peak"] = math.ceil(
            (result["peak_write_qps"] + result["peak_read_qps"]) / server_qps
        )
    result["human"] = {
        "writes_per_day": human_count(writes_per_day),
        "write_qps": human_count(write_qps),
        "peak_write_qps": human_count(result["peak_write_qps"]),
        "read_qps": human_count(read_qps),
        "peak_read_qps": human_count(result["peak_read_qps"]),
        "average_object": human_size(average_object),
        "storage_per_day": human_size(storage_per_day),
        "storage_retained": human_size(storage_retained),
        "ingress": human_size(ingress) + "/s",
        "egress": human_size(egress) + "/s",
        "cache": human_size(cache_bytes),
    }
    if "servers_at_peak" in result:
        result["human"]["servers_at_peak"] = str(result["servers_at_peak"])
    return result


def availability(percent: float) -> dict[str, Any]:
    if not 0 < percent < 100:
        raise ParseError("availability must be between 0 and 100 (exclusive)")
    down_fraction = 1 - percent / 100
    per_day = down_fraction * SECONDS_PER_DAY
    per_year = per_day * DAYS_PER_YEAR
    nines = -math.log10(down_fraction) if down_fraction > 0 else float("inf")
    return {
        "availability_percent": percent,
        "nines": round(nines, 2),
        "downtime_seconds_per_day": per_day,
        "downtime_seconds_per_month": per_day * 30,
        "downtime_seconds_per_year": per_year,
        "human": {
            "per_day": human_duration(per_day),
            "per_month": human_duration(per_day * 30),
            "per_year": human_duration(per_year),
        },
    }


def powers() -> list[dict[str, Any]]:
    names = {10: "thousand (KB)", 20: "million (MB)", 30: "billion (GB)", 40: "trillion (TB)", 50: "quadrillion (PB)"}
    return [{"power": p, "exact": 2**p, "approximate": names[p]} for p in names]


def latency_table() -> list[dict[str, Any]]:
    return [{"operation": name, "seconds": seconds, "human": human_duration(seconds)} for name, seconds in LATENCY_NUMBERS]


def render_traffic_markdown(result: dict[str, Any]) -> str:
    a = result["assumptions"]
    h = result["human"]
    lines = [
        "| Quantity | Value | Derivation |",
        "| --- | --- | --- |",
        f"| Writes per day | {h['writes_per_day']} | {human_count(a['dau'])} DAU × {a['actions_per_day']:g} |",
        f"| Write QPS (avg / peak) | {h['write_qps']} / {h['peak_write_qps']} | ÷ 86,400 s; × {a['peak_factor']:g} |",
        f"| Read QPS (avg / peak) | {h['read_qps']} / {h['peak_read_qps']} | write QPS × {a['read_write_ratio']:g} |",
        f"| Average object | {h['average_object']} | {human_size(a['payload_bytes'])} + {a['media_share']:g} × {human_size(a['media_size_bytes'])} |",
        f"| Storage per day | {h['storage_per_day']} | writes per day × object |",
        f"| Storage retained | {h['storage_retained']} | × {a['retention_days']:g} days × {a['replication']:g} replicas |",
        f"| Ingress / egress | {h['ingress']} / {h['egress']} | storage per day ÷ 86,400; read QPS × object |",
        f"| Cache ({a['cache_share']:.0%} of daily reads) | {h['cache']} | reads per day × {a['cache_share']:g} × object |",
    ]
    if "servers_at_peak" in h:
        lines.append(f"| Servers at peak | {h['servers_at_peak']} | peak QPS ÷ per-server QPS |")
    lines.append("")
    lines.append(f"Units: {a['units']}.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    sub = parser.add_subparsers(dest="command", required=True)

    t = sub.add_parser("traffic", help="QPS, storage, bandwidth, cache, servers")
    group = t.add_mutually_exclusive_group(required=True)
    group.add_argument("--dau", help="daily active users, e.g. 150M")
    group.add_argument("--mau", help="monthly active users; combine with --dau-ratio")
    t.add_argument("--dau-ratio", default="0.5", help="DAU as a share of MAU (default 0.5)")
    t.add_argument("--actions-per-day", default="1", help="write actions per user per day")
    t.add_argument("--payload", default="1KB", help="size of one written record, e.g. 300B, 1KB")
    t.add_argument("--media-share", default="0", help="fraction of writes that carry media, e.g. 0.1 or 10%%")
    t.add_argument("--media-size", default="0B", help="size of one media object, e.g. 1MB")
    t.add_argument("--read-write-ratio", default="10", help="reads per write, e.g. 10 or 10:1")
    t.add_argument("--peak-factor", default="2", help="peak QPS as a multiple of average")
    t.add_argument("--retention", default="1y", help="how long data is kept, e.g. 5y, 30d")
    t.add_argument("--replication", default="1", help="copies kept on disk")
    t.add_argument("--cache-share", default="0.2", help="share of daily reads to cache (80/20 rule)")
    t.add_argument("--server-qps", default=None, help="QPS one server sustains, to size the fleet")

    a = sub.add_parser("availability", help="downtime for an availability percentage")
    a.add_argument("percent", help="e.g. 99.99")

    sub.add_parser("latency", help="latency numbers every programmer should know")
    sub.add_parser("powers", help="powers of two")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "traffic":
            dau = parse_count(args.dau) if args.dau else parse_count(args.mau) * parse_ratio(args.dau_ratio)
            result = traffic(
                dau=dau,
                actions_per_day=parse_count(args.actions_per_day),
                payload=parse_size(args.payload),
                read_write_ratio=parse_ratio(args.read_write_ratio),
                peak_factor=float(args.peak_factor),
                media_share=parse_ratio(args.media_share),
                media_size=parse_size(args.media_size),
                retention_days=parse_duration_days(args.retention),
                replication=float(args.replication),
                cache_share=parse_ratio(args.cache_share),
                server_qps=parse_count(args.server_qps) if args.server_qps else None,
            )
            print(json.dumps(result, indent=2) if args.format == "json" else render_traffic_markdown(result))
        elif args.command == "availability":
            result = availability(float(args.percent.rstrip("%")))
            if args.format == "json":
                print(json.dumps(result, indent=2))
            else:
                h = result["human"]
                print(f"{result['availability_percent']:g}% ({result['nines']:g} nines): "
                      f"{h['per_day']} per day, {h['per_month']} per month, {h['per_year']} per year")
        elif args.command == "latency":
            rows = latency_table()
            if args.format == "json":
                print(json.dumps(rows, indent=2))
            else:
                print("| Operation | Time |\n| --- | --- |")
                for row in rows:
                    print(f"| {row['operation']} | {row['human']} |")
        elif args.command == "powers":
            rows = powers()
            if args.format == "json":
                print(json.dumps(rows, indent=2))
            else:
                print("| Power | Exact | Approximate |\n| --- | --- | --- |")
                for row in rows:
                    print(f"| 2^{row['power']} | {row['exact']:,} | {row['approximate']} |")
    except ParseError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
