# Nearby friends

Source: Vol. 2 ch. 2 (upstream `17. Nearby Friends`).
Unlike the proximity service, positions change constantly.

## Scope and numbers

Friends within 5 miles (configurable), straight-line distance;
list refreshes every few seconds with distance and timestamp;
inactive friends disappear after 10 minutes; location history kept for analysis.
Low latency, eventual consistency, occasional lost updates acceptable.
1 billion users, 10 % use the feature → 100 M; 10 % concurrent → 10 M;
400 friends each, all using it; 20 per page;
update every 30 s → 10 M ÷ 30 ≈ 334 k location updates/s.

## High-level design

Peer-to-peer is impractical on mobile, so a backend fans out:
receive every update, find the friends who should see it (within range), forward.

Components: load balancer, **REST API servers** (friends, profiles),
**WebSocket servers** (stateful; hold client connections; seed the client with
nearby friends on connect), **Redis location cache** (`user_id → lat, long, ts`
with TTL, expiry = inactive), **user DB** (relational or NoSQL; sharded by `user_id`),
**location history DB** (Cassandra, write-heavy), **Redis pub/sub** as a message bus
with one channel per user.

## Periodic update flow

Client → WebSocket server → save to history DB → update the location cache
(and keep it in memory for distance checks) → publish to the user's channel →
every WebSocket server hosting a friend receives it, computes distance,
and forwards if within range.
With 400 friends and 10 % online, each update fans out to about 40 clients.

## API

WebSocket: location update, location broadcast to clients, client initialisation
(server returns nearby friends), subscribe to a new friend, unsubscribe.
HTTP for everything else.

## Scaling each part

- API servers: auto-scaling.
- WebSocket servers: scale out; drain connections before removing a node.
- Client init: fetch friends, subscribe to their channels, read their cached locations.
- User DB: shard by `user_id`; likely owned by another team behind a service.
- Location cache: shard across Redis nodes; TTL bounds memory; heavy writes are fine.
- Pub/sub: an idle channel costs nothing, so pre-allocate one per user.

### Pub/sub at scale

Channels for 100 M users need about 200 GB (two 100 GB nodes) for memory,
but ~14 M pushes/s (334 k updates × 40 subscribers) need about 140 servers
at ~100 k pushes/s each: CPU, not memory, drives the cluster size.
Track live nodes in ZooKeeper or etcd; map channels to nodes with a hash ring
cached in every WebSocket server.
Resize by a daily job on historical traffic, or overprovision.
Resizing moves channels, causes resubscription storms and lost updates;
do it at the traffic trough and use consistent hashing to move fewer channels.

## Edge cases

- Adding or removing a friend: the client tells its WebSocket server to
  subscribe or unsubscribe.
- Users with many friends: cap friends (Facebook: 5,000);
  a whale's server takes more load but survives.
- **Nearby random person**: channels per geohash;
  everyone in a cell subscribes to it and to bordering cells.

## Alternative to Redis pub/sub

Erlang/OTP: millions of lightweight processes handling both WebSocket
connections and channels; powerful but hard to hire for.
