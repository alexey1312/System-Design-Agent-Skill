# Real-time gaming leaderboard

Source: Vol. 2 ch. 10 (upstream `25. Real-time Gaming Leaderboard`).

## Scope and numbers

A point per match won; monthly tournaments reset the board;
top 10; a user's own rank; users four above and below (bonus);
ties share a rank; real-time, not batched.
5 million DAU, 25 million MAU; 10 matches per user per day.
Users evenly spread → 50 per second, peak 250;
score updates 500 QPS, peak 2,500; top-10 fetches about 50 QPS.

## API

- `POST /v1/scores` (`user_id`, `points`) — callable by game servers only.
- `GET /v1/scores` → top 10 with rank and score.
- `GET /v1/scores/{user_id}` → the user's score and rank.

## High-level design

Client → game service (validates the win) → leaderboard service → leaderboard store.
Clients must not write scores directly: a proxy could forge them.
A message queue between game and leaderboard only if other consumers need the events.

## Data model

**Relational**: `leaderboard(user_id, score)`, one table or a `month` column;
`INSERT … ON DUPLICATE KEY UPDATE score = score + 1`;
top 10 with an index on `score` and `LIMIT 10`;
rank of one user needs a correlated `COUNT(*) WHERE score >= …`, which scans.
Fine for small scale only.

**Redis sorted set** (hash map + skip list): keeps members ordered by score;
add and find are O(log N), which beats scanning a table.

| Command | Purpose | Cost |
| --- | --- | --- |
| `ZADD` | Insert or update a member | O(log N) |
| `ZINCRBY` | Add points (starts at 0) | O(log N) |
| `ZREVRANGE k 0 9 WITHSCORES` | Top 10 | O(log N + M) |
| `ZREVRANK` | A user's rank | O(log N) |
| `ZREVRANGE k rank−4 rank+4` | Neighbours | O(log N + M) |

Key per month: `leaderboard_feb_2021`; old boards move to history.
Storage: 25 M members × (24-byte ID + 16-bit score) ≈ 650 MB,
double for skip-list overhead, still one node;
2,500 updates/s is well within one Redis server.
Add a replica and persistence; MySQL tables hold user details and the win log
(used to rebuild the board after a Redis loss); cache the top-10 user details.

## Deep dive

### Managed or self-hosted

Own servers: Redis, MySQL, a profile cache.
Cloud: API Gateway → Lambda functions → Redis and DynamoDB;
no servers to manage, auto-scaled; recommended for a new game.

### Scaling Redis

At 500 million DAU: 65 GB and 250 k QPS need sharding.

- **Fixed (range) partitions by score**: `[0–100)`, `[100–200)`, …;
  the app keeps `user_id → shard`;
  top 10 comes from the top shard;
  a user's rank = rank within the shard + sizes of higher shards (from `INFO keyspace`).
  Rebalance when users move between ranges.
- **Hash partitions (Redis Cluster)**: 16,384 slots by `CRC16(key) % 16384`;
  top 10 needs scatter-gather across all shards;
  latency grows with partitions; no direct way to compute a rank.
  The chapter prefers fixed partitions.

Allocate twice the memory for write-heavy nodes (snapshots);
measure with `redis-benchmark`.

### NoSQL alternative (DynamoDB)

Partition by month with `score` as sort key → hot partition for the current month.
Write-shard by appending `user_id % n` to the partition key;
reads then scatter-gather across *n* partitions.
More partitions: more write scale, slower reads; benchmark to choose *n*.
Exact rank is hard; report a percentile computed by a periodic job instead.

## Wrap-up

Cache user objects in a Redis hash; break ties by last win time;
rebuild from the MySQL log after a Redis outage.
