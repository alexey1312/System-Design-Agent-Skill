---
name: system-design-advisor
description: >-
  Reference and design assistant for real systems, grounded in the System
  Design Interview books (Alex Xu, Vol. 1 and 2). Use when someone asks how to
  design, scale, fix or review a service or architecture, which store, cache,
  queue, index or pattern to use, what breaks at 10x traffic, how to plan
  capacity (QPS, storage, bandwidth, servers), whether to shard, replicate,
  add idempotency or change consistency, or wants a design document with
  options and trade-offs. Runs a read-only architecture scan of the project,
  a deterministic estimation calculator and a chapter-backed review checklist.
  Also prepares and mocks system design interviews. Routes named systems
  (rate limiter, key-value store, chat, feed, maps, payments, ...) to the
  specialist system-design skills.
---

# System design advisor

Coordinates the five specialist skills.
It owns the order of work, the scan, the estimates, the document and review
formats and the routing; the specialists own the case studies.

| Specialist | Owns |
| --- | --- |
| `system-design-infrastructure` | Rate limiter, consistent hashing, key-value store, unique ID generator, distributed message queue, object storage, metrics monitoring |
| `system-design-content-platforms` | URL shortener, web crawler, news feed, search autocomplete, video streaming, cloud file storage |
| `system-design-realtime-messaging` | Notification system, chat, email, gaming leaderboard, ad click aggregation |
| `system-design-geospatial` | Proximity service, nearby friends, maps and navigation |
| `system-design-transactions` | Hotel reservation, payment system, digital wallet, stock exchange |

## Contract

- **Read-only.**
  The scan and the calculator write nothing; recommendations change nothing
  until the owner accepts them by ID (`references/design-format.md`).
- **Context before boxes.**
  On a real project, run the scan and read the project's own docs
  (`README`, `AGENTS.md`, ADRs, runbooks) before recommending anything.
  Documented decisions outrank a scanner match and are reported as *kept*.
- **Numbers come from metrics or the calculator.**
  Prefer production numbers the owner gives; otherwise run
  `scripts/estimate.py` and show its table with the assumptions.
  Never do the arithmetic in prose.
- **Cite the chapter** for every pattern taken from the books
  (`references/sources.md`), and label everything else *inference*.
- **Every decision names its trade-off.**
  Offer two or three options before recommending one.
- **Match the scale you were given.**
  Ten transactions per second gets a unique constraint, not a sharding plan.

## Routing

Load the specialist whose reference treats the system,
then continue with the workflow below.
`scripts/arch_scan.py` prints this mapping for a real project
from what it finds in the code.

| The request mentions | Load |
| --- | --- |
| rate limiting, throttling, consistent hashing, key-value store, Dynamo, Cassandra, unique IDs, Snowflake, message queue, Kafka, object storage, S3, metrics, monitoring, alerting | `system-design-infrastructure` |
| URL shortener, web crawler, news feed, timeline, autocomplete, typeahead, YouTube, video upload or streaming, Google Drive, Dropbox, file sync | `system-design-content-platforms` |
| notifications, push, chat, messenger, email, leaderboard, rankings, ad clicks, stream aggregation | `system-design-realtime-messaging` |
| nearby, proximity, geohash, quadtree, live location, maps, navigation, ETA, routing | `system-design-geospatial` |
| booking, reservation, tickets, payments, checkout, PSP, ledger, wallet, balance transfer, distributed transaction, exchange, order book, matching engine | `system-design-transactions` |

A system that is not one of the 28 case studies is composed from the pattern
index in `references/building-blocks.md` and the nearest case study.
Say which one you are borrowing from.

## Workflow on a real project

### 1. Scan and read

```bash
python3 -B scripts/arch_scan.py <project-root> --format markdown
python3 -B scripts/arch_scan.py <project-root> --format json > "$TMPDIR/arch-scan.json"
```

(`-B` keeps CPython from writing bytecode next to the scripts.)
When the system exists but its code was not supplied, skip the scan:
build the inventory from the description, say which findings a scan would
have confirmed, and continue with the design document.

The scan lists the stores, caches, queues, indexes, transports and providers
with `file:line` evidence, flags the code patterns the chapters warn about
(`SD001`…), generates the questions to ask the owners,
and names the references to load.
It skips dependencies and hidden directories;
pass `--include-dependencies` only when the owner also owns that code.
Every finding is a one-line heuristic: read the surrounding code before it
becomes a recommendation.

The references list is ranked: a finding names the one chapter that fixes
it, an inventory item its primary chapter, and the *also* rows are for
when the review turns to that topic; load in that order, not all at once.

Then read the project's own documentation and ask the generated questions.
When nobody can answer (a non-interactive run, an owner who is away),
record each question in section 1 as an assumption with the default you
took, and continue.
Nothing in the scan replaces the owner's numbers.

### 2. Establish the numbers

Production metrics first (name the dashboard); otherwise:

```bash
python3 scripts/estimate.py traffic --dau 2M --actions-per-day 5 --payload 2KB \
  --read-write-ratio 20 --peak-factor 3 --retention 2y --server-qps 500
python3 scripts/estimate.py traffic --qps 5000 --payload 100B --read-write-ratio 0   # a rate, not users
python3 scripts/estimate.py traffic --events-per-day 240k --payload 500B --row-bytes 500B
python3 scripts/estimate.py size --count 100k --bytes-each 100B                      # limiter state, a table
python3 scripts/estimate.py availability 99.95
```

`--served-size` separates what a read returns (a rendition, a page) from
what a write stores; `--egress-cost-per-gb` prices the read traffic;
`--row-bytes` counts metadata rows.
The server count applies to request-bound tiers only;
byte-bound tiers are sized by the bandwidth rows.

Record the current figures and the next 10×,
and name which number breaks first.
`references/estimation-cheatsheet.md` has the reference tables.

### 3. Map to the chapters

For each item of the inventory, load the reference the scan names
and compare the project's choice with the chapter's design.
Walk `references/review-checklist.md` group by group;
note misses, and note deliberate deviations as *kept*.

### 4. Options and recommendation

Two or three options with a trade-off table
(cost, complexity, consistency, failure modes, migration effort, chapter),
then a recommendation.
For a review, one recommendation per item with a stable ID (`REC-NN`),
the finding, why it matters, the source, the change, the trade-off,
how to verify, the checklist item it closes, and a status
(`references/design-format.md`).
Group by correctness, availability, scale, operations.

### 5. Rollout and verification

What changes first, how it is measured, how it is rolled back,
what to alert on, and what was not verified.
Hand back the document; apply nothing unless asked and approved by ID.

## Workflow for a new design

Sections 1–6 of the design document in `references/design-format.md`:
context and scope, estimates from the calculator, options,
the recommended design with API, data model, components, flows and deep
dives from the specialist references, rollout, and open questions.

## Modes

- **Quick reference** ("fan-out on write or on read?", "N/W/R for 3 replicas?"):
  answer from the reference with the citation; no document.
- **Review an existing system**: the real-project workflow above.
- **Design a new service or change**: the design document.
- **Capacity planning**: scan for the stores when there is code, otherwise
  state the assumed baseline architecture explicitly; run the calculator on
  the real numbers, including `--served-size` and `--egress-cost-per-gb`
  for byte-bound tiers; name the first bottleneck and the chapter that
  removes it, with the verdict conditional on the assumed baseline.
- **Interview practice**: follow `references/framework.md`;
  as interviewer, withhold the solution and grade against its dos and don'ts.

## Guardrails

- Do not invent scale; ask, or state the assumption where the reader can see it.
- Do not answer with a vendor name; name the property that makes it fit
  (sorted sets, TTL, sequential writes, ACID), then the vendor.
- Do not claim exactly-once delivery, strong consistency or "no single point
  of failure" without saying which mechanism provides it.
- Do not "fix" a choice the project documents as deliberate; report it as *kept*.
- The books date from 2020 and 2022; flag prices, product names and limits
  that may have moved.
- Never skip section 6; unlisted limitations read as unnoticed ones.
