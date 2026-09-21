# Metrics monitoring and alerting system

Source: Vol. 2 ch. 5 (upstream `20. Metrics Monitoring and Alerting System`).

## Scope

Internal use; operational metrics (CPU, memory, disk, requests per second,
queue depth), not business metrics, logs or tracing.
100 million DAU, 1,000 pools × 100 machines × ~100 metrics ≈ 10 million series.
Retention one year: raw for 7 days, 1-minute rollups for 30 days,
1-hour rollups for a year.
Alerts to email, phone, PagerDuty, webhooks.
Scalable, low query latency, reliable (never miss a critical alert), flexible.

## Data model

A time series = metric name + labels + (timestamp, value) points,
written in line protocol (`cpu.load host=i631,region=us-west 1613707265 50`).
Writes are heavy and steady; reads are spiky (dashboards during incidents).

General-purpose and NoSQL databases can be made to work but poorly.
Use a **time-series database**: InfluxDB, Prometheus (in-memory cache + disk),
OpenTSDB on HBase, Amazon Timestream, Twitter's MetricsDB.
InfluxDB sustains 250 k writes/s on 8 cores and 32 GB.
Keep **label cardinality low**; indexes are per label.

## High-level design

Metrics sources → **metrics collector** → time-series DB →
**query service** → alerting system and visualisation (Grafana).

## Collection: pull vs push

- **Pull**: the collector scrapes `/metrics` from a service list held in
  ZooKeeper or etcd (service discovery); several collectors share the hosts
  via a consistent hash ring so no host is scraped twice.
- **Push**: an agent on each host aggregates locally and pushes;
  the collector sits behind a load balancer in an auto-scaling group.

| | Pull | Push |
| --- | --- | --- |
| Debugging | Hit `/metrics` yourself | Silence could be the network |
| Health check | No response = host down | Ambiguous |
| Short-lived jobs | Miss them (push gateway fixes) | Natural |
| Firewalls, multi-DC | Every target must be reachable | Any host can push |
| Transport | TCP | Often UDP, lower latency |
| Authenticity | Targets are configured | Anyone can push; allow-list or authenticate |

Prometheus pulls; CloudWatch and Graphite push.
A large organisation ends up supporting both.

## Transmission pipeline

Collectors → **Kafka** → stream processor (Flink, Spark, Storm) → TSDB.
Kafka buffers when the database is down, decouples collection from processing,
and can partition by metric name (further by labels, with priorities).
The cost is operating Kafka; Facebook's Gorilla is the in-memory alternative.

Where to aggregate:
in the agent (simple counters),
in the pipeline (Flink; smaller writes, raw precision lost),
or at query time (no loss, slow queries).

## Query and storage

A query service decouples clients from the database and can cache;
often unnecessary because Grafana and alert managers integrate directly.
Time-series query languages (Flux, PromQL) replace long SQL window queries.

Facebook found 85 % of queries hit the last 26 hours;
pick a database that caches recent data.
Encode timestamps as deltas and compress values;
downsample by the retention policy above;
cold storage for old data.

## Alerting

Rules in YAML (`expr: up == 0`, `for: 5m`, severity labels) loaded into a cache.
The alert manager evaluates rules on a schedule against the query service,
filters, merges and deduplicates, enforces access control, retries;
alert state lives in a key-value store (Cassandra);
events go to Kafka; consumers send email, SMS, PagerDuty, webhooks.

## Visualisation

Grafana. Building your own is rarely justified, and the same holds for alerting.
