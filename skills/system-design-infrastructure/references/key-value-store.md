# Design a key-value store

Source: Vol. 1 ch. 6 (upstream `06. Key-Value Store`).
The design follows Amazon Dynamo, with the storage engine from Cassandra.

## Scope

`put(key, value)` and `get(key)`; pairs under 10 KB;
big data; high availability and scalability; automatic scaling;
tunable consistency; low latency.

A single server is a hash table in memory with compression and cold data on disk.
It runs out of memory quickly, so the rest is about the distributed version.

## CAP

Consistency, availability, partition tolerance: pick two.
Network partitions happen, so real systems choose CP or AP;
CA does not exist in practice.
When node *n3* is cut off:
a CP store blocks writes to *n1* and *n2* to avoid divergence (banks);
an AP store keeps serving reads (possibly stale) and accepts writes,
syncing *n3* when the partition heals.

## Components

### Partitioning

Consistent hashing with virtual nodes (`consistent-hashing.md`):
automatic scaling as nodes come and go,
and heterogeneity by giving bigger servers more virtual nodes.

### Replication

Walk clockwise from the key's position and store copies on the first *N*
distinct physical servers (skip virtual nodes of the same machine).
Put replicas in different data centers.

### Consistency: quorum

*N* replicas, *W* acknowledgements for a write, *R* responses for a read,
mediated by a coordinator.

| Setting | Effect |
| --- | --- |
| R = 1, W = N | Fast reads |
| W = 1, R = N | Fast writes |
| W + R > N | Strong consistency (typically N = 3, W = R = 2) |
| W + R ≤ N | Not guaranteed |

Models: strong (a read sees the latest write), weak, eventual (Dynamo, Cassandra).
Eventual consistency lets concurrent writes diverge; the client reconciles.

### Inconsistency resolution: vector clocks

A value carries `D([S1, v1], [S2, v2], …)`.
A write at server *Si* increments `vi` or adds `[Si, 1]`.
*X* is an ancestor of *Y* if every counter in *X* ≤ the counter in *Y*;
otherwise they are siblings and the client must merge.
Costs: client complexity and clock growth
(trim old entries beyond a threshold; Dynamo notes this is rarely a problem).

### Failure detection

One server's opinion is not enough; use gossip:
each node keeps member IDs with heartbeat counters,
increments its own periodically, sends heartbeats to random nodes,
and marks a member offline when its counter has not moved for a while.

### Temporary failures: sloppy quorum and hinted handoff

Instead of enforcing the quorum on the intended replicas,
use the first *W* and *R* healthy servers on the ring.
Writes meant for a down server are held elsewhere with a hint
and pushed back when it returns.

### Permanent failures: anti-entropy with Merkle trees

Divide the key space into buckets, hash each key, hash each bucket,
build the tree upward.
Compare roots; on mismatch descend to find the differing buckets;
sync only those.

### Data center outage

Replicate across data centers.

## Write path (Cassandra)

1. Append to the commit log.
2. Write to the memtable (in-memory cache).
3. When the memtable is full, flush to an SSTable on disk.

## Read path

1. Check the memtable.
2. Miss → consult a Bloom filter to find which SSTables may hold the key.
3. Read from those SSTables and return.

## Architecture summary

Clients call `get`/`put` through a coordinator that proxies to the ring.
Every node has the same responsibilities (no single point of failure);
nodes join and leave automatically; data is replicated.

| Goal | Technique |
| --- | --- |
| Store big data | Consistent hashing |
| High read availability | Replication |
| High write availability | Versioning, vector clocks |
| Partition tolerance | Consistent hashing |
| Incremental scalability | Consistent hashing |
| Heterogeneity | Virtual nodes |
| Tunable consistency | Quorum |
| Temporary failures | Sloppy quorum, hinted handoff |
| Permanent failures | Merkle trees |
| Data center outage | Cross-DC replication |
