# Design checks

Every check the skills perform on a real project, with its source.
Automated checks live in `scripts/arch_scan.py`;
manual checks are the review checklist every skill carries
(`references/review-checklist.md`).

## Automated: inventory

`arch_scan.py` reads dependency manifests, Docker Compose and Kubernetes
files, Terraform, `.env` files and import lines,
and reports every technology it recognises with the file and line.
Each hit maps to the references worth loading and to questions for the owners.

| Category | Recognised (examples) | Leads to |
| --- | --- | --- |
| relational | PostgreSQL, MySQL, SQLite, ORMs | `building-blocks.md`, `hotel-reservation.md` |
| cache | Redis, Memcached | `building-blocks.md`, `rate-limiter.md`, `gaming-leaderboard.md`, `nearby-friends.md` |
| queue | Kafka, RabbitMQ, SQS/SNS/Pub/Sub, Celery, Sidekiq, BullMQ, NATS, Pulsar | `distributed-message-queue.md`, `notification-system.md`, `ad-click-aggregation.md` |
| nosql | Cassandra, Scylla, DynamoDB, MongoDB, HBase, RocksDB | `key-value-store.md`, `email-service.md`, `gaming-leaderboard.md` |
| search | Elasticsearch, OpenSearch, Meilisearch, Typesense, Solr | `email-service.md`, `search-autocomplete.md` |
| object-storage | S3, MinIO, GCS, Azure Blob | `object-storage.md`, `cloud-file-storage.md` |
| cdn | CloudFront, Cloudflare, Fastly, Akamai | `building-blocks.md`, `video-streaming.md` |
| metrics | Prometheus, Grafana, Datadog, OpenTelemetry, InfluxDB, Timescale | `metrics-monitoring.md` |
| coordination | ZooKeeper, etcd, Consul, Raft libraries, CockroachDB | `distributed-message-queue.md`, `digital-wallet.md` |
| websocket | socket.io, ws, Action Cable, Phoenix Channels, Centrifugo | `chat-system.md`, `nearby-friends.md` |
| messaging-provider | APNS, FCM, Twilio, SendGrid, SES | `notification-system.md`, `email-service.md` |
| payments | Stripe, Braintree, Adyen, PayPal | `payment-system.md`, `digital-wallet.md` |
| geo | geohash, H3, S2, PostGIS, quadtree | `proximity-service.md`, `maps-navigation.md` |
| rate-limiting | express-rate-limit, rack-attack, bucket4j, nginx `limit_req` | `rate-limiter.md` |
| ids | Snowflake, UUID, ULID, KSUID, Hashids | `unique-id-generator.md`, `url-shortener.md` |
| load-balancer | nginx, HAProxy, Envoy, Traefik, ALB | `building-blocks.md` |
| stream-processing | Flink, Spark, Beam, ksqlDB | `ad-click-aggregation.md` |

## Automated: findings

| ID | Severity | Finding | Source | Advice |
| --- | --- | --- | --- | --- |
| SD001 | warning | Money in a floating-point type annotation or `parseFloat` | Vol. 2 ch. 11 | String or integer minor units |
| SD002 | info | `SELECT … FOR UPDATE` | Vol. 2 ch. 7 | Justify under contention; consider optimistic locking or a constraint |
| SD003 | warning | `hash % number_of_servers` placement | Vol. 1 ch. 5 | Consistent hashing with virtual nodes |
| SD004 | warning | Money column declared FLOAT, DOUBLE or REAL | Vol. 2 ch. 11 | DECIMAL or integer minor units |
| SD005 | info | Optimistic lock compares `updated_at` | Vol. 2 ch. 7 | Version numbers, not timestamps |
| SD006 | info | Redis `KEYS pattern*` | inference | SCAN or an index set |
| SD007 | warning | Rank by `COUNT(*) … score >=` | Vol. 2 ch. 10 | Sorted set, ZREVRANK |

Every finding is a heuristic on one line of text;
comments are not stripped and the surrounding code must be read before
the finding becomes a recommendation.

## Manual: review checklist

`references/review-checklist.md` holds 45 checks in nine groups
(availability, data stores, caches and CDN, queues, correctness of money
and inventory, real-time, rate limiting and IDs, streams, operations),
each with the chapter it comes from.
