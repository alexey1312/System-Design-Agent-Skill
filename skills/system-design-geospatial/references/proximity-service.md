# Proximity service

Source: Vol. 2 ch. 1 (upstream `16. Proximity Service`).
Nearby restaurants, hotels, gas stations: Yelp and the "nearby" part of Google Maps.

## Scope and numbers

Search businesses by latitude, longitude and radius;
owners add, update, delete businesses (not real-time; next-day is fine);
business detail pages.
Low latency, GDPR/CCPA compliance, high availability with peak-hour spikes in dense areas.
100 million DAU, 200 million businesses;
5 searches per user per day → 100 M × 5 ÷ 86,400 ≈ 5,000 QPS.

## API

- `GET /v1/search/nearby?latitude&longitude&radius` (default 5,000 m) →
  business IDs with the fields needed to render a list.
- `GET|POST|PUT|DELETE /v1/businesses/{id}`.

## Data model

Reads dominate (search, detail views); writes are rare → MySQL with primary
and read replicas.
Tables: `business` (details) and a **geospatial index** table.
Replication lag is harmless because business data is not real-time.

Two services behind a load balancer:
**location-based service** (LBS; read-only, stateless, high QPS) and
**business service** (CRUD by owners, detail reads by customers).

## Finding nearby businesses

1. **Two-dimensional range query** on lat/long columns: an index helps one
   dimension at a time; scans too much.
2. **Even grid**: fixed cells; dense cities and empty deserts get the same cell size.
3. **Geohash**: recursively split the world into quadrants, alternating
   longitude and latitude bits, base-32 encode; 12 precision levels.
   Longer shared prefix ⇒ closer (mostly).
   Radius picks the precision (500 m ⇒ length 6; 1 km ⇒ 5; 20 km ⇒ 4).
   **Boundary problem**: neighbours across a cell edge share no prefix
   (worse at the equator and prime meridian), so query the 8 neighbouring cells too.
   Sparse areas: widen the radius by dropping a character.
4. **Quadtree**: in-memory tree built at LBS start-up;
   split a node until it holds ≤ 100 businesses.
   200 million businesses ⇒ about 1.7 million leaves, a few GB of memory,
   a few minutes to build (n log n): roll out new versions gradually.
   Supports k-nearest and adapts to density;
   updates are harder (rebuild incrementally or lock for in-place edits).
5. **Google S2**: maps the sphere onto a Hilbert curve;
   great for geofencing and arbitrary regions with min/max levels;
   harder to explain in an interview.

| | Geohash | Quadtree | S2 |
| --- | --- | --- | --- |
| Implement | Easy; no tree | Moderate | Hard |
| Fixed radius | Yes | k-nearest | Regions |
| Density adaptive | No | Yes | Yes |
| Index update | Easy row update | Rebuild or lock | |

The chapter picks geohash for the walkthrough.

## Scaling and caching

`business` table sharded by ID; the geohash table is small enough for one node
plus read replicas.
Cache by **geohash → business IDs** (GPS coordinates jitter; geohash is stable)
and **business_id → details**; precompute all precisions 4–6 for 200 M rows
in Redis (≈ 1.7 GB per precision) with replicas per region.
Deploy LBS and business service in multiple regions and availability zones.

## Final flow

Client (lat, long, 500 m) → load balancer → LBS → geohash length 6 →
9 geohashes (cell + neighbours) → parallel Redis reads for business IDs →
details from the business cache → rank by distance → return.
