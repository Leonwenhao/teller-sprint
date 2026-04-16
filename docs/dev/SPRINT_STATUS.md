# Sprint Status

**Day:** 1 of 5 (Thursday 2026-04-16)
**Current task:** Repo audit in Leon review; parallel day-1 work per Path B
**Last passing regression:** N/A — first regression run is the day-1 evening gate
**Active blockers:** 1 — see `BLOCKED.md` BLOCK-01 (Treasury corpus location)

## Bootstrap Checklist (Next-Session Entry Point)

When resuming a fresh session, read in this order before any other action:
1. This file (`SPRINT_STATUS.md`).
2. `ARCHITECTURE_DECISIONS.md`.
3. `BLOCKED.md`.
4. `/Users/leonliu/Desktop/arena-cohort0/Revised_TELLER_STRATEGY.md`.
5. `/Users/leonliu/Desktop/arena-cohort0/Revised_TELLER_DEVELOPMENT_PLAN.md`.
6. `day_N_log.md` for the current day.

Confirm verbally with Leon before any work: which day we are on, last passing regression, and next task.

## Day 1 — Foundation, Abstraction, Regression Gate

**Goal:** Treasury domain runs through a clean abstraction and passes a 20-question regression at ≥70%.

**Deliverables:**
- [x] `REPO_AUDIT.md` written. Leon approved with additions (FINAL_REPORT.md → `docs/research/final_report.md`, sentient-arena-cohort0-journey.md → `docs/research/journey.md`) and judgment-call ratifications.
- [x] `teller/` sibling directory skeleton (pyproject.toml, LICENSE, .gitignore, .env.example, CHANGELOG, __init__.py files).
- [x] `ARCHITECTURE_DECISIONS.md` with ADR-001 (iron rules), ADR-003 (reasoning effort = medium), ADR-004 (regression stratification — **methodology + UID list pending Leon review in REGRESSION_SET_SELECTION.md**), ADR-005 (prompt split validation gate with Diff Summary populated). ADR-002 reserved for day-2 XBRL library choice.
- [x] Scaffolded public API: `Agent`, `Result` (+ `Source`, `XBRLValidation`), `Corpus`, `config.py` with `NotImplementedError` internals. `from teller import Agent, Corpus, Result` works.
- [x] `prompts/base.j2` — full universal content (iron rules + generic workflow + 20 named formulas + universal table-reading + output format + web search). 7 Jinja blocks for domain overlays.
- [x] `prompts/_source_goose_prompt.j2` — immutable Arena-winning source with protective header comment.
- [x] `src/teller/domains/treasury/prompt.j2` — treasury overlay extending base, filling all 7 domain blocks.
- [x] `src/teller/domains/treasury/skill.md` — 138-line treasury skill content.
- [x] `tests/test_iron_rules.py` — 6/6 passing (base anchors + treasury overlay anchors).
- [x] ADR-005 Diff Summary populated. 95.4% similarity, 3 replaced lines (all intentional generic-base rephrasing with no content loss). Pending Leon annotation.
- [x] Corpus migrated: 697 Treasury Bulletin TXT files + index.txt → `tests/fixtures/treasury_bulletins/` (379 MB on disk, ~95 MB git pack). `README.md` with provenance note written.
- [x] Production artifacts migrated: `prompts/_source_goose_prompt.j2`, `src/teller/domains/treasury/skill.md`, `recipes/treasury.yaml` (renamed from recipe.yaml), `arena.yaml`.
- [x] Test fixtures migrated: `tests/fixtures/officeqa/{officeqa_full.csv, reward.py, complete_246_results.json, variance_matrix.csv}`.
- [x] Research material copied: `docs/research/final_report.md`, `docs/research/journey.md`.
- [x] Scoring infrastructure migrated: `scripts/{regression.py, aggregate_results.py, local_score.py}`.
- [x] `REGRESSION_SET_SELECTION.md` — concrete 20 UIDs proposed, 4 ALWAYS-FAIL picks flagged for Leon review. **Awaiting Leon approval.**
- [x] PyPI `teller-agent` verified available. Locked in pyproject.toml.
- [ ] (Post-approval) ADR-004 concrete UID list appended; `tests/fixtures/officeqa/regression_twenty.json` generated.
- [ ] (Post-approval) Implement `Corpus.describe`/`.index` against `tests/fixtures/treasury_bulletins/`.
- [ ] (Post-approval) Wire `Agent.ask` via goose/openhands-sdk against the bundled corpus.
- [ ] (Day-1 evening) 20-question treasury regression run ≥70%.
- [ ] (Day-1 evening) Initial git commit and Leon hand-off.

## Hard Gates

- Day 2 does not begin until day 1's 20-question regression is ≥70%.
- Day 3 does not begin until day 2's Apple `pip install` → `teller ask` smoke test passes.
- Day 4 does not begin until day 3's 25-question SEC test passes (tiers 1–2 ≥80%, tier 3 abstention ≥60%) **and** treasury regression still ≥70%.
- Day 5 does not begin until private beta is out and no catastrophic feedback.
- Launch does not ship until Leon has approved the blog post, Twitter thread, and Show HN copy.

## Protected Invariants (Sprint-Wide)

- Iron rules (write-answer insurance, Python-only math, termination signal) are preserved by `tests/test_iron_rules.py`. Any prompt change that alters a semantic anchor requires a new ADR that explicitly deprecates the old form.
- Every day ends with a treasury regression run. If regression drops below 70%, day work stops and the drift is restored before proceeding.
- `reasoning_effort: medium` is locked by ADR-003. Any change requires a new ADR with Arena-evidence or SEC-evidence citing why medium is wrong for the target domain.
- Model default is MiniMax M2.5 via OpenRouter. Swap is a one-line change in `src/teller/config.py`.
- The corpus abstraction is grep-based. No vector search, embeddings, or RAG in v0.1. Semantic retrieval is a v0.3 backlog item.

## Sprint Budget

- OpenRouter: funded (headroom well past $10/single-run threshold).
- Projected sprint spend: ~$6 regression runs + ~$4 full benchmarks ≈ $10.
- Routine regression runs: no pre-spend confirmation needed.
- Pre-spend confirmation required: any single experimental run >$10.

## Tier-3 Items (Flag but Non-Blocking for Today)

- **EDGAR user-agent** (day 2): `leon@dolores.research` if live, else Gmail fallback with BLOCKED-list swap entry.
- **PyPI `teller-agent`** (~~day-1 evening~~ verified 2026-04-16 15:50): **AVAILABLE**. Locked in `pyproject.toml`. Fallback `dolores-teller` also available, not needed.
- **GitHub `dolores-research/teller`** (day 2): Leon creating the org. Develop in personal repo and transfer when ready; no day-1 dependency.

## Last Updated

2026-04-16 late afternoon. Day 1 session 1. Migration complete. Prompt split complete. Treasury corpus migrated (379 MB, 697 files). ADR-005 diff summary populated. `REGRESSION_SET_SELECTION.md` ready for Leon review. Tests 6/6 green. All authorized Leon-approved work finished; next step is Leon's approval on the regression set.
