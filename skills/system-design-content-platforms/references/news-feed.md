# Design a news feed system

Source: Vol. 1 ch. 11 (upstream `11. News Feed System`).

## Scope

Web and mobile; publish posts; see friends' posts in reverse chronological order;
up to 5,000 friends; 10 million DAU; text, images, videos.

## API

- `POST /v1/me/feed` with `content` and `auth_token`.
- `GET /v1/me/feed` with `auth_token`.

## Two flows

**Feed publishing**: user → load balancer → web servers (auth, rate limit) →
post service (write to DB and cache) → fanout service (push to friends' feed caches) →
notification service.

**Feed building**: user → load balancer → web servers → news feed service →
news feed cache (post IDs) → hydrate posts and users from their caches → return.

## Deep dive: fan-out

| Model | How | Pros | Cons |
| --- | --- | --- | --- |
| Fan-out on write (push) | Precompute friends' feeds at post time | Feed reads are instant | Expensive for users with many friends; wasted work for inactive users (hotkey problem) |
| Fan-out on read (pull) | Build the feed when requested | No wasted work; cheap for inactive users | Slow reads |

Hybrid: push for most users; for celebrities, followers pull at read time.
Consistent hashing spreads the fan-out load.

Fanout service steps:
fetch friend IDs from the graph database;
filter by settings (muted friends, selective sharing);
send `post_id` plus friend list to a message queue;
fanout workers append `post_id` to each friend's feed cache
(store `<post_id, user_id>`, not whole objects; cap the list length).

## Deep dive: retrieval and cache layers

| Cache | Holds |
| --- | --- |
| News feed | Post IDs per user |
| Content | Post details; hot cache for popular posts |
| Social graph | Relationships |
| Action | Likes, replies, shares per user |
| Counters | Like, reply, follower counts |

## Wrap-up

Scale the database (sharding, read replicas); stateless web tier;
cache as much as possible; multiple data centers;
message queues to decouple; monitor QPS, latency, cache hit rates.
