---
name: system-design-transactions
description: >-
  Design the money- and inventory-critical systems the System Design
  Interview books cover: a hotel reservation system (room-type inventory,
  idempotency key, optimistic vs pessimistic locking, database constraints,
  overbooking), a payment system (PSP integration, hosted payment page,
  double-entry ledger, reconciliation, retries with idempotency,
  exactly-once), a digital wallet (2PC vs Try-Confirm/Cancel vs Saga, event
  sourcing, CQRS, Raft, 1M TPS) and a stock exchange (sequencer, matching
  engine, order book, mmap event bus, application loop, multicast). Use when
  asked to design, compare or review bookings, checkout, ledgers, balance
  transfers, distributed transactions, order matching, or anything where
  double-booking or double-charging is the risk.
---

# Transactions and money movement

Four case studies where correctness outranks throughput and the deep dive
is always about concurrency, atomicity and auditability.
The advisor (`system-design-advisor`) owns the scan, the numbers and the
answer format; this skill owns the case studies.

| System | Reference | Where the risk is |
| --- | --- | --- |
| Hotel reservation | `references/hotel-reservation.md` | Room-type inventory table; double booking; locking options; sharding by hotel |
| Payment system | `references/payment-system.md` | PSP hosted page and webhooks; ledger; reconciliation; retry and idempotency |
| Digital wallet | `references/digital-wallet.md` | 2PC vs TC/C vs Saga; event sourcing; local mmap log; Raft; CQRS |
| Stock exchange | `references/stock-exchange.md` | Sequencer and determinism; order book structure; single-server mmap; failover |

## How to use

1. On a real project, run `scripts/arch_scan.py` first;
   payment providers and relational stores in its inventory, and findings
   `SD001`, `SD002`, `SD004` and `SD005` (money types, locking), say where
   to look.
   For a new design, run the advisor's scope and estimate steps;
   note that three of the four case studies have low TPS, so the answer is
   never "shard first" but "make it correct, then scale".
2. Load the one reference the request names;
   the wallet's event-sourcing section is shared by the exchange.
3. Lead with the failure that costs money (double booking, double charge,
   lost transfer, unfair fill) and design backwards from it.
4. Cite the chapter (`references/sources.md`) and label your own additions.
5. When there is nobody to ask (a non-interactive run, an owner who is
   away), write each open question into section 1 of the document as an
   assumption with the default you took, and continue
   (`references/design-format.md` › Rules).

## On a real project

- **Mutating endpoints**: list every POST/PUT that moves money or
  inventory and check each for an idempotency key with a unique constraint
  (`RC-5.1`).
- **Money types**: `SD001` and `SD004` mark floats; check the API too
  (amounts as strings).
- **Locking**: `SD002` marks pessimistic locks; read the transaction
  length and the contention; `SD005` marks timestamp-based versions.
- **Providers**: find the webhook handler, its idempotency, and the
  nightly reconciliation against the settlement file.
- **Ledger**: find whether every movement has two entries and whether
  balances are derived or stored.
- **Cross-service consistency**: find distributed transactions; check for
  a phase status table (TC/C) or an orchestrator (Saga) and the
  compensation path.
- **Matching or ordering**: find the sequencer, determinism (no
  wall-clock reads in the engine), and the replay path.

## Cross-cutting rules

- **Idempotency key on every mutating request**, enforced by a unique
  constraint; the PSP gets it as the nonce.
- **Amounts are strings or integers in minor units**, never floats.
- **Choose the concurrency control by contention**: optimistic locking or a
  constraint when conflicts are rare, pessimistic only under heavy contention,
  and say why.
- **Distributed transactions are a last resort**: keep dependent operations
  in one database when you can; otherwise TC/C for latency, Saga
  orchestration for linear workflows, 2PC almost never.
- **Immutable history**: double-entry ledger, event sourcing, sequencer
  streams; current state is derived and rebuildable.
- **Reconciliation is part of the design**, not an afterthought.
- **Determinism enables replay and failover**: no wall-clock reads, no
  external I/O inside the state machine.

## Pitfalls

- Reserving a room ID instead of a room type.
- `SELECT … FOR UPDATE` on a long-lived transaction stalls everyone.
- Storing card numbers: PCI scope you do not want; use the hosted page.
- Retrying a payment without an idempotency key charges twice.
- `−1 / +1` in a single TC/C try phase needs 2PC after all.
- Kafka as an exchange sequencer: milliseconds where microseconds are needed.
- Logging on the critical path of the matching engine.

Shared references: `references/review-checklist.md`,
`references/estimation-cheatsheet.md`, `references/building-blocks.md`,
`references/design-format.md`;
scripts: `scripts/arch_scan.py` (read-only project scan),
`scripts/estimate.py` (calculator).
