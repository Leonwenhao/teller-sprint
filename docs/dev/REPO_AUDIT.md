# Repo Audit — `arena-cohort0/` → `teller/`

**Date:** 2026-04-16 (Day 1)
**Author:** Claude Code (Opus 4.7)
**Status:** Awaiting Leon review. Do not migrate any files until approved.

---

## Purpose

Inventory `/Users/leonliu/Desktop/arena-cohort0/` and recommend, per asset, whether to **migrate** (move into `teller/`), **copy** (duplicate into `teller/` while preserving `arena-cohort0` as the historical artifact), or **leave behind**. This is a judgment-driven recommendation, not a neutral inventory — the audit exists because you want an engineering agent's call on the salvage, not a file-moving script's output.

The sibling directory has already been scaffolded at `/Users/leonliu/Desktop/teller/` with a bare skeleton (`pyproject.toml`, `LICENSE`, `.gitignore`, `.env.example`, `CHANGELOG.md`, empty `__init__.py` files under `src/teller/`, empty `docs/dev/`, empty `tests/`). No `arena-cohort0` files have been moved, no destructive operations performed, and no git commits made. Everything is reversible until you approve the migration list below.

---

## Critical Finding Before You Approve Anything

**`BLOCKED.md` entry BLOCK-01: the Treasury corpus is not in `arena-cohort0/`.**

In your Tier-1 answer you said: *"The parsed Treasury Bulletin TXT files are in the arena-cohort0/ repo under the data directory used during Arena iteration. Copy them into the new teller/ repo under `tests/fixtures/treasury_bulletins/` and commit them."*

That is not what is on disk. I searched thoroughly: zero `treasury_bulletin_*` files, no `data/` directory, no `corpus/` directory. The file `arena-cohort0/scripts/standalone_eval.py:40` reveals the corpus is pulled at execution time from the Docker image `ghcr.io/sentient-agi/harbor/officeqa-corpus:latest` and mounted at `/app/corpus/` inside each task container. The corpus was never a repo artifact.

Three options for shipping a self-contained regression (my recommendation: **A**):

**Option A (recommended).** On day-1 evening, pull the Docker image, extract the 697 parsed TXT files, and commit them to `tests/fixtures/treasury_bulletins/`. Size: likely 80–150 MB of text. Public-domain Treasury data, redistribution is legal, and the README cites the Sentient Arena source. Benefit: `pip install -e .` + `pytest` works on a fresh clone with no Docker dependency, which is the self-contained-regression goal you asked for. Cost: slow first clone.

**Option B.** Commit only the files covering the 20 regression questions. Smaller repo. Downside: `Corpus.describe()` behavior with ~20 files diverges from the real 697-file distribution, and retrospective-table multi-file logic is under-exercised.

**Option C.** Don't ship the corpus. Provide `scripts/pull_corpus.sh` that pulls and extracts. Repo stays tiny. Downside: breaks self-contained regression; installs need Docker. Not what you asked for.

If Option A feels too heavy, I can propose a stratified ~80-file subset (roughly one-per-year plus the retrospective bulletins) that exercises the full retrieval-pattern space while keeping `git clone` fast. That is a middle path worth considering.

**I need your call before day-1 evening so the Corpus abstraction has something real to point at.** The rest of the audit assumes Option A is approved; if you choose B, C, or the middle path, the migration list below needs adjustment only on that single fixture entry.

---

## Production Artifacts — Migrate (The Winning Config)

These are the files that actually won the Arena. They are the source of truth for the day-1 universal/treasury prompt split and the behavioral regression gate.

| `arena-cohort0/` path | `teller/` destination | Notes |
|---|---|---|
| `prompts/goose_prompt.j2` (84 lines) | `src/teller/domains/treasury/_source_goose_prompt.j2` | Preserve verbatim for the ADR-005 advisory diff. Leading underscore signals "reference, not loaded at runtime." The split product is `prompts/base.j2` + `src/teller/domains/treasury/prompt.j2` — both written during day 1 after your review. |
| `skills_consolidated/core/SKILL.md` (138 lines) | `src/teller/domains/treasury/skill.md` | The 138-line treasury skill. Migrates with a light rename. |
| `recipe.yaml` | `recipes/treasury.yaml` (new top-level dir) | Goose recipe for the Arena-winning config. Rename because `teller` will have per-domain recipes; see judgment call 2 below. Internal references updated to new paths. |
| `arena.yaml` | `arena.yaml` | Kept for potential v0.1.1 verification submission to Sentient Arena. Inactive after launch. |
| `officeqa_full.csv` (154 KB) | `tests/fixtures/officeqa/officeqa_full.csv` | 246-question benchmark with ground truth. Required for ADR-004 stratification and day-4/5 full-benchmark runs. |
| `reward.py` (17 KB) | `tests/fixtures/officeqa/reward.py` | Official 1% fuzzy-tolerance scorer. Required for regression scoring. |
| `results/complete_246_results.json` (52 KB) | `tests/fixtures/officeqa/complete_246_results.json` | Last full-benchmark per-question results (status, difficulty, expected answer). Feeds ADR-004 stratification. |
| `notes/variance_matrix.csv` (10 KB) | `tests/fixtures/officeqa/variance_matrix.csv` | Per-question 6-run cross-submission variance with ALWAYS-PASS / ALWAYS-FAIL / SWING categorization. The direct basis for the 20-question stratified selection. |

## Scoring Infrastructure — Migrate with Renames

These scripts run the regression. Not product code, but load-bearing for day-1-through-5 testing.

| `arena-cohort0/` path | `teller/` destination | Notes |
|---|---|---|
| `scripts/standalone_eval.py` | `scripts/regression.py` | Adapt: parameterize over 20-question and 246-question modes, emit structured JSON. Keep the Docker-mounted corpus path unchanged so regression exactly reproduces the Arena measurement. |
| `scripts/aggregate_results.py` | `scripts/aggregate_results.py` | Generic aggregator. Light cleanup. |
| `scripts/local_score.py` | `scripts/local_score.py` | Simple local scorer using `reward.py`. Day-1 sanity. |

All other scripts in `arena-cohort0/scripts/` (`run_full_eval.sh`, `run_rerun.sh`, `run_panel.sh`, `run_targeted.sh`, `run_untested.sh`, `generate_samples.py`, `verify_samples.py`, `diagnostic_panel.json`, `daytona_eval.py`) — **leave behind.** They are Arena-orchestration glue that `teller` does not reuse.

## Research Output — Copy (Launch-Material Only)

These are research artifacts, not code. The launch blog post and post-mortem thread will cite them, so we want copies under `teller/docs/launch/`. The authoritative originals stay in `arena-cohort0/`.

| `arena-cohort0/` path | `teller/` destination | Why |
|---|---|---|
| `FINAL_REPORT.md` (20 KB) | `docs/launch/final_report.md` | The research paper. Linked from the README rather than embedded — too long for the storefront. |
| `SUBMISSION_REPORT.md` (7 KB) | `docs/launch/submission_report.md` | Competition report. |
| `analysis/failure_catalog.md` | `docs/launch/arena_failure_catalog.md` | Record of what was found and fixed, a good base for a future "how we debugged the model" post. |
| `analysis/path_to_200_review.md` (14 KB) | `docs/launch/path_to_200_review.md` | Strategic mid-sprint review. Blog material. |
| `analysis/iteration_tracker.csv` | `docs/launch/arena_iteration_tracker.csv` | Score progression for the "what we learned" narrative. |

`notes/session*_journey.md`, `notes/codex_*.md`, `notes/solution_proposal.md`, `notes/raw_traces.json`, `notes/traces_clean.json`, `notes/gemini_extract.txt`, `notes/*.md` (deep research artifacts) — **leave behind.** Too raw for launch material. Dredge case-by-case only when a specific blog post needs a specific quote.

## Strategy / Business Docs — Leave Behind

These files live in `arena-cohort0/` for incidental reasons but are Dolores Research artifacts rather than `teller` artifacts. Leaving them in `arena-cohort0/` keeps `teller/` clean.

- `Revised_TELLER_STRATEGY.md`, `Revised_TELLER_DEVELOPMENT_PLAN.md` — source-of-truth for this sprint. Referenced by path from `teller/docs/dev/SPRINT_STATUS.md`.
- `TELLER_STRATEGY.md`, `TELLER_DEVELOPMENT_PLAN.md` — the superseded originals.
- `PRESENTATION_BRIEF.md`, `presentation.html` — Sentient presentation materials.
- `sentient-arena-cohort0-journey.md`, `chinese-ai-with-american-characteristics.md` — long-form essays.
- `GENESIS.md`, `BOTCOIN_AUDIT.md`, `SETUP.md`, `QUICKREF.md`, `COLD_START.md`, `COLD_START_SESSION9.md`, `CLAUDE.md`, `SCRATCHPAD.md` — Arena project docs. `teller` gets its own README and `CLAUDE.md` on day 4.
- `ChatGPT_DeepResearch.md`, `Claude_DeepResearch.md`, `Gemini_DeepResearch.pdf`, `arena_status_report.md`, `program.md`, `findings_for_chat.md`, `notes/recon_findings.md`, `notes/deepresearch_prompt.md` — external-research products.
- `arena_submission.pdf`, `findings_for_chat.md` — Sentient deliverables.
- `Teller Thread.pdf`, `Teller_DemoDay_McKinsey.pptx.pdf` (on Desktop) — presentation drafts. Not in repo.

## Iteration Scar Tissue — Leave Behind

Twelve prompt iterations and five harness experiments left a lot of backup files. They have no product value; their signal is already captured in `FINAL_REPORT.md`.

- `prompts/officeqa_prompt.j2`, `prompts/officeqa_prompt_sdk_overlay.j2`, `prompts/officeqa_prompt_v2_backup.j2`, `prompts/officeqa_prompt_v3_megaprompt.j2` — superseded prompts.
- `skills/`, `skills_v4_backup/`, `skills_v5_backup/`, `skills_v5_megaskills/`, `skills_v6/` — superseded skill trees.
- `arena.yaml.bak`, `arena.yaml.deepseek-v3.2`, `arena.yaml.megaprompt-v3`, `arena.yaml.minimax-*` (4 variants), `arena.yaml.openhands-sdk-v4`, `arena.yaml.pre-v3-backup`, `arena.yaml.sonnet-backup`, `arena.yaml.sonnet-backup-safe`, `arena.yaml.test-reasoning-low`, `arena.yaml.v5-*` (2 variants), `arena.yaml.v6-medium-effort` — config experiments.
- `.arena/runs/` (411 run dirs), `.arena/samples/` (453 sample dirs) — Arena CLI runtime artifacts.
- `arena-cli-latest/` — upstream Arena CLI binary/source.
- `assets/` — Sentient presentation assets.
- `{prompts,skills,analysis,notes}/` (a literal directory with that name, artifact of a shell glob gone wrong) — a previous `mkdir` accident. Leave behind.
- `pyproject.toml` (302 bytes) — stub, superseded by fresh PEP 621 metadata.
- `.python-version`, `.env.example` — fresh versions in `teller/`.

## Loose Ends

- `LICENSE` (MIT): already mirrored to `teller/LICENSE`; no re-migration needed.
- `dolores_goose_v1.tar.gz` (on Desktop, 6 KB): the minimal production-pair export (arena.yaml + goose_prompt.j2 + skills_consolidated/core/SKILL.md). Reference-only; does not need to be committed.
- `.env` and `.env.example` in `arena-cohort0/` — contain the OpenRouter key for Arena work. Not migrated; `teller/.env.example` is already in place as a template.

---

## Three Judgment Calls

1. **Preserve the original winning prompt verbatim inside `teller/` as `_source_goose_prompt.j2`.** The revised dev plan (Section "Day One") and ADR-005 both specify the prompt split is validated by diffing against the original. That diff needs the original committed inside `teller/`, not on your filesystem. The leading underscore marks it as reference-only, not loaded by the runtime. Two-month-from-now Leon will want to know why it's there — the filename, the ADR reference, and a header comment on the file itself will all tell him.

2. **Rename `recipe.yaml` → `recipes/treasury.yaml`.** The bare name made sense when `teller` was a single-domain Arena submission. Day-2 SEC demos will need `recipes/sec_filings.yaml`, and a `recipes/` directory scales. Cost: internal path references in Goose need one-line updates. Benefit: the SEC recipe lands in the obvious place.

3. **Treat the `notes/` corpus as launch-material, not code.** Copying `FINAL_REPORT.md`, `path_to_200_review.md`, and `failure_catalog.md` into `docs/launch/` gives the post-launch blog drafts a local source to cite. Copying the 25+ session journals and 10+ Codex review artifacts does not — the value-density is too low for the storage cost and the signal is already distilled in `FINAL_REPORT.md`. Dredge case-by-case only if a blog post needs a specific quote.

## Proposed `teller/` Layout (Already Scaffolded; Files Not Yet Populated)

```
teller/
├── pyproject.toml                      ✓ written
├── README.md                           (day 4)
├── LICENSE                             ✓ written
├── CHANGELOG.md                        ✓ written (empty)
├── .gitignore                          ✓ written
├── .env.example                        ✓ written
├── arena.yaml                          (migrate after approval)
├── recipes/
│   └── treasury.yaml                   (renamed from recipe.yaml, after approval)
├── src/teller/
│   ├── __init__.py                     ✓ written (stub)
│   ├── agent.py                        (post-audit, parallel track)
│   ├── corpus.py                       (post-audit, parallel track)
│   ├── result.py                       (post-audit, parallel track)
│   ├── config.py                       (post-audit, parallel track)
│   ├── domains/
│   │   ├── __init__.py                 ✓ written
│   │   ├── treasury/
│   │   │   ├── __init__.py             ✓ written
│   │   │   ├── prompt.j2               (day 1, post-audit)
│   │   │   ├── skill.md                (migrated from skills_consolidated/core/SKILL.md)
│   │   │   └── _source_goose_prompt.j2 (reference copy of original, for ADR-005 diff)
│   │   └── sec_filings/                (day 2)
│   ├── downloaders/                    (day 2)
│   ├── harness/                        (day 2)
│   ├── validation/                     (day 2)
│   └── cli/                            (day 2)
├── prompts/
│   └── base.j2                         (day 1, post-audit — universal iron rules + workflow)
├── tests/
│   ├── __init__.py                     ✓ written
│   ├── test_iron_rules.py              (parallel track — next)
│   └── fixtures/
│       ├── treasury_bulletins/         (day 1 evening, blocked on BLOCK-01)
│       └── officeqa/
│           ├── officeqa_full.csv       (migrated from arena-cohort0)
│           ├── reward.py
│           ├── complete_246_results.json
│           └── variance_matrix.csv
├── scripts/
│   ├── regression.py                   (renamed from standalone_eval.py)
│   ├── aggregate_results.py
│   └── local_score.py
├── docs/
│   ├── dev/
│   │   ├── REPO_AUDIT.md               ✓ written (this file)
│   │   ├── SPRINT_STATUS.md            ✓ written (next)
│   │   ├── ARCHITECTURE_DECISIONS.md   (post-audit — ADR-001, 003, 004, 005)
│   │   ├── BLOCKED.md                  ✓ written (next)
│   │   └── day_1_log.md                ✓ written (next)
│   ├── launch/                         (post-audit — copies from arena-cohort0)
│   └── TELEMETRY.md                    (day 4)
└── examples/
    └── sec_filings_walkthrough.ipynb   (day 4)
```

## What's Been Done in Parallel (Path B)

Per your approval of Path B on day-1 latency, the following reversible work has begun alongside this audit and will continue while you review:

- Sibling `teller/` directory scaffolded at `/Users/leonliu/Desktop/teller/`.
- `pyproject.toml` (PEP 621, package `teller-agent`, import `teller`), `LICENSE` (MIT), `.gitignore`, `.env.example`, `CHANGELOG.md`, empty `__init__.py` files written.
- Next: ADR-001 (iron rules), ADR-003 (reasoning effort), ADR-004 (regression stratification), ADR-005 (prompt split validation gate); `Agent`/`Result`/`Corpus`/`config.py` scaffolds with `NotImplementedError` internals; `prompts/base.j2` containing only the three iron rules; `tests/test_iron_rules.py`.

No `arena-cohort0/` files have been moved. No git commits have been made. Everything below `teller/` is freshly written; if you reject any of the judgment calls or the layout, the changes revert cleanly.

## What I Need From You

1. **Corpus plan (BLOCK-01).** Approve Option A (pull Docker + commit 697 TXT files), B (minimal subset), C (don't ship, pull script), or the middle path (stratified ~80-file subset). Blocks Corpus abstraction validation.
2. **Migration list.** Thumbs-up or corrections on the migrate / copy / leave-behind calls above.
3. **Layout.** Thumbs-up or corrections on the proposed `teller/` tree.
4. **Judgment calls.** Thumbs-up or objections to (1) preserving the winning prompt as `_source_goose_prompt.j2`, (2) `recipe.yaml` → `recipes/treasury.yaml`, (3) the launch-material-only treatment of `notes/` and `analysis/`.

Once approved, I migrate the files, commit initial scaffold + audit + migrated assets as `chore: initial scaffold with migrated Arena assets`, and proceed with the day-1 prompt split, corpus abstraction implementation, and the 20-question regression gate.

Aiming to resume under one hour of your review turnaround. If slower, I continue with other reversible day-1 work (ADRs, API scaffold, iron-rules test) and note progress in `day_1_log.md`.
