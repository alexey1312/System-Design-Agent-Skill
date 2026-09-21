<p align="center">
  <img src="assets/banner.svg" alt="System Design Agent Skills — scope, estimate, design, deep dive and wrap up any system design question" width="100%">
</p>

# System Design Agent Skills

[![Validate](https://github.com/alexey1312/System-Design-Agent-Skill/actions/workflows/validate.yml/badge.svg)](https://github.com/alexey1312/System-Design-Agent-Skill/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/alexey1312/System-Design-Agent-Skill?sort=semver)](https://github.com/alexey1312/System-Design-Agent-Skill/releases)
[![GitHub Stars](https://img.shields.io/github/stars/alexey1312/System-Design-Agent-Skill?style=flat&color=brightgreen)](https://github.com/alexey1312/System-Design-Agent-Skill/stargazers)

**Six coordinated Agent Skills that answer system design questions the way
the *System Design Interview* books teach** —
scope first, back-of-the-envelope numbers from a calculator,
a high-level design, a deep dive, a wrap-up —
with all 28 case studies from both volumes condensed into references.
They work in any AI coding tool that supports the
[Agent Skills open format](https://agentskills.io/home).

The skills turn Alex Xu's *System Design Interview – An Insider's Guide*
(Vol. 1) and *Volume 2* (with Sahn Lam), as summarised in the
[system-design-notes](https://github.com/liquidslr/system-design-notes)
repository, into a repeatable workflow:
clarify the scope, estimate with a deterministic script,
propose the design, go deep where the risk is,
and cite the chapter behind every pattern.

## Who this is for

- Engineers preparing for system design interviews
  who want a coach that follows the four-step framework
  and can play the interviewer
- Teams writing or reviewing an architecture document
  who want every recommendation tied to a known trade-off
- Anyone who needs QPS, storage, bandwidth and server estimates
  that are shown with their assumptions instead of asserted

## What it covers

- **The framework** — the four steps, the time budget,
  the questions to ask, the dos and don'ts, and how to run a mock interview
- **Estimation** — powers of two, latency numbers, availability nines,
  and a calculator that turns DAU and payload sizes into QPS,
  storage, bandwidth, cache and server counts
- **Building blocks** — the scaling ladder from a single server
  to sharded, multi-data-center systems,
  plus an index of which chapter develops each recurring pattern
- **Infrastructure** — rate limiter, consistent hashing, key-value store,
  unique ID generator, distributed message queue, object storage,
  metrics monitoring and alerting
- **Content platforms** — URL shortener, web crawler, news feed,
  search autocomplete, video streaming, cloud file storage
- **Real-time and messaging** — notification system, chat, email,
  gaming leaderboard, ad click aggregation
- **Geospatial** — proximity service, nearby friends, maps and navigation
- **Transactions** — hotel reservation, payment system, digital wallet,
  stock exchange

The chapter-to-skill map is in [references/sources.md](references/sources.md).

## Scope before boxes

A system design answer that starts with a diagram is guessing.
The skills treat "design X" as permission to ask, not to draw.

Before any architecture, you get:

- Functional and non-functional requirements, and what was left out
- Every assumption written down where you can challenge it
- An estimate table with its derivation, produced by the calculator
- The chapter each pattern comes from, or the label *inference*

Then the design, then two or three deep dives with trade-off tables,
then a wrap-up that names the bottlenecks instead of claiming completeness.
In a design review, every recommendation carries a stable ID and a status
you can accept, decline, or mark as *kept*.

## How it works

Unlike text-only skills, this repository ships a read-only Python calculator,
so your agent reasons over a table instead of doing arithmetic in prose.

**When it triggers:**

- You ask how to design, architect or scale a system,
  or say "how would you design X".
- You ask for a mock system design interview or feedback on your answer.
- You need QPS, storage, bandwidth, cache or server estimates.
- You name one of the 28 systems, or a pattern from them:
  fan-out, geohash, consistent hashing, quorum, idempotency key, Saga,
  event sourcing, sequencer.

**What you can ask:**

- `Design a news feed for 10M DAU. Walk me through it like a 45-minute interview.`
- `Be my interviewer. Pick a problem and push back on my choices.`
- `Estimate QPS and storage for 20M DAU posting 3 times a day with 10% media.`
- `Token bucket or sliding window for our API gateway? We must allow bursts.`
- `Two users keep booking the last room. Fix the data model and the locking.`
- `Review this architecture doc against the books and tell me what's missing.`

**Under the hood:**

- `scripts/estimate.py` — turns DAU, actions per day, payload sizes,
  read/write ratio, peak factor and retention into QPS, storage,
  bandwidth, cache size and server count, as JSON or a Markdown table
  with derivations.
  Also prints the latency and powers-of-two tables and the downtime
  behind any availability figure.
  Reads nothing, writes nothing.
- `references/` — four shared references (sources, estimation cheat sheet,
  answer format, building blocks) copied into every skill,
  and one condensed reference per chapter inside the skill that owns it.
- `skills/*/evals/` — skill-creator evals and trigger queries
  for each skill.

## The skills

| Skill | What it does |
| --- | --- |
| [`system-design-interview`](skills/system-design-interview/SKILL.md) | Orchestrator: scope, estimate, high-level design, deep dive, wrap-up; mock interviews; design reviews; routes to specialists |
| [`system-design-infrastructure`](skills/system-design-infrastructure/SKILL.md) | Rate limiter, consistent hashing, key-value store, unique ID generator, distributed message queue, object storage, metrics monitoring |
| [`system-design-content-platforms`](skills/system-design-content-platforms/SKILL.md) | URL shortener, web crawler, news feed, search autocomplete, video streaming, cloud file storage |
| [`system-design-realtime-messaging`](skills/system-design-realtime-messaging/SKILL.md) | Notification system, chat, email, gaming leaderboard, ad click aggregation |
| [`system-design-geospatial`](skills/system-design-geospatial/SKILL.md) | Proximity service, nearby friends, maps and navigation |
| [`system-design-transactions`](skills/system-design-transactions/SKILL.md) | Hotel reservation, payment system, digital wallet, stock exchange |

Start with `system-design-interview` for any design question;
call a specialist directly for a focused one.
Every skill carries its own copy of the shared references and the calculator,
so any subset installs cleanly.

## How to Use These Skills

### Option A: Using skills.sh

Install all six with a single command:

```bash
npx skills add https://github.com/alexey1312/System-Design-Agent-Skill
```

Or just one:

```bash
npx skills add https://github.com/alexey1312/System-Design-Agent-Skill --skill system-design-transactions
```

Then use it in your AI agent, for example:

> Use the system design interview skill and design a rate limiter with me.

### Option B: Claude Code Plugin

#### Personal Usage

1. Add the marketplace:

```bash
/plugin marketplace add alexey1312/System-Design-Agent-Skill
```

2. Install the plugin:

```bash
/plugin install system-design-skills@system-design-skills
```

#### Project Configuration

To provide the skills to everyone working in a repository,
configure the repository's `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "system-design-skills@system-design-skills": true
  },
  "extraKnownMarketplaces": {
    "system-design-skills": {
      "source": {
        "source": "github",
        "repo": "alexey1312/System-Design-Agent-Skill"
      }
    }
  }
}
```

When team members open the project, Claude Code will prompt them to install the plugin.

### Option C: Codex / OpenAI-compatible tools

This repository includes an `agents/openai.yaml` manifest.
Copy or symlink the skill folders into your Codex skills directory:

```bash
cp -R skills/system-design-* "$CODEX_HOME/skills/"
```

See the [Codex skills documentation](https://developers.openai.com/codex/skills/)
for details on where to save skills.

### Option D: Using pi package manager

Install via [pi](https://github.com/badlogic/pi-mono):

```bash
pi install https://github.com/alexey1312/System-Design-Agent-Skill
```

### Option E: Manual install

1. **Clone** this repository.
2. **Install or symlink** the folders under `skills/` following your tool's
   official skills installation docs (see links below).
3. **Ask your AI tool** to use the `system-design-interview` skill.

Or download a single `.skill` archive from the
[latest release](https://github.com/alexey1312/System-Design-Agent-Skill/releases/latest).

#### Where to Save Skills

- **Codex:** [Where to save skills](https://developers.openai.com/codex/skills/#where-to-save-skills)
- **Claude:** [Using Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
- **Cursor:** [Enabling Skills](https://cursor.com/docs/context/skills#enabling-skills)

**How to verify:**

Ask for a design.
Your agent should ask scope questions (or state assumptions) before drawing
anything, run the bundled calculator and show its table,
cite a volume and chapter for each pattern it uses,
and end with bottlenecks and open questions.

## Skill Structure

```text
skills/
  system-design-interview/          Orchestrator: framework, routing, modes
    references/framework.md         Vol. 1 ch. 3
  system-design-infrastructure/     + rate-limiter, consistent-hashing, key-value-store,
                                      unique-id-generator, distributed-message-queue,
                                      object-storage, metrics-monitoring
  system-design-content-platforms/  + url-shortener, web-crawler, news-feed,
                                      search-autocomplete, video-streaming, cloud-file-storage
  system-design-realtime-messaging/ + notification-system, chat-system, email-service,
                                      gaming-leaderboard, ad-click-aggregation
  system-design-geospatial/         + proximity-service, nearby-friends, maps-navigation
  system-design-transactions/       + hotel-reservation, payment-system, digital-wallet,
                                      stock-exchange
    SKILL.md                        Workflow and rules for the skill
    references/                     sources, estimation-cheatsheet, design-format,
                                    building-blocks (shared copies) + the case studies above
    scripts/                        estimate.py (shared copy)
    evals/                          skill-creator evals and trigger queries
references/                         Canonical shared references
scripts/                            estimate.py, sync_skill_copies.py, package_skills.py
tests/                              Deterministic unit tests
```

## This skill's approach

- **Grounded**: every pattern cites a volume and chapter;
  anything else is labelled as inference.
- **Numerate**: estimates come from a script that shows its assumptions,
  reproduces the books' worked examples in its tests,
  and uses the same decimal units interviews do.
- **Scale-honest**: ten transactions per second gets a relational database
  and a unique constraint, not a sharding plan.
- **Token efficient**: one reference per case study loads only when that
  system is asked about; the calculator returns a compact table instead of
  paragraphs of arithmetic.
- **Respectful of your decisions**: in a design review, a documented,
  deliberate choice is reported as *kept*, not rewritten.
- **Read-only**: the skills advise on designs and change nothing.

## Sources

- *System Design Interview – An Insider's Guide* (Alex Xu, 2020) — Vol. 1, chapters 1–15
- *System Design Interview – An Insider's Guide: Volume 2* (Alex Xu, Sahn Lam, 2022) — chapters 1–13
- [liquidslr/system-design-notes](https://github.com/liquidslr/system-design-notes) —
  the community notes these references condense;
  they carry no licence, so nothing here is quoted and no figure is copied
- [ByteByteGo](https://bytebytego.com/courses/system-design-interview) — the authors' course version of the same material

Chapter-level map and further reading: [references/sources.md](references/sources.md).

## Contributing

Contributions are welcome — especially corrections to a case study,
dated facts that have moved since the books were written,
and evals for behaviour the skills get wrong.
Please read [CONTRIBUTING.md](CONTRIBUTING.md).

## About the author

Created by [Aleksei Kakoulin](https://github.com/alexey1312).
Packaging follows the
[iPhone Duo Agent Skills](https://github.com/alexey1312/iPhone-Duo-Agent-Skill)
and Antoine van der Lee's
[Xcode Build Optimization](https://github.com/AvdLee/Xcode-Build-Optimization-Agent-Skill)
Agent Skills.
The system design material is Alex Xu's and Sahn Lam's;
this project is not affiliated with them or with ByteByteGo.

## License

This project is open-source and available under the MIT License.
See [LICENSE](LICENSE) for details.
