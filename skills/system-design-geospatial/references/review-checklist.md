# Design review checklist

What to check when reviewing a real system, with the chapter behind each item.
`scripts/arch_scan.py` automates the items marked *scan*;
everything else is read from the code, the infrastructure files and the
owners' answers.
Report each miss as a recommendation in the format of `design-format.md`,
and report a deliberate, documented choice as *kept*.

## RC-1 Availability and the tiers

| ID | Check | Why | Source |
| --- | --- | --- | --- |
| RC-1.1 | Every tier has more than one instance, including the cache and the queue | A single node anywhere is the outage | Vol. 1 ch. 1 |
| RC-1.2 | The web tier is stateless; sessions live in a shared store | Otherwise auto-scaling and failover break | Vol. 1 ch. 1 |
| RC-1.3 | Database failover has been exercised; replicas may lag on promotion | Promoted slaves are behind; recovery scripts exist | Vol. 1 ch. 1 |
| RC-1.4 | Multi-region only when the numbers demand it; GeoDNS, replication and deploy automation come with it | Cheap to say, expensive to run | Vol. 1 ch. 1 |
| RC-1.5 | The availability target is written down and the calculator's downtime budget matches it | 99.99 % is 52 minutes a year | Vol. 1 ch. 2 |

## RC-2 Data stores

| ID | Check | Why | Source |
| --- | --- | --- | --- |
| RC-2.1 | The store matches the access pattern (ACID vs write volume vs sorted sets vs time series) | The wrong store is rewritten later at cost | `building-blocks.md` › Choosing a store |
| RC-2.2 | The shard key is the column every hot query filters on, and it spreads load | Otherwise cross-shard queries or hot shards | Vol. 1 ch. 1, Vol. 2 ch. 7 |
| RC-2.3 | Celebrity or hot-key handling exists | One key can pin a shard or a cache node | Vol. 1 ch. 1, ch. 11 |
| RC-2.4 | Joins across shards are gone; data is denormalised deliberately | Cross-shard joins do not scale | Vol. 1 ch. 1 |
| RC-2.5 | *scan* `hash % N` placement is replaced by consistent hashing | Resizing remaps almost every key | Vol. 1 ch. 5 |
| RC-2.6 | Quorum settings (N, W, R) are stated for replicated stores | W + R > N or not is a product decision | Vol. 1 ch. 6 |
| RC-2.7 | Cassandra-style tables have no filter on non-key columns; denormalised copies exist instead | Such filters are scans or forbidden | Vol. 2 ch. 8 |

## RC-3 Caches and CDN

| ID | Check | Why | Source |
| --- | --- | --- | --- |
| RC-3.1 | What is cached, its TTL and its eviction policy are written down | Permanent, unbounded caches fill memory | Vol. 1 ch. 1 |
| RC-3.2 | The write path updates or invalidates the cache; the inconsistency window is known | Cache and DB are not one transaction | Vol. 1 ch. 1 |
| RC-3.3 | Cache keys are stable (geohash, not raw coordinates; IDs, not objects) | Unstable keys never hit | Vol. 2 ch. 1, Vol. 1 ch. 11 |
| RC-3.4 | Static assets go through a CDN with invalidation and an origin fallback | CDN outage must not be a site outage | Vol. 1 ch. 1 |
| RC-3.5 | *scan* No `KEYS *` on production Redis | Blocks the server | inference |

## RC-4 Queues and asynchronous work

| ID | Check | Why | Source |
| --- | --- | --- | --- |
| RC-4.1 | Delivery semantics are named and consumers are idempotent for at-least-once | Duplicates are normal | Vol. 2 ch. 4 |
| RC-4.2 | Ordering is per partition key where it matters; nobody assumes global order | Global order does not scale | Vol. 2 ch. 4 |
| RC-4.3 | Retry queue and dead-letter queue exist; backoff is exponential | Terminal failures need a place to go | Vol. 2 ch. 11 |
| RC-4.4 | Consumer lag and queue depth are alerted on | Growth means dead consumers or dead downstream | Vol. 2 ch. 8, ch. 6 |
| RC-4.5 | Notification sends are persisted before sending and deduplicated on an event ID | Provider retries produce duplicates | Vol. 1 ch. 10 |

## RC-5 Correctness of money and inventory

| ID | Check | Why | Source |
| --- | --- | --- | --- |
| RC-5.1 | Every mutating endpoint carries an idempotency key enforced by a unique constraint | Double clicks and retries double-book or double-charge | Vol. 2 ch. 7, ch. 11 |
| RC-5.2 | *scan* Money is a string or integer minor units, never float | Cents disappear | Vol. 2 ch. 11 |
| RC-5.3 | *scan* Locking strategy matches contention; long `FOR UPDATE` transactions are justified | Pessimistic locks stall under load | Vol. 2 ch. 7 |
| RC-5.4 | *scan* Optimistic locking uses a version number, not a timestamp | Clocks drift | Vol. 2 ch. 7 |
| RC-5.5 | Money movement is recorded double-entry and reconciled against the provider | Drift is otherwise invisible | Vol. 2 ch. 11 |
| RC-5.6 | Distributed transactions are avoided; where unavoidable, TC/C or an orchestrated Saga with a phase status table | 2PC blocks and its coordinator is a SPOF | Vol. 2 ch. 12 |
| RC-5.7 | Inventory is per type and date, not per physical unit, when customers book a type | The model decides the queries | Vol. 2 ch. 7 |

## RC-6 Real-time and connections

| ID | Check | Why | Source |
| --- | --- | --- | --- |
| RC-6.1 | Stateful connection servers have service discovery and graceful draining | Deploys otherwise drop everyone | Vol. 1 ch. 12, Vol. 2 ch. 2 |
| RC-6.2 | Presence uses heartbeats with an offline threshold longer than a brief disconnect | Otherwise status flaps | Vol. 1 ch. 12 |
| RC-6.3 | Offline clients have a pull path on reconnect | Push alone loses updates | Vol. 1 ch. 15, Vol. 2 ch. 8 |
| RC-6.4 | Pub/sub fan-out is sized by pushes per second, not by memory | CPU is the limit | Vol. 2 ch. 2 |

## RC-7 Rate limiting, IDs, and the edge

| ID | Check | Why | Source |
| --- | --- | --- | --- |
| RC-7.1 | Public APIs are rate limited at the gateway with atomic counters and 429 plus headers | Abuse and cost | Vol. 1 ch. 4 |
| RC-7.2 | Fixed-window limiters are known to admit 2× at the edges | Choose knowingly | Vol. 1 ch. 4 |
| RC-7.3 | IDs are time-sortable where ordering matters and not guessable where exposed | Sequential IDs leak volume | Vol. 1 ch. 7, ch. 8 |
| RC-7.4 | *scan* Rank queries do not count rows per request | O(N) per request | Vol. 2 ch. 10 |

## RC-8 Streams and analytics

| ID | Check | Why | Source |
| --- | --- | --- | --- |
| RC-8.1 | Aggregations use event time with an explicit watermark | Late events otherwise vanish | Vol. 2 ch. 6 |
| RC-8.2 | Raw events are retained (cold storage) for backfill and reconciliation | Aggregates alone cannot be recomputed | Vol. 2 ch. 6 |
| RC-8.3 | Billing-grade counts have exactly-once processing and a nightly reconciliation | Small drift is real money | Vol. 2 ch. 6 |

## RC-9 Operations

| ID | Check | Why | Source |
| --- | --- | --- | --- |
| RC-9.1 | Host, aggregate and business metrics exist; alerts page on symptoms | Nothing is scaled blind | Vol. 1 ch. 1, Vol. 2 ch. 5 |
| RC-9.2 | Label cardinality is bounded | High cardinality kills the TSDB | Vol. 2 ch. 5 |
| RC-9.3 | Deploys are automated and identical across regions | Drift causes the next outage | Vol. 1 ch. 1 |
| RC-9.4 | The next 10× has been estimated with the calculator and the first bottleneck named | Growth is planned, not discovered | Vol. 1 ch. 2 |
