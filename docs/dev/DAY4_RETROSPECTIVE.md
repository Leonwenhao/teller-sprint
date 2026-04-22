# Day 4 Retrospective — Teller v0.1 Sprint

**Dates:** 2026-04-21 afternoon through 2026-04-22 afternoon Pacific, one continuous two-day session.
**Author:** Claude Code (Opus 4.7) with Leon's direct review at each gate. Zero Codex calls (day-4 scope was entirely polish + one-decision-loop work; cadence criterion from day-3 held).
**Status:** Day 4 closed. Three commits on `main`: `39da1d7` (retry-on-timeout + launch docs), `ecedddd` (examples + artifacts), `c445175` (SPRINT_STATUS close note). Working tree clean.

## Executive Summary

Day 4 was launch polish with three open architectural decisions carried from day-3 retrospective: retry-on-timeout scope, ADR-011 severity (v0.1 vs v0.1.1), and strict canonical answer format. All three resolved. ADR-012 (single same-model retry on `TimeoutExpired` only) drafted, accepted, implemented, regression-verified, and earned its value on first live run — UID0014 and SEC0007 both converted from 600 s timeouts to clean passes at ~1175 s cumulative. ADR-011 resolved for v0.1.1 with a 10-day calendar commitment and a re-escalation trigger on first customer-visible both-attempts-timeout. The strict-canonical + principle-backstop bundle was drafted, applied, regression-tested, and **reverted** when its pre-committed threshold fired — tier-1/2 dropped to 14/18 = 77.8 % with three previously-passing questions degrading plus one both-attempts-timeout (SEC0016), despite the bundle's target question (SEC0017) passing cleanly. Launch polish landed as a tight set: NOTICE, OUTPUT_CONVENTIONS, PRIVATE_BETA_ONBOARDING, two example scripts, fresh-clone install verified in `python:3.12-slim` Docker.

One-sentence takeaway: **day 4 proved that gate discipline governs scope even when the scope change has a demonstrably correct answer — the strict-canonical bundle's design was right (SEC0017 passed), but its delivery mechanism imposed context pressure that regressed three previously-passing questions, and the pre-committed revert threshold caught the trade honestly before launch copy could absorb it.**

## What Shipped

**Commits:**
- `39da1d7` — ADR-012 retry-on-timeout + `tests/test_agent_retry.py` (6 cases) + ADR-011 flip to Accepted-for-v0.1.1 + NOTICE + `docs/OUTPUT_CONVENTIONS.md` + `docs/PRIVATE_BETA_ONBOARDING.md`.
- `ecedddd` — `examples/treasury_query.py`, `examples/sec_query.py`, day-4 regression JSONs (morning gate + strict-canonical-bundle gate + UID0002 spot-check), `results/day4/*.log` run logs capturing retry-event stderr.
- `c445175` — SPRINT_STATUS close note. Isolated per the "SPRINT_STATUS commit-per-day-boundary" discipline so `git log --oneline -- docs/dev/SPRINT_STATUS.md` reads as a clean day-boundary narrative.

**Additional artifacts:**
- `src/teller/agent.py` — `_run_once()` helper extracted, retry loop in `ask()`, `RETRY_ON_TIMEOUT: bool = True` class attribute.
- Unit suite: 51 passed, 1 skipped (39 → 45 → 51 across day-2/3/4; the +6 are ADR-012 retry tests).
- Fresh-clone install verified in `python:3.12-slim` container — `pip install -e .`, `teller --help`, full suite green. Confirms `requires-python = ">=3.10"` is honest and the pyproject dependency declaration is complete.
- ADR log: ADR-012 Accepted; ADR-011 flipped from "Open question" to "Accepted for v0.1.1" with commitment language + re-escalation trigger.

## What Was Attempted and Reverted

**The bundle.** Two intertwined SEC-overlay prompt changes: (a) a new `domain_output_format` block in `prompts/base.j2` (empty default, treasury unaffected) filled in the SEC overlay with four strict-canonical rules — monetary integer-millions, ratios as decimals, per-share decimal dollars, multi-period answers in labeled `YEAR: value, ...` form; (b) a principle backstop appended to the SEC overlay's `early_abstention` block covering segment-intent questions the enumeration didn't cover. Scorer unchanged in this diff (separate punch-list item). Total: ~20 added overlay lines, ~600 added tokens in the rendered recipe.

**What the bundle got right.**
- **SEC0017** (ExxonMobil two-year total assets — the specific fail that motivated the bundle): **PASSED** with `'2024: 453475, 2025: 448980'`. Labeled-list form produced exactly as designed; OfficeQA reward handled the labeled-vs-bare-list equivalence.
- **SEC0013** (MSFT three-year net income): passed with `'2025: 101832, 2024: 88136, 2023: 72361'`. Latest-year-first as specified.
- **Tier-3 held at 7/7** with the new "worldwide consolidated total" principle-backstop wording (Leon's fix to an earlier draft that failed on Apple-US-revenue). No over-abstention observed on any currently-passing tier-1/2 question.

**What the bundle broke.**
- **SEC0005** (NVIDIA net income FY26): `no_answer_file_written` at 593 s (ADR-007 class). Morning run: pass at 333 s with `120067`.
- **SEC0008** (Alphabet cash FY25): content miss `23466` vs expected `30708`. Morning: pass at 211 s with `30708`.
- **SEC0011** (Apple revenue % change FY24→FY25): content miss `0.0202` vs expected `0.0643`. Morning: loose-scored pass.
- **SEC0016** (JPM two-year total assets): `timeout_600s` at 1360 s cumulative — **both attempts timed out**. Morning: pass at 319.7 s. This is the exact customer-visible-opacity event ADR-011's re-escalation trigger was written for; fired pre-launch in regression, not in private beta.

**Revert execution.** Pre-committed threshold: tier-1/2 < 17/18 OR SEC0017 still fails OR tier-3 < 7/7. Actual: 14/18. First criterion fired. Revert was `git checkout -- prompts/base.j2 src/teller/domains/sec_filings/prompt.j2` + `render_recipes.py` regeneration. Working tree restored to morning-gate-passing state. `docs/OUTPUT_CONVENTIONS.md` kept as an additive reference spec the v0.1.1 fix will enforce. Reverted content never committed — per Leon's "reverts are log events, not recommits" discipline.

## Load-Bearing Patterns From Day 4

### Pre-committed revert thresholds are distinct from gate thresholds

A gate threshold answers "does this launch" (treasury ≥13/20, SEC tier-1/2 ≥80 %). A revert threshold answers "does this diff land" and is written BEFORE the diff's measurement run. Revert is typically strictly stricter than gate — the gate measures the whole system's pass/fail; the revert measures whether THIS CHANGE was worth the regression risk it introduced.

Day 4's concrete case: gate is 80 % tier-1/2. Revert threshold was 17/18 = 94.4 %. A softer revert (say "below 15/18 = 83 %") would have shipped the bundle because SEC0017 passed and 14/18 is still above the gate — the diff would have traded a known paper cut for three silent regressions on previously-passing questions, and the launch-copy narrative would have absorbed the trade as a win. The pre-committed 17/18 threshold made execution mechanical at completion, no negotiation.

Principle: when proposing a diff against a locked gate, write the revert threshold before the measurement run. The threshold protects against the specific failure mode of "saw a partial result, rationalized toward keeping the progress." That failure mode is strongest exactly when the diff has a demonstrably correct part (SEC0017) that can be narrated as the headline.

### Context-pressure as a distinct failure class from stochastic variance

Stochastic variance signature (see UID0002 morning): isolated flip, one question regressing in a distribution of passes, stands out as anomaly against its own history. Cheap test: re-run the question in isolation. Variance typically re-passes on re-run.

Context-pressure signature (the bundle): **multiple previously-passing questions regressing in a single run, plus latency inflation on a subset.** Day-4 evidence — SEC0005 at 593 s silent-exit (morning: 333 s pass); SEC0016 at 1360 s both-timed-out (morning: 319.7 s pass). Latency 2-4× baseline is harder to reconcile with stochastic variance than content misses are. The correlation with prompt-length increase (~20 lines / ~600 tokens) is the diagnostic.

Diagnostic rule: if a diff regresses 3+ previously-passing questions in one run AND shows 2-4× latency inflation on 2+ questions vs baseline, suspect context pressure. The fix is not to retry the questions; the fix is to shrink the diff or change its delivery (post-processor, narrower block, progressive rollout).

### Honest variance accounting resists re-narration

The treasury 13→15 breakdown is:
- +1 real retry-on-timeout win (UID0014, SWING-5, two-day-running 600 s timeout → 1173 s pass)
- +1 stochastic variance win (UID0168 passed today without retry; previously day-1 timeout)
- +1 tolerance-edge variance win (UID0052 `2.23` exact vs day-1 `2.26`)
- −1 variance flip (UID0002 ALWAYS_PASS regressed; spot-check confirmed stochastic)
- −1 variance flip (UID0199 SWING-4 F-001 gold bloc)

Net +2 is within ADR-004's ±2-pass MiniMax variance band. Reading day 4 as "retry lifted us to 75 %" overclaims: retry contributed one pass (UID0014). Two passes are stochastic, two flips are stochastic, the net is noise-band.

Leon's exact phrasing for launch copy: *"retry eliminated two tail-latency failures that would have been visibly flaky to users; regression score is within measurement variance of prior runs."* Scar against drift: the honest account names what retry did (+1) and what variance did (net 0). Re-narration typically drops the minuses.

### Two-criterion disagreement resolution

ADR-011 escalation had two triggers. Cold-start qualitative: "third reasoning-opacity scar on day 4 pushes to v0.1 launch-blocker." ADR-012 quantitative: ">2 % stderr retry-event rate escalates ADR-011 to v0.1.1 launch-blocker." Day-4 evidence fired both. They disagreed on shape: cold-start implied v0.1; ADR-012 implied v0.1.1.

Resolution: the criterion with a pre-committed numeric threshold governed (v0.1.1). The qualitative criterion converted to a **watch trigger** — re-escalate to v0.1 hotfix on the first customer-visible both-attempts-timeout event in private beta.

Tentative principle (n=1, day-4 evidence): when two criteria point in the same direction but disagree on magnitude, the pre-committed quantitative one governs, the other becomes a watch. Revisit if v0.1.x surfaces a second case where the criteria diverge. The watch is not a downgrade — SEC0016's both-attempts-timeout in regression was pre-launch evidence, literal trigger not met, but it confirmed the watch is real.

### First-retry evidence for ADR-012

2/45 retries across day-4 regression (UID0014 treasury, SEC0007 tier-1). Both converted to passes at ~1175 s cumulative (1173 s and 1186 s respectively). The design shipped and worked on first live test — 100 % retry-recovery rate on this sample.

Without retry: treasury would be 14/20 (still gate-pass), SEC tier-1+2 would be 16/18 = 88.9 % (still gate-pass). Both gates would have held without ADR-012. **Retry's value is not "kept gates passing"; retry's value is "turned customer-visible tail-latency flakes into silently-recovered latency."** The 4.4 % retry-event rate is a latency tax, not an accuracy defect. That framing matters for how v0.1.1 planning treats the ADR-011 trace persistence work — trace is not about fixing retry, it's about letting customers inspect the rare double-stall (SEC0016-class) without re-running.

## Methodology Additions

Day 2-3 named: cheapest-discriminating-test-first; Arena-artifacts-authoritative; don't-pull-forward-while-blocked; code-behavior-authoritative; ADR-before-code; classification-before-retrieval; false-agreement-as-failure-class; observability-scar; Codex-cadence-criterion; MiniMax-tail-latency-as-launch-blocker.

Day 4 adds:

**Pre-committed revert thresholds are distinct from gate thresholds.** See pattern section above. Short form: gate = does the system pass; revert = did this diff earn its risk. Revert threshold is written before the measurement run; it is the discipline that protects against rationalizing toward a partial-result narrative.

**Context-pressure is a named failure class.** Signature: multi-question regression clustered in one run + 2-4× latency inflation on a subset, correlated with prompt-length increase. Distinct from stochastic variance in both shape (multi-question vs isolated) and evidence (latency vs content).

**"Reverted ≠ failed" framing.** The bundle's SEC0017 success is still useful evidence — the *design* was sound, the *delivery* was wrong. A future session revisiting the strict-canonical fix should not read "reverted in day 4" as "strict canonical doesn't work"; it should read as "this prompt-length delivery mechanism didn't work, try a smaller diff or a post-processor." The revert is a protocol output, not a protocol failure.

## Velocity

Day-4 wall-clock bottleneck was serial regression runs (~186 min total across treasury + SEC + strict-canonical bundle), not agent throughput or Leon review. Unit suite + implementation + ADR drafting completed in ~3 hours of active work; the remaining ~4 hours were regression wall-clock + Leon review interleaved with sleep. Future days with multiple gate-bearing diffs should front-load regression launches to parallelize against review, or accept serial wall-clock as the binding constraint (goose session-race per ADR-007 forbids parallel gate runs on one host).

## Open Items Carried to Day 5

- **SEC0017 remains a paper cut** in v0.1. Known-issued in `docs/PRIVATE_BETA_ONBOARDING.md` issue #1 with v0.1.1 fix commitment (labeled-list answer format).
- **ADR-011 v0.1.1 calendar: 10 days** from v0.1 tag. Non-negotiable. Trace persistence is the first v0.1.1 item; if not ready at day-14-from-tag we ship a smaller trace shape and pick up the remainder in v0.1.2, we do not slip the calendar.
- **SEC0016 both-attempts-timeout is pre-launch evidence, re-escalation trigger armed but not fired.** Watch for first customer-visible both-attempts-timeout in private beta. If it happens, hotfix ADR-011 trace persistence before the second private-beta recipient.
- **Private-beta recipient selection** — Leon's task. Onboarding note is ready.
- **Launch copy discipline** — README / Twitter thread / Show HN must carry the honest-variance breakdown. Any draft that frames retry as "lifted us to 75 %" needs the Leon-phrased correction applied. This is the launch-copy scar against drift.
- **Day-5 scope** per cold-start: private beta out, launch copy finalized, retrospective. No new regression runs unless structural change lands.

## What Not to Redo

- **Do not expand the SEC overlay prompt** without measuring context-pressure hit on previously-passing questions first. The day-4 bundle added ~20 lines and regressed 3 previously-passing questions; any future expansion must demonstrate non-regression in the same band before landing.
- **Do not re-open the SEC0017 list-ordering fix on v0.1.** It is a v0.1.1 commitment, documented in PRIVATE_BETA_ONBOARDING.md known-issue #1. Re-opening it means re-litigating the bundle that was reverted on pre-committed evidence.
- **Do not soften pre-committed revert criteria after seeing a partial result.** The threshold exists because partial-result-sees-tempting-narrative is the moment the threshold is most load-bearing. A revert-threshold written ahead of time is worth more than the revert decision it forces.
- **Do not retry the strict-canonical bundle and principle-backstop as a bundle**, even if a future session can articulate why "this time will be different." The bundle-as-bundle is the reverted artifact; components land separately or not at all. Options if v0.1.x revisits: principle backstop alone (3 lines, held tier-3 at 7/7 without issue), or labeled-list rule alone (5 lines, direct SEC0017 fix), or a post-processing normalization layer outside the prompt entirely (the XBRL traceability concern is solvable). Bundling them was a diagnosis-coarseness cost on day 4 — which of the two caused which fail? — and that cost repeats if re-bundled.
- **Do not re-anchor the treasury gate to 15/20.** 13/20 remains the ADR-004 honest baseline. Day-4's +2 is within variance. Gate thresholds are empirical floors, not high-water marks.
- **Do not generalize the three-commit day-4 pattern into a standing rule.** Day-4 landed three discrete commits per Leon's explicit instruction (ADR-012 core, examples + artifacts, SPRINT_STATUS close). The "SPRINT_STATUS as separate commit per day boundary" discipline is load-bearing for cross-session continuity; preserve it. Other commit-batching decisions are per-day-judgment, not a standing rule.
- **Do not treat ADR-011 v0.1.1 as a v0.2 deferral.** The 10-day calendar is binding. If the first private-beta run produces a both-attempts-timeout, hotfix to v0.1 per re-escalation trigger.

---

*End of retrospective. Day 5 proceeds from this document plus `SPRINT_STATUS.md` plus the three day-4 commits (`39da1d7`, `ecedddd`, `c445175`). Retry-on-timeout and ADR-011 v0.1.1 both load-bearing; launch copy drift and SEC0016-class re-escalation trigger are the two named watches.*
