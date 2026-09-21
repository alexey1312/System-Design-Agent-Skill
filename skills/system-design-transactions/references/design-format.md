# Design document and review format

Use these shapes for every deliverable:
a design document for a new service or a change,
a review of an existing system,
or, in interview mode, a spoken answer.
They follow the four steps of Vol. 1 ch. 3 and keep every claim traceable.

## Design document

```markdown
# <System or change> — design

## 1. Context and scope
Current state: <what exists today; numbers from production metrics where available>
Functional: <3–6 bullets, each a capability the design must provide>
Non-functional: <latency, availability, consistency, durability, privacy, cost>
Out of scope: <what was explicitly excluded and why>
Assumptions: <every number or constraint you supplied yourself>

## 2. Estimates
| Quantity | Value | Derivation |
| --- | --- | --- |
| Write QPS (avg / peak) | … | … |
| Read QPS (avg / peak) | … | … |
| Storage (per day / retained) | … | … |
| Bandwidth / cache / servers | … | … |
Source: scripts/estimate.py <arguments>   (or the metrics dashboard, named)
Next 10×: <which number breaks first>

## 3. Options
<2–3 options, one paragraph each, then a trade-off table: cost, complexity,
 consistency, failure modes, migration effort, the chapter each comes from>

## 4. Recommended design
API: <endpoints with parameters and responses>
Data model: <tables or key spaces, partition keys, why this store>
Components: <diagram in text or Mermaid, then one line per box>
Main flows: <write path, read path, numbered>
Deep dive: <the 2–3 components that carry the risk, each with alternatives>

## 5. Rollout and verification
<what changes first, how it is measured, how it is rolled back,
 what to alert on, which checklist items (RC-x.y) this closes>

## 6. Risks and open questions
<bottlenecks, failure modes, questions for the owners, what was not verified>
```

## Review recommendations

When reviewing an existing system, start from `scripts/arch_scan.py`
and `references/review-checklist.md`,
then give every recommendation an ID and a status the owner can act on.

```markdown
### SD-03 · Move rank queries off MySQL

- **Finding:** `api/scores.py:41` — `SELECT COUNT(*) FROM leaderboard WHERE score >= …` per request (scan SD007)
- **Why it matters:** O(N) per request; the table has 25 M rows and p99 is 4 s
- **Source:** Vol. 2 ch. 10 › Redis solution
- **Change:** Redis sorted set keyed per season; ZINCRBY on score, ZREVRANK for rank; MySQL stays the source of truth and rebuilds the set on loss
- **Trade-off:** one more stateful service to run; replica and persistence needed
- **Verify:** p99 of `GET /scores/{user}` under 50 ms at 2,500 updates/s; rebuild drill from MySQL
- **Checklist:** RC-7.4
- **Status:** proposed
```

| Status | Meaning |
| --- | --- |
| `proposed` | Recommendation made; nothing changed |
| `accepted` | Owner agreed; to be implemented |
| `declined` | Owner disagreed; record the reason |
| `kept` | Existing choice is deliberate and documented; leave it |
| `needs-data` | Cannot decide without a measurement; say which |

Group recommendations by impact:
**correctness** (money, inventory, data loss),
**availability** (single points of failure, failover),
**scale** (the first bottleneck at the next 10×),
**operations** (monitoring, rollout).
Inside a group, order by user impact, not by file.

## Rules

- **Scope before boxes.**
  If the requirements are unknown, ask; if nobody can answer, write the
  assumptions into section 1 and continue.
  Never draw the architecture first.
- **Numbers come from metrics or the calculator.**
  Name the dashboard, or run `scripts/estimate.py` and paste its derivation.
  Arithmetic in prose is where estimates go wrong.
- **Every decision names its trade-off.**
  "Use Redis" is not a decision; "Redis sorted set because rank queries are
  O(log N) and the whole board fits in 650 MB" is.
- **Cite the chapter** for a pattern taken from the books (`references/sources.md`),
  and label anything else *inference*.
- **Respect deliberate decisions.**
  A documented choice that contradicts a chapter is reported as *kept*
  with the reason, not rewritten.
- **Depth over breadth in the deep dive.**
  A URL shortener's deep dive is the hash; a chat system's is delivery and presence.
- **Say what you did not verify.**
  A recommendation whose *Verify* line was not run is a step for the owner,
  not a claim.

## Interview mode

The spoken answer uses sections 1, 2, 4 and 6 in that order,
with section 3 folded into the deep dive as alternatives,
inside this budget for a 45-minute interview:

| Step | Minutes |
| --- | --- |
| Scope and requirements | 3–10 |
| High-level design and buy-in | 10–15 |
| Deep dive | 10–25 |
| Wrap-up | 3–5 |
