# Design a search autocomplete system

Source: Vol. 1 ch. 13 (upstream `13. Search Autocomplete`).

## Scope and numbers

Match prefixes; return the 5 most popular queries by historical frequency;
lowercase English only; no spell check.
Fast (under 100 ms), relevant, sorted by popularity, scalable, highly available.
10 million DAU, 10 searches a day, 20 bytes per query;
each keystroke is a request: 20 requests per search →
24,000 QPS average, 48,000 peak;
20 % of queries are new → 0.4 GB of new data per day.

## High-level design

- **Data gathering service**: aggregates queries and their frequencies.
- **Query service**: given a prefix, returns the top 5.

## Trie

A prefix tree whose nodes carry a frequency.
Naive top-k: find the prefix node (O(p)), traverse the subtree (O(c)),
sort the candidates (O(c log c)).
Two optimisations make it fast:

1. **Limit prefix length** (say 50 characters); users rarely type more.
2. **Cache top-k at every node**; each node stores its five best queries,
   so a lookup is O(1) after the prefix walk, at the cost of memory.

## Data gathering pipeline

Updating the trie on every query is infeasible at billions per day,
and top suggestions change slowly.

Analytics logs (append-only, unindexed) → **aggregators**
(weekly for most products, minutes for Twitter-like freshness) →
frequency table → **workers** rebuild the trie → **trie DB** (snapshot) →
**trie cache** (weekly snapshot loaded in memory).

Trie DB options: a document store (MongoDB) holding the serialised snapshot,
or a key-value store mapping every prefix to its node data.

## Query service

Client → load balancer → API servers → trie cache (fallback to trie DB).
Optimisations: AJAX requests; browser caching of results
(Google caches for an hour); data sampling for logs.

## Trie operations

- Create: workers, weekly, from the aggregated table.
- Update: replace weekly, or update nodes and their ancestors in place.
- Delete: a filter layer in front of the cache removes hateful, violent
  or explicit suggestions; the database is cleaned asynchronously.

## Scaling

Shard the trie by first letter, then by ranges (`a–m`, `n–z`; then `aa–ag`, …);
letter frequencies are uneven, so a **shard map manager** learns historical
distribution and routes prefixes to shards.

## Follow-ups

Multi-language via Unicode in the trie;
per-country tries served from CDN-like placement;
trending queries by weighting recent data and shortening the aggregation window.
