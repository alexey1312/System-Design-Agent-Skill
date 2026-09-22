---
name: system-design-realtime-messaging
description: >-
  Design the real-time delivery and event pipelines the System Design
  Interview books cover: a notification system (APNS, FCM, SMS, email; queues,
  retries, deduplication), a chat system (WebSocket, presence, multi-device
  sync, group fan-out), a distributed email service (SMTP flows, metadata
  store, search index), a real-time gaming leaderboard (Redis sorted sets,
  sharding, DynamoDB alternative) and ad click event aggregation (Kafka,
  MapReduce nodes, watermarks, windows, exactly-once, reconciliation). Use
  when asked to design, compare or review any of these or a similar system:
  push notifications, messenger, live rankings, stream aggregation, mail.
---

# Real-time and messaging systems

Five case studies about getting events to the right place quickly and
without losing or duplicating them.
The advisor (`system-design-advisor`) owns the scan, the numbers and the
answer format; this skill owns the case studies.

| System | Reference | Where the risk is |
| --- | --- | --- |
| Notification system | `references/notification-system.md` | Queue per channel; persistence, retry, dedup; user settings and rate limits |
| Chat system | `references/chat-system.md` | WebSocket; service discovery; message sync by ID; heartbeat presence |
| Email service | `references/email-service.md` | Send and receive flows; metadata store partitioned by user; search index |
| Gaming leaderboard | `references/gaming-leaderboard.md` | Sorted set operations; sharding by score range; percentile fallback |
| Ad click aggregation | `references/ad-click-aggregation.md` | Event time and watermarks; windows; exactly-once; hotspots; reconciliation |

## How to use

1. On a real project, run `scripts/arch_scan.py` first;
   WebSocket libraries, push and SMS providers, payment or job queues and
   stream processors in its inventory point at the reference to load,
   and finding `SD007` marks rank queries that scan.
   For a new design, run the advisor's scope and estimate steps;
   these designs turn on concurrent connections, events per second and
   fan-out factor.
2. Load the one reference the request names.
   The notification system is a component of the chat and email designs;
   load it when delivery to offline users matters.
3. State the delivery guarantee up front (at-most, at-least, exactly-once)
   and the mechanism that provides it.
4. Cite the chapter (`references/sources.md`) and label your own additions.
5. When there is nobody to ask (a non-interactive run, an owner who is
   away), write each open question into section 1 of the document as an
   assumption with the default you took, and continue
   (`references/design-format.md` › Rules).

## On a real project

- **Notifications**: find where a send is persisted before the provider
  call, the dedup key, per-user rate limits, the opt-out table and the
  retry policy.
- **Chat and presence**: find how clients pick a server, the heartbeat
  interval and offline threshold, the message ID scheme and the sync
  cursor per device.
- **Email**: find the outgoing and incoming queues, what is monitored on
  them, the metadata partition key, and how the search index is updated.
- **Leaderboards and rankings**: find the rank query; if it counts rows,
  that is `SD007`; check the rebuild path when the cache is lost.
- **Event aggregation**: find event time versus processing time, the
  window and watermark, the offset commit order, and the reconciliation job.

## Cross-cutting rules

- **Persistent connections are state.**
  WebSocket and presence servers are stateful; pair them with service
  discovery (ZooKeeper), graceful draining and reconnect logic.
- **Decouple with a queue, then say what the queue buys**:
  buffering bursts, retry, independent scaling of workers.
- **Deduplicate on an ID**, never on content: event IDs, message IDs,
  Kafka offsets plus snapshots.
- **Order is per key**: per channel, per partition, per user;
  global order is neither needed nor cheap.
- **Real-time means push to online users and pull on reconnect**;
  every chapter here has both paths.
- **Money changes the guarantee**: ad counts feed billing, so exactly-once
  and reconciliation are mandatory there and optional elsewhere.

## Pitfalls

- Long polling for chat: wasteful and cannot tell when a client left.
- A single notification server is the classic single point of failure.
- `COUNT(*) WHERE score >= …` for rank scans the table; sorted sets exist for this.
- Processing time instead of event time makes late clicks disappear.
- Filtering Cassandra on a non-key column: denormalise (read/unread tables).
- Clients must never write their own score.

Shared references: `references/review-checklist.md`,
`references/estimation-cheatsheet.md`, `references/building-blocks.md`,
`references/design-format.md`;
scripts: `scripts/arch_scan.py` (read-only project scan),
`scripts/estimate.py` (calculator).
