# skill-creator review, 2026-09-22

First evaluation of the skills with Anthropic's
[skill-creator](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator):
four evals, each run once with the skill and once without
(the baseline is the same model with no skill and no access to this
repository), graded against the expectations in `skills/*/evals/evals.json`.
Model: `claude-fable-5-1`.
The raw runs, transcripts, grading and the static viewer
(`review.html`) live in the ignored workspace, not in the repository.

## Evals

| Eval | Skill under test | Fixture |
| --- | --- | --- |
| review-existing-checkout | `system-design-advisor` → `system-design-transactions` | `evals/files/Checkout` |
| capacity-plan-real-numbers | `system-design-advisor` (capacity mode) | none |
| double-booking | `system-design-transactions` | none |
| rate-limiter-choice | `system-design-infrastructure` | none |

## Results

Summary in `benchmark.md`, per-eval rows in `per-eval.md`.
With the skill every expectation passed (25 of 25);
without it 59 % passed.
The baseline runs were strong on content:
the same model finds float money, the missing idempotency key,
the modulo worker placement and the rank scan on its own,
and the double-booking baseline reproduced the race in SQLite.
What the skill adds, and what the failed baseline expectations measure,
is the part a reference is for:
chapter citations on every pattern,
a scan that runs before any recommendation,
recommendation IDs with sources, trade-offs and statuses,
the `kept` status for the documented MySQL decision,
and the calculator's tables in place of prose arithmetic.
By the subagents' own usage reports (`per-eval.md`) the skill costs about
a third more tokens (104 k against 77 k per run on average)
at comparable wall-clock time (520 s against 551 s on the runs with timing).

Three caveats on the numbers.
One run per configuration is too few for the stddev to mean much;
the token and time columns in `benchmark.md` are the aggregator's proxies
(the rate-limiter baseline ended with an API error after writing its
outputs and reported no usage, which drags its time average down);
and the content expectations pass in both configurations,
so they measure the model rather than the skill.
The discriminating expectations are the ones about citations,
the scan, IDs and statuses.

## What the runs said about the skill

The with-skill runs each wrote `user_notes.md` on where the instructions
did not fit.
Every point below was applied in the commit that adds this directory.

- The calculator only took users × actions per day.
  A 40-orders-per-minute checkout and a 5,000-requests-per-second limiter
  had to be faked as DAU.
  Added `--qps` and `--events-per-day`, a `size` subcommand for tables
  and key spaces, `--served-size` for byte-bound read paths,
  `--egress-cost-per-gb`, `--row-bytes`, and peak rows for bandwidth.
- The scanner's "references to load" listed every chapter that mentions
  a technology.
  It now ranks them: the chapter that fixes a finding first,
  each technology's primary chapter second, the rest marked *also*.
- Recommendation IDs `SD-NN` collided visually with scanner rule IDs
  `SD00N`.
  Recommendations are now `REC-NN`.
- Nothing said what to do when there is nobody to ask.
  The advisor, the five specialists and the design format now say:
  record each open question as an assumption with the default taken,
  and continue.
- The advisor had no branch for an existing system whose code was not
  supplied.
  It now skips the scan, builds the inventory from the description,
  and writes the document with a changes-by-ID table.
- `rate-limiter.md` said `INCR` and `EXPIRE` were the whole data
  structure; that is true of a fixed window, not a token bucket.
  Corrected, with a token-bucket Lua sketch and a throughput figure,
  both labelled inference.
- `hotel-reservation.md` gave the CHECK constraint without the 10 %
  allowance and said nothing about multi-night atomicity or taking
  payment outside the lock.
  All three added.
- Importing the scripts left `__pycache__` in the skill tree.
  Documented `python3 -B`; the scanner also disables bytecode writes.

## Not done

Description optimisation with skill-creator's `run_loop` was not run
(see the repository's contributing notes on its parallel-worker bug);
trigger accuracy rests on the hand-written `trigger-evals.json` sets.
