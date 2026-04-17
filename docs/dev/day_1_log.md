# Day 1 Log — 2026-04-16

## Session 1 — Kickoff, scope alignment, audit

### 14:20 — Read the revised plans and the cold start

Read `Revised_TELLER_STRATEGY.md`, `Revised_TELLER_DEVELOPMENT_PLAN.md`, and Leon's cold start in full. Summarized the scope change back: previous 12-milestone multi-domain plan shelved, Teller v0.1 ships as a single-vertical SEC-filings tool inside a 5-day sprint with XBRL cross-validation + abstention as the defensibility story. My role: sole day-to-day engineering agent (Opus 4.7), Codex consulted only in two narrow windows (day-2 XBRL library choice, day-3 prompt iteration stuck patterns).

### 14:25 — Raised 10 questions and two pushbacks

Tier-1 blockers (4), Tier-2 day-1 items (3), Tier-3 flaggable (3). Two pushbacks: (a) day-1 review-gate latency risk, recommended Path B (scaffold API + iron-rules test while audit is in review), (b) prompt-split validation gate, recommended Path B (regression score as hard gate, byte-diff advisory).

### 14:30 — Leon locked the plan

- Repo location: sibling `teller/`, not in-place.
- Canonical prompt: `prompts/goose_prompt.j2` (84 lines), cross-reference `skills_consolidated/core/SKILL.md` (138 lines).
- Regression set: 20-question, stratified 8 always-pass + 8 swing + 4 always-fail.
- Corpus: Leon said "in arena-cohort0 under a data directory." Actually not — Docker-mounted. Raised BLOCK-01.
- OpenRouter: funded. No pre-spend confirmation except >$10/run.
- Iron rules: derive from winning prompt, ADR-001. Semantic anchors, not full sentences.
- Reasoning effort: medium. ADR-003 with Arena cost-coefficient evidence.
- EDGAR user-agent: `leon@dolores.research` if live, else Gmail fallback.
- PyPI: verify day-1 evening.
- GitHub: `dolores-research/teller`. Org creation is Leon's task.
- Path B approved for both pushbacks. Prompt-split nuance: advisory diff still runs and gets Leon-annotated in the ADR.

### 14:35 — Inventoried `arena-cohort0/`

Top-level: 70+ files and subdirectories. Canonical artifacts confirmed:
- `prompts/goose_prompt.j2` (6167 bytes, 84 lines) — iron rules on lines 1–4.
- `skills_consolidated/core/SKILL.md` (138 lines) — treasury skill content.
- `recipe.yaml` (active Goose recipe; goose harness + MiniMax M2.5 + reasoning_effort medium + max_iterations 100).
- `arena.yaml` (Arena submission config).

Critical finding: treasury corpus not in the repo. Confirmed via `scripts/standalone_eval.py:40` — corpus is pulled from `ghcr.io/sentient-agi/harbor/officeqa-corpus:latest` Docker image and mounted at `/app/corpus/`. Raised as BLOCK-01 in `BLOCKED.md`.

Other useful finds:
- `officeqa_full.csv` (246 questions + ground truth).
- `reward.py` (1% fuzzy scorer).
- `results/complete_246_results.json` (per-question status + difficulty from last full run).
- `notes/variance_matrix.csv` (per-question 6-run categorization — ALWAYS-PASS 114, SWING 89, ALWAYS-FAIL 43). Direct basis for ADR-004 stratification.
- `FINAL_REPORT.md`, `analysis/path_to_200_review.md`, `analysis/failure_catalog.md` — launch-material assets.
- Dozens of iteration backups (`arena.yaml.*`, `skills_v*_backup/`, `prompts/officeqa_prompt_*`) — scar tissue, leave behind.

### 15:00 — Scaffolded sibling `teller/` directory

Created `/Users/leonliu/Desktop/teller/` with pyproject.toml (PEP 621, `teller-agent` PyPI name, `teller` import name), LICENSE (MIT), .gitignore, .env.example, CHANGELOG.md, empty `__init__.py` files under `src/teller/`, `src/teller/domains/`, `src/teller/domains/treasury/`, `tests/`. No `arena-cohort0` files moved, no git commits.

### 15:15 — Wrote audit and scratchpad

- `docs/dev/REPO_AUDIT.md` — full migrate/copy/leave-behind recommendations with reasoning, critical-finding flag on BLOCK-01, proposed teller/ layout, three judgment calls (preserve `_source_goose_prompt.j2`, rename to `recipes/treasury.yaml`, copy `notes/` only as launch-material).
- `docs/dev/SPRINT_STATUS.md` — bootstrap checklist, day-1 deliverables, hard gates, protected invariants, budget, tier-3 items.
- `docs/dev/BLOCKED.md` — BLOCK-01 with four options (A pull+commit full corpus, B minimal subset, C don't ship, middle ~80-file subset) and recommendation.
- This file (`day_1_log.md`).

Audit is awaiting Leon review. Continuing with Path-B parallel work next: ADRs (001, 003, 004, 005), Agent/Result/Corpus/config scaffolds, iron-rules unit test, minimal `prompts/base.j2` with iron rules only.

### 15:30 — Path B parallel work complete

All day-1 Path-B deliverables landed without touching arena-cohort0. No git commits yet; waiting on audit approval.

Files written to `/Users/leonliu/Desktop/teller/`:

| File | Purpose |
|---|---|
| `pyproject.toml` | PEP 621, PyPI `teller-agent`, import `teller`, pytest configured |
| `.gitignore`, `LICENSE` (MIT), `.env.example`, `CHANGELOG.md` | Standard repo metadata |
| `src/teller/__init__.py` | Re-exports `Agent`, `Corpus`, `Result`, `Source`, `XBRLValidation` |
| `src/teller/agent.py` | `class Agent` with `domain`, `corpus`, `model` — `ask` raises `NotImplementedError` |
| `src/teller/result.py` | `@dataclass Result`, `Source`, `XBRLValidation` — full field surface locked |
| `src/teller/corpus.py` | `class Corpus` with `path`, `pattern` — `describe()`, `index()` stubbed |
| `src/teller/config.py` | `ModelConfig` + `MINIMAX_M2_5` + `CLAUDE_SONNET_4_5` + `GPT_4_1_MINI` + `DEFAULT_MODEL` |
| `prompts/base.j2` | Iron rules only (lines 1–4 of goose_prompt.j2) with `{% block domain_content %}` |
| `tests/test_iron_rules.py` | Iron-rules anchor assertion, parametrized, covers base + every domain overlay |
| `docs/dev/ARCHITECTURE_DECISIONS.md` | ADR-001 (iron rules), ADR-002 (reserved), ADR-003 (reasoning=medium), ADR-004 (regression stratification methodology), ADR-005 (prompt split validation gate) |
| `docs/dev/SPRINT_STATUS.md` | Bootstrap checklist, day-1 deliverables, hard gates, protected invariants, budget |
| `docs/dev/BLOCKED.md` | BLOCK-01 corpus location with 4 options |
| `docs/dev/REPO_AUDIT.md` | Migrate/copy/leave-behind with reasoning and judgment calls |
| `docs/dev/day_1_log.md` | This file |

### 15:45 — Sanity checks passed

- `python3 -c "from teller import Agent, Corpus, Result"` → imports resolve via `src/` layout.
- `pytest tests/` → 3 passed (base iron-rule anchors present), 3 skipped (no domain overlay yet — correct day-1 pre-split behavior).
- No arena-cohort0 files have been moved. No git init yet.

### 15:50 — Tier-3 PyPI check (bonus — pulled forward from day-1 evening)

Ran the PyPI name check early since it is a 5-second curl and prevents a day-4 surprise.

Verified via the JSON API (authoritative — `pypi.org/project/X/` HTML returns 200 for some non-existent names):

- `pypi.org/pypi/teller-agent/json` → **404, AVAILABLE**. This is the locked PyPI name in `pyproject.toml`.
- `pypi.org/pypi/teller/json` → 200, taken (squat at version 0.0.1, summary "teller"). Expected per Leon's note "almost certainly taken, not worth the verification round-trip." No action.
- `pypi.org/pypi/dolores-teller/json` → 404, available. Documented fallback, not needed.

No publish attempted. The day-4 step is `gh actions run publish-pypi` on a tag push.

### Next (pending Leon audit review)

1. Leon reviews `REPO_AUDIT.md` + judgment calls + BLOCK-01 options.
2. On approval: migrate production artifacts per the audit table, author universal content in `base.j2`, author `src/teller/domains/treasury/prompt.j2`, ADR-005 Diff Summary, ADR-004 concrete UID selection.
3. Implement `Corpus.describe()` and `Corpus.index()` against the chosen corpus-fixtures strategy (BLOCK-01 resolution).
4. Implement `Agent.ask()` with the chosen harness integration (likely goose recipe first, openhands-sdk as alternative per dev plan).
5. Day-1 regression gate: 20 questions, ≥70%.

---

## Session 1 continued — Leon approved; migration + split + regression-set proposal

### 17:30 — Leon's approvals received

- **BLOCK-01:** Option A approved (pull Docker, extract 697 TXT files, commit).
- **Migration list:** approved with additions — `FINAL_REPORT.md` → `docs/research/final_report.md` and `sentient-arena-cohort0-journey.md` → `docs/research/journey.md` (not left behind; these are primary-source records that belong with the product).
- **Layout:** approved. `tests/fixtures/treasury_bulletins/` and `tests/fixtures/sec_filings/` will be sibling directories.
- **Judgment call 1 (preserve `_source_goose_prompt.j2`):** approved. Lives at `prompts/_source_goose_prompt.j2` (root prompts/ dir, not inside domains/).
- **Judgment call 2 (rename `recipe.yaml` → `recipes/treasury.yaml`):** approved.
- **Judgment call 3 (notes/ + analysis/ launch-material only, not migrated):** approved.
- **New requirement:** `REGRESSION_SET_SELECTION.md` — per-question Arena accuracy breakdown + proposed stratified 20 + defense of the 4 ALWAYS-FAIL picks, for Leon's direct review before the first regression run.
- **Coaching:** flagged the pull-forward-decisions pattern risk. Don't let slack time during waiting produce more decisions than fit on the next review gate; use slack for scratchpad updates, daily logs, drafting next ADRs, not new work.

### 17:35 — Corpus extraction

Docker image `ghcr.io/sentient-agi/harbor/officeqa-corpus:latest` already cached locally (725 MB). Extracted via `docker create` + `docker cp` → 697 `treasury_bulletin_YYYY_MM.txt` files + 1 `index.txt` = 698 files, 379 MB on disk. Not 80-150 MB as I estimated — flagged the size discrepancy in `tests/fixtures/treasury_bulletins/README.md` and in the Leon update. Git pack estimated at ~95 MB (based on gzip ratio of 25%), so clone transfer stays in the estimated range. Removed `.gitignore` rule excluding `*.txt` in the fixture dir.

### 17:40 — Migration

Copied per the approved audit list:
- `prompts/goose_prompt.j2` → `prompts/_source_goose_prompt.j2` (immutable source reference, header comment added).
- `skills_consolidated/core/SKILL.md` → `src/teller/domains/treasury/skill.md`.
- `recipe.yaml` → `recipes/treasury.yaml`.
- `arena.yaml` → `arena.yaml` (unchanged).
- `officeqa_full.csv`, `reward.py`, `results/complete_246_results.json`, `notes/variance_matrix.csv` → `tests/fixtures/officeqa/`.
- `FINAL_REPORT.md` → `docs/research/final_report.md`.
- `sentient-arena-cohort0-journey.md` → `docs/research/journey.md`.
- `scripts/{standalone_eval.py → regression.py, aggregate_results.py, local_score.py}` → `scripts/`.

No arena-cohort0 files modified. Source repo preserved intact.

### 17:50 — Prompt split

Wrote `prompts/base.j2` (universal) with 7 Jinja blocks where the overlay injects domain content:
- `workflow_multi_period`, `domain_unit_conversion`, `domain_time_conventions`, `domain_table_example`, `domain_traps`, `domain_multi_file`, `domain_external_data`.

Wrote `src/teller/domains/treasury/prompt.j2` (Treasury overlay) using `{% extends "base.j2" %}` and filling each block from the corresponding sections in the source prompt.

### 17:55 — Advisory diff for ADR-005

Rendered overlay vs rendered source: 95.4% similarity, 3 replaced lines, 0 added, 0 removed. All three replacements are domain-neutral rephrasings in the base template (generic `*.txt` corpus path instead of `treasury_bulletin_YYYY_*.txt`; "source" instead of "bulletin" in WORKFLOW step 1; generic corpus wording in WEB SEARCH header). No content lost. Domain-specific wording preserved verbatim in the overlay. Diff summary and per-change rationale appended to `docs/dev/ARCHITECTURE_DECISIONS.md` under ADR-005 Diff Summary (Run 1). Awaiting Leon annotation before declaring the ADR-005 gate passed.

### 18:00 — Iron-rules test re-run

6/6 passed: 3 base anchors + 3 treasury-overlay anchors. Both sources of prompt content preserve all three iron rules.

### 18:10 — Regression set selection

Wrote `docs/dev/REGRESSION_SET_SELECTION.md` with:

- Tier 1 (8 ALWAYS-PASS): UID0002, 0011, 0024, 0064, 0095, 0108, 0152, 0190 — pattern-spread (single-file, multi-period, computed-metric) across 1939/1946/modern.
- Tier 2 (8 SWING): UID0014, 0052, 0168 (SWING-5) + 0127, 0199 (SWING-4) + 0220 (SWING-3) + 0097, 0102 (SWING-2/1). Four of these have documented failure-catalog entries (F-001 through F-004), which makes their semantics traceable.
- Tier 3 (4 ALWAYS-FAIL canary): UID0041 (Theil formula gap), UID0057 (12-value multi-file step exhaustion), UID0055 (external-data WWII/Korea reasoning), UID0174 (arc elasticity formula + extraction). Four distinct failure modes, all plausibly flippable by a future capability improvement.

Baseline prediction: ~14/20 (70%), right at the gate. Expected regression run noise: ±1–2 questions (based on Arena ±5/246 ≈ 2%).

### 18:20 — Next

1. Initial git commit (scaffold + migration + split + scratchpad + fixtures + research).
2. Hand off to Leon for `REGRESSION_SET_SELECTION.md` review — especially the 4 ALWAYS-FAIL picks.
3. On approval: append concrete UID list to ADR-004, generate `tests/fixtures/officeqa/regression_twenty.json`.
4. Implement `Corpus.describe`/`.index` pointed at `tests/fixtures/treasury_bulletins/`.
5. Implement `Agent.ask` — likely wraps the existing `scripts/regression.py` Docker flow for day 1, swappable to native goose / openhands-sdk later.
6. First regression run. Target ≥14/20.
7. Update ADR-004 concrete selection section with first-run score per UID.
8. Close day 1 → SPRINT_STATUS.md update, hand off for day 2 kickoff.

---

## Session 1 continued — Leon's second approval round

### 18:50 — Leon's second round

- BLOCK-01: Option A approved (commit 697 files). README under `tests/fixtures/treasury_bulletins/README.md` documents provenance + size.
- Migration: approved with additions (FINAL_REPORT.md → `docs/research/final_report.md`, journey.md → `docs/research/journey.md`). Done.
- Judgment calls: all three approved. `_source_goose_prompt.j2` lives at `prompts/` root (not inside domains/).
- **Harness correction:** Revised Dev Plan's "openhands-sdk" claim was wrong. Arena winner was **goose** (per recipe.yaml, arena.yaml, FINAL_REPORT.md §2.4). Write ADR-006, update the dev plan inline.
- **Leon's meta-observation (saved as feedback memory):** For Arena-specific facts, the repo artifacts are authoritative, not his stated memory. Wrong twice in two days (corpus location, now harness). Pattern: verify before acting.
- **Pulled-forward discipline:** do not pile on top of review gates. Every pull-forward item adds to the next review surface. Use blocked-waiting time for scratchpad updates, daily logs, drafting next ADR — not new implementation work.
- **Git config:** set repo-local (not global). Env-var approach was the right pattern for the commit; now make it persistent locally.
- **Prompt split annotation (ADR-005):** Leon signed. 3-replaced-line diff accepted as domain-neutral rephrasing.
- **Regression set:** 8 ALWAYS-PASS and 8 SWING approved sight unseen. For slot 4 ALWAYS-FAIL, swap UID0055 only if a cleanly-diagnosed termination-signal ALWAYS-FAIL candidate exists; otherwise keep UID0055.
- **Regression result bands:** 68-72% = close day 1; below 65% = stop and debug before day 2.

### 19:00 — Termination-signal canary check

Grepped notes/ for self-sabotage diagnostics. The "smoking gun self-sabotage" case is documented as **UID0021** (`notes/session10_journey.md:15,90`, `notes/codex_v12lean_context.md:109`), but UID0021 is SWING-4, not ALWAYS-FAIL — the overwrite-gate fix in v12A promoted it from always-failing to mostly-passing. No ALWAYS-FAIL question has a clean termination-signal diagnostic. **Per Leon's fallback, UID0055 retained.** Documented in ADR-004 with the check.

### 19:10 — ADRs + memory + plan correction

- `ARCHITECTURE_DECISIONS.md` — ADR-004 concrete UID list locked (all 20), ADR-005 Leon-annotated, ADR-006 written (harness correction with full evidence chain citing recipe.yaml, arena.yaml, FINAL_REPORT.md §2.4).
- `~/.claude/projects/.../memory/feedback_arena_artifacts_authoritative.md` saved + pointer added to MEMORY.md.
- `arena-cohort0/Revised_TELLER_DEVELOPMENT_PLAN.md` corrected inline (Architecture Principles section now reads "goose with auto-compaction at 80% context utilization").
- `tests/fixtures/officeqa/regression_twenty.json` generated (20 UIDs + per-UID tier, variance bucket, difficulty, expected, pattern).
- `git config --local user.email leon@dolores.research / user.name "Leon Liu"` set.

### 19:20 — Goose install + Corpus abstraction + Agent.ask

- `brew install block-goose-cli` → goose v1.31.0 installed.
- `Corpus.describe` returns `{file_count: 697, total_mb: 361.9, date_range: (1939, 2025), has_index: true, ...}` against the fixture dir.
- `Corpus.index()` parses `index.txt`, returns 697 basenames.
- `Agent.ask` wraps goose subprocess. At call time it copies `recipes/treasury.yaml` into a temp workspace and substitutes `/app/corpus` → `corpus.path`, `/app/answer.txt` → `workspace/answer.txt`, so goose runs locally without requiring root-owned `/app` to exist. Environment variables pin `GOOSE_PROVIDER=openrouter` and `GOOSE_MODEL=<model name>`.
- Error classes: `GooseNotFoundError`, `MissingAPIKeyError` — both with actionable install/export instructions.

### 19:45 — Smoke test passed

UID0002 (easy ALWAYS-PASS, expected `507`, question about Veterans Administration FY1934 expenditures) → Agent.ask returned `'507.0'` in 152.5s. Within 1% tolerance, counts as PASS. Pipeline validated end-to-end.

### 19:55 — Regression kicked off

`scripts/regression.py --set twenty` running in background (ID `bk26gieqj`). Expected elapsed: ~50 min at ~2.5 min/question. Goal: ≥14/20 (70%). Stop threshold: <13/20 (65%).

---

### 20:49 — Regression completed at 13/20 = 65.0 %

Exactly at stop boundary. Not the clear pass I projected, but below the 68-72 % expected range. Failure pattern looked infrastructural: three 0-second `no_answer_file_written` exits (UID0190, UID0052, UID0168) in the middle of the run. Escalated to Leon. He approved diagnose-and-rerun.

### 21:10 — SQLite-race hypothesis (wrong)

Inspected `~/.local/state/goose/logs/cli/2026-04-16/`. Two log files showed multiple `Recipe execution started` within 15-35 ms but only one `Headless session started` each. The 4 MB `sessions.db-wal` file suggested active SQLite WAL contention. Wrote ADR-007 proposing `--name <uuid>` + 300 ms settle delay. Implemented. Smoke-tested UID0190 standalone: **still failed at 0.4 s**. Hypothesis refuted.

### 21:25 — Newline correlation check (right)

Counted newlines in question text across all 20 regression UIDs. Perfect segregation: 3 zero-second failures have 1, 1, 6 newlines respectively; all 13 passes have 0 newlines; all 3 genuine 600 s timeouts have 0 newlines. `--params instruction=<text with \n>` breaks goose's CLI parser. One-line fix: `instruction_arg = " ".join(question.split())` before passing to `--params`.

Smoke test UID0190 post-fix: returns `-11` in 79 s. Fix validated. ADR-007 rewritten with the correct root cause + the diagnostic lesson.

### 21:45 — Rerun of UID0190, UID0052, UID0168

All three reached the model this time. All three failed, but in different modes than before:

- UID0190 → `-54` vs expected `-11`. MiniMax stochastic variance (same question returned `-11` in the pre-rerun smoke test).
- UID0052 → `2.26` vs expected `2.23 %`. 1.34 % off, just outside the 1 % fuzzy tolerance.
- UID0168 → timeout_600s. Hard multi-month extraction; 600 s budget insufficient.

Net score unchanged at 13/20 = 65 %. Per Leon's stop-and-escalate rule for different-mode failures, stopped and escalated. Leon approved Option 1: close day 1 at 65 % as the honest baseline.

### 22:05 — Close day 1

Three lock-in items per Leon:
1. ADR-004 — added Day-1 Run-1 Baseline table (all 20 per-UID outcomes) and Forward-Looking Notes for UID0190 (variance), UID0052 (tolerance-edge), UID0168 (timeout-budget). Day-2 Gate Threshold Reset section: **stop below 12/20**, warn at 12/20, pass at ≥ 13/20. 14/20 pre-run projection explicitly retired.
2. `SPRINT_STATUS.md` — Hard Gates section rewritten with the new thresholds and a note against reverting under schedule pressure. Bootstrap checklist includes `METHODOLOGY.md` for future sessions.
3. `METHODOLOGY.md` — new file with three cross-day working principles: cheapest-discriminating-test-first (demonstrated by ADR-007's diagnosis arc), Arena-artifacts-authoritative, and don't-pull-forward-when-blocked-waiting.

**Day 1 closed.** Second commit imminent with Agent.ask fix, ADR-007, updated ADR-004, regression results, SPRINT_STATUS, and METHODOLOGY.
