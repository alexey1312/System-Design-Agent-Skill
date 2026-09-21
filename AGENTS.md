# Agent guidance

This repository contains Agent Skills that answer system design questions
and review architectures.
They advise; they do not change the user's code.

- **Scope before boxes.**
  A design answer starts with requirements and assumptions,
  never with a diagram.
  `references/design-format.md` is the shape every answer takes.
- **Scan before recommending.**
  On a real project, `scripts/arch_scan.py` runs first and its inventory,
  findings and questions frame the review.
  Findings are one-line heuristics; read the code around them.
  A choice the project documents as deliberate is reported as *kept*.
- **Numbers come from metrics or `scripts/estimate.py`.**
  Never do estimation arithmetic in prose;
  name the dashboard, or run the calculator and show its table with the
  assumptions.
- **Both scripts are read-only.**
  `arch_scan.py` and `estimate.py` must never write to the scanned project
  or anywhere else; `test_scan_does_not_modify_files` guards the scanner.
- **Every pattern cites a chapter** (`references/sources.md`).
  Anything not from the books is labelled *inference*.
  New reference material must name the volume and chapter it condenses.
- **The references are rewrites, not quotations.**
  The upstream notes carry no licence and the books are copyrighted;
  condense in your own words and never copy the figures.
- **Shared files have one source.**
  Edit `references/*.md` and `scripts/{estimate,arch_scan}.py` at the root,
  then run `python3 scripts/sync_skill_copies.py`.
  Never edit the copies under `skills/*/references` or `skills/*/scripts`
  that the sync script owns.
  Case-study references live only in their skill and are edited there.
- **Keep SKILL.md descriptions between 200 and 1024 characters**
  and the `name` equal to the directory name.
- **Calculator changes need tests** in `tests/test_estimate.py`,
  including one that reproduces a figure from a chapter.
- **Scanner changes need tests** for a positive and a negative case in
  `tests/test_arch_scan.py`, a `source` that names a chapter (or says
  *inference*), references that exist, and a row in `DESIGN-CHECKS.md`.
- **Behaviour changes need evals.**
  Each skill keeps skill-creator evals in `skills/<skill>/evals/`
  (`evals.json` and `trigger-evals.json`).
  Re-run them with and without the skill before claiming an improvement;
  `scripts/package_skills.py` leaves `evals/` out of release archives.
- Keep the plugin version identical in `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json` and
  `agents/openai.yaml`.
  A GitHub release is cut by pushing a matching `vX.Y.Z` tag;
  the `Release` workflow builds the `.skill` archives
  (`CONTRIBUTING.md` › Releasing).
- Markdown in this repository uses semantic line breaks:
  one sentence or clause per line, wrapped at about 80 columns.
- Run before completing a change:

  ```bash
  python3 scripts/sync_skill_copies.py --check
  python3 -m unittest discover -s tests -v
  ```
