# Contributing

Thanks for helping keep these skills accurate.

## Good contributions

- **Corrections to a case study.**
  Name the volume and chapter, say what the reference gets wrong,
  and rewrite it in your own words.
  Do not paste book text or figures.
- **Calculator features.**
  A new subcommand or flag in `scripts/estimate.py` comes with tests in
  `tests/test_estimate.py`, at least one of which reproduces a number
  from a chapter.
- **Evals** for behaviour the skills get wrong:
  a case in `skills/<skill>/evals/evals.json` or a query in
  `skills/<skill>/evals/trigger-evals.json`.
- **Dated facts.**
  The books are from 2020 and 2022.
  When a limit, price or product name has moved,
  add the current figure with a source and keep the chapter's figure
  labelled as the chapter's.

## Rules

- Guidance must trace to a chapter or be labelled as inference.
- Edit shared references and scripts at the repository root,
  then run `python3 scripts/sync_skill_copies.py`.
- No third-party Python dependencies.
- Markdown uses semantic line breaks.

## Evaluating a change

The skills are developed with Anthropic's
[skill-creator](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator):
run each eval with and without the skill, grade the expectations,
and review the outputs.
Trigger accuracy is tuned against `trigger-evals.json`.
Keep workspaces outside the repository (`*-workspace/` is ignored).

## Checks

```bash
python3 scripts/sync_skill_copies.py --check
python3 -m unittest discover -s tests -v
```

## Releasing

1. Bump the version in `.claude-plugin/plugin.json`,
   `.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json` and
   `agents/openai.yaml` (the tests check they agree) and merge it to `main`.
2. Tag that commit and push the tag:

   ```bash
   git tag v1.1.0 && git push origin v1.1.0
   ```

The `Release` workflow (`.github/workflows/release.yml`) refuses a tag that
does not match the plugin version, re-runs the checks,
builds one `.skill` archive per skill with `scripts/package_skills.py`,
and publishes a GitHub release with the archives and generated notes.
