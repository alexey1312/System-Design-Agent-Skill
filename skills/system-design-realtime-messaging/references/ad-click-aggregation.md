# Ad click event aggregation

Source: Vol. 2 ch. 6 (upstream `21. Ad Click Event Aggregation`).
A stream-processing design whose output feeds real-time bidding and billing.

## Scope and numbers

1 billion clicks per day, 2 million ads, 30 % yearly growth.
Queries: clicks for `ad_id` in the last *M* minutes;
top 100 ads in the last minute; filter by `ip`, `user_id`, `country`.
Late and duplicate events happen; parts of the system fail.
End-to-end latency of a few minutes is fine (billing), RTB itself is sub-second.
Correctness matters: this is money.
10,000 QPS average, 50,000 peak; 0.1 KB per event → 100 GB per day, 3 TB per month.

## API

- `GET /v1/ads/{ad_id}/aggregated_count?from&to&filter` → `{ad_id, count}`.
- `GET /v1/ads/popular_ads?count&window&filter` → list of `ad_id`.

## Data model

Raw events: `ad_id, click_timestamp, user_id, ip, country`.
Aggregated: `ad_id, click_minute, filter_id, count`
plus `most_clicked_ads(window_size, update_time_minute, ad_ids)`.
`filter_id` points at a predefined filter (region, IP, user).

Keep both: raw for backfill and debugging (cold storage after a while),
aggregated for fast queries.
Raw is write-heavy (Cassandra, InfluxDB, or S3 with Parquet/ORC);
aggregated is read- and write-heavy (Cassandra again).

## High-level design

Log watcher → **Kafka** (raw) → **aggregation service** → **Kafka** (aggregated)
→ database writer → aggregation DB → query service → dashboards.
The second queue exists for end-to-end exactly-once (atomic commit).

Aggregation as **MapReduce** nodes in a DAG:
map (read, filter, transform, partition by `ad_id`),
aggregate (count per `ad_id` per minute in memory; a heap for top-N),
reduce (merge to the final result).
Pre-aggregate per dimension for filters: a **star schema** with dimension columns;
simple, reuses the service, fast, but multiplies records with each filter.

## Deep dive

### Streaming vs batching

Online services respond to users; batch systems process bounded input
(MapReduce); streaming systems process unbounded input (Flink).
**Lambda** runs batch and stream paths with two codebases;
**kappa** uses one stream engine for both, and this design is kappa:
recalculation replays raw data through a dedicated aggregation service
into the same aggregated queue.

### Time

Event time is accurate but late events must be handled and clients can lie;
processing time is reliable but wrong for late events.
Use event time with a **watermark**: extend each window by a grace period.
Short watermark: lower latency, more missed events; long: the reverse.
Some events are always missed; end-of-day reconciliation fixes them.

### Windows

Tumbling (fixed) for per-minute counts; sliding for top-N in the last *M* minutes;
hopping and session windows exist.

### Delivery and deduplication

At-least-once is not enough for billing; aim for exactly-once.
Duplicates come from client retries (a risk engine handles malice)
and from a node crashing after sending downstream but before committing its offset.
Storing the offset in HDFS before sending risks losing the result;
the safe path commits the offset and the downstream write atomically
(a distributed transaction), or makes the downstream write idempotent.

### Scaling

Kafka: producers unlimited; more consumers need enough partitions up front;
rebalance off-peak; partition topics by geography.
Aggregation: more nodes, multi-threading, or a resource manager (YARN).
Database: Cassandra rebalances with consistent hashing.
**Hotspots**: an aggregation node asks the resource manager for extra nodes,
splits its events among them, and merges; or use global–local aggregation
and split-distinct aggregation.

### Fault tolerance

In-memory state is lost on crash; restart from the committed Kafka offset
plus a periodic snapshot of the running top-N.

### Monitoring and correctness

Latency by event timestamps, Kafka records lag, node resources.
A nightly **reconciliation** batch recomputes from raw data and compares.

### Alternative

Hive for storage with Elasticsearch for queries;
ClickHouse or Druid for OLAP aggregation.

## Wrap-up

Prior knowledge of Kafka, Spark and Flink makes this design easier to explain.
