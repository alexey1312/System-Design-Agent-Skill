# Design a rate limiter

Source: Vol. 1 ch. 4 (upstream `04. Rate Limiter`).

A rate limiter caps how many requests a client or service may send in a period
and rejects the excess.
It prevents resource starvation from abusive or buggy clients,
cuts the cost of serving needless calls to paid third-party APIs,
and keeps servers from overloading.

## Scope questions

- Client-side or server-side? (Server-side: client code can be forged.)
- Throttle by what? IP, user ID, API key, endpoint, or several rules at once.
- Scale: many servers, many rules, distributed environment.
- A separate service or middleware, or code inside the application?
- Should the user learn they were throttled? (Yes: HTTP 429 plus headers.)

Requirements the chapter settles on:
accurate limiting, low latency added to the request path,
little memory, works across many servers, clear rejection,
and high fault tolerance (a limiter outage must not take the API down).

## Where it lives

| Placement | Verdict |
| --- | --- |
| Client | Unreliable; clients are forged |
| Server application code | Fine for a monolith with one rule set |
| Middleware / API gateway | Preferred with microservices; gateways already do auth, IP allow-lists, SSL termination |

Pick by the tech stack you already run and by whether you can afford to build one.
Commercial gateways are a legitimate answer when engineering time is short.

## Algorithms

| Algorithm | How | Pros | Cons |
| --- | --- | --- | --- |
| Token bucket | Bucket of size *b* refilled at *r* tokens/s; each request takes one token; empty bucket → reject | Simple, tiny memory, allows short bursts | Two parameters to tune per rule |
| Leaking bucket | FIFO queue drained at a fixed rate; full queue → reject | Stable outflow, tiny memory | Bursts of new traffic wait behind old requests; tuning |
| Fixed window counter | Counter per window; reset at the edge | Simplest, memory-light | A burst straddling a window edge passes 2× the quota |
| Sliding window log | Store every request timestamp; count those inside the trailing window | Exact | Memory grows with traffic, even rejected requests keep their log entry |
| Sliding window counter | Weighted blend of the previous and current fixed windows | Smooths edge bursts, memory-light | Approximate (Cloudflare measured 0.003 % wrong decisions) |

Token bucket is the default answer for APIs
(Amazon and Stripe use it);
one bucket per endpoint, per IP, or a global bucket for a system-wide cap.
Leaking bucket suits a fixed processing rate (Shopify).
Uber's `ratelimit` Go package is a leaky-bucket implementation.

## Architecture

- Counters live in an in-memory store, not a database.
  For a fixed-window counter, Redis `INCR` and `EXPIRE` are the whole data
  structure; a token bucket keeps two fields per key (tokens, last refill
  time) and must read, refill and decrement them in one atomic step.
- Middleware fetches the counter, compares with the rule, and either
  forwards the request or returns 429.
- Rules are files on disk, cached by workers, refreshed periodically.
- Rejected requests may be dropped or queued for later
  (a queue is the right choice when the excess is legitimate).
- Return headers: `X-Ratelimit-Remaining`, `X-Ratelimit-Limit`, `X-Ratelimit-Retry-After`.

## Distributed environment

- **Race conditions** on read-modify-write of a counter.
  Locks are slow; use a Lua script or a Redis sorted set for an atomic check-and-increment.
  A token-bucket script (inference, not from the chapter):

  ```lua
  -- KEYS[1] = bucket key; ARGV = rate per second, capacity, now (ms), cost
  local tokens = tonumber(redis.call('HGET', KEYS[1], 'tokens') or ARGV[2])
  local last = tonumber(redis.call('HGET', KEYS[1], 'ts') or ARGV[3])
  tokens = math.min(ARGV[2], tokens + (ARGV[3] - last) / 1000 * ARGV[1])
  local allowed = tokens >= tonumber(ARGV[4])
  if allowed then tokens = tokens - ARGV[4] end
  redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', ARGV[3])
  redis.call('PEXPIRE', KEYS[1], math.ceil(ARGV[2] / ARGV[1] * 1000) * 2)
  return { allowed and 1 or 0, math.floor(tokens) }
  ```

  One Redis node runs such scripts on the order of 100k per second
  (inference; measure on your hardware), so 5,000 requests per second is
  one primary with a replica, and the first thing to break at 10× is that
  single primary; shard buckets by client key before that.
- **Synchronization** across many limiter instances.
  Sticky sessions do not scale;
  a centralised store (Redis) is the standard fix.
- **Multi-region**: deploy limiters and stores near users,
  accept eventual consistency between regions.
- **Monitoring** whether the algorithm and the rules match reality:
  too many rejections on a flash sale means the rule is too tight.

## Wrap-up talking points

Hard limits versus soft limits (brief overshoot allowed);
limiting at other layers (IPtables at L3);
client-side hygiene: cache responses, honour `Retry-After`,
back off exponentially, catch exceptions gracefully.
