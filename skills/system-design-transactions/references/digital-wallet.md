# Digital wallet

Source: Vol. 2 ch. 12 (upstream `27.  Digital Wallet`).

## Scope and numbers

Balance transfers between wallets; 1 million TPS; 99.99 % availability;
transactional guarantees; **reproducibility** (replay history to prove
correctness, not just detect drift); no foreign exchange.
A cloud relational node does ~1,000 TPS; a transfer has two legs, so 2 M TPS
means 2,000 nodes at 1,000 TPS or 200 at 10,000: raise per-node TPS.

## API

`POST /v1/wallet/balance_transfer` with `from_account, to_account,
amount (string), currency, transaction_id` (idempotency key) → `{status, transaction_id}`.

## Design evolution

### In-memory sharding

`map<user_id, balance>` in Redis, partitioned by `hash(account) % n`
with the partition count and node list in ZooKeeper;
a stateless wallet service does the transfers.
Scales, but a transfer across two shards is not atomic and Redis is not durable.

### Two-phase commit

Sharded relational databases with a coordinator:
prepare on all shards, then commit or abort everywhere.
Locks are held across the round trips (slow) and the coordinator is a single
point of failure.

### Try-Confirm/Cancel

Two independent local transactions instead of one distributed one:

| Phase | Account A | Account C |
| --- | --- | --- |
| Try | −$1 | nothing |
| Confirm | nothing | +$1 |
| Cancel | +$1 | nothing |

Database-agnostic; the complexity moves into application logic.
The coordinator keeps a **phase status table** in each shard
(transaction ID and content, try status, which second phase, its status,
out-of-order flag) so it can recover after a crash.
Accounts are briefly inconsistent while in flight; that is safe only if
deductions always run before additions (never `−1 / +1` in the same try phase,
which would need 2PC anyway).
Out-of-order delivery (cancel arriving before try) is handled by the flag:
a try that finds it set fails.

### Saga

Ordered local transactions; on failure, compensate backwards.
Choreography (services react to events) scatters the logic;
**orchestration** (one coordinator) is preferred for wallets.

| | TC/C | Saga |
| --- | --- | --- |
| Compensation | Cancel phase | Rollback phase |
| Coordination | Central | Central (orchestration) |
| Order | Any; parallel | Linear |
| Partial inconsistency visible | Yes | Yes |

Parallel TC/C wins on latency; both need audit and replay.

### Event sourcing

Commands (intent; may fail; ordered in a FIFO queue such as Kafka) →
validated by a deterministic **state machine** → **events** (facts; immutable;
ordered) → applied to **state** (balances).
Replaying events from the start reconstructs any historical balance,
verifies correctness, and lets two code versions be compared on the same history.
**CQRS**: read-only state machines answer balance queries from the event log.

## Deep dive: performance and reliability

- Keep commands and events on local disk via **mmap** (append-only, page-cached),
  not a remote queue.
- State in a local **RocksDB** (LSM tree, write-optimised) or SQLite.
- Periodic **snapshots** to HDFS so replay need not start from zero.
- Only the **event list** needs replication (state and snapshots derive from it;
  commands are non-deterministic, so events cannot be regenerated from them).
  Replicate with **Raft**: a leader and followers; survives a minority failure.
- Polling in CQRS is slow and heavy; a **reverse proxy** submits commands and
  polls for many users; read state machines **push** results to the proxy
  for near-real-time responses.
- Shard into several Raft groups and run TC/C or a Saga across them.

Final transfer: client → Saga coordinator (phase status record) →
partition 1 leader validates `A−1`, replicates the event, read machine pushes
the result → coordinator records success → `C+1` on partition 2 → client informed.
