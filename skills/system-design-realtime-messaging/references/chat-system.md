# Design a chat system

Source: Vol. 1 ch. 12 (upstream `12. Chat System`).

## Scope

One-on-one and group chat (up to 100 members); text up to 100,000 characters;
online presence; multiple devices per user; push notifications;
50 million DAU; history stored forever; no end-to-end encryption.

## Protocols

Sending is HTTP with keep-alive.
Receiving needs a server-initiated path:

| Option | Behaviour |
| --- | --- |
| Polling | Client asks repeatedly; wasteful |
| Long polling | Server holds the request until a message or timeout; sender and receiver may be on different servers; hard to know when a client is gone |
| WebSocket | Persistent bidirectional connection over ports 80/443; used for both directions |

## Components

- **Stateless**: login, sign-up, profile, and **service discovery**
  (ZooKeeper) that picks the best chat server by location and load.
- **Stateful**: chat servers holding WebSocket connections;
  **presence servers** with WebSocket connections for status.
- **Third party**: push notifications for offline recipients.
- **Storage**: a key-value store for history
  (horizontal scaling, low latency, good with long tails of old messages;
  Facebook Messenger uses HBase, Discord uses Cassandra).

## Data model

One-on-one: `message_id, message_from, message_to, content, created_at`.
Group: `channel_id, message_id, …` with primary key `(channel_id, message_id)`.
`message_id` must be unique and sortable by time:
Snowflake works; a per-channel local sequence is enough because order only
matters within a channel.

## Flows

**One-on-one**: A → chat server 1 → ID generator → key-value store →
if B online, chat server 2 over WebSocket; else push notification.

**Group**: the message is copied into every member's inbox (sync queue);
simple to sync and fine for small groups, expensive beyond WeChat's 500-member cap.
Each recipient's inbox merges messages from many senders.

**Multi-device sync**: each device keeps `cur_max_message_id`;
new messages are those addressed to the user with a larger ID.

## Presence

- Login and logout update `status` and `last_active_at` in the presence store.
- **Heartbeat**: the client pings every few seconds;
  no heartbeat for *x* (say 30) seconds → offline.
  Avoids flapping on brief disconnects.
- **Fan-out** of status changes over pub/sub channels per friend pair;
  fine for small groups; large groups fetch presence on entry or manually.

## Wrap-up

Media (compression, cloud storage, thumbnails); end-to-end encryption;
client-side caching; faster loads with geographically distributed
caching networks (Slack); error handling: server failover via ZooKeeper,
message resend and retry.
