# Stock exchange

Source: Vol. 2 ch. 13 (upstream `28. Stock Exchange`).

## Scope and numbers

Stocks only; place and cancel **limit orders**; trading hours only;
real-time fills and order book; tens of thousands of concurrent users,
~100 symbols, billions of orders a day; simple risk checks
(for example 1 M shares of one stock per user per day); wallet holds funds for
pending orders.
Availability ≥ 99.99 %, fault tolerance with fast recovery,
millisecond round trips with attention to p99, KYC, DDoS protection.
1 billion orders over 6.5 trading hours → 43 k QPS; peak 5× → 215 k;
the open is the busiest.

## Business 101

Brokers (Robinhood, Fidelity) front the exchange; institutions use special
software and split large orders.
Limit orders name a price and may fill partially; market orders fill at once.
Bid = highest buy, ask = lowest sell.
Market data tiers: L1 best bid/ask, L2 several price levels, L3 queued
quantities per level.
Candlesticks: open, close, high, low per interval.
FIX is the wire protocol most vendors speak.

## High-level design

**Trading flow (critical path)**: client → broker → **client gateway**
(validation, rate limit, auth) → **order manager** (risk checks from the
risk manager, wallet check) → **sequencer** → **matching engine** → fills back
through the sequencer to the gateway.

**Market data flow**: matching engine executions → **market data publisher**
(rebuilds order book, candlesticks) → data service → brokers.

**Reporting flow**: **reporter** persists orders and executions for history,
tax, compliance, settlement; accuracy over latency.

- **Matching engine**: order book per symbol; matches produce two fills;
  emits the execution stream; must be **deterministic**.
- **Sequencer**: stamps every inbound order and outbound fill with a sequence
  ID for fairness, replay and exactly-once; Kafka would work but is too slow.
- **Order manager**: order state, risk, wallet, forwards trimmed orders,
  returns fills; event sourcing manages its state transitions.
- **Client gateway**: lightweight; several variants (retail, institutional
  colocated engines).

## API

`POST /v1/order` (symbol, side, price, orderType, quantity) →
id, creationTime, filledQuantity, remainingQuantity, status.
`GET /execution?symbol&orderId&startTime&endTime`.
`GET /marketdata/orderBook/L2?symbol&depth`.
`GET /marketdata/candles?symbol&resolution&startTime&endTime`.

## Data models

Product, order, execution: in memory on the critical path (recovered from the
sequencer), written by the reporter, forwarded to market data.

**Order book**: per side, a map from price to a **price level**
(limit price, total volume, doubly linked list of orders) plus best bid/offer
and `orderMap` by order ID.
Add = append to tail O(1); match = pop head O(1);
cancel = O(1) via `orderMap` and the doubly linked node.
Matching is FIFO within a price level.

**Candlesticks**: ring buffers, bounded in memory, rest on disk;
an in-memory columnar store (KDB) for real-time analytics, persisted after close.

## Deep dive

### Latency

Shorten the critical path (no logging on it) and each task
(no network, no disk).
Everything on **one server**; components talk through an **mmap** event store
(a file in `/dev/shm`, so no disk at all); each component runs an **application
loop** pinned to a core (no context switches, no lock contention).
Target tens of microseconds rather than tens of milliseconds.

### Event sourcing

Immutable state transitions instead of current state
(see `digital-wallet.md`).
Gateway speaks FIX; order manager validates and emits events;
matching core emits `OrderFilledEvent`; every component subscribes to the
event store; the sequencer is a single writer that orders events before they
enter the store.
Each component embeds the order manager as a library.

### High availability

99.99 % is 8.64 s of downtime a day.
Warm standbys of the matching engine consume inbound events but do not
publish until promoted; heartbeats detect failure; failover is automated.
Beyond one server: hot/warm replica servers with the event store replicated
over reliable UDP.

### Fault tolerance

Replicate to data centers in other cities; decide failover triggers,
leader election (Raft), RTO, and degraded modes.
Bugs hit primary and replicas alike, so use chaos engineering and start with
manual failover.
Data loss is unacceptable: back up often and rely on Raft replication.

### Determinism

Functional determinism comes from the sequencer: wall-clock time is irrelevant.
Latency determinism is measured at p99 and p99.99;
garbage-collection pauses are the usual culprit.

### Market data

Ring buffer (fixed, preallocated, lock-free) with cache-line padding.
**Multicast** over reliable UDP so all subscribers receive data at once
(fairness); retransmissions patch UDP loss.
**Colocation** sells brokers rack space next to the engine.

### Security

Isolate public services; cache infrequently changing data;
prefer cacheable URLs (`/data/recent` over query strings);
allow-lists and block-lists; rate limiting.

## Wrap-up

Not every exchange is one big box; many now run in the cloud and some use
automated market makers instead of an order book.
