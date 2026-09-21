# Design a unique ID generator in distributed systems

Source: Vol. 1 ch. 7 (upstream `07. Unique-Id Generator`).

Auto-increment on one database does not work across many servers.
The target: 64-bit numeric IDs, unique, roughly ordered by time,
more than 10,000 generated per second.

## Requirements

- Unique, numeric, fits in 64 bits.
- Increases with time (not necessarily by 1).
- Sortable by date.
- 10,000+ IDs per second.

## Options

| Option | How | Why not (or why) |
| --- | --- | --- |
| Multi-master replication | Each of *k* databases auto-increments by *k* | Hard to scale across data centers; IDs not time-ordered across servers; adding or removing servers breaks the stride |
| UUID | 128-bit random ID generated independently | No coordination, but 128 bits, non-numeric, not time-sortable |
| Ticket server | One database hands out increments (Flickr) | Numeric and simple, but a single point of failure; several ticket servers bring synchronisation problems |
| Twitter Snowflake | 64 bits split into sections | The chosen design |

## Snowflake layout

| Bits | Field | Notes |
| --- | --- | --- |
| 1 | Sign | Always 0 |
| 41 | Timestamp | Milliseconds since a custom epoch (Twitter: 1288834974657 = 2010-11-04); 2^41 ms ≈ 69 years, then a new epoch |
| 5 | Datacenter ID | 32 data centers |
| 5 | Machine ID | 32 machines per data center |
| 12 | Sequence | Up to 4,096 IDs per millisecond per machine; resets every millisecond |

Datacenter and machine IDs are fixed at startup;
timestamp and sequence are computed per ID.
IDs sort by time because the timestamp is the high-order field.

## Follow-ups

- **Clock synchronisation**: the design assumes one clock;
  multi-core machines and multiple servers drift. NTP is the usual answer.
- **Section tuning**: fewer sequence bits and more timestamp bits for long-lived,
  low-concurrency systems.
- **High availability**: the generator is mission-critical; run redundant instances.
