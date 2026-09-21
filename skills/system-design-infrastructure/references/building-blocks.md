# Building blocks: scale from zero to millions of users

Condensed from Vol. 1 ch. 1,
followed by a cross-chapter index of the patterns the case studies reuse.
Load this when a design needs the standard tiers
or when someone asks how to scale an existing service.

## The scaling ladder

Each rung fixes the bottleneck the previous one exposed.

1. **Single server.**
   Web app, database and cache on one machine;
   DNS resolves the domain, clients speak HTTP and get HTML or JSON.
2. **Separate the database.**
   Web tier and data tier scale independently.
   Relational for structured data and joins;
   NoSQL (key-value, document, column, graph) when latency must be very low,
   the data is unstructured, it only needs serialising, or the volume is massive.
3. **Vertical scaling** has a hard ceiling and no redundancy.
   **Horizontal scaling** needs a load balancer.
4. **Load balancer.**
   Private IPs behind it; a dead server drops out of rotation;
   add servers for spikes.
5. **Database replication.**
   One master takes writes, slaves serve reads (reads dominate, so more slaves).
   A slave failure redirects reads; a master failure promotes a slave,
   and the promoted slave may be behind, so recovery scripts fix the gap.
6. **Cache tier.**
   For data read often and written rarely.
   Decide expiration, consistency with the store (they are not one transaction),
   eviction (LRU is the default), and avoid a single cache node.
7. **CDN** for static assets, geographically close to users.
   Watch cost, TTL, fallback to origin when the CDN is down, and invalidation.
8. **Stateless web tier.**
   Session state moves to a shared store (NoSQL is common);
   any server can serve any request, so auto-scaling works.
9. **Multiple data centers.**
   GeoDNS routes users to the nearest; data replicates between centers;
   deployments must be automated so all centers stay identical.
10. **Message queue** decouples producers from consumers
    and buffers bursts; each side scales on its own.
11. **Logging, metrics, automation.**
    Errors, host and aggregated metrics, business metrics; CI/CD.
12. **Database sharding.**
    Rows split by a shard key (`user_id % n`);
    same schema per shard, different data.
    Problems: resharding on growth or uneven fill (consistent hashing helps),
    the celebrity problem (a hot shard; give the celebrity its own),
    joins across shards (denormalise).

Takeaways: stateless web tier, redundancy at every tier,
cache as much as you can, multiple data centers, CDN for static content,
shard the data tier, split into services, monitor and automate.

## Pattern index

The same handful of mechanisms recur across the 28 chapters.
When a design needs one, load the chapter that treats it most fully.

| Pattern | Where it is developed | Also used in |
| --- | --- | --- |
| Consistent hashing, virtual nodes | Vol. 1 ch. 5 | KV store (ch. 6), crawler (ch. 9), nearby friends, metrics collectors, ad aggregation, object storage |
| Quorum reads and writes, vector clocks, gossip, hinted handoff, Merkle trees | Vol. 1 ch. 6 | |
| Snowflake IDs | Vol. 1 ch. 7 | URL shortener, chat message IDs |
| Idempotency key with a unique constraint | Vol. 2 ch. 7 (reservation), ch. 11 (payment) | wallet, notification dedup |
| Optimistic vs pessimistic locking, DB constraints | Vol. 2 ch. 7 | |
| Fan-out on write vs on read, hybrid for celebrities | Vol. 1 ch. 11 | chat group inboxes, presence, nearby friends |
| WebSocket vs long polling vs polling | Vol. 1 ch. 12 | Drive notifications, Maps delivery, email real-time servers, nearby friends |
| Heartbeat and presence | Vol. 1 ch. 12 | KV store failure detection, MQ consumer groups, placement service |
| Trie with cached top-k | Vol. 1 ch. 13 | |
| DAG task pipeline with resource manager | Vol. 1 ch. 14 | |
| Block-level delta sync, dedup by hash | Vol. 1 ch. 15 | |
| Geohash, quadtree, S2 | Vol. 2 ch. 1 | nearby friends, Maps tiles |
| Redis pub/sub as fan-out bus | Vol. 2 ch. 2 | |
| Tiles at multiple zoom levels | Vol. 2 ch. 3 | |
| Write-ahead log, segments, sequential disk I/O | Vol. 2 ch. 4 | object storage data nodes, wallet event store |
| Pull vs push (consumers, metrics collection) | Vol. 2 ch. 4, ch. 5 | |
| At-most / at-least / exactly-once | Vol. 2 ch. 4 | ad aggregation, payments |
| Time-series storage, downsampling | Vol. 2 ch. 5 | |
| Event time vs processing time, watermarks, windows | Vol. 2 ch. 6 | |
| Lambda vs kappa architecture | Vol. 2 ch. 6 | |
| End-of-day reconciliation | Vol. 2 ch. 6, ch. 11 | |
| Replication vs erasure coding, checksums | Vol. 2 ch. 9 | |
| Sorted set / skip list leaderboard | Vol. 2 ch. 10 | |
| Double-entry ledger | Vol. 2 ch. 11 | wallet |
| 2PC, Try-Confirm/Cancel, Saga | Vol. 2 ch. 12 | reservation across services |
| Event sourcing, CQRS, Raft replication | Vol. 2 ch. 12 | stock exchange |
| Sequencer, mmap event bus, ring buffer, application loop | Vol. 2 ch. 13 | |
| LSM trees | Vol. 2 ch. 8 (search), ch. 12 (RocksDB) | KV store SSTables |

## Choosing a store

| Need | Reach for | Chapter |
| --- | --- | --- |
| ACID, low write volume, clear relations | Relational (MySQL, PostgreSQL) | reservation, payment |
| Massive write volume, simple keys | Cassandra-style wide column | location history, ad clicks, alerts, email metadata |
| Sub-millisecond reads, sorted structures, TTL | Redis | leaderboard, location cache, rate limiter counters, geohash cache |
| Time series | InfluxDB, Prometheus | metrics |
| Full-text search | Elasticsearch | email |
| Large blobs | Object storage (S3) | video, Drive blocks, routing tiles, attachments |
| Coordination, small consistent config | ZooKeeper, etcd | MQ metadata, service discovery, Redis cluster map |
| Streams with retention | Kafka | almost every Vol. 2 design |
