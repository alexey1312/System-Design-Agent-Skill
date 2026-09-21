#!/usr/bin/env python3
"""Read-only architecture scan of a project.

Walks a repository and reports, as JSON or Markdown:

  inventory   the stores, caches, queues, search indexes, transports and
              providers the project depends on, with the file and line that
              proves it, mapped to the chapter references that cover them
  findings    code patterns the System Design Interview books warn about,
              each with a stable rule ID, severity, source chapter and advice
  questions   what to ask the owners before recommending anything
  references  the skill references worth loading for this project

Dependency directories (node_modules, vendor, Pods, ...) and hidden
directories are skipped unless --include-dependencies is given. Comments are
not stripped, so every finding needs the surrounding code read before it
becomes a recommendation. The scanner never writes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

VERSION = "1.0.0"

SKIP_ALWAYS = {".git", ".hg", ".svn", "__pycache__", "DerivedData", "coverage", ".idea", ".vscode"}
DEPENDENCY_DIRS = {
    "node_modules",
    "vendor",
    "Pods",
    "Carthage",
    ".build",
    "checkouts",
    "venv",
    ".venv",
    "site-packages",
    "dist",
    "build",
    "target",
    ".terraform",
}
MANIFEST_NAMES = {
    "package.json",
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "Pipfile",
    "setup.py",
    "go.mod",
    "Gemfile",
    "Cargo.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "composer.json",
    "Package.swift",
    "Podfile",
    "Cartfile",
    "mix.exs",
    "Procfile",
    "serverless.yml",
    "serverless.yaml",
    "Chart.yaml",
    "values.yaml",
    "nginx.conf",
}
INFRA_PATTERNS = (
    re.compile(r"^docker-compose[\w.-]*\.ya?ml$"),
    re.compile(r"^compose[\w.-]*\.ya?ml$"),
    re.compile(r"^Dockerfile[\w.-]*$"),
    re.compile(r"\.tf$"),
    re.compile(r"^\.env[\w.-]*$"),
    re.compile(r"\.env$"),
)
YAML_SUFFIXES = {".yml", ".yaml"}
CODE_SUFFIXES = {
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".rb", ".java", ".kt", ".kts",
    ".swift", ".rs", ".php", ".cs", ".ex", ".exs", ".scala", ".sql", ".prisma",
}
IMPORT_LINE = re.compile(
    r"^\s*(import\b|from\b|require\b|using\b|use\b|extern crate\b|#include\b|@import\b|gem\b|pod\b|implementation\b|api\b|compile\b)|require\(|import\("
)
MAX_FILE_BYTES = 1_000_000


@dataclass(frozen=True)
class Technology:
    name: str
    category: str
    pattern: re.Pattern[str]
    references: tuple[tuple[str, str], ...]


def _tech(name: str, category: str, words: Iterable[str], refs: Iterable[tuple[str, str]]) -> Technology:
    alternation = "|".join(re.escape(word) for word in words)
    return Technology(name, category, re.compile(rf"(?<![\w-])(?:{alternation})(?![\w-])", re.I), tuple(refs))


INFRA = "system-design-infrastructure"
CONTENT = "system-design-content-platforms"
REALTIME = "system-design-realtime-messaging"
GEO = "system-design-geospatial"
TX = "system-design-transactions"
ADVISOR = "system-design-advisor"

TECHNOLOGIES: tuple[Technology, ...] = (
    _tech("PostgreSQL", "relational", ["postgres", "postgresql", "psycopg2", "psycopg", "pg", "asyncpg", "pgx", "libpq"], [(ADVISOR, "references/building-blocks.md"), (TX, "references/hotel-reservation.md")]),
    _tech("MySQL / MariaDB", "relational", ["mysql", "mariadb", "mysql2", "pymysql", "mysqlclient"], [(ADVISOR, "references/building-blocks.md"), (TX, "references/hotel-reservation.md")]),
    _tech("SQLite", "relational", ["sqlite", "sqlite3", "better-sqlite3"], [(ADVISOR, "references/building-blocks.md"), (INFRA, "references/object-storage.md")]),
    _tech("ORM", "relational", ["sqlalchemy", "prisma", "typeorm", "sequelize", "gorm", "hibernate", "activerecord", "diesel", "sqlx", "knex", "drizzle-orm"], [(ADVISOR, "references/building-blocks.md")]),
    _tech("Redis", "cache", ["redis", "ioredis", "redis-py", "elasticache", "jedis", "lettuce", "go-redis", "rediss"], [(ADVISOR, "references/building-blocks.md"), (INFRA, "references/rate-limiter.md"), (REALTIME, "references/gaming-leaderboard.md"), (GEO, "references/nearby-friends.md")]),
    _tech("Memcached", "cache", ["memcached", "memcache", "pymemcache"], [(ADVISOR, "references/building-blocks.md")]),
    _tech("Kafka", "queue", ["kafka", "kafkajs", "kafka-python", "confluent", "confluent-kafka", "sarama", "librdkafka", "redpanda", "msk"], [(INFRA, "references/distributed-message-queue.md"), (REALTIME, "references/ad-click-aggregation.md")]),
    _tech("RabbitMQ / AMQP", "queue", ["rabbitmq", "amqp", "amqplib", "pika", "bunny"], [(INFRA, "references/distributed-message-queue.md"), (REALTIME, "references/notification-system.md")]),
    _tech("Cloud queue", "queue", ["sqs", "sns", "pubsub", "google-cloud-pubsub", "azure-servicebus", "eventbridge", "kinesis"], [(INFRA, "references/distributed-message-queue.md"), (REALTIME, "references/notification-system.md")]),
    _tech("Job queue", "queue", ["celery", "sidekiq", "bull", "bullmq", "resque", "delayed_job", "oban", "asynq", "machinery", "temporalio"], [(INFRA, "references/distributed-message-queue.md"), (REALTIME, "references/notification-system.md")]),
    _tech("NATS / Pulsar", "queue", ["nats", "pulsar", "zeromq", "zmq"], [(INFRA, "references/distributed-message-queue.md")]),
    _tech("Cassandra / Scylla", "nosql", ["cassandra", "scylla", "scylladb", "gocql", "datastax"], [(INFRA, "references/key-value-store.md"), (REALTIME, "references/email-service.md")]),
    _tech("DynamoDB", "nosql", ["dynamodb", "dynamo"], [(INFRA, "references/key-value-store.md"), (REALTIME, "references/gaming-leaderboard.md")]),
    _tech("MongoDB", "nosql", ["mongodb", "mongo", "mongoose", "pymongo", "mongoid"], [(ADVISOR, "references/building-blocks.md"), (CONTENT, "references/search-autocomplete.md")]),
    _tech("Other NoSQL", "nosql", ["couchbase", "couchdb", "hbase", "bigtable", "cosmosdb", "firestore", "rocksdb", "leveldb", "etcd3"], [(INFRA, "references/key-value-store.md")]),
    _tech("Elasticsearch / OpenSearch", "search", ["elasticsearch", "opensearch", "elastic"], [(REALTIME, "references/email-service.md"), (CONTENT, "references/search-autocomplete.md")]),
    _tech("Other search", "search", ["meilisearch", "typesense", "solr", "algolia", "sphinx"], [(CONTENT, "references/search-autocomplete.md")]),
    _tech("Object storage", "object-storage", ["s3", "minio", "gcs", "google-cloud-storage", "azure-blob", "blob-storage", "cloudflare-r2"], [(INFRA, "references/object-storage.md"), (CONTENT, "references/cloud-file-storage.md")]),
    _tech("CDN", "cdn", ["cloudfront", "cloudflare", "fastly", "akamai", "cdn"], [(ADVISOR, "references/building-blocks.md"), (CONTENT, "references/video-streaming.md")]),
    _tech("Metrics", "metrics", ["prometheus", "grafana", "datadog", "statsd", "opentelemetry", "otel", "newrelic", "cloudwatch", "graphite", "telegraf"], [(INFRA, "references/metrics-monitoring.md")]),
    _tech("Time series", "metrics", ["influxdb", "timescaledb", "timescale", "victoriametrics", "opentsdb"], [(INFRA, "references/metrics-monitoring.md")]),
    _tech("Coordination", "coordination", ["zookeeper", "etcd", "consul"], [(INFRA, "references/distributed-message-queue.md"), (REALTIME, "references/chat-system.md")]),
    _tech("WebSocket", "websocket", ["socket.io", "socket.io-client", "ws", "websocket", "websockets", "starscream", "gorilla/websocket", "actioncable", "action_cable", "phoenix_channels", "sockjs", "centrifugo", "pusher", "ably"], [(REALTIME, "references/chat-system.md"), (GEO, "references/nearby-friends.md")]),
    _tech("Push notifications", "messaging-provider", ["apns", "apns2", "fcm", "firebase-admin", "firebase_admin", "onesignal", "expo-server-sdk"], [(REALTIME, "references/notification-system.md")]),
    _tech("SMS / email provider", "messaging-provider", ["twilio", "nexmo", "vonage", "sendgrid", "mailgun", "postmark", "ses", "mailchimp", "smtp", "nodemailer"], [(REALTIME, "references/notification-system.md"), (REALTIME, "references/email-service.md")]),
    _tech("Payments provider", "payments", ["stripe", "braintree", "adyen", "paypal", "squareup", "checkout.com", "tipalti", "razorpay"], [(TX, "references/payment-system.md"), (TX, "references/digital-wallet.md")]),
    _tech("Geospatial", "geo", ["geohash", "h3", "s2geometry", "postgis", "georedis", "geopy", "turf", "quadtree", "rtree"], [(GEO, "references/proximity-service.md"), (GEO, "references/maps-navigation.md")]),
    _tech("Rate limiting", "rate-limiting", ["express-rate-limit", "rate-limiter-flexible", "rack-attack", "rack::attack", "ratelimit", "throttled", "django-ratelimit", "limit_req", "slowapi", "bucket4j", "resilience4j"], [(INFRA, "references/rate-limiter.md")]),
    _tech("ID generation", "ids", ["snowflake", "uuid", "ulid", "ksuid", "nanoid", "cuid", "shortid", "hashids"], [(INFRA, "references/unique-id-generator.md"), (CONTENT, "references/url-shortener.md")]),
    _tech("Load balancer / proxy", "load-balancer", ["nginx", "haproxy", "envoy", "traefik", "caddy", "alb", "elb", "kong", "istio"], [(ADVISOR, "references/building-blocks.md"), (INFRA, "references/rate-limiter.md")]),
    _tech("Stream processing", "stream-processing", ["flink", "spark", "beam", "ksqldb", "storm", "faust", "bytewax"], [(REALTIME, "references/ad-click-aggregation.md"), (INFRA, "references/metrics-monitoring.md")]),
    _tech("Serverless", "compute", ["aws-lambda", "aws_lambda", "cloud-functions", "azure-functions", "cloudflare-workers"], [(REALTIME, "references/gaming-leaderboard.md")]),
    _tech("Consensus / replication", "coordination", ["raft", "paxos", "hashicorp/raft", "cockroachdb", "yugabyte", "tikv", "spanner"], [(TX, "references/digital-wallet.md"), (TX, "references/payment-system.md")]),
    _tech("Media processing", "media", ["ffmpeg", "hls.js", "mpeg-dash", "dash.js", "mediaconvert", "transcoder"], [(CONTENT, "references/video-streaming.md")]),
    _tech("Crawling", "crawling", ["scrapy", "puppeteer", "playwright", "colly", "robotparser", "robots.txt"], [(CONTENT, "references/web-crawler.md")]),
)

QUESTIONS: dict[str, list[str]] = {
    "relational": [
        "Which tables take the write load, what is the shard key if any, and how is failover tested? (Vol. 1 ch. 1)",
        "Which endpoints mutate inventory or money, and what idempotency key do they carry? (Vol. 2 ch. 7, ch. 11)",
    ],
    "cache": [
        "Is the in-memory store a cache, a lock, a queue or the source of truth, and what happens when it loses its data? (Vol. 1 ch. 1)",
        "What are the TTL, eviction policy and the write path that keeps it consistent with the database? (Vol. 1 ch. 1)",
    ],
    "queue": [
        "Which delivery semantics do consumers assume, and are they idempotent for duplicates? (Vol. 2 ch. 4)",
        "What is the partition key, is per-key ordering required, and who watches consumer lag? (Vol. 2 ch. 4)",
    ],
    "nosql": [
        "Which access patterns drove the partition key, and which queries cannot be served without a scan? (Vol. 1 ch. 6, Vol. 2 ch. 8)",
    ],
    "search": [
        "How is the index kept in sync with the primary store, and what happens when reindexing lags? (Vol. 2 ch. 8)",
    ],
    "object-storage": [
        "Are uploads multipart and resumable, and who garbage-collects abandoned parts? (Vol. 2 ch. 9)",
    ],
    "cdn": [
        "What is the cache TTL, how are stale files invalidated, and what does the client do when the CDN is down? (Vol. 1 ch. 1)",
    ],
    "metrics": [
        "Which alerts page a human, and what is the label cardinality of the busiest series? (Vol. 2 ch. 5)",
    ],
    "websocket": [
        "How do clients rediscover a server after a deploy, and how is presence decided (heartbeat interval, offline threshold)? (Vol. 1 ch. 12)",
    ],
    "messaging-provider": [
        "How are duplicate sends prevented on retry, and can users opt out per channel? (Vol. 1 ch. 10)",
    ],
    "payments": [
        "Which idempotency key reaches the provider, and how is the nightly reconciliation done? (Vol. 2 ch. 11)",
    ],
    "geo": [
        "Which index answers the radius query, and are neighbouring cells included? (Vol. 2 ch. 1)",
    ],
    "rate-limiting": [
        "Which algorithm, where do the counters live, and is the counter update atomic across instances? (Vol. 1 ch. 4)",
    ],
    "ids": [
        "Are IDs sortable by time, and do they leak sequence to the outside? (Vol. 1 ch. 7, ch. 8)",
    ],
    "load-balancer": [
        "Is the web tier stateless, or does anything depend on sticky sessions? (Vol. 1 ch. 1)",
    ],
    "stream-processing": [
        "Event time or processing time, and how long is the watermark? (Vol. 2 ch. 6)",
    ],
    "coordination": [
        "What is stored there, and how many nodes does the quorum need? (Vol. 2 ch. 4)",
    ],
}


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    pattern: re.Pattern[str]
    severity: str
    source: str
    advice: str
    references: tuple[tuple[str, str], ...]
    suffixes: frozenset[str] = frozenset(CODE_SUFFIXES)
    negative: re.Pattern[str] | None = None


MONEY_WORDS = r"(?:amount|price|balance|fee|total|cost|payout|refund|salary|wage)"

RULES: tuple[Rule, ...] = (
    Rule(
        "SD001",
        "Money stored in a floating-point type",
        re.compile(
            rf"\b\w*{MONEY_WORDS}\w*\s*:\s*(?:float|double|Float|Double|number|f32|f64|CGFloat)\b"
            rf"|\b(?:float|double|Float|Double|f32|f64|CGFloat)\s+\w*{MONEY_WORDS}\w*\b"
            rf"|\bparseFloat\(\s*\w*{MONEY_WORDS}",
            re.I,
        ),
        "warning",
        "Vol. 2 ch. 11 › APIs for payment service",
        "Represent money as a string or an integer in minor units; floating point loses cents.",
        ((TX, "references/payment-system.md"),),
    ),
    Rule(
        "SD002",
        "Pessimistic lock (SELECT ... FOR UPDATE)",
        re.compile(r"\bFOR\s+UPDATE\b", re.I),
        "info",
        "Vol. 2 ch. 7 › Concurrency issues",
        "Fine under heavy contention on few rows; long transactions or wide selects stall everyone. Consider optimistic locking or a constraint when conflicts are rare.",
        ((TX, "references/hotel-reservation.md"),),
    ),
    Rule(
        "SD003",
        "Modulo hashing across a server or shard pool",
        re.compile(
            r"%\s*(?:len\(\s*\w*(?:server|node|shard|replica|worker)s?\w*\s*\)"
            r"|(?:num|n|count)_?(?:of_?)?(?:server|node|shard|replica|worker)s?\b"
            r"|\w*(?:server|node|shard|replica|worker)s?\.(?:length|count|size)\b"
            r"|(?:server|node|shard|replica|worker)_?count\b)",
            re.I,
        ),
        "warning",
        "Vol. 1 ch. 5 › The rehashing problem",
        "Adding or removing a server remaps almost every key. Use consistent hashing with virtual nodes.",
        ((INFRA, "references/consistent-hashing.md"),),
    ),
    Rule(
        "SD004",
        "Money column declared as FLOAT, DOUBLE or REAL",
        re.compile(rf"\b\w*{MONEY_WORDS}\w*\s+(?:FLOAT|DOUBLE(?:\s+PRECISION)?|REAL)\b", re.I),
        "warning",
        "Vol. 2 ch. 11 › APIs for payment service",
        "Use DECIMAL/NUMERIC or an integer minor-unit column.",
        ((TX, "references/payment-system.md"),),
        frozenset({".sql", ".prisma", ".rb", ".py", ".ts", ".js", ".go", ".kt", ".java"}),
    ),
    Rule(
        "SD005",
        "Timestamp-based version for optimistic locking",
        re.compile(r"\b(?:updated_at|modified_at|last_modified)\s*(?:=|==|<>|!=)\s*(?:\?|:\w+|\$\d|%s|\{)", re.I),
        "info",
        "Vol. 2 ch. 7 › Optimistic locking",
        "Version numbers are recommended over timestamps because server clocks drift.",
        ((TX, "references/hotel-reservation.md"),),
    ),
    Rule(
        "SD006",
        "Unbounded Redis KEYS scan",
        re.compile(r"(?:\.keys\(\s*['\"][^'\"]*\*|\bKEYS\s+['\"]?[\w:]*\*)", re.I),
        "info",
        "inference (Redis documentation; the chapters use SCAN-free access by key)",
        "KEYS blocks the server; use SCAN or maintain an index set.",
        ((INFRA, "references/rate-limiter.md"),),
    ),
    Rule(
        "SD007",
        "Rank computed by counting rows with a higher score",
        re.compile(r"COUNT\s*\(\s*\*?\s*\)[^;]{0,80}\bscore\s*>=?", re.I),
        "warning",
        "Vol. 2 ch. 10 › Relational database solution",
        "This scans the table per request. A Redis sorted set answers ZREVRANK in O(log N).",
        ((REALTIME, "references/gaming-leaderboard.md"),),
    ),
)


@dataclass
class Evidence:
    file: str
    line: int
    text: str


@dataclass
class Inventory:
    name: str
    category: str
    evidence: list[Evidence] = field(default_factory=list)
    references: tuple[tuple[str, str], ...] = ()


def iter_files(root: Path, include_dependencies: bool) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts[:-1]
        if any(part in SKIP_ALWAYS or part.startswith(".") for part in relative_parts):
            continue
        if not include_dependencies and any(part in DEPENDENCY_DIRS for part in relative_parts):
            continue
        yield path


def classify(path: Path) -> str | None:
    name = path.name
    if name in MANIFEST_NAMES or any(p.search(name) for p in INFRA_PATTERNS):
        return "manifest"
    if path.suffix in YAML_SUFFIXES:
        return "manifest"
    if path.suffix in CODE_SUFFIXES:
        return "code"
    return None


def read_lines(path: Path) -> list[str]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return []
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def scan(root: Path, include_dependencies: bool = False) -> dict[str, Any]:
    root = root.resolve()
    inventory: dict[str, Inventory] = {}
    findings: list[dict[str, Any]] = []
    files_scanned = 0

    for path in iter_files(root, include_dependencies):
        kind = classify(path)
        if kind is None:
            continue
        lines = read_lines(path)
        if not lines:
            continue
        files_scanned += 1
        relative = path.relative_to(root).as_posix()
        for number, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
            if kind == "manifest" or IMPORT_LINE.search(line):
                for tech in TECHNOLOGIES:
                    if tech.pattern.search(line):
                        item = inventory.setdefault(tech.name, Inventory(tech.name, tech.category, [], tech.references))
                        if len(item.evidence) < 5:
                            item.evidence.append(Evidence(relative, number, stripped[:160]))
            if kind == "code":
                for rule in RULES:
                    if path.suffix not in rule.suffixes:
                        continue
                    if rule.pattern.search(line) and not (rule.negative and rule.negative.search(line)):
                        findings.append(
                            {
                                "id": rule.id,
                                "title": rule.title,
                                "severity": rule.severity,
                                "file": relative,
                                "line": number,
                                "snippet": stripped[:160],
                                "source": rule.source,
                                "advice": rule.advice,
                                "references": [{"skill": s, "file": f} for s, f in rule.references],
                            }
                        )

    categories = sorted({item.category for item in inventory.values()})
    references: dict[str, list[str]] = {}
    for item in inventory.values():
        for skill, file in item.references:
            references.setdefault(skill, [])
            if file not in references[skill]:
                references[skill].append(file)
    for finding in findings:
        for ref in finding["references"]:
            references.setdefault(ref["skill"], [])
            if ref["file"] not in references[ref["skill"]]:
                references[ref["skill"]].append(ref["file"])
    questions = [q for category in categories for q in QUESTIONS.get(category, [])]

    return {
        "scanner": {"name": "arch_scan", "version": VERSION},
        "root": str(root),
        "files_scanned": files_scanned,
        "inventory": [
            {
                "name": item.name,
                "category": item.category,
                "evidence": [{"file": e.file, "line": e.line, "text": e.text} for e in item.evidence],
                "references": [{"skill": s, "file": f} for s, f in item.references],
            }
            for item in sorted(inventory.values(), key=lambda i: (i.category, i.name))
        ],
        "categories": categories,
        "findings": findings,
        "questions": questions,
        "references": {skill: sorted(files) for skill, files in sorted(references.items())},
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [f"# Architecture scan — {result['root']}", "", f"{result['files_scanned']} files scanned.", ""]
    lines.append("## Inventory")
    lines.append("")
    if result["inventory"]:
        lines.append("| Category | Technology | Evidence |")
        lines.append("| --- | --- | --- |")
        for item in result["inventory"]:
            first = item["evidence"][0]
            more = f" (+{len(item['evidence']) - 1})" if len(item["evidence"]) > 1 else ""
            lines.append(f"| {item['category']} | {item['name']} | `{first['file']}:{first['line']}`{more} |")
    else:
        lines.append("Nothing recognised. Check for a manifest or infrastructure file the scanner does not know.")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    if result["findings"]:
        lines.append("| ID | Severity | Where | Title | Source |")
        lines.append("| --- | --- | --- | --- | --- |")
        for f in result["findings"]:
            lines.append(f"| {f['id']} | {f['severity']} | `{f['file']}:{f['line']}` | {f['title']} | {f['source']} |")
    else:
        lines.append("No rule matched. That is not a clean bill of health; the rules are few and the manual checklist still applies.")
    lines.append("")
    lines.append("## Questions for the owners")
    lines.append("")
    lines.extend(f"- {q}" for q in result["questions"]) if result["questions"] else lines.append("- None generated.")
    lines.append("")
    lines.append("## References to load")
    lines.append("")
    for skill, files in result["references"].items():
        lines.append(f"- `{skill}`: " + ", ".join(f"`{f}`" for f in files))
    if not result["references"]:
        lines.append("- `system-design-advisor`: `references/building-blocks.md`")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", help="Project directory to scan")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--include-dependencies", action="store_true", help="Also scan node_modules, vendor, Pods and similar")
    args = parser.parse_args(argv)
    root = Path(args.root)
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    result = scan(root, include_dependencies=args.include_dependencies)
    print(json.dumps(result, indent=2) if args.format == "json" else render_markdown(result), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
