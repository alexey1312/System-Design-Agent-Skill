# Design a web crawler

Source: Vol. 1 ch. 9 (upstream `09. Web Crawler`).

Used for search indexing, web archiving, web mining, and monitoring
(copyright, trademarks).
A good crawler is scalable, robust (bad HTML, hangs, malicious links),
polite, and extensible.

## Scope and numbers

Search-engine indexing; HTML only; new and updated pages;
5 years of retention; duplicates ignored.
1 billion pages per month → ~400 pages/s, peak 800/s;
500 KB per page → 500 TB per month, 30 PB over 5 years.

## Components

1. **Seed URLs**: chosen by locality or topic to reach as much of the graph as possible.
2. **URL frontier**: the queue of URLs to fetch (details below).
3. **HTML downloader**.
4. **DNS resolver** with a cache.
5. **Content parser**: validates and parses; drops malformed pages.
6. **Content seen?**: hash comparison against stored pages to skip duplicates.
7. **Content storage**: disk, with popular pages in memory.
8. **URL extractor**: relative links become absolute.
9. **URL filter**: blocklists, error URLs, unwanted content types.
10. **URL seen?**: Bloom filter or hash table of visited URLs.
11. **URL storage**.

Workflow: seeds → frontier → downloader (DNS) → parser → content seen? →
extractor → filter → URL seen? → frontier.

## Deep dive

### Traversal

The web is a directed graph; BFS, because DFS goes too deep.
Plain BFS ignores politeness (all links on one page hit one host)
and priority (not every page matters equally).

### URL frontier

- **Politeness**: one connection per host at a time, with a delay between fetches.
  A queue router maps each host to its own back queue;
  a queue selector hands each worker thread one queue.
- **Priority**: a prioritizer scores URLs (PageRank, traffic, update frequency)
  into front queues; the selector picks high-priority queues more often.
  Front queues handle priority, back queues handle politeness.
- **Freshness**: recrawl by update history and importance.
- **Storage**: the frontier holds hundreds of millions of URLs;
  keep most on disk with in-memory buffers for enqueue and dequeue.

### HTML downloader

Honour `robots.txt` (cache it per host).
Performance: distributed crawl, DNS cache, geographic locality,
short timeouts.

### Robustness

Consistent hashing to spread load across downloaders;
save crawl state for restart; exception handling; data validation.

### Extensibility

Plug in modules: a PNG downloader, a web-monitor module.

### Problematic content

Duplicate content by hash; spider traps by URL length limits and manual blocking;
noise (ads, spam) filtered out.

## Wrap-up

Server-side rendering for JavaScript pages before parsing;
anti-spam filtering; database replication and sharding;
horizontal scaling with stateless crawl servers; availability, consistency, reliability;
analytics.
