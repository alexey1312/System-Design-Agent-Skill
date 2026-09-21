# Design consistent hashing

Source: Vol. 1 ch. 5 (upstream `05. Consistent Hashing`).

Consistent hashing places keys and servers on the same hash ring
so that adding or removing a server moves only the keys next to it.
It is the standard way to spread requests or data across servers
while keeping redistribution small.

## The rehashing problem

With `serverIndex = hash(key) % N`, changing *N* remaps almost every key:
after one server dies, most cache lookups miss at once and the database absorbs the storm.
That is acceptable only when the pool size never changes.

## The ring

1. Hash space `0 … 2^160 − 1` (SHA-1) joined end to end forms a ring.
2. Servers are hashed by IP or name onto the ring.
3. A key belongs to the first server found walking clockwise from its hash.
4. Adding a server takes over only the keys between it and its predecessor.
5. Removing a server hands only its own keys to the next server clockwise.

## Two problems with the naive ring

- **Partition sizes are uneven**: random placement leaves some servers with huge arcs.
- **Key distribution is uneven**: a hot arc means a hot server.

## Virtual nodes

Each physical server owns many points on the ring (Dynamo used hundreds).
More virtual nodes means smaller standard deviation of load:
100 virtual nodes give about 10 % deviation, 200 give about 5 %,
at the cost of memory for the ring map.
Heterogeneous servers get virtual nodes in proportion to capacity.

## Affected keys

- New server *s4* between *s3* and *s4*: keys in `(s3, s4]` move to *s4*.
- Removed server *s1*: keys in `(s0, s1]` move to *s2*.

## Benefits

Minimal key movement, horizontal scaling that just works,
and hotspot mitigation through even distribution.

## Where it is used

Amazon Dynamo and DynamoDB partitioning, Cassandra, Discord's chat servers,
Akamai's CDN, Google's Maglev load balancer.
Within these skills: the key-value store, the crawler's downloader pool,
metrics collectors, nearby-friends pub/sub shards, object-storage replica groups.
