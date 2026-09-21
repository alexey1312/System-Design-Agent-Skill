# Design answer format

Use this shape whether the output is an interview answer,
a design document for a real system,
or feedback on someone else's design.
It follows the four-step framework of Vol. 1 ch. 3
and keeps every claim traceable.

## Skeleton

```markdown
# <System> — design

## 1. Scope
Functional: <3–6 bullets, each one a feature the design must support>
Non-functional: <latency, availability, consistency, durability, privacy>
Out of scope: <what was explicitly excluded and why>
Assumptions: <every number or constraint you supplied yourself>

## 2. Estimates
| Quantity | Value | Derivation |
| --- | --- | --- |
| Write QPS (avg / peak) | … | … |
| Read QPS (avg / peak) | … | … |
| Storage (per day / retained) | … | … |
| Bandwidth / cache / servers | … | … |
Source: scripts/estimate.py <arguments>

## 3. High-level design
API: <endpoints with parameters and responses>
Data model: <tables or key spaces, partition keys, why SQL or NoSQL>
Components: <diagram in text or Mermaid, then one line per box>
Main flows: <write path, read path, numbered>

## 4. Deep dive
<2–3 components chosen because they carry the risk: the algorithm,
 the consistency mechanism, the hot path. Each with alternatives and a
 trade-off table.>

## 5. Wrap-up
Bottlenecks and how to remove them · failure modes · what to add with more time ·
open questions for the interviewer or stakeholders
```

## Rules

- **Scope before boxes.**
  If the requirements are unknown, ask; if nobody can answer, state assumptions
  in section 1 and continue.
  Never draw the architecture first.
- **Numbers come from the calculator.**
  Run `scripts/estimate.py` and paste its derivation.
  Hand arithmetic in prose is where estimates go wrong.
- **Every decision names its trade-off.**
  "Use Redis" is not a decision; "Redis sorted set because rank queries are
  O(log N) and the whole board fits in 650 MB" is.
- **Cite the chapter** for a pattern taken from the books (`references/sources.md`),
  and label anything else *inference*.
- **Depth over breadth in the deep dive.**
  Pick the parts the interviewer or reviewer cares about;
  a URL shortener's deep dive is the hash, a chat system's is delivery and presence.
- **Say what you did not cover.**
  A wrap-up that lists open questions beats one that claims completeness.

## Status vocabulary for design reviews

When reviewing an existing system rather than inventing one,
give every recommendation an ID and a status the owner can act on:

| Status | Meaning |
| --- | --- |
| `proposed` | Recommendation made; nothing changed |
| `accepted` | Owner agreed; to be implemented |
| `declined` | Owner disagreed; record the reason |
| `kept` | Existing choice is deliberate and documented; leave it |
| `needs-data` | Cannot decide without a measurement; say which |

```markdown
### SD-03 · Move rank queries off MySQL
- **Finding:** `GET /scores/{user}` runs a correlated COUNT over the table
- **Why it matters:** O(N) per request; the table has 25 M rows
- **Source:** Vol. 2 ch. 10 › Redis solution
- **Change:** Redis sorted set, ZREVRANK; MySQL stays as the source of truth
- **Trade-off:** one more stateful service; rebuild from MySQL on Redis loss
- **Status:** proposed
```

## Time budget for a 45-minute interview

| Step | Minutes |
| --- | --- |
| Scope and requirements | 3–10 |
| High-level design and buy-in | 10–15 |
| Deep dive | 10–25 |
| Wrap-up | 3–5 |
