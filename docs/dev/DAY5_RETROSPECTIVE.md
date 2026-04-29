# Day 5 Retrospective — Teller v0.1 Sprint

**Dates:** 2026-04-22 morning through 2026-04-28 evening Pacific. The day-5 calendar window stretched across multiple sessions because mid-sprint findings forced a packaging hotfix and a Phase-3 hardening pass before close.
**Authors:** Claude Code (Opus 4.7) for implementation, Codex (audit + adversarial test + treasury diagnostic + hardening) for second-opinion and verification, Leon for decision-making at every gate.
**Status:** Day 5 closed. v0.1.0 tagged at `63c35e6`, pushed to private mirror `Leonwenhao/teller-sprint`. Wheel + sdist artifacts built in `dist/`. Three commits landed across the sprint: `3fbbe3f` (post-audit copy reconciliation), `88ca710` (wheel-safe packaging hotfix), `63c35e6` (v0.1 hardening — XBRL guardrails + CLI input validation + onboarding updates).

## Top-line outcome

Teller v0.1.0 ships as a private-beta wheel artifact for invited recipients. Distribution is private repo + wheel + invited install path; PyPI publish is paused while the repo is private. Both regression gates pass: treasury 14/20 (within ADR-004 ±2 variance band of the 13/20 baseline), SEC tier-1+2 15/18 = 83.3% (gate ≥80%), SEC tier-3 7/7 = 100% (gate ≥60%). Unit suite 61 passed / 1 skipped. Wheel install is end-to-end verified from a fresh `/tmp` venv outside the repo: `pip install <wheel>` → `teller --help` → `from teller import Agent, Corpus, Result` → `Agent.ask()` round-trip → XBRL validation → JSON Result.

The first-recipient round-trip gate (#6 from the day-5 cold-start prompt) is **not yet satisfied**. The recipient is selected and onboarded, but no external user has completed an install → `teller ask` → answer round-trip. That gate moves to v0.1.1 timeline.

One-sentence takeaway: **day 5 proved that strategic external review is a load-bearing engineering input, not a polish nicety — Codex's audit, adversarial test, and diagnostic each surfaced a class of bug that Claude Code had not seen, including a wheel packaging ship-blocker that day-4's editable-install Docker verification had masked.**

## What shipped

**Commits:**
- `3fbbe3f` — post-audit copy reconciliation per Codex's 6-axis review. Five drift points fixed: README "abstains" overclaim → "surfaces both", `Result.sources` overclaim → "reserved citation field", `OUTPUT_CONVENTIONS.md` reverted-but-documented enforcement → labeled as v0.1.1 reference spec, `PRIVATE_BETA_ONBOARDING.md` retry-correctness guarantee softened to "in day-4 regression both observed retries recovered; inspect XBRL/citations before relying on it", ADR-011 calendar reconciled from "two weeks" to "10 calendar days" matching the public commitment.
- `88ca710` — wheel-safe packaging hotfix. `git mv recipes/ src/teller/recipes/` and `git mv prompts/ src/teller/prompts/` (pure renames, byte-identical content), `[tool.setuptools.package-data]` directive added, `Agent._repo_root()` parent-walk replaced with `_recipe_path(domain)` static helper using `importlib.resources.files("teller")`. `tests/test_agent_retry.py` monkeypatch swapped from `_repo_root` to `_recipe_path`. `tests/test_iron_rules.py` `PROMPTS_DIR` updated. `scripts/render_recipes.py` paths updated. `scripts/regression.py` and `scripts/gate_sec.py` removed the `sys.path.insert(0, str(REPO / "src"))` workaround so regression evidence comes from the wheel-installed `teller`, not the source tree.
- `63c35e6` — Phase-3 hardening. `Agent._post_validate()` adds four pre-validation gates that fire in order before any XBRL lookup: `non_numeric_answer` (catches `"NOT_IN_FILING"` sentinels and other non-parseable strings), `entity_mismatch` (compares question's named entity against `dei:EntityRegistrantName`), `period_unspecified` (requires explicit fiscal period in the question), `concept_unsupported` (catches scoped concepts like "services revenue" that a coarse keyword match would otherwise mis-route to a more general concept). CLI `ask` rejects empty/whitespace-only questions with non-zero exit before any inference. `PRIVATE_BETA_ONBOARDING.md` updated with two new known-issue entries: `no_answer_file_written` overload (provider stream decode vs structural failure) and `agreed=false` interpretation guidance.

**Artifacts:**
- `dist/teller_agent-0.1.0-py3-none-any.whl` — 63230 bytes, SHA-256 `384022a0f94947977467151568bee46326b0a03141b25e9cd97183541216179f`.
- `dist/teller_agent-0.1.0.tar.gz` — 65871 bytes, SHA-256 `cb8cb06a35a1474595b4095c1d7803f5b5c7d8e9570ae9db6ab120eb4e114289`.
- `v0.1.0` git tag, annotated, pushed to origin.
- Codex reports preserved at `docs/dev/CODEX_DAY5_AUDIT.md`, `docs/dev/CODEX_DAY5_TEST_REPORT.md`, `docs/dev/CODEX_DAY5_TREASURY_DIAGNOSTIC.md`.

## Load-bearing patterns from day 5

### External review is a strategic engineering input, not a polish step

Day 4 closed with a self-test that said "the wheel install works." The verification was `pip install -e .` in a `python:3.12-slim` Docker container. Day-5 Codex caught the gap on the first adversarial query: the wheel ships only `.py` files, no recipes, no prompts; `Agent.ask` fails with `FileNotFoundError` before any inference. This was a ship-blocker that the day-4 regression discipline had no way to catch because the regression tools themselves used `pip install -e .`. Codex saw it because Codex tested the wrong-for-development install path — which was the right-for-distribution install path.

The pattern: an external reviewer with the same context but a different starting habit will surface bugs that the implementer's habits hide. Day-5's three-agent loop — Leon decides, Chat strategizes, Code implements, Codex audits — is now a documented working mode, not an ad-hoc move. The cost is real (Codex sessions consume context and time), but two of the three commits this day were Codex catches that would otherwise have shipped as broken.

### Verify the distribution artifact, not the source tree

The wheel-vs-editable distinction is now a discipline. Future "fresh-clone install verified" notes must specify which install path was used, and the launch-gate verification must be wheel install from outside the repo. Editable install verification is acceptable for unit-test runs and developer-loop sanity checks; it is not acceptable as a release gate. The corollary in this sprint: `python:3.12-slim` Docker is no longer a sufficient verification environment unless the install command is `pip install <wheel>` rather than `pip install -e .`.

### Stated-memory-vs-artifacts-authoritative carries forward and bites at scale

Three instances of this scar this sprint:
1. **174 vs 176 OfficeQA question count.** Cold-start said 71.5%; the research doc had 70.7% (174/246). Reconciliation revealed two distinct evaluation runs: original Apr 6 (174 correct, 70.7%, score 192.046) and Apr 8 Sentient rerun (176 correct, 71.5%, score 187.823). Both numbers are real; the public claim is the rerun.
2. **$4/question Opus 4.5 cost figure** propagated through six docs without a primary citation. WebFetch of the Databricks blog confirmed no cost data is published. The 1/500th cost claim was dropped from the README; the unsourced number remains in arena-cohort0 artifacts as a follow-up, out of v0.1 scope.
3. **arXiv:2603.08655 reference** was used as a footnote source for the cost claim; verification revealed it's a *different benchmark* (OfficeQA Pro, 133 questions, Opus 4.6) — not the OfficeQA Full (246 questions, Opus 4.5) we ran against.

The scar is consistent: facts in non-machine-checked artifacts decay or were wrong from the start. **For load-bearing claims, verification before commit is the protocol** — not "did Claude Code remember it correctly." The `feedback_arena_artifacts_authoritative.md` memory file existed before this sprint and still got tripped twice on day 5 alone.

### Pre-flight cite + arithmetic verification on launch-class footnotes

Claude Code's first README footnote drafted a clean sentence with a wrong arXiv link and arithmetic that didn't match the source claims. Forced verification (re-fetch the blog, paste the exact sentence, do the math) caught both. The rule: launch-class footnotes get a cite + arithmetic check before the commit, not after. This is a special case of the artifacts-authoritative scar but worth its own line because launch copy is the highest-blast-radius surface in a sprint.

### Service variance is a distinct failure class from code drift

The treasury 12/20 result on the post-hotfix run looked like behavioral drift. Codex's diagnostic spot-check on UID0014 attributed the failure to provider stream-decode events, not packaging changes. Recipe and prompt content was byte-identical to pre-hotfix; the only difference was the install path — which doesn't affect the prompt the LLM sees. The right move was to spend $0.02 on one isolating query before spending $0.50 on a regression re-run.

The principle: **regression results within ADR-004 variance bands but with anomalous patterns** (timeout clusters, 2× runtime, multiple `no_answer_file_written` events in close succession) **require diagnostic before attribution.** "In-band per ADR letter" is not sufficient evidence on its own when the failure shape is novel. The reverse is also true: "out-of-band" can be service-side; check before assuming code drift.

### `no_answer_file_written` is overloaded

Same exit code, two root causes: (a) goose subprocess crashed before writing the answer file (structural failure, ADR-007 loud-signal), or (b) provider stream decode error mid-response (transient, retry-eligible-in-spirit-not-yet-in-code). Day-5 evidence: 5 occurrences across treasury+SEC regressions, vs 1 on day 4. Codex's diagnostic confirmed at least one was provider-side. ADR-012 currently does not retry on this class because it's defined as loud-signal; with this evidence, the v0.1.1 work plan should consider extending the retry trigger after ADR-011 trace persistence lets us positively identify the class from goose session logs. For now: documented in `PRIVATE_BETA_ONBOARDING.md` as a known limitation with provider attribution, and retro candidate from earlier in the day promoted to launch-copy.

### XBRL guardrail-gap is one root cause with four shapes

Phase-3 adversarial matrix surfaced `agreed=false` signals on:
- a non-numeric answer (`"NOT_IN_FILING"`),
- an entity mismatch (Apple question against XOM corpus),
- a period-unspecified question (model picked FY2024, validator picked FY2025),
- a scoped concept (services revenue mis-routed to total revenue concept).

All four were the same root cause: the validator ran without question-context guardrails. The hardening commit `63c35e6` adds the four gates explicitly, in fixed order. They are intentionally narrow — the "concept_unsupported" gate uses a curated list of scoped revenue terms, not a heuristic. Future XBRL guardrail work should expand this list with evidence, not preemptively.

### Distribution shape is a product decision, not release plumbing

PyPI vs GitHub-private vs wheel-attached-to-invite vs README-stranger-safety vs first-recipient-round-trip are not separable. Treating them separately produced a brief plan to publish to PyPI while the repo was private — which would have created a 404-pointer launch surface for any stranger who clicked the package metadata. Halting that and switching to private-beta-wheel-invite was a product call about who v0.1 is for, not a release-engineering tweak.

## What not to redo on day 6 or v0.1.1

- **Do not reopen the XBRL guardrail set** to add more preconditions without spot-check evidence. Four gates (non-numeric, entity, period, concept-scope) are the fixed v0.1 scope. Adding a fifth without evidence is the same diagnosis-coarseness cost the day-4 strict-canonical bundle paid.
- **Do not propose retry trigger extension to the stream-decode class** until ADR-011 trace persistence lands. Without trace, we can't positively identify stream-decode vs structural failure, and broadening retry on ambiguity will mask real bugs.
- **Do not run regressions unless a structural change lands.** Day-5 regression evidence is the v0.1.0 ship baseline; re-running for fun burns cost and adds noise to the baseline.
- **Do not re-litigate `dolores-research` org / repo public-flip / PyPI publish during v0.1.1 work.** Those are post-feedback decisions, not v0.1.1 scope. v0.1.1 ships into the same private-beta-wheel-invite shape unless first-recipient feedback materially changes the distribution case.
- **Do not propose Arena-cohort0 cost-claim cleanup in v0.1.1 work.** Out of repo scope. Track as a follow-up in the arena-cohort0 repo separately.
- **Do not reanchor regression baselines to today's numbers.** Treasury 14/20 and SEC 15/18 are *single runs at the v0.1.0 ship boundary*. ADR-004 baselines (13/20 treasury, ≥80% SEC tier-1+2, ≥60% tier-3) remain the empirical floors. v0.1.1 regression discipline runs against ADR-004 thresholds.
- **Do not soften pre-committed revert criteria after seeing partial results.** The day-4 strict-canonical revert and the day-5 packaging-hotfix gate-pause both held this discipline. v0.1.1 must hold it too — especially on ADR-011 trace persistence, where partial implementations will be tempting to ship as "good enough."

## v0.1.1 calendar — started 2026-04-28

10-day commitment from `v0.1.0` tag. Target ship: **2026-05-08**. Non-negotiable per ADR-011 acceptance and the public commitments in README, CHANGELOG, and `PRIVATE_BETA_ONBOARDING.md`.

Committed v0.1.1 scope:
- **ADR-011 reasoning-trace persistence.** Load-bearing. The first v0.1.1 item; if not ready by day-7-from-tag, ship a smaller trace shape and pick up the remainder in v0.1.2 — do not slip the calendar.
- **SEC0017 labeled-list answer format.** Documented v0.1.1 fix (multi-year list ordering as `2024: ..., 2025: ...`).
- **Editable install `.pth` resolution** for Python 3.12.12+ / 3.14. Reclassified from SHIP-BLOCKER (Codex's halt) to v0.1.1 developer-ergonomics debt now that the wheel install path is verified clean.
- **Arelle warning suppression** on user-facing CLI paths (demote known-benign `ix11.*:invalidTransformation` to debug while preserving in goose logs).
- **CLI input validation extension** — empty/whitespace already in v0.1; v0.1.1 should add minimum-length and obvious-non-question filters with explicit error messages.
- **Latency-copy recalibration** if first-recipient runs cluster above 180s. Watch trigger: if 3+ first-recipient queries land between 180s and 300s, update README + onboarding to "under 3 minutes typical" rather than the current "under 2 minutes typical."
- **Stream-decode-as-retry-trigger** — only after trace persistence lands. Cannot be done blind.

Out of scope for v0.1.1 (carry to v0.2 or backlog):
- Concept-family normalization layer (ADR-008, reserved).
- Sub-5s XBRL-only fast path (ADR-009, reserved).
- Comparative accuracy on alternative models (model-pluggable in API; not benchmarked yet).
- Hosted deployment, second vertical, anything from strategy §9.

## Spend + budget

OpenRouter session totals (cumulative across Codex + Claude Code passes this sprint):
- Pre-day-5 baseline: $87.79.
- Day-5 close: $91.32.
- Day-5 delta: $3.53 (across hotfix verify, two regression-gate runs, treasury diagnostic, Phase-3 adversarial matrix, hardening verify, and Codex's parallel SEC regate).

Original soft cap of $5 was honored. Leon expanded the cap to "use what's needed" mid-sprint after the regression cost became visible, but actual usage stayed under the original cap.

Per-query unit economics from Phase-3 matrix: $0.013–$0.020 range, avg ~$0.017. Useful for v0.1.1 first-recipient cost projections: at observed rates, an active user at 50 queries/week would cost ~$1/week.

## Open watches carried to v0.1.1

- **First-recipient round-trip gate (#6) not yet satisfied.** Recipient selected; install + ask round-trip pending. This is the actual launch-readiness signal, not the regression numbers.
- **SEC0007 both-attempts-timeout** in the Phase-3 SEC re-run is the SEC0016-class event ADR-011 was armed for. Fired in regression, not in customer-facing beta. Watch for first customer-visible both-attempts-timeout — re-escalation trigger flips ADR-011 trace persistence from v0.1.1 calendar item to v0.1 hotfix.
- **Latency tail.** Phase-3 matrix mostly within band (8–190s); two regression-window calls hit 1000s+ via retry. Watch first-recipient runs for cluster pattern.
- **Service variance band on MiniMax.** Two days of evidence (day-4 baseline, day-5 ship run) plus one diagnostic indicate the ±2-pass band is real and frequent. Plan v0.1.1 regression schedule to include at least two runs at different times of day before any threshold change.
- **`no_answer_file_written` retry-trigger discipline.** Currently not retry-eligible; v0.1.1 candidate after trace persistence lands. Do not extend without trace evidence.

---

*End of retrospective. v0.1 sprint closed. v0.1.1 work begins from this document plus `SPRINT_STATUS.md` plus the three day-5 commits (`3fbbe3f`, `88ca710`, `63c35e6`). The three named scars on day 5 — wheel-vs-editable verification, artifacts-authoritative-not-memory, distribution-shape-as-product-decision — are the load-bearing carry-forward into v0.1.1 planning.*
