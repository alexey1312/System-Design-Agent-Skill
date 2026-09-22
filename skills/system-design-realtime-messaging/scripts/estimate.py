#!/usr/bin/env python3
"""Back-of-the-envelope calculator for system design estimates.

Deterministic arithmetic for the numbers an interview answer or design
review needs, so the agent reasons over a table instead of doing mental
math in prose. Reads nothing and writes nothing.

Subcommands:
  traffic       QPS, storage, bandwidth, cache and server counts from DAU,
                events per day or a QPS figure
  size          bytes for N rows, keys or objects (metadata tables, limiter state)
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
    if suffix == "":
        return value  # a bare number is bytes
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
    dau: float | None = None,
    actions_per_day: float = 1.0,
    events_per_day: float | None = None,
    qps: float | None = None,
    payload: float = 0.0,
    read_write_ratio: float = 10.0,
    peak_factor: float = 2.0,
    media_share: float = 0.0,
    media_size: float = 0.0,
    served_size: float | None = None,
    retention_days: float = DAYS_PER_YEAR,
    replication: float = 1.0,
    cache_share: float = 0.2,
    server_qps: float | None = None,
    row_bytes: float | None = None,
    egress_cost_per_gb: float | None = None,
) -> dict[str, Any]:
    """Derive rates, storage, bandwidth and sizes from one write-volume input.

    Exactly one of `dau` (with `actions_per_day`), `events_per_day` or `qps`
    describes the write volume. `served_size` is the object a read returns
    (a rendition, a page); it defaults to the average stored object.
    `row_bytes` sizes the metadata row written per event; `egress_cost_per_gb`
    prices the read traffic.
    """
    given = [x is not None for x in (dau, events_per_day, qps)]
    if sum(given) != 1:
        raise ParseError("give exactly one of dau, events_per_day or qps")
    if qps is not None:
        writes_per_day = qps * SECONDS_PER_DAY
    elif events_per_day is not None:
        writes_per_day = events_per_day
    else:
        writes_per_day = dau * actions_per_day
    write_qps = writes_per_day / SECONDS_PER_DAY
    read_qps = write_qps * read_write_ratio
    reads_per_day = writes_per_day * read_write_ratio
    average_object = payload + media_share * media_size
    served = average_object if served_size is None else served_size
    storage_per_day = writes_per_day * average_object
    storage_retained = storage_per_day * retention_days * replication
    ingress = storage_per_day / SECONDS_PER_DAY
    egress = read_qps * served
    egress_per_day = reads_per_day * served
    cache_bytes = reads_per_day * cache_share * served
    result: dict[str, Any] = {
        "assumptions": {
            "dau": dau,
            "actions_per_day": actions_per_day if dau is not None else None,
            "events_per_day": writes_per_day,
            "payload_bytes": payload,
            "media_share": media_share,
            "media_size_bytes": media_size,
            "served_size_bytes": served,
            "read_write_ratio": read_write_ratio,
            "peak_factor": peak_factor,
            "retention_days": retention_days,
            "replication": replication,
            "cache_share": cache_share,
            "row_bytes": row_bytes,
            "egress_cost_per_gb": egress_cost_per_gb,
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
        "peak_ingress_bytes_per_second": ingress * peak_factor,
        "egress_bytes_per_second": egress,
        "peak_egress_bytes_per_second": egress * peak_factor,
        "egress_bytes_per_day": egress_per_day,
        "cache_bytes": cache_bytes,
    }
    if row_bytes is not None:
        result["rows_retained"] = writes_per_day * retention_days
        result["metadata_retained_bytes"] = writes_per_day * retention_days * row_bytes * replication
    if egress_cost_per_gb is not None:
        result["egress_cost_per_day"] = egress_per_day / 1e9 * egress_cost_per_gb
    if server_qps:
        result["servers_at_peak"] = math.ceil(
            (result["peak_write_qps"] + result["peak_read_qps"]) / server_qps
        )
        result["servers_note"] = "request-bound tiers only; byte-bound tiers (upload proxies, origins) size by bandwidth"
    result["human"] = {
        "writes_per_day": human_count(writes_per_day),
        "write_qps": human_count(write_qps),
        "peak_write_qps": human_count(result["peak_write_qps"]),
        "read_qps": human_count(read_qps),
        "peak_read_qps": human_count(result["peak_read_qps"]),
        "average_object": human_size(average_object),
        "served_object": human_size(served),
        "storage_per_day": human_size(storage_per_day),
        "storage_retained": human_size(storage_retained),
        "ingress": human_size(ingress) + "/s",
        "peak_ingress": human_size(ingress * peak_factor) + "/s",
        "egress": human_size(egress) + "/s",
        "peak_egress": human_size(egress * peak_factor) + "/s",
        "egress_per_day": human_size(egress_per_day),
        "cache": human_size(cache_bytes),
    }
    if "rows_retained" in result:
        result["human"]["rows_retained"] = human_count(result["rows_retained"])
        result["human"]["metadata_retained"] = human_size(result["metadata_retained_bytes"])
    if "egress_cost_per_day" in result:
        result["human"]["egress_cost_per_day"] = f"${_sig(result['egress_cost_per_day'])}"
    if "servers_at_peak" in result:
        result["human"]["servers_at_peak"] = str(result["servers_at_peak"])
    return result


def size(*, count: float, bytes_each: float, replication: float = 1.0, growth_per_day: float | None = None, retention_days: float | None = None) -> dict[str, Any]:
    """Bytes for a set of rows, keys or objects; optionally grown over a retention period."""
    total = count * bytes_each * replication
    result: dict[str, Any] = {
        "assumptions": {"count": count, "bytes_each": bytes_each, "replication": replication, "growth_per_day": growth_per_day, "retention_days": retention_days},
        "bytes": total,
        "human": {"count": human_count(count), "bytes": human_size(total)},
    }
    if growth_per_day is not None and retention_days is not None:
        grown = (count + growth_per_day * retention_days) * bytes_each * replication
        result["bytes_after_retention"] = grown
        result["count_after_retention"] = count + growth_per_day * retention_days
        result["human"]["count_after_retention"] = human_count(result["count_after_retention"])
        result["human"]["bytes_after_retention"] = human_size(grown)
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
    if a["dau"] is not None:
        writes_derivation = f"{human_count(a['dau'])} DAU × {a['actions_per_day']:g}"
    else:
        writes_derivation = "given (events per day or QPS × 86,400)"
    lines = [
        "| Quantity | Value | Derivation |",
        "| --- | --- | --- |",
        f"| Writes per day | {h['writes_per_day']} | {writes_derivation} |",
        f"| Write QPS (avg / peak) | {h['write_qps']} / {h['peak_write_qps']} | ÷ 86,400 s; × {a['peak_factor']:g} |",
        f"| Read QPS (avg / peak) | {h['read_qps']} / {h['peak_read_qps']} | write QPS × {a['read_write_ratio']:g} |",
        f"| Average stored object | {h['average_object']} | {human_size(a['payload_bytes'])} + {a['media_share']:g} × {human_size(a['media_size_bytes'])} |",
        f"| Served object | {h['served_object']} | given, or the stored object |",
        f"| Storage per day | {h['storage_per_day']} | writes per day × stored object |",
        f"| Storage retained | {h['storage_retained']} | × {a['retention_days']:g} days × {a['replication']:g} replicas |",
        f"| Ingress (avg / peak) | {h['ingress']} / {h['peak_ingress']} | storage per day ÷ 86,400; × {a['peak_factor']:g} |",
        f"| Egress (avg / peak) | {h['egress']} / {h['peak_egress']} | read QPS × served object; × {a['peak_factor']:g} |",
        f"| Egress per day | {h['egress_per_day']} | reads per day × served object |",
        f"| Cache ({a['cache_share']:.0%} of daily reads) | {h['cache']} | reads per day × {a['cache_share']:g} × served object |",
    ]
    if "rows_retained" in h:
        lines.append(f"| Metadata rows retained | {h['rows_retained']} | writes per day × {a['retention_days']:g} days |")
        lines.append(f"| Metadata retained | {h['metadata_retained']} | rows × {human_size(a['row_bytes'])} × {a['replication']:g} replicas |")
    if "egress_cost_per_day" in h:
        lines.append(f"| Egress cost per day | {h['egress_cost_per_day']} | egress per day × ${a['egress_cost_per_gb']:g}/GB |")
    if "servers_at_peak" in h:
        lines.append(f"| Servers at peak (request-bound tiers) | {h['servers_at_peak']} | peak QPS ÷ per-server QPS |")
    lines.append("")
    lines.append(f"Units: {a['units']}.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    sub = parser.add_subparsers(dest="command", required=True)

    t = sub.add_parser("traffic", help="QPS, storage, bandwidth, cache, servers")
    group = t.add_mutually_exclusive_group(required=True)
    group.add_argument("--dau", help="daily active users, e.g. 150M (combine with --actions-per-day)")
    group.add_argument("--mau", help="monthly active users; combine with --dau-ratio")
    group.add_argument("--events-per-day", help="write events per day, when users are not the unit, e.g. 240k reservations")
    group.add_argument("--qps", help="write requests per second, e.g. 5000 (peak factor still applies)")
    t.add_argument("--dau-ratio", default="0.5", help="DAU as a share of MAU (default 0.5)")
    t.add_argument("--actions-per-day", default="1", help="write actions per user per day")
    t.add_argument("--payload", default="1KB", help="size of one written record, e.g. 300B, 1KB")
    t.add_argument("--media-share", default="0", help="fraction of writes that carry media, e.g. 0.1 or 10%%")
    t.add_argument("--media-size", default="0B", help="size of one media object, e.g. 1MB")
    t.add_argument("--served-size", default=None, help="size of the object a read returns, e.g. 300KB rendition (default: the stored object)")
    t.add_argument("--row-bytes", default=None, help="metadata row written per event, e.g. 500B, to count rows and metadata bytes")
    t.add_argument("--egress-cost-per-gb", default=None, help="price of read traffic, e.g. 0.02, to print egress cost per day")
    t.add_argument("--read-write-ratio", default="10", help="reads per write, e.g. 10 or 10:1")
    t.add_argument("--peak-factor", default="2", help="peak QPS as a multiple of average")
    t.add_argument("--retention", default="1y", help="how long data is kept, e.g. 5y, 30d")
    t.add_argument("--replication", default="1", help="copies kept on disk")
    t.add_argument("--cache-share", default="0.2", help="share of daily reads to cache (80/20 rule)")
    t.add_argument("--server-qps", default=None, help="QPS one server sustains, to size the fleet")

    z = sub.add_parser("size", help="bytes for N rows, keys or objects of a given size")
    z.add_argument("--count", required=True, help="number of rows, keys or objects, e.g. 73M")
    z.add_argument("--bytes-each", required=True, help="size of one, e.g. 1KB, 100B")
    z.add_argument("--replication", default="1", help="copies kept")
    z.add_argument("--growth-per-day", default=None, help="new rows per day, with --retention, to project the end state")
    z.add_argument("--retention", default=None, help="how long rows are kept, e.g. 2y")

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
            dau = None
            if args.dau:
                dau = parse_count(args.dau)
            elif args.mau:
                dau = parse_count(args.mau) * parse_ratio(args.dau_ratio)
            result = traffic(
                dau=dau,
                actions_per_day=parse_count(args.actions_per_day),
                events_per_day=parse_count(args.events_per_day) if args.events_per_day else None,
                qps=parse_count(args.qps) if args.qps else None,
                payload=parse_size(args.payload),
                read_write_ratio=parse_ratio(args.read_write_ratio),
                peak_factor=float(args.peak_factor),
                media_share=parse_ratio(args.media_share),
                media_size=parse_size(args.media_size),
                served_size=parse_size(args.served_size) if args.served_size else None,
                retention_days=parse_duration_days(args.retention),
                replication=float(args.replication),
                cache_share=parse_ratio(args.cache_share),
                server_qps=parse_count(args.server_qps) if args.server_qps else None,
                row_bytes=parse_size(args.row_bytes) if args.row_bytes else None,
                egress_cost_per_gb=float(args.egress_cost_per_gb) if args.egress_cost_per_gb else None,
            )
            print(json.dumps(result, indent=2) if args.format == "json" else render_traffic_markdown(result))
        elif args.command == "size":
            result = size(
                count=parse_count(args.count),
                bytes_each=parse_size(args.bytes_each),
                replication=float(args.replication),
                growth_per_day=parse_count(args.growth_per_day) if args.growth_per_day else None,
                retention_days=parse_duration_days(args.retention) if args.retention else None,
            )
            if args.format == "json":
                print(json.dumps(result, indent=2))
            else:
                h = result["human"]; a = result["assumptions"]
                print(f"{h['count']} × {human_size(a['bytes_each'])} × {a['replication']:g} replicas = {h['bytes']}")
                if "bytes_after_retention" in h:
                    print(f"after {a['retention_days']:g} days at {human_count(a['growth_per_day'])}/day: {h['count_after_retention']} rows = {h['bytes_after_retention']}")
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
