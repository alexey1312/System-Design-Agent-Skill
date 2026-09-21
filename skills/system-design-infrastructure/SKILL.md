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
The orchestrator (`system-design-interview`) owns scope, estimates and the
answer format; this skill owns the mechanisms.

| System | Reference | The deep dive the interviewer expects |
| --- | --- | --- |
| Rate limiter | `references/rate-limiter.md` | Algorithm choice; atomic counters in Redis; 429 with headers |
| Consistent hashing | `references/consistent-hashing.md` | Ring, virtual nodes, which keys move |
| Key-value store | `references/key-value-store.md` | CAP choice; N/W/R quorum; vector clocks; failure handling |
| Unique ID generator | `references/unique-id-generator.md` | Snowflake bit layout; clock drift |
| Distributed message queue | `references/distributed-message-queue.md` | WAL segments; pull consumers; ISR and ACK levels; rebalancing |
| Object storage | `references/object-storage.md` | Metadata vs data path; replication vs erasure coding; multipart |
| Metrics monitoring | `references/metrics-monitoring.md` | Time-series model; pull vs push; Kafka buffer; downsampling |

## How to use

1. Run the orchestrator's scope and estimate steps first;
   these designs are parameterised by QPS, key size and retention.
2. Load the one reference the request names.
   Load a second only when the design composes them
   (the key-value store uses consistent hashing; the metrics pipeline uses
   the message queue).
3. Present the chapter's progression: naive approach, its failure, the fix.
   Interviewers grade the reasoning, not the final diagram.
4. Cite the chapter (`references/sources.md`) and label your own additions.

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

Shared references: `references/estimation-cheatsheet.md`,
`references/building-blocks.md`, `references/design-format.md`;
calculator: `scripts/estimate.py`.
