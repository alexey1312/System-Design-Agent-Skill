---
name: system-design-interview
description: >-
  Run a system design interview answer, mock interview or architecture review
  the way the System Design Interview books (Alex Xu, Vol. 1 and 2) teach:
  clarify scope, estimate with back-of-the-envelope numbers, propose a
  high-level design, deep dive, wrap up. Use when someone asks to design,
  architect or scale a system, prepare for or mock a system design interview,
  estimate QPS, storage, bandwidth or servers, choose SQL vs NoSQL, add
  caching, CDN, load balancing, replication or sharding, or asks "how would
  you design X". Routes named systems (rate limiter, key-value store, chat,
  news feed, YouTube, Google Maps, payments, stock exchange, ...) to the
  specialist system-design skills and ships a deterministic estimation
  calculator.
---

# System design interview

Coordinates the five specialist skills.
It owns the order of work, the estimates, the answer format and the routing;
the specialists own the case studies.

| Specialist | Owns |
| --- | --- |
| `system-design-infrastructure` | Rate limiter, consistent hashing, key-value store, unique ID generator, distributed message queue, object storage, metrics monitoring |
| `system-design-content-platforms` | URL shortener, web crawler, news feed, search autocomplete, video streaming, cloud file storage |
| `system-design-realtime-messaging` | Notification system, chat, email, gaming leaderboard, ad click aggregation |
| `system-design-geospatial` | Proximity service, nearby friends, maps and navigation |
| `system-design-transactions` | Hotel reservation, payment system, digital wallet, stock exchange |

## Contract

- **Scope before boxes.**
  Ask the questions in `references/framework.md` first.
  If nobody can answer them (self-study, no interviewer),
  state assumptions explicitly and keep going.
- **Numbers come from the calculator.**
  Run `scripts/estimate.py` and show its table with the assumptions;
  never do the arithmetic in prose.
- **Cite the chapter** for every pattern taken from the books
  (`references/sources.md`), and label everything else *inference*.
- **Every decision names its trade-off.**
  There is no single right answer; there are answers with known costs.
- **Match the scale you were given.**
  Ten transactions per second does not need sharding;
  say so instead of designing for a billion users.
- **In a mock interview, withhold the solution.**

## Routing

Load the specialist whose reference treats the system,
then continue with the workflow below.

| The request mentions | Load |
| --- | --- |
| rate limiting, throttling, consistent hashing, key-value store, Dynamo, Cassandra, unique IDs, Snowflake, message queue, Kafka, object storage, S3, metrics, monitoring, alerting | `system-design-infrastructure` |
| URL shortener, web crawler, news feed, timeline, autocomplete, typeahead, YouTube, video upload or streaming, Google Drive, Dropbox, file sync | `system-design-content-platforms` |
| notifications, push, chat, messenger, email, Gmail, leaderboard, rankings, ad clicks, stream aggregation | `system-design-realtime-messaging` |
| nearby, proximity, Yelp, geohash, quadtree, nearby friends, live location, maps, navigation, ETA, routing | `system-design-geospatial` |
| hotel, booking, reservation, tickets, payments, checkout, PSP, ledger, wallet, balance transfer, distributed transaction, stock exchange, order book, matching engine | `system-design-transactions` |

A system that is not one of the 28 case studies is composed from the pattern
index in `references/building-blocks.md` and the nearest case study.
Say which one you are borrowing from.

## Workflow

### 1. Scope (3–10 minutes of a 45-minute interview)

Functional requirements, non-functional requirements, what is out of scope,
and the numbers: users, DAU, actions per user, payload sizes, retention,
read/write ratio, latency and availability targets.
Write the assumptions down before drawing anything.

### 2. Estimate

```bash
python3 scripts/estimate.py traffic --dau 10M --actions-per-day 2 --payload 1KB \
  --read-write-ratio 10 --peak-factor 2 --retention 5y
python3 scripts/estimate.py availability 99.99
python3 scripts/estimate.py latency
```

Paste the table into section 2 of the answer.
`references/estimation-cheatsheet.md` has the reference numbers
(powers of two, latency, availability) and the worked Twitter example.

### 3. High-level design

API endpoints, data model and store choice
(`references/building-blocks.md` › Choosing a store), the components,
and the main write and read flows, numbered.
Draw the diagram in Mermaid when the tool renders it, otherwise in text.
Ask for buy-in before going deeper.

### 4. Deep dive

Choose two or three components that carry the risk
and load the specialist reference for the case study.
For each: the mechanism, the alternatives, a trade-off table, the citation.

### 5. Wrap-up

Bottlenecks, failure modes, the next order of magnitude,
what you would add with more time, open questions.
The full skeleton and the review-status vocabulary are in
`references/design-format.md`.

## Modes

- **Interview answer**: the full skeleton, in the time budget.
- **Mock interview**: play the interviewer as described in
  `references/framework.md` › Running a mock interview;
  grade against the dos and don'ts at the end.
- **Design review of an existing system**: ask for the architecture, code or
  runbooks; map each part to a chapter; produce recommendations with stable
  IDs and statuses (`references/design-format.md`); change nothing unless asked.
- **Quick question** ("fan-out on write or on read?"):
  answer from the reference with the citation; skip the skeleton.

## Guardrails

- Do not invent scale.
  Ask, or state the assumption where the reader can see it.
- Do not answer with a vendor name; name the property that makes it fit
  (sorted sets, TTL, sequential writes, ACID), then the vendor.
- Do not claim exactly-once delivery, strong consistency or "no single point
  of failure" without saying which mechanism provides it.
- The books date from 2020 and 2022.
  Flag prices, product names and limits that may have moved.
- Never skip the wrap-up; unlisted limitations read as unnoticed ones.
