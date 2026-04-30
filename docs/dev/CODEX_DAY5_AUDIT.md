# Codex Day-5 Audit — Teller v0.1

## Top line

**Verdict: ship v0.1 to the first external user as a private-beta round-trip now; pause public/PyPI distribution until the public copy is made strictly code-true.** The core sprint outcome matches the strategic direction: SEC-first, XBRL-moated, abstention-aware, model-pluggable, with Treasury retained as the regression canary. The launch surface is close but not yet stranger-safe: README and docs still overclaim citation/source behavior, one README sentence promises XBRL-disagreement abstention that the code does not implement, OUTPUT_CONVENTIONS says a reverted prompt block is enforced, and PyPI metadata points to a private repo. These are distribution blockers, not reasons to reopen SEC0017 or rerun regressions.

## 1. Strategy-execution alignment — IMPORTANT

**Finding.** The shipped product mostly matches the narrowed thesis, but v0.1 under-delivers on two parts of the stated analyst promise: page-level citations and abstention-on-XBRL-disagreement.

**Evidence.** Strategy says Teller extracts SEC filing figures with "page-level citations and XBRL cross-validation" and that citation/cross-validation is the product, not a feature (`/Users/leonliu/Desktop/arena-cohort0/Revised_TELLER_STRATEGY.md:11`, `:19`, `:21`). The implementation returns a `Result` with a `sources` field, but `Agent.ask` constructs successful Results with `answer`, `confidence`, `xbrl_validation`, and `latency_ms` only (`src/teller/agent.py:307-314`); `Result.sources` defaults to an empty list (`src/teller/result.py:63`). README still advertises "`sources` — page-level citations" (`README.md:73`). Similarly, strategy says that when model output and XBRL disagree, Teller abstains and shows both (`Revised_TELLER_STRATEGY.md:35`). Code only returns `xbrl_validation.agreed=False`; it does not set `abstained=True` on disagreement (`src/teller/agent.py:307-314`; `src/teller/validation/xbrl.py:389-408`). README itself later describes the implemented behavior correctly: disagreement surfaces `agreed=False` and both values (`README.md:51`).

**Recommendation.** Do not change code on day 5. Make launch copy match v0.1 behavior: "surfaces disagreement" rather than "abstains" for XBRL disagreement, and "citation-oriented prompt / sources field reserved" rather than "page-level citations" unless sources are actually populated before public release.

**Finding.** The sprint intentionally over-delivered on Treasury relative to the revised single-domain SEC thesis, but it is correctly framed as regression canary plus second domain, not ICP expansion.

**Evidence.** Strategy says v0.1 is "a single-domain tool" for SEC filings (`Revised_TELLER_STRATEGY.md:11`) and auditors/journalists/etc. are out of scope (`:51`). README says v0.1 does SEC filings and Treasury Bulletins (`README.md:9`), while sprint docs preserve Treasury as the regression canary (`SPRINT_STATUS.md:80-87`; ADR-004 at `docs/dev/ARCHITECTURE_DECISIONS.md:277-410`). No public copy positions Treasury as a new ICP.

**Recommendation.** Accept Treasury as inherited benchmark/domain surface. Do not let Treasury become launch narrative except as "the Arena-derived regression corpus."

## 2. Honest-copy discipline in README — IMPORTANT

**Finding.** README holds the day-4 scars on latency, retry, 15/20, and SEC0017, but one lead sentence drifts from code truth.

**Evidence.** The README does not use sub-30-second latency; it states 60-120 s typical and ~180 s worst observed (`README.md:77-86`), matching SPRINT_STATUS's retired 30 s narrative (`docs/dev/SPRINT_STATUS.md:167-186`). It reports Treasury 13/20, explicitly says 15/20 is variance-band, and rejects high-water-mark framing (`README.md:88-93`), matching Day 4's honest variance account (`docs/dev/DAY4_RETROSPECTIVE.md:61-72`, `:119`). It names SEC0017/list-order as a known v0.1 limitation with v0.1.1 fix (`README.md:95-101`), matching Day 4's "do not reopen" scar (`docs/dev/DAY4_RETROSPECTIVE.md:106-118`). It frames retry as a latency tax, not an accuracy lift (`README.md:93`), matching ADR-012's consequence framing (`docs/dev/ARCHITECTURE_DECISIONS.md:796-803`).

**Drift.** README line 7 says: "When the two disagree, Teller abstains and shows both." Code and README line 51 say disagreement is surfaced via `agreed=False`, not `Result.abstained=True`.

**Recommendation.** Replace line 7 before public distribution. Suggested: "When the two disagree, Teller surfaces both values instead of hiding the conflict."

## 3. Launch-copy risk surface — SHIP-BLOCKER FOR PUBLIC, NOT PRIVATE BETA

**Finding.** `docs/OUTPUT_CONVENTIONS.md` claims enforcement that was explicitly reverted.

**Evidence.** OUTPUT_CONVENTIONS says "The SEC domain prompt overlay enforces these" (`docs/OUTPUT_CONVENTIONS.md:3-5`) and "These conventions are enforced in `src/teller/domains/sec_filings/prompt.j2` (`domain_output_format` block)" (`:18-19`). But Day 4 says the strict-canonical bundle was reverted and only the docs spec stayed (`docs/dev/DAY4_RETROSPECTIVE.md:26-42`; `SPRINT_STATUS.md:146-160`). Current prompt/recipe still say "Write ONLY the bare number... No labels" (`prompts/base.j2:47`; `recipes/sec_filings.yaml:48`) and there is no `domain_output_format` block in the SEC overlay.

**Recommendation.** Public docs must say "reference spec for v0.1.1; not enforced in v0.1." Keeping the current text would let a critic disprove the claim with one grep.

**Finding.** Private-beta onboarding turns observed retry recovery into a guarantee.

**Evidence.** Onboarding says about 5% of queries "trigger an automatic retry, and come back correct" and "The answer is still correct when it returns" (`docs/PRIVATE_BETA_ONBOARDING.md:51`). Day-4 evidence is only 2/45 retries, both recovered (`SPRINT_STATUS.md:11`; `DAY4_RETROSPECTIVE.md:82-86`). ADR-012 explicitly projects residual failure under an independence assumption, not a correctness guarantee (`docs/dev/ARCHITECTURE_DECISIONS.md:728-730`, `:800-801`).

**Recommendation.** Change to "in day-4 regression both observed retries recovered; inspect the returned answer and XBRL signal normally."

**Finding.** PyPI metadata would create a dead public path if published while the repo stays private.

**Evidence.** `pyproject.toml` points Homepage/Repository/Issues to `https://github.com/Leonwenhao/teller-sprint` (`pyproject.toml:42-45`). User context says that mirror is private. README install path says `pip install teller-agent` (`README.md:23`).

**Recommendation.** Do not publish PyPI with private repo URLs. Either flip the repo public first or send a private invite and install instructions that do not rely on PyPI.

## 4. ADR commitments — IMPORTANT

**Finding.** ADR-011's calendar is softened inside the ADR file relative to day-4 and public copy.

**Evidence.** Day-4 retrospective says ADR-011 resolved for v0.1.1 with a "10-day calendar commitment" (`docs/dev/DAY4_RETROSPECTIVE.md:9`) and "10-day calendar is binding" (`:121`). README says v0.1.1 is "<=10 days from v0.1 tag" (`README.md:124-126`). CHANGELOG says SEC0017 fix is "<=10 days from v0.1 tag" (`CHANGELOG.md:31-33`). Private beta says trace target is 10 days (`docs/PRIVATE_BETA_ONBOARDING.md:53`). But ADR-011 status and commitment language say "no later than two weeks after the v0.1 tag" (`docs/dev/ARCHITECTURE_DECISIONS.md:666-689`).

**Recommendation.** Treat this as a documentation contradiction, not a product decision. Source of truth for launch should be the stricter public commitment: 10 days. The audit should push Claude to fix ADR-011 before public release, but not in this read-only pass.

**Finding.** ADR-012 and ADR-004 remain operative.

**Evidence.** ADR-012's retry trigger is timeout-only and excludes `no_answer_file_written`, `empty_answer_file`, `ABSTAIN`, and XBRL disagreement (`docs/dev/ARCHITECTURE_DECISIONS.md:711-727`); `Agent.ask` matches that shape (`src/teller/agent.py:168-203`, `:266-271`, `:316-325`). ADR-004's 13/20 pass baseline and no-reanchor instruction are preserved (`docs/dev/ARCHITECTURE_DECISIONS.md:402-410`; `SPRINT_STATUS.md:66-78`; README `:90`).

**Recommendation.** No ADR contradiction in code. The only ADR-blocking issue is the ADR-011 calendar mismatch.

## 5. Day-4 load-bearing patterns — IMPORTANT

**Finding.** Day-5 public docs partially violate the "reverted = log event, not shipped behavior" pattern by documenting reverted output enforcement as current behavior.

**Evidence.** Day 4 explicitly says the strict-canonical bundle was reverted, content not committed, and OUTPUT_CONVENTIONS stayed only as an additive reference spec (`docs/dev/DAY4_RETROSPECTIVE.md:41`, `:98`, `:113-118`). OUTPUT_CONVENTIONS claims current enforcement (`docs/OUTPUT_CONVENTIONS.md:18-19`).

**Recommendation.** Add to DAY5_RETROSPECTIVE: "reference specs must be labeled as future specs when enforcement is reverted." This is the same root cause as launch-copy drift: a correct future design got narrated as present behavior.

**Finding.** Other patterns still hold.

**Evidence.** Pre-committed revert threshold remains separate from gate threshold (`DAY4_RETROSPECTIVE.md:43-51`). Context-pressure is named and not reopened (`:53-60`, `:115-118`). Arena artifacts are authoritative via the 174/176 reconciliation note (`docs/research/final_report.md:7`) and README cites the public 71.5% number (`README.md:130-134`). Reverts were not recommitted (`SPRINT_STATUS.md:5-6`).

**Recommendation.** Preserve the freeze. No regression reruns unless copy fixes become structural code/prompt changes.

## 6. Distribution-shape recommendation — SHIP PRIVATE, PAUSE PUBLIC/PYPI

**Recommendation.** Sequence: tag an internal/private v0.1.0 release candidate, invite exactly one first-wave user to the private repo, send `docs/PRIVATE_BETA_ONBOARDING.md` after softening the retry guarantee, capture the round-trip and stderr log, then choose public/PyPI after one real install path succeeds. Do not publish PyPI while the repo is private. Do not public-launch until README/OUTPUT_CONVENTIONS/ADR-011 copy is reconciled.

**Argument.** Strategy wants open-source distribution and build-in-public (`Revised_TELLER_STRATEGY.md:63-71`, `:93-97`), but the dev plan also makes private beta the catastrophic-feedback gate before launch (`Revised_TELLER_DEVELOPMENT_PLAN.md:98-100`, `:124`). Current state has not satisfied the user-stated v0.1 gate of at least one external user round-trip. Public PyPI now creates a broken trust path: package metadata points to a private repo (`pyproject.toml:42-45`), README speaks to strangers (`README.md:13-31`), and issue links would 404/deny. A private invite preserves momentum, exercises the actual ICP install path, and keeps copy drift from becoming public debt.

## Drift catalog

**README line 7.** Current: "When the two disagree, Teller abstains and shows both." Source of truth: code returns `xbrl_validation.agreed=False` without `abstained=True` (`src/teller/agent.py:307-314`); README line 51 already says this. Replacement: "When the two disagree, Teller surfaces both values instead of hiding the conflict."

**README line 73 / `Result.sources`.** Current: "`sources` — page-level citations to source documents." Source of truth: `sources` defaults empty and is never populated on success (`src/teller/result.py:63`; `src/teller/agent.py:307-314`). Replacement: "`sources` — reserved citation field; v0.1 answer text is numeric and XBRL validation carries the auditable tagged fact for supported SEC metrics."

**OUTPUT_CONVENTIONS lines 3-5 and 18-19.** Current: "SEC domain prompt overlay enforces these" and "`domain_output_format` block." Source of truth: strict-canonical bundle reverted (`DAY4_RETROSPECTIVE.md:26-42`) and current recipe says bare number/no labels (`recipes/sec_filings.yaml:48`). Replacement: "Reference spec for v0.1.1; v0.1 does not enforce this in the SEC prompt."

**PRIVATE_BETA_ONBOARDING line 51.** Current: "come back correct" / "The answer is still correct when it returns." Source of truth: observed 2/2 recovery, not a guarantee (`SPRINT_STATUS.md:11`; ADR-012 projection at `ARCHITECTURE_DECISIONS.md:800-801`). Replacement: "In day-4 regression both observed retries recovered; treat the returned answer normally and inspect XBRL/citations before relying on it."

**ADR-011 lines 668 and 687.** Current: "two weeks." Source of truth: day-4 and public docs say 10 days (`DAY4_RETROSPECTIVE.md:107`, `README.md:124-126`, `CHANGELOG.md:31-33`). Replacement: "no later than 10 calendar days after the v0.1 tag."

**pyproject URLs.** Current: public package URLs point at private mirror (`pyproject.toml:42-45`). Source of truth: PyPI + private repo is a dead pointer for outsiders. Replacement: keep unpublished until public repo exists, or set URLs only when visibility is public.

## What Claude Code missed for DAY5_RETROSPECTIVE.md

**Present-vs-future spec labeling is now a scar.** OUTPUT_CONVENTIONS was kept as a future reference after a revert, but day-5 copy stated it as current enforcement. Rule: after a reverted behavior, docs may preserve the design only if every reference is explicitly future-tense.

**Public API docstrings can overclaim even when README is fixed.** `Source` says every Result carries citations (`src/teller/result.py:10-15`) and `to_dataframe()` is still stubbed (`src/teller/result.py:76-82`) despite the original public API plan including it (`Revised_TELLER_DEVELOPMENT_PLAN.md:24`). These are not launch blockers if unadvertised, but they are debt in the public surface.

**ADR calendar commitments need a single source of truth.** Day-4, README, CHANGELOG, and onboarding converged on 10 days; ADR-011 retained two weeks. The stricter public promise should govern, but the mismatch itself is the failure mode.

**Distribution shape is a product decision, not release plumbing.** PyPI, GitHub visibility, README stranger-safety, and external-user round-trip are coupled. Treating them separately creates dead links and false launch confidence.
