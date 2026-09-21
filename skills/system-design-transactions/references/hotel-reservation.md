# Hotel reservation system

Source: Vol. 2 ch. 7 (upstream `22. Hotel Reservation System`).
The same shape covers Airbnb, flights, cinema tickets.

## Scope and numbers

5,000 hotels, 1 million rooms; pay in full at booking; web and app only;
cancellations; 10 % overbooking allowed; prices change daily.
Focus: hotel and room pages, reservations, admin, overbooking.
High concurrency in peak season; a few seconds of latency is acceptable.
70 % occupancy, 3-night stays → 1 M × 0.7 ÷ 3 ≈ 240 k reservations a day ≈ 3 TPS.
With a 10 % conversion funnel (detail page → booking page → reservation),
3 reservations mean 30 booking-page views and 300 detail-page views.

## API

- Hotels: `GET /v1/hotels/{id}`; `POST/PUT/DELETE` for staff.
- Rooms: `GET /v1/hotels/{id}/rooms/{id}`; `POST/PUT/DELETE` for staff.
- Reservations: `GET /v1/reservations`, `GET /v1/reservations/{id}`,
  `POST /v1/reservations`, `DELETE /v1/reservations/{id}`.

`POST /v1/reservations` body: `startDate, endDate, hotelID, roomTypeID,
roomCount, reservationID`.
`reservationID` is the **idempotency key**.

## Data model

Relational: reads dominate, writes are few, ACID prevents negative inventory
and double charges, and the schema is obvious.
Reservation `status` is a state machine: pending → paid → refunded / cancelled / rejected.

The first schema reserves a specific room (Airbnb style).
Hotels sell **room types**, so the improved schema adds
`room_type_rate` and `room_type_inventory(hotel_id, room_type_id, date,
total_inventory, total_reserved)`, one row per hotel, type and date,
prepopulated by a daily job.

Availability check:

```sql
SELECT date, total_inventory, total_reserved
FROM room_type_inventory
WHERE room_type_id = ? AND hotel_id = ? AND date BETWEEN ? AND ?
-- ok when total_reserved + rooms_to_reserve <= 1.1 * total_inventory
```

Size: 5,000 hotels × 20 types × 2 years × 365 days ≈ 73 M rows;
one server with read replicas.
If it ever outgrows that: archive past reservations to cold storage;
shard by `hash(hotel_id)` because every query filters on `hotel_id`.

## High-level design

Microservices behind a public API gateway (rate limiting, auth) and an internal
API for staff over VPN; CDN for static assets.
Services: hotel (static, cacheable), rate, reservation (also owns inventory),
payment, hotel management; gRPC between them.

## Deep dive: double booking

**Same user clicks twice**: disable the button client-side, and make the API
idempotent — the unique constraint on `reservation_id` rejects the second insert.

**Two users, same room, non-serializable isolation**: both read 99 of 100
reserved, both update, both commit → 101.

| Option | Mechanism | Pros | Cons |
| --- | --- | --- | --- |
| Pessimistic locking | `SELECT … FOR UPDATE` | Serialises updates; simple; good under heavy contention | Deadlocks; long locks stall everyone; not recommended here |
| Optimistic locking | `version` column, compare-and-set, retry on mismatch | No DB locks; fast when conflicts are rare | Many rollbacks under heavy contention |
| Database constraint | `CHECK (total_inventory - total_reserved >= 0)` | Trivial to implement | Same contention profile; constraints are hard to version-control; not every DB supports them |

Reservation QPS is low, so optimistic locking or a constraint fits.

## Scalability

Services are stateless; the database is the bottleneck.
Shard by `hotel_id`: 30,000 QPS across 16 shards is under 2,000 per shard.
Cache inventory in Redis with keys `hotelID_roomTypeID_date` and TTLs,
kept in sync by CDC (Debezium); the database still rejects invalid bookings,
so a stale cache only means a user sees "sold out" after a refresh.

## Consistency across services

Reservation and inventory share one service and database to use ACID.
A purist microservice split needs **two-phase commit** (slow; blocks on one
laggard) or a **Saga** (local transactions with compensations; eventually consistent).
Both add complexity; say so and prefer the pragmatic shared database.
