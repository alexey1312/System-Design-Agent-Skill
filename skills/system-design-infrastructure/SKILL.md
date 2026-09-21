---
name: system-design-infrastructure
description: >-
  Design the infrastructure components the System Design Interview books
  cover: a rate limiter (token bucket, leaky bucket, sliding windows),
  consistent hashing with virtual nodes, a Dynamo-style key-value store
  (quorum, vector clocks, gossip, hinted handoff, Merkle trees), a Snowflake
  unique ID generator, a Kafka-style distributed message queue (partitions,
  consumer groups, in-sync replicas, delivery semantics), S3-like object
  storage (data nodes, erasure coding, multipart upload) and a metrics
  monitoring and alerting system (time-series database, pull vs push, Kafka
  pipeline). Use when asked to design, compare, explain or review any of
  these, or when another design needs one of them as a building block.
---

# Infrastructure components

Seven case studies that other designs lean on.
The advisor (`system-design-advisor`) owns the scan, the numbers and the
answer format; this skill owns the mechanisms.

| System | Reference | Where the risk is |
| --- | --- | --- |
| Rate limiter | `references/rate-limiter.md` | Algorithm choice; atomic counters in Redis; 429 with headers |
| Consistent hashing | `references/consistent-hashing.md` | Ring, virtual nodes, which keys move |
| Key-value store | `references/key-value-store.md` | CAP choice; N/W/R quorum; vector clocks; failure handling |
| Unique ID generator | `references/unique-id-generator.md` | Snowflake bit layout; clock drift |
| Distributed message queue | `references/distributed-message-queue.md` | WAL segments; pull consumers; ISR and ACK levels; rebalancing |
| Object storage | `references/object-storage.md` | Metadata vs data path; replication vs erasure coding; multipart |
| Metrics monitoring | `references/metrics-monitoring.md` | Time-series model; pull vs push; Kafka buffer; downsampling |

## How to use

1. On a real project, run `scripts/arch_scan.py` first;
   its inventory says which of these seven components the project already
   runs and which reference to load.
   For a new design, run the advisor's scope and estimate steps;
   these components are parameterised by QPS, key size and retention.
2. Load the one reference the request names.
   Load a second only when the design composes them
   (the key-value store uses consistent hashing; the metrics pipeline uses
   the message queue).
3. Present the chapter's progression: naive approach, its failure, the fix.
   Reviewers and interviewers grade the reasoning, not the final diagram.
4. Cite the chapter (`references/sources.md`) and label your own additions.

## On a real project

- **Rate limiter**: find the middleware or gateway config;
  which algorithm, where the counters live, whether the update is atomic,
  what the client receives (429, headers).
  Scan finding `SD006` marks `KEYS *` on the same Redis.
- **Consistent hashing**: scan finding `SD003` marks `hash % N` placement;
  read how the pool is resized and what happens to cached keys.
- **Key-value store**: find the replication factor and the consistency
  level per query; ask which writes may be lost during a partition.
- **Unique IDs**: find the generator; check time-sortability, the epoch,
  and what happens on clock drift.
- **Message queue**: find producer acks, consumer commit order, partition
  key, consumer-group size versus partitions, retention, and lag alerts.
- **Object storage**: find multipart handling, checksums, lifecycle rules
  and who deletes orphaned parts.
- **Metrics**: find the scrape or push path, label cardinality, retention
  and downsampling, and which alerts page a human.

## Cross-cutting rules

- **Counters and coordination need a store with atomic operations**
  (Redis Lua scripts, ZooKeeper): say which operation is atomic and why the
  naive read-modify-write races.
- **Quorums are a dial, not a setting**: state N, W and R and what each
  choice buys (`key-value-store.md`).
- **Sequential disk access is fast**; the queue and the object store both
  rest on append-only files.
  Do not reach for a database when the access pattern is a log.
- **Delivery semantics follow from the order of process and commit**;
  spell the order out whenever you promise at-least-once or exactly-once.
- **Replication factor and failure domains** decide durability;
  quote the chapter's figures (three replicas across domains reach six nines
  at a 0.81 % annual disk failure rate; 8+4 erasure coding reaches eleven at
  half the overhead).
- Every component here is a candidate single point of failure in someone
  else's design: the ticket server, one Redis node, the coordinator.
  Name the redundancy.

## Pitfalls

- Fixed-window counters let 2× the quota through at window edges;
  say so before proposing them.
- `hash(key) % N` is not consistent hashing.
- A CA system cannot exist across a network partition.
- Push-based consumers overwhelm slow consumers; the chapters choose pull.
- Sharding the object table by bucket alone creates hot shards.
- Label cardinality is what kills a time-series database.

Shared references: `references/review-checklist.md`,
`references/estimation-cheatsheet.md`, `references/building-blocks.md`,
`references/design-format.md`;
scripts: `scripts/arch_scan.py` (read-only project scan),
`scripts/estimate.py` (calculator).
