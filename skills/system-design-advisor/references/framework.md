# A framework for system design interviews

Source: Vol. 1 ch. 3 (upstream `03. System Design Framework`).

The interview simulates real design work with a vague problem.
It tests collaboration, handling ambiguity, asking good questions,
and resisting over-engineering as much as technical depth.
Red flags: narrow-mindedness, stubbornness, jumping to a solution.

## Step 1: understand the problem and establish scope (3–10 min)

Do not answer without thinking.
Ask; slow down; write assumptions down.
Questions to ask:

- What exact features are we building?
- How many users? What growth in 3, 6, 12 months?
- Web, mobile, or both?
- What does the company already run (tech stack, existing services to reuse)?
- What do the read/write patterns look like?

Example (news feed): mobile, web, or both?
Most important features? Feed order (reverse chronological or ranked)?
Max friends per user? Traffic volume? Media in posts?

## Step 2: propose a high-level design and get buy-in (10–15 min)

- Draw the boxes: clients, APIs, web servers, data stores, cache, CDN,
  message queue, and so on.
- Treat the interviewer as a teammate; ask for feedback as you go.
- Back-of-the-envelope estimates to check the sketch holds; ask first whether
  they want them.
- Walk through a few concrete use cases to find edge cases.
- Include API endpoints and the database schema only if the problem is small
  enough or the interviewer asks; for a large system it is too low-level.

Example (news feed): two flows, feed publishing and feed building,
each drawn end to end.

## Step 3: design deep dive (10–25 min)

By now you agree on goals, scope and a blueprint, and you know which parts
carry risk.
Pick the components that matter for this problem;
sometimes the interviewer signals which.
Manage time: do not sink into details that show nothing
(the EdgeRank algorithm is a distraction when the system's scalability is the question).

Examples: URL shortener → the hash function; chat → latency and presence;
news feed → publishing and retrieval flows with fan-out trade-offs.

## Step 4: wrap-up (3–5 min)

- Name the bottlenecks and possible improvements; never claim perfection.
- Recap the design, especially where alternatives were weighed.
- Failure modes: a server dies, the network partitions.
- Operations: monitoring metrics and error logs, rollout.
- The next scale curve: 1 million users → 10 million.
- Further refinements with more time.

## Dos and don'ts

Do: ask for clarification; understand requirements; remember there is no
single right answer; communicate your thinking; suggest several approaches;
after buy-in, go deep on the most critical components; bounce ideas off the
interviewer; never give up.

Don't: arrive without practising common questions; start without clarifying;
go too deep on one component too early; go silent when stuck;
think the interview ends at the diagram (ask for feedback early and often).

## Time budget (45 minutes)

| Step | Minutes |
| --- | --- |
| 1. Scope | 3–10 |
| 2. High-level design | 10–15 |
| 3. Deep dive | 10–25 |
| 4. Wrap-up | 3–5 |

## Running a mock interview

When asked to play the interviewer:
state the problem in one sentence,
answer scope questions the way the chapters do (give numbers, cut scope),
withhold the solution, prompt for estimates, push on one deep-dive area,
and grade with the dos and don'ts above plus `design-format.md`.
