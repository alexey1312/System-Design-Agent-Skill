---
name: system-design-content-platforms
description: >-
  Design the read-heavy content products the System Design Interview books
  cover: a URL shortener (base-62 vs hash, 301 vs 302), a web crawler (URL
  frontier, politeness, priority, freshness), a news feed (fan-out on write vs
  on read, cache layers), search autocomplete (trie with cached top-k, weekly
  aggregation, sharding), YouTube-style video upload and streaming
  (transcoding DAG, CDN, pre-signed URLs) and Google Drive-style file sync
  (block servers, delta sync, deduplication, long polling). Use when asked to
  design, compare or review any of these or a similar product: link
  shortener, timeline, typeahead, media upload and playback, cloud storage
  sync.
---

# Content platforms

Six case studies where reads dwarf writes and the design is about caches,
CDNs and precomputation.
The orchestrator (`system-design-interview`) owns scope, estimates and the
answer format; this skill owns the case studies.

| System | Reference | The deep dive the interviewer expects |
| --- | --- | --- |
| URL shortener | `references/url-shortener.md` | Hash vs base-62; 301 vs 302; cache in front of the DB |
| Web crawler | `references/web-crawler.md` | URL frontier: front queues for priority, back queues for politeness |
| News feed | `references/news-feed.md` | Fan-out on write vs read; hybrid for celebrities; five caches |
| Search autocomplete | `references/search-autocomplete.md` | Trie with top-k per node; offline aggregation; shard map |
| Video streaming | `references/video-streaming.md` | Transcoding DAG and resource manager; CDN cost; pre-signed uploads |
| Cloud file storage | `references/cloud-file-storage.md` | Blocks, delta sync, dedup; conflict resolution; long polling |

## How to use

1. Run the orchestrator's scope and estimate steps;
   these systems are sized by DAU, read/write ratio and object size,
   and the CDN cost line often decides the design.
2. Load the one reference the request names.
   Borrow from a sibling when the product mixes them
   (a feed with video, a crawler feeding autocomplete).
3. Follow the chapter's shape: API, data model, two flows
   (write path, read path), then the deep dive.
4. Cite the chapter (`references/sources.md`) and label your own additions.

## Cross-cutting rules

- **Precompute for reads.**
  Feed caches, trie snapshots, transcoded renditions and CDN copies are all
  the same move: pay at write time so reads are O(1).
- **Say what the cache holds**: IDs rather than objects
  (news feed), top-k rather than subtrees (autocomplete),
  blocks rather than files (Drive).
- **Hot users and hot content** break uniform designs;
  name the celebrity, the popular video, the common prefix, and the fallback.
- **Idempotent, resumable writes** for large uploads: chunks, pre-signed URLs,
  resumable upload sessions.
- **Analytics is a design input**: 302 redirects and event tracking exist
  because someone will ask for click counts.

## Pitfalls

- Sequential base-62 IDs are guessable; mention the security concern.
- DFS on the web graph goes too deep; BFS without priority wastes the crawl.
- Fan-out on write alone melts on users with 5,000 friends.
- Updating the trie per query is infeasible; aggregate offline.
- Serving every video from the CDN costs more than the servers do.
- WebSocket for Drive notifications is over-engineering; the chapter picks long polling.

Shared references: `references/estimation-cheatsheet.md`,
`references/building-blocks.md`, `references/design-format.md`;
calculator: `scripts/estimate.py`.
