# Payment system

Source: Vol. 2 ch. 11 (upstream `26. Payment System`).

## Scope and numbers

Payment backend for an e-commerce site; credit cards through a third-party
**payment service provider** (Stripe, Braintree, Adyen);
no card data stored (PCI); single currency; 1 million transactions a day;
pay-in and pay-out; reconciliation.
1 M per day ≈ 10 TPS: throughput is not the problem; correctness is.

## Pay-in flow

Actors: **payment service** (accepts events, risk check via a third party for
AML and fraud), **payment executor** (runs one payment order via the PSP),
**PSP** (moves money), **card schemes** (Visa, Mastercard),
**ledger** (every money movement), **wallet** (merchant balances).

1. Order placed → payment event stored by the payment service.
2. For each payment order: executor stores it and calls the PSP.
3. Wallet updated with the seller's balance.
4. Ledger records the movement.

## API

`POST /v1/payments` with `buyer_info, checkout_id, credit_card_info,
payment_orders[]`; each order has `seller_account, amount (string), currency,
payment_order_id` (globally unique, forwarded to the PSP as the idempotency key).
`GET /v1/payments/{id}` → status.
Amounts are strings: floating point is wrong for money.

## Data model

Relational (ACID, mature tooling, DBAs, financial track record).
`payment_events(checkout_id PK, buyer_info, seller_info, credit_card_info,
is_payment_done)`.
`payment_orders(payment_order_id PK, buyer_account, amount, currency,
checkout_id FK, payment_order_status, ledger_updated, wallet_updated)`.
Status: `NOT_STARTED → EXECUTING → SUCCESS | FAILED`, driven by a background job
that alerts when an order stalls.

**Double-entry ledger**: every movement debits one account and credits another;
the entries sum to zero; end-to-end traceability.

**Hosted payment page**: the PSP's widget collects card details so the site
never touches them.

## Pay-out

Same components, money flows from the site to merchants;
an accounts-payable provider (Tipalti) handles the bookkeeping.

## Deep dive

### PSP integration

Direct bank or card-scheme connections are rare.
Hosted-page flow: client → payment service registers the order with the PSP
(amount, currency, expiry, order UUID as nonce) → PSP returns a token →
token stored → hosted page shown with the token and redirect URLs →
user pays → redirected back → PSP webhook confirms asynchronously → status recorded.

### Reconciliation

Nightly settlement file from the PSP compared with internal state;
also ledger versus wallet.
Mismatches: auto-adjustable, manually adjustable, or investigated by finance.

### Delays

Risk review or 3-D Secure can take hours:
wait for the webhook (or poll), show "pending", email on completion.

### Communication

Synchronous HTTP: simple, but slow chains, poor failure isolation, coupling,
no buffer.
Asynchronous: single-receiver queues or pub/sub with many receivers;
pub/sub fits because one payment has several side effects.

### Failed payments

Track state; a **retry queue** for transient failures;
a **dead-letter queue** for terminal failures to inspect.

### Exactly-once

At-least-once via retries (immediate, fixed, incremental, exponential backoff
as the default, cancel on terminal errors; honour `Retry-After`).
At-most-once via **idempotency**: an `idempotency-key` header (UUID);
the server inserts it under a unique constraint and returns the existing result
on violation; the PSP deduplicates on the nonce.

### Consistency

Exactly-once processing plus reconciliation gives eventual consistency
across PSP, ledger, wallet and payment service.
Replication lag: serve from the primary and keep replicas for failover,
or use consensus-based databases (Paxos/Raft; YugabyteDB, CockroachDB).

### Security

HTTPS, integrity monitoring, certificate pinning, multi-region replication and
snapshots, rate limiting and firewalls, tokenisation instead of card storage,
PCI DSS, fraud checks (AVS, CVV, behaviour analysis).

## Wrap-up

Monitoring and alerting, debugging tools for failed payments,
currency exchange, regional payment methods, cash, Apple/Google Pay.
