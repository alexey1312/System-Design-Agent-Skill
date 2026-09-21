---
name: system-design-geospatial
description: >-
  Design the location-based systems the System Design Interview books cover:
  a proximity service (geohash vs quadtree vs Google S2, neighbour cells,
  Redis geohash cache), nearby friends (WebSocket servers, Redis pub/sub
  fan-out, location cache with TTL, hash ring for channels) and Google Maps
  (map tiles per zoom level on a CDN, routing tiles, A* across tiles,
  batched location updates into Cassandra and Kafka, adaptive ETA and
  rerouting). Use when asked to design, compare or review anything with
  coordinates, radius search, live location sharing, geofencing, tiles,
  routing, ETA or navigation: Yelp, Find My Friends, Uber-style maps.
---

# Geospatial systems

Three case studies that turn two-dimensional positions into one-dimensional
keys and then apply the usual caching and fan-out patterns.
The advisor (`system-design-advisor`) owns the scan, the numbers and the
answer format; this skill owns the case studies.

| System | Reference | Where the risk is |
| --- | --- | --- |
| Proximity service | `references/proximity-service.md` | Geohash precision by radius; neighbour cells; quadtree trade-offs; cache keys |
| Nearby friends | `references/nearby-friends.md` | Pub/sub fan-out; CPU-bound Redis cluster sizing; resubscription on resize |
| Maps and navigation | `references/maps-navigation.md` | Tiles on a CDN; routing tiles and A*; write-heavy location store; rerouting |

## How to use

1. Decide first whether positions are **static** (businesses: proximity
   service) or **moving** (people, vehicles: nearby friends);
   the index and the transport differ completely.
2. On a real project, run `scripts/arch_scan.py`;
   PostGIS, geohash or H3 libraries, WebSocket servers and Redis in its
   inventory say which reference to load.
   For a new design, run the advisor's estimate step;
   update interval × concurrent users is the number that sizes everything.
3. Load the one reference the request names;
   Maps borrows the location pipeline from nearby friends and the geohash
   from the proximity service.
4. Cite the chapter (`references/sources.md`) and label your own additions.

## On a real project

- **Radius search**: find the index behind the query (bounding box on
  lat/long columns is `RC-2.1` territory), whether neighbouring cells are
  included, and the cache key.
- **Live location**: find the update interval, the TTL on cached
  positions, the fan-out mechanism and how it is sized (pushes per second),
  and the retention of location history.
- **Maps and routing**: find tile generation and caching, the zoom levels
  served, whether tiles are raster or vector, and how routes are
  recomputed when traffic changes.
- **Privacy**: find the opt-in, the retention policy and the GDPR/CCPA
  deletion path.

## Cross-cutting rules

- **Pick the geospatial index by the question**: fixed radius → geohash;
  k-nearest or density-adaptive → quadtree; arbitrary regions → S2.
- **Always query neighbouring cells**; boundary misses are the standard
  follow-up.
- **Cache by geohash, not by coordinates**: GPS jitters, the cell does not.
- **Location history is write-heavy**: Cassandra with `user_id` partition key
  and `timestamp` clustering key; stream it through Kafka for analytics.
- **Precompute what does not move**: map tiles, routing tiles, geohash
  buckets at every precision.
- **Privacy is a requirement**: GDPR/CCPA, TTLs on live location, opt-in.

## Pitfalls

- Indexing latitude and longitude separately still scans.
- Sharding a geohash table that fits on one node adds nothing; add replicas.
- Redis pub/sub memory is small; push throughput per second is what needs
  140 servers.
- Rebuilding a quadtree on every business update invalidates every cache.
- Client-side tile URL computation is a commitment you cannot revoke.
- Rendering whole maps server-side instead of tiles cannot be cached.

Shared references: `references/review-checklist.md`,
`references/estimation-cheatsheet.md`, `references/building-blocks.md`,
`references/design-format.md`;
scripts: `scripts/arch_scan.py` (read-only project scan),
`scripts/estimate.py` (calculator).
