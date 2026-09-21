# Design a URL shortener

Source: Vol. 1 ch. 8 (upstream `08. URL Shortener`).

## Scope and numbers

Shorten a long URL; redirect a short one; high availability, scalability,
fault tolerance.
100 million URLs created per day → 1,160 writes/s;
reads 10:1 → 11,600 reads/s;
10 years → 365 billion records;
100 bytes per URL → 36.5 TB.
Short URLs as short as possible, from `[0-9a-zA-Z]`; no deletion or update.

## API

- `POST /api/v1/data/shorten` with `{longUrl}` → short URL.
- `GET /api/v1/{shortUrl}` → HTTP redirect to the long URL.

**301** (permanent) lets browsers cache the mapping and skip the service on repeat
clicks: less load.
**302** (temporary) sends every click through the service: click analytics.
Choose by whether analytics matter.

## Data model

Do not keep the map in memory; store `id, shortURL, longURL` in a relational table.

## Hash function

Seven characters of base 62 give 62^7 ≈ 3.5 trillion combinations, enough
for 365 billion.

| Approach | Length | Needs ID generator | Collisions | Guessable |
| --- | --- | --- | --- | --- |
| Hash (CRC32, MD5, SHA-1) truncated to 7 chars + collision resolution | Fixed | No | Yes; on collision append a salt and rehash, checking the DB each time (a Bloom filter makes the check cheap) | No |
| Base-62 conversion of a unique ID | Grows with the ID | Yes | No | Yes, if IDs are sequential; a security concern |

Example: ID 11157 → `2TX`; ID 2009215674938 → `zn9edcu`.
The chapter picks base 62 with a distributed ID generator (`unique-id-generator.md`).

## Flows

Shorten: look up the long URL; if present return its short URL;
otherwise get an ID, encode it, insert `id, shortURL, longURL`.

Redirect: check the cache for the short URL; on a miss read the database
(and warm the cache); return 301 or 302.

## Wrap-up

Rate limiting by IP (`rate-limiter.md` in the infrastructure skill);
stateless web tier; database replication and sharding;
analytics on clicks (source, time); availability through redundancy.
