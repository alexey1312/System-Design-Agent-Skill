# Distributed email service

Source: Vol. 2 ch. 8 (upstream `23. Distributed Email Service`).

## Scope and numbers

1 billion users; send, receive, fetch, filter, search; anti-spam;
HTTP APIs for the web client (SMTP, IMAP, POP still supported for others);
attachments up to 25 MB.
10 sent per user per day → 100 k emails/s.
40 received per user per day at 50 KB metadata → 730 PB per year;
20 % with a 500 KB attachment → 1,460 PB per year.
Reliable (no loss), available, scalable, extensible.

## Email 101

SMTP sends between servers; POP downloads and deletes;
IMAP keeps mail on the server; webmail uses HTTPS.
DNS MX records name the servers accepting mail for a domain.
Attachments travel base64-encoded.

Traditional servers keep one file per message on local disk;
disk I/O becomes the bottleneck and availability is poor.

## APIs

- `POST /v1/messages` (To, Cc, Bcc in the body).
- `GET /v1/folders`; `GET /v1/folders/{id}/messages` (paginated);
  `GET /v1/messages/{id}`.

## High-level design

Web servers (login, profile), **real-time servers** (WebSocket, long-polling
fallback), **metadata DB**, **attachment store** (S3), distributed cache
(recent mail in Redis), **search store**.

**Sending**: load balancer (rate limit) → web server (validate size, spam check,
short-circuit same-domain) → outgoing queue (attachments by reference) →
SMTP outgoing workers (spam and virus check, route by MX) → Sent folder.
Watch the outgoing queue: growth means a dead recipient server
(retry with backoff) or too few workers.

**Receiving**: SMTP load balancer → SMTP servers (acceptance policy) →
large attachments to object store → incoming queue → mail-processing workers →
metadata DB, cache, object store, real-time push; offline users pull later.

## Metadata database

Headers small and hot; bodies read once; operations are per user;
recent mail dominates; no loss allowed.
Relational databases are tuned for small rows; object stores cannot search
or flag; Gmail's Bigtable is not open.
Describe the properties instead: single-digit-MB columns, strong consistency,
low disk I/O, highly available, incremental backups.

Partition by `user_id`.
Tables: `folders`, `emails` (`email_id` is a TIMEUUID clustering key),
`attachments`.
Read/unread filtering on a non-key column is not allowed in Cassandra,
so denormalise into `emails_read` and `emails_unread`.
Conversation threads come from the `Message-Id`, `In-Reply-To`, `References` headers.
Choose consistency over availability: brief unavailability during failover is acceptable.

## Deliverability

Dedicated IPs, separate marketing from transactional mail,
warm up new IPs over 2–6 weeks, ban spammers fast,
feedback loops with ISPs, SPF and DKIM.

## Search

Per-user scope, sorted by attributes, must be instant and accurate.
Writes outnumber reads (every mutation reindexes).
Elasticsearch partitioned by `user_id`, reindexing asynchronously via Kafka;
or a custom LSM-tree index (write-optimised, as in Cassandra, Bigtable, RocksDB)
that can be the datastore itself.

## Scalability and availability

Users are independent, so components scale out;
multi-DC with leader-follower failover.

## Wrap-up

Fault tolerance per component; GDPR and PII; encryption, phishing protection;
attachment deduplication.
