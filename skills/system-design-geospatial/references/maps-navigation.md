# Google Maps

Source: Vol. 2 ch. 3 (upstream `18. Google Maps`).

## Scope and numbers

Location updates, navigation with ETA, map rendering;
road data is terabytes from many sources;
traffic matters for ETA; walking, cycling, driving; no multi-stop, no places or photos.
Accuracy, smooth rendering, low data and battery use, availability, scale.
1 billion DAU; 35 minutes of navigation per user per week → 5 billion minutes a day;
batched GPS updates → about 200 k QPS, 1 M at peak.
Storage: map tiles about 70 PB after compressing similar tiles; road data as routing tiles.

## Map 101

- Latitude and longitude on a sphere; projection to 2D distorts something;
  Google uses Web Mercator.
- Geocoding turns addresses into coordinates (reverse geocoding the opposite),
  often by interpolation from street data.
- Geohashing subdivides the flattened world into quadrants.
- **Map tiles**: the world is 256 × 256 pixel images per zoom level;
  zoom 0 is one tile; each level quadruples the count;
  the client stitches the tiles it needs.
- **Routing tiles**: roads as a graph (intersections = nodes, roads = edges);
  Dijkstra or A* on the whole world is infeasible,
  so the graph is tiled too, tiles reference neighbours,
  and coarser tiles cover long-distance legs.

## High-level design

### Location service

`POST /v1/locations` with a batch of `(lat, long, timestamp)`;
client-side batching cuts request volume;
Cassandra for the write-heavy store; Kafka streams updates to
traffic, ETA and analytics consumers.

### Navigation service

`GET /v1/nav?origin&destination` → distance, duration, polyline,
turn-by-turn instructions, waypoints.
Route need not be optimal but must be correct; some latency is fine.

### Map rendering

Tiles are static, precomputed, named by geohash (or a URL scheme the server hands out),
and served from a **CDN** so clients hit the nearest point of presence.
Client-side tile URL computation must be stable forever;
a tiny API that returns URLs avoids that commitment.
Vector tiles (paths and polygons rendered on the client) save bandwidth
over raster images.

## Deep dive

### Data

- Routing tiles: produced offline from raw road data, stored in object storage
  (no database features needed), cached aggressively, adjacency lists compressed.
- User locations: Cassandra, partition key `user_id`, clustering key `timestamp`;
  availability over consistency.
- Geocoding: `lat,long ↔ place` in Redis (read-heavy).
- Map tiles: CDN.

### Navigation components

Geocoding service → route planner → **shortest-path service**
(A* over routing tiles fetched by geohash from origin to destination) →
**ETA service** (ML on traffic data) → **ranker** (user filters: no tolls,
no highways) → **updater services** refresh traffic and routing tiles asynchronously.

### Adaptive ETA and rerouting

Track each navigating user's route as tiles;
when traffic changes on a tile, find affected users and reroute.
Store the origin tile plus its ancestors at coarser levels until the
destination is covered, so checking impact is a containment test on few tiles.

### Delivery to clients

Mobile push is limited and absent on web; WebSocket beats long polling on cost;
server-sent events are one-way, and bidirectional helps features like last-mile delivery.

## Wrap-up

Multi-stop navigation as a paid feature for logistics customers.
