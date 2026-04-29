# Sprint Status

**Day:** 5 of 5 (sprint window stretched 2026-04-22 → 2026-04-28) — **CLOSED. v0.1.0 tagged at `63c35e6`, pushed to private mirror.**
**Current task:** v0.1.1 work begins. First-recipient round-trip gate (#6 from day-5 cold-start) pending — that is the actual launch-readiness signal.
**v0.1.0 ship state:**
- Tag: `v0.1.0` (annotated), pushed to `Leonwenhao/teller-sprint`. Tag object SHA `ae846a93e6c34abaa2014295f79a73d672b1443f` → commit `63c35e66580c72cb076ef612d24655bbf003aaa0`.
- Wheel: `dist/teller_agent-0.1.0-py3-none-any.whl` (63230 bytes, SHA-256 `384022a0f94947977467151568bee46326b0a03141b25e9cd97183541216179f`).
- Sdist: `dist/teller_agent-0.1.0.tar.gz` (65871 bytes, SHA-256 `cb8cb06a35a1474595b4095c1d7803f5b5c7d8e9570ae9db6ab120eb4e114289`).
- Distribution shape: private repo + wheel + invited install. PyPI publish paused (private repo would create a dead pointer).
- Day-5 commits on main: `3fbbe3f` (post-audit copy reconciliation), `88ca710` (wheel-safe packaging hotfix), `63c35e6` (XBRL guardrails + CLI input validation + onboarding updates).
**v0.1.0 ship-baseline regression (single run at the v0.1.0 commit):**
- **Treasury:** 14/20 = 70 % (gate ≥13/20 per ADR-004; ±2 variance band). Recorded in `results/regression_twenty_20260427T234106Z.json`.
- **SEC tier-1+2:** 15/18 = 83.3 % (gate ≥80 %). Three single-run fails: SEC0007 both-attempts-timeout/null, SEC0015 sign error, SEC0016 scale/format. SEC0017 PASSED today under the loose scorer (still v0.1.1 fix scope for the labeled-list format). Recorded in `results/gate_sec_20260428T171334Z.json`.
- **SEC tier-3:** 7/7 = 100 % (gate ≥60 %). Strict `segment_level_dimensional` reason-code match held.
- **Unit suite:** 61 passed, 1 skipped, 1 deselected.
- **Fresh-clone install verified:** wheel install from `/tmp/.venv-v010-final` (Python 3.12.12) outside the repo. `teller --help`, `from teller import Agent, Corpus, Result`, and `Agent._recipe_path()` all resolve cleanly from site-packages. **This is the authoritative pre-distribution test going forward — wheel install from outside the repo, not editable install.**
**v0.1.1 calendar (started 2026-04-28):** target ship 2026-05-08 (10 calendar days from `v0.1.0` tag). Non-negotiable per ADR-011. Scope: ADR-011 reasoning-trace persistence (load-bearing), SEC0017 labeled-list answer format, editable install `.pth` resolution (developer-ergonomics debt), Arelle warning suppression, CLI input validation extensions, latency-copy recalibration if first-recipient runs cluster above 180s. Stream-decode-as-retry-trigger waits on trace persistence. Detail in `DAY5_RETROSPECTIVE.md`.
**Active blockers:** none. First-recipient round-trip gate is open but not blocking close.

## Bootstrap Checklist (Next-Session Entry Point)

When resuming a fresh session, read in this order before any other action:
1. This file (`SPRINT_STATUS.md`).
2. `ARCHITECTURE_DECISIONS.md`.
3. `METHODOLOGY.md` (cross-day working principles — cheapest-discriminating-test-first, artifacts-over-memory, no-pull-forward).
4. `BLOCKED.md`.
5. `/Users/leonliu/Desktop/arena-cohort0/Revised_TELLER_STRATEGY.md`.
6. `/Users/leonliu/Desktop/arena-cohort0/Revised_TELLER_DEVELOPMENT_PLAN.md`.
7. `day_N_log.md` for the current day.

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
- [x] ADR-004 concrete UID list appended (20 UIDs locked). `tests/fixtures/officeqa/regression_twenty.json` generated.
- [x] ADR-005 signed by Leon. Diff accepted as domain-neutral; hard-gate (regression) remains the binding criterion.
- [x] ADR-006 added — harness correction (goose, not openhands-sdk); Revised Dev Plan Architecture Principles section corrected inline with pointer to ADR-006.
- [x] Feedback memory saved: `feedback_arena_artifacts_authoritative.md` in ~/.claude/projects memory.
- [x] Git config set repo-local (`leon@dolores.research`, `Leon Liu`). No global config touched.
- [x] Initial git commit landed (`e50aac8`).
- [x] Goose CLI installed (`brew install block-goose-cli`; v1.31.0 verified).
- [x] `Corpus.describe` and `Corpus.index` implemented against `tests/fixtures/treasury_bulletins/`. `describe()` reports 697 files, 362 MB, 1939-2025 range, has_index=true.
- [x] `Agent.ask` implemented wrapping goose via subprocess with path substitution (/app/corpus → corpus fixture dir, /app/answer.txt → temp workspace).
- [x] `scripts/regression.py` rewritten for --set twenty using Agent.ask path.
- [x] Smoke test passed: UID0002 → `'507.0'` (expected `507`) in 152.5s.
- [x] **20-question treasury regression run — baseline 13/20 = 65 %.** Honest empirical result. 3 rerun failures (UID0190 variance, UID0052 tolerance-edge, UID0168 timeout-budget) all failed in different modes than the original 0-second no-answer bug. ADR-007 fix resolved the harness infrastructure issue; residual failures are genuine behavior/parameter concerns documented in ADR-004 forward-looking notes.
- [x] Day-2 regression gate re-anchored to the empirical baseline: stop below 12/20.
- [x] ADR-007 recorded with correct root cause (newlines in `--params`) + the "cheapest discriminating test first" lesson.
- [x] `METHODOLOGY.md` created with three cross-day working principles.
- [x] Agent.ask fix committed; ADR-004 updated with Day-1 Run-1 baseline + per-UID forward notes.

## Hard Gates

- **Day 1 regression baseline:** 13/20 = 65 % (day-1 run-1 result after ADR-007 fix). This supersedes the pre-run 14/20 (70 %) projection.
- **Day 2+ regression gate:**
  - Pass: ≥ 13/20 (matches or exceeds the day-1 baseline).
  - Warn: 12/20 (60 %) — below baseline but above stop. Investigate drift but do not auto-stop.
  - **Stop: < 12/20 (60 %).** Day work halts until the drift is diagnosed and restored. Do not revert the threshold to 14/20 under schedule pressure — the baseline is empirical, not aspirational.
- **Day 3 does not begin until day 2's Apple `pip install` → `teller ask` smoke test passes.**
- **Day 4 does not begin until day 3's 25-question SEC test passes (tiers 1–2 ≥ 80 %, tier 3 abstention ≥ 60 %) AND the treasury regression is still ≥ 12/20.** (≥12/20 at a day boundary is the ADR-004 warn threshold, not the pass threshold — the day-3→4 transition is intentionally permissive of one-day variance rather than requiring ≥13/20, since day-3 prompt iteration on SEC may produce treasury drift. A warn-level result does not block day-4 but does require investigation before day-5 launch prep.)
- Day 5 does not begin until private beta is out and no catastrophic feedback.
- Launch does not ship until Leon has approved the blog post, Twitter thread, and Show HN copy.

See ADR-004 "Day-2 Gate Threshold Reset" for the reasoning behind the baseline change.

## Protected Invariants (Sprint-Wide)

- Iron rules (write-answer insurance, Python-only math, termination signal) are preserved by `tests/test_iron_rules.py`. Any prompt change that alters a semantic anchor requires a new ADR that explicitly deprecates the old form.
- Every day ends with a treasury regression run. Gate thresholds per ADR-004 Day-2+ reset: pass ≥13/20 (65%), warn at 12/20 (60%), **stop below 12/20**. Pre-baseline 14/20 (70%) target is retired — do not revert under schedule pressure.
- `reasoning_effort: medium` is locked by ADR-003. Any change requires a new ADR with Arena-evidence or SEC-evidence citing why medium is wrong for the target domain.
- Model default is MiniMax M2.5 via OpenRouter. Swap is a one-line change in `src/teller/config.py`.
- The corpus abstraction is grep-based. No vector search, embeddings, or RAG in v0.1. Semantic retrieval is a v0.3 backlog item.

## Sprint Budget

- OpenRouter: funded (headroom well past $10/single-run threshold).
- Projected sprint spend: ~$6 regression runs + ~$4 full benchmarks ≈ $10.
- Routine regression runs: no pre-spend confirmation needed.
- Pre-spend confirmation required: any single experimental run >$10.

## Day-4 strict-canonical + principle-backstop bundle — landed, tested, reverted

**Outcome:** bundle reverted per Leon's pre-committed threshold (tier-1/2 < 17/18 OR SEC0017 still fails OR tier-3 < 7/7). Gate result with bundle: **tier-1/2 = 14/18 (77.8 %, below 80 % gate), tier-3 = 7/7**. Revert triggered on the first criterion.

**What the bundle did right:**
- SEC0017 (ExxonMobil two-year total assets — the specific question that motivated the bundle) **PASSED** with `'2024: 453475, 2025: 448980'`. Labeled-list form worked exactly as designed.
- SEC0013 (MSFT three-year net income) also passed with labeled form `'2025: 101832, 2024: 88136, 2023: 72361'`. Strict canonical clearly lands on questions that reach extraction.
- Tier-3 held at 7/7 with the expanded principle-backstop wording. Principle backstop did not cause over-abstention on currently-passing tier-1/2 questions (no tier-1/2 answers flipped to `abstained=True`).

**What the bundle broke:**
- **SEC0005** (NVIDIA net income FY26) — `no_answer_file_written` at 593 s. Previously passed day-4 morning at 333 s with `120067`. This is the ADR-007 loud-signal class: structural failure, not retry-triggerable.
- **SEC0008** (Alphabet cash FY25) — content miss: `23466` vs expected `30708`. Previously passed at 211 s with `30708`. Wrong balance-sheet line extracted.
- **SEC0011** (Apple % revenue change FY24→FY25) — content miss: `0.0202` vs expected `0.0643`. Previously passed at 89.7 s with `6.43` (loose scorer). Wrong computation.
- **SEC0016** (JPM two-year total assets) — `timeout_600s` at 1360 s cumulative. **Both attempts timed out.** Previously passed morning at 319.7 s. This is the exact customer-visible-opacity event ADR-011's re-escalation trigger was written for — but fired in pre-launch regression, not private beta.

**Diagnosis — context-pressure hypothesis.** The bundle added ~20 lines to the SEC overlay (~600 tokens). Three of the four fails were previously-passing questions that today either (a) exited silently (`no_answer_file_written`), (b) extracted the wrong value, or (c) both-timed-out. The pattern — degraded extraction quality on questions that were reliably passing under a shorter prompt — is consistent with context-pressure on MiniMax M2.5 more than it is with stochastic variance. Stochastic variance typically shows as single-run flips distributed across the question set (as we saw in UID0002 this morning); three content/structural fails plus one both-attempts-timeout clustered in one run lines up more cleanly with prompt-length causation.

**What is not reverted (kept as additive):**
- `docs/OUTPUT_CONVENTIONS.md` stays. The conventions are still the right canonical for v0.1 launch copy; enforcement will have to come from either a narrower prompt change (e.g. only the labeled-list rule) or a post-processing normalization layer, decided post-revert.
- `NOTICE` file stays. Apache 2.0 compliance is additive.
- ADR-012 retry-on-timeout stays. Independent of bundle; already proven load-bearing today.
- ADR-011 stays accepted-for-v0.1.1 with the re-escalation trigger. SEC0016's both-attempts-timeout is pre-launch evidence pointing toward the trigger but not private-beta customer-visible, so we flag but do not auto-escalate. Leon's call.

**Post-revert state:** `prompts/base.j2`, `src/teller/domains/sec_filings/prompt.j2`, `recipes/sec_filings.yaml` all match the this-morning-gate-passing state (git diff empty). Unit suite 51 passed / 1 skipped. The morning gate (17/18 tier-1+2, 7/7 tier-3) is the authoritative day-4 SEC gate result. SEC0017 remains unresolved (ordering-mismatch fail).

## Day-4 regression variance notes

The treasury 13→15 count change is not clean "ADR-012 won us two." Honest accounting:

- **UID0014 (SWING-5):** day-1 and day-3 both 600 s timeout; day-4 passed at 1173 s cumulative via ADR-012 retry. This is a genuine retry-on-timeout win. First live production evidence the implementation earns its keep.
- **UID0168 (SWING-5):** day-1 600 s timeout; day-4 passed at 340 s with no retry needed. Stochastic variance, not a retry win.
- **UID0052 (SWING-5 tolerance-edge):** day-1 failed at `2.26` (1.34 % off); day-4 passed at `2.23` exact. Stochastic variance.
- **UID0002 (ALWAYS_PASS):** day-1 passed at `507.0`; day-4 failed at `661.0` vs `507`. This is a flip on an easy-tier VA FY1934 single-file lookup that has no business regressing. Worth investigating post-launch but not day-4 scope to chase.
- **UID0199 (SWING-4):** day-1 passed at `0.479`; day-4 failed at `0.455` (5 % off). F-001 gold bloc.

Net: 15 = 13 stable + 2 retry-or-variance wins − 2 variance flips. The 15 count is real gate-wise; treating it as a moat-validation signal would be overclaiming. The MiniMax variance band documented in ADR-004 remains the governing reality: single-run delta of ±2 passes is within the expected noise.

## ADR-011 severity landing — escalation triggered (decision pending Leon)

Two independent criteria converged this day on escalating ADR-011 out of "Reserved for v0.2 / open question."

**Criterion 1 — Day-4 cold-start qualitative:** "if day-4 polish surfaces a third reasoning-opacity scar, move to v0.1; clean close keeps v0.2." The two day-3 scars plus today's two retry events on questions we cannot introspect (UID0014 treasury, SEC0007 tier-1) is more than the qualitative threshold. Each retry event is a customer-observable opacity hit: *why did it stall the first time*.

**Criterion 2 — ADR-012 §telemetry-gap pre-commit:** ">2 % stderr retry-event rate escalates ADR-011 to v0.1.1 launch-blocker." Observed: 4.4 %. Above threshold.

The two criteria disagree on the *shape* of escalation:
- Cold-start criterion says **v0.1 launch-blocker** (ship blocks until trace persistence lands).
- ADR-012 criterion says **v0.1.1 launch-blocker** (ship v0.1, fix in v0.1.1).

I'd push toward the ADR-012 wording. v0.1 ships without trace persistence but with a named v0.1.1 commitment, because: (a) the retries are *succeeding*, which means the customer sees a correct answer with elevated latency, not a mystery failure; (b) the opacity scar only becomes load-bearing when *both* attempts time out, and today's evidence shows that rate is zero so far; (c) blocking v0.1 to build trace persistence delays first-contact feedback, which is the more valuable signal for what observability shape customers actually need. Flag this for Leon's call.

## Launch Punch List (tracked for day 4 — do not drop under compression)

- **`NOTICE` file** per Apache 2.0 §4 — ✅ DONE (commit `39da1d7`). Attributes arelle-release (Apache 2.0 / Workiva); notes jinja2/click/rich under non-Apache licenses that do not require NOTICE.

- **Strict canonical answer format in SEC prompt overlay.** ⚠️ ATTEMPTED AND REVERTED. The strict-canonical + principle-backstop bundle landed in the working tree and was regression-tested; tier-1/2 dropped to 14/18 with three previously-passing questions regressing plus one both-attempts-timeout (SEC0016), triggering the pre-committed revert threshold. Context-pressure hypothesis: ~20 added prompt lines (~600 tokens) degraded MiniMax extraction quality globally. Accepted as known v0.1 limitation: SEC0017's ordering-vs-list-form failure is documented in `docs/PRIVATE_BETA_ONBOARDING.md` known-issue #1, with v0.1.1 fix committed (labeled-list answer format, ≤10 days from v0.1 tag). `docs/OUTPUT_CONVENTIONS.md` kept as the reference spec the v0.1.1 fix will enforce.

- **Principle-based segment-intent markers.** ⚠️ ATTEMPTED AND REVERTED (same bundle as above). The "other than the worldwide consolidated total" principle backstop wording held tier-3 at 7/7 with no tier-1/2 over-abstention observed, so the *content* was sound — but the bundle as a whole tripped context pressure. If we revisit in v0.1.x, land the principle backstop *alone* (3-line addition) and measure, since it was not the regression-causing piece.

- **Fresh-clone install path verification.** ✅ DONE. Verified in `python:3.12-slim` Docker container: `pip install -e .`, `from teller import Agent, Corpus, Result`, `teller --help`, and full 51-test unit suite all green.

- **Example scripts.** ✅ DONE (commit `ecedddd`). `examples/treasury_query.py` and `examples/sec_query.py` demonstrate the two v0.1 domains via the public API surface.

- **Private-beta onboarding note.** ✅ DONE (commit `39da1d7`) at `docs/PRIVATE_BETA_ONBOARDING.md`. Contains: install (Python ≥3.10, goose prereq), `2>&1 | tee teller.log` telemetry ask, three known limitations (list order, latency tail, rare double-stall), v0.1.1 commitment inline.

- **Telemetry hooks.** ✅ DROPPED FROM SCOPE. Retry-event stderr capture already handled by the onboarding-note `tee` instruction. Anything beyond that is ADR-011 work (v0.1.1).

## Open Architectural Items (tracked for upcoming ADRs)

- **Concept-family normalization layer (ADR-008, Reserved).** Per ADR-002 + Codex probe-2: multi-period SEC questions will need a layer above the XBRL parser that maps deprecated/replaced/re-parented US-GAAP concepts across annual FASB taxonomy versions. Not required for day-2 Apple smoke test (single-year). **Required before day-3 SEC test set implementation** if any tier-2 multi-period question touches a concept deprecated or renamed between filing years. Input data: FASB 2025 + 2026 GAAP Taxonomy Release Notes (deprecation/replacement metadata). Write ADR before implementing the layer.
- **Fast-path for top-line extraction (ADR-009, Reserved for v0.2).** Sub-5 s XBRL-only answers for consolidated revenue / net income / total assets class of questions. v0.1 ships without it; v0.2 decision after telemetry.

## Latency Characteristics (empirical, 2026-04-17)

Dev-plan day-2 gate specified "under 30 seconds end-to-end." That was aspirational and pre-measurement. Actual numbers on MiniMax M2.5 + goose against a real iXBRL 10-K:

- **Typical:** 60–120 s per `teller ask` call.
- **Worst case observed:** ~180 s on a 1.5 MB 10-K (Apple FY2025).
- **Best case observed:** ~40 s on simple Treasury Bulletin single-file lookups.
- **Constraint:** LLM + harness latency dominates. The XBRL validation leg is ~200 ms (measured).
- **Download phase:** ~5 s for a complete 10-K filing + XBRL support files (6 documents, ~1.7 MB).
- **End-to-end (download + ask):** 65–125 s typical, ~185 s worst case.

### Launch narrative implication (day-4 / day-5 scope)

The positioning story shifts from "sub-30-second" to "under-two-minute" answers. This is still a decisive win vs. the alternatives in the strategy doc §6 competitive frame:

- Manual 10-K reading: 20–40 minutes per question.
- AlphaSense interactive search: conversational, but hallucinates on precise figures and carries enterprise-subscription cost.
- ChatGPT/Claude with file upload: comparable latency but no citation + no XBRL validation.

README, Twitter launch thread, and Show HN copy must reflect the empirical numbers, not the aspirational 30 s. Documented here so launch materials do not drift back to the pre-measurement number under polish pressure.

## Tier-3 Items (Flag but Non-Blocking for Today)

- **EDGAR user-agent** (day 2): `leon@dolores.research` if live, else Gmail fallback with BLOCKED-list swap entry.
- **PyPI `teller-agent`** (~~day-1 evening~~ verified 2026-04-16 15:50): **AVAILABLE**. Locked in `pyproject.toml`. Fallback `dolores-teller` also available, not needed.
- **GitHub `dolores-research/teller`** (day 2): Leon creating the org. Develop in personal repo and transfer when ready; no day-1 dependency.

## Last Updated

2026-04-22 afternoon, day-4 close (session spanned 2026-04-21 afternoon through 2026-04-22 afternoon Pacific). Day-5 begins from this file plus the day-4 close commits (`39da1d7`, `ecedddd`). All launch-punch-list items either landed or explicitly de-scoped with rationale above. SEC0017 is the single documented v0.1 paper cut, known-issue'd in the private-beta onboarding note with a v0.1.1 commitment.

### Prior snapshot — 2026-04-21 afternoon, day-4 post-regression (preserved) ADR-012 (retry-on-timeout) Accepted and shipped: `RETRY_ON_TIMEOUT: bool = True` class attribute, `_run_once()` helper extracted from `Agent.ask`, single same-model retry on `subprocess.TimeoutExpired` only, stderr line `"teller: model timed out after 600s, retrying (attempt 2/2)..."`, fresh tempdir+uuid on retry, cumulative `latency_ms`. Six test cases in `tests/test_agent_retry.py` cover the full contract including `RETRY_ON_TIMEOUT=False` patch for single-attempt assertions. Unit suite 51 passed / 1 skipped. Treasury 15/20 (ADR-012 retry converted UID0014 from two-day 600 s timeout → 1173 s PASS at `988.2`; UID0168 passed without retry; UID0002 and UID0199 flipped fail from day-1 within MiniMax variance band — not paper over). SEC 17/18 tier-1+2 = 94.4 % (only fail SEC0017 ExxonMobil two-year list is an ordering mismatch, both values correct; retry on SEC0007 converted a 600 s timeout → 1186 s PASS at `448980`); 7/7 tier-3 = 100 % strict-reason. Retry telemetry: 2/45 = 4.4 % — **above ADR-012's pre-committed 2 % threshold, triggering ADR-011 escalation per that ADR's Telemetry gap section**. ADR-011 severity landing pending Leon's call on v0.1 vs v0.1.1 shape (see "ADR-011 severity landing" section above). Remaining day-4 work: ADR-011 decision, then punch-list (NOTICE file, strict canonical format, principle-based segment markers, fresh-clone install, ample scripts, telemetry hooks, private-beta onboarding note per ADR-012 `2>&1 | tee teller.log` ask).

## 2026-04-17 day-2 close snapshot (preserved)

Both day-2 gates met: Apple literal question `"what was Apple's revenue last fiscal year"` → LLM `416161` ↔ XBRL `$416,161,000,000` agreed in 56.5 s; treasury regression re-run landed at 13/20 = 65.0 % (matches day-1 baseline; 4 UIDs flipped up, 4 down — within ADR-004 MiniMax-variance band). Day-2 shipped: ADR-002 Accepted with Amendment A (fail-closed narrowing) + Codex concurrence; XBRL parser + translator; SEC EDGAR downloader (primary .htm + 5 XBRL support files + cache warm-up); SEC domain overlay + recipe with temporal-disambiguation line; Click CLI (ask/download-sec/inspect); `Agent._post_validate` with keyword→concept map + order-of-magnitude normalization. 39 unit tests green, 1 skipped (deferred to Apple smoke). Empirical latency band logged: 60–120 s typical, ~180 s worst — 30 s dev-plan target retired with launch-narrative implication flagged. ADR-008 (concept-family normalization) and ADR-009 (v0.2 fast-path) reserved. `scripts/regression.py` exit-code threshold fixed to 13/20.

## Cold-start SHA drift note (2026-04-17, day-2 bootstrap)

Leon's day-2 cold-start prompt cited the day-1 close commit as `7c47255`. Local `git log` on `main` shows three commits: `e50aac8` (initial scaffold), `7a8c088` (day-1 close with ADR-007 newline fix and the 13/20 baseline), `e9a8e65` (retrospective). No `7c47255` in the history. The 13/20 baseline is consistent across ADR-004, this file, and the retrospective; treating those as ground truth. The cited SHA is assumed stale from the cold-start prompt draft. Breadcrumb only — do not chase unless it matters later.
