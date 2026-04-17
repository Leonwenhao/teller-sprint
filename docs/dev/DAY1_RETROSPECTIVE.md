# Day 1 Retrospective — Teller v0.1 Sprint

**Dates:** 2026-04-16 afternoon through 2026-04-17 early session (Pacific time).
**Author:** Claude Code (Opus 4.7) with Leon's direct review at each gate.
**Status:** Day 1 closed. Day 2 has not begun.
**Artifact scope:** standalone project record. Read as the authoritative summary of day 1 without needing to open any individual ADR.

## Executive Summary

Day 1 built a fresh `teller/` sibling repository from a cold start through the close of the day-1 regression gate. What shipped: a scaffolded public API (Agent / Corpus / Result / Source / XBRLValidation), a universal + treasury prompt split driven by Jinja inheritance, the full 697-file Treasury Bulletin corpus migrated in-repo as test fixtures at 379 MB on disk (~95 MB git-packed), a 20-question regression harness wrapping goose via subprocess, seven architecture decision records, a cross-day methodology note, and three clean git commits. The Arena-winning behavior is now measurably reproducible from a fresh clone via `pip install -e .` plus `pytest tests/` plus `python scripts/regression.py --set twenty`. Nothing below `teller/` existed at day-1 start.

The empirical day-1 regression baseline is **13/20 = 65.0 %**. The number sits below the 68-72 % expected-variance band Leon named in advance, but it is the honest result of the pipeline as built rather than a flaky number hiding real behavior. Three of seven failures were initially masked by a goose CLI bug in which newlines in the `--params` instruction argument silently terminate parsing; that bug was caught, diagnosed, and fixed as ADR-007. The rerun confirmed three genuine residual failure modes: stochastic variance on an ALWAYS-PASS question (UID0190), a 1.34 % tolerance-edge miss (UID0052), and a 600 s timeout miss (UID0168). Two ALWAYS-FAIL questions flipped to passes unexpectedly (Theil at UID0041 and WWII/Korea at UID0055), each of which was 0/6 in Arena.

One-sentence takeaway: **day 1 proved that the v0.1 abstraction can reproduce Arena-winning behavior end-to-end, exposed three residual behavioral edges that are now documented and traceable, and established an honest regression baseline against which every subsequent refactor will be measured.**

## What Shipped

Three commits landed on `main`: `e50aac8` (initial scaffold with migrated Arena assets and the prompt split), `7a8c088` (day-1 close with ADR-007 newline fix and the honest 13/20 baseline), and `7c47255` (this retrospective). Net change is roughly 1,300 lines of code and documentation plus the 697 Treasury Bulletin text files that account for most of the repository size.

The repository uses the standard src layout. The public surface lives at `src/teller/{agent.py, corpus.py, result.py, config.py}`; `from teller import Agent, Corpus, Result` resolves with locked v0.1 signatures. The prompt architecture uses Jinja inheritance: `prompts/base.j2` holds the universal content (three iron rules, generic workflow, twenty named statistical formulas, universal table-reading principle, output format, web-search fallback); `src/teller/domains/treasury/prompt.j2` extends it with treasury-specific unit-conversion rules, fiscal-year conventions, domain traps, multi-file strategy, and CPI reference data. The 84-line Arena-winning prompt is preserved verbatim at `prompts/_source_goose_prompt.j2` with a header comment disallowing modification. The Goose recipe lives at `recipes/treasury.yaml` (renamed from the Arena-era `recipe.yaml` to accommodate day-2's `recipes/sec_filings.yaml`).

Seven ADRs are locked. ADR-001 canonicalizes the three iron rules as semantic anchor phrases. ADR-002 is reserved for day-2's XBRL library evaluation. ADR-003 locks `reasoning_effort: medium`. ADR-004 locks the 20-question regression set with the day-1 baseline and per-UID forward-looking notes. ADR-005 records the prompt-split validation as a dual gate (regression hard, byte-diff advisory with Leon's signed annotation). ADR-006 corrects the Revised Development Plan's "openhands-sdk" harness claim to goose. ADR-007 records the newline-in-`--params` fix with both the wrong initial hypothesis and the correct diagnosis.

The iron-rules test runs 6/6 green — three anchor assertions against base and three against the treasury overlay. The PyPI name `teller-agent` was verified available and is locked in `pyproject.toml`; `teller` was confirmed squatted. Git config is repo-local (`leon@dolores.research`, `Leon Liu`); no global git config exists on this machine and none was created.

## Regression Baseline — The Honest 13/20

| # | UID | Tier | Result | Latency | Note |
|---|---|---|---|---|---|
| 1 | UID0002 | ALWAYS-PASS | ✓ `507.0` | 150 s | VA FY1934 single-file lookup |
| 2 | UID0011 | ALWAYS-PASS | ✓ `42` | 150 s | page-number lookup, Jul 1946 |
| 3 | UID0024 | ALWAYS-PASS | ✓ `0.13` | 16 s | cross-period ratio |
| 4 | UID0064 | ALWAYS-PASS | ✓ `113864.0` | 55 s | multi-date averaging |
| 5 | UID0095 | ALWAYS-PASS | ✓ `0.154` | 38 s | cross-period difference |
| 6 | UID0108 | ALWAYS-PASS | ✓ `1400.306` | 42 s | MAD statistical formula |
| 7 | UID0152 | ALWAYS-PASS | ✓ `451` | 77 s | Jan 1939 bulletin |
| 8 | UID0190 | ALWAYS-PASS | ✗ `-54` vs `-11` | 30 s | **variance-sensitive** |
| 9 | UID0014 | SWING-5 | ✗ timeout_600s | 600 s | hard regression |
| 10 | UID0052 | SWING-5 | ✗ `2.26` vs `2.23 %` | 87 s | **tolerance-edge (1.34 % off)** |
| 11 | UID0168 | SWING-5 | ✗ timeout_600s | 600 s | **timeout-budget** |
| 12 | UID0127 | SWING-4 | ✗ timeout_600s | 600 s | F-004 ESF unit conversion |
| 13 | UID0199 | SWING-4 | ✓ `0.479` | 138 s | F-001 gold bloc |
| 14 | UID0220 | SWING-3 | ✓ `27.0` | 179 s | F-002 "reported IN" |
| 15 | UID0097 | SWING-2 | ✓ `[8.124, 12.852]` | 205 s | F-003 capital vs total |
| 16 | UID0102 | SWING-1 | ✓ `57.52` vs `57.50` | 438 s | hardest SWING, H-Spread |
| 17 | UID0041 | ALWAYS-FAIL | ✓ `0.011` | 58 s | **unexpected win — Theil** |
| 18 | UID0057 | ALWAYS-FAIL | ✗ timeout_600s | 600 s | expected step-exhaustion |
| 19 | UID0055 | ALWAYS-FAIL | ✓ `0.0` | 39 s | **unexpected win — WWII/Korea** |
| 20 | UID0174 | ALWAYS-FAIL | ✗ `-3.147` vs `-3.524` | 136 s | expected arc-elasticity miss |

Three residual failures have forward-looking interpretive notes. **UID0190 is variance-sensitive**: it is ALWAYS-PASS 6/6 in Arena and returned the correct `-11` on a day-1 standalone smoke test, yet returned `-54` ninety minutes later on the same question with the same code. MiniMax M2.5 is stochastic and this question lives at the reliable-but-not-deterministic end of its capability envelope. A single-run miss on UID0190 is not by itself a regression signal; only a sustained miss across consecutive runs is diagnostic. **UID0052 is tolerance-edge**: extracted `2.26` versus expected `2.23 %` is 1.34 % off against a 1 % tolerance. The question lives on the scoring boundary; chasing it with prompt tweaks is a warning sign that we are optimizing against the scorer rather than the domain. **UID0168 is timeout-budget**: a hard multi-month extraction across many 1939 bulletins does not fit the 600 s hard timeout. Either the retrospective-table strategy needs to be more efficient, or this question deserves a longer budget; the choice is deferred.

Two unexpected ALWAYS-FAIL wins — UID0041 (Theil, 0/6 in Arena) and UID0055 (WWII/Korea, 0/6 in Arena) — are the day-1 net-positive signal. The Arena "ALWAYS-FAIL" label was relative to six configuration snapshots, not a claim of structural impossibility. Two flips from a 43-question tier where Arena produced zero correct suggests the clean v0.1 abstraction plus goose's local auto-compaction may be doing something Arena's cloud evaluation did not. This is not a new baseline — future runs should not assume these continue to pass, and a flip back to fail is not a regression.

The day-2 regression gate is re-anchored to the empirical baseline: pass ≥ 13/20, warn at 12/20, **stop below 12/20**. The pre-run 14/20 projection was an estimate made before any Teller run had measured the pipeline and has been explicitly retired. `SPRINT_STATUS.md` carries an instruction against reverting to 14/20 under schedule pressure.

## Decisions Made and Why

**Corpus location (BLOCK-01).** Leon's stated position was that parsed Treasury Bulletin TXT files lived under a `data/` directory in `arena-cohort0/`; disk reality was that they lived only in the Sentient Docker image `ghcr.io/sentient-agi/harbor/officeqa-corpus:latest`. Four options were offered: commit the full 697 files, commit a minimal subset, provide a pull-at-runtime script, or commit a stratified ~80-file middle path. Leon chose the first. Rationale: a self-contained regression is worth the working-tree size cost (379 MB on disk, ~95 MB git-packed), and eliminating a dependency on Sentient's container registry preserves reproducibility beyond the life of the Arena program. Rejected most forcefully: the runtime pull, which would have made every fresh-clone contributor's first `pytest tests/` require Docker.

**Harness correction (ADR-006).** The Revised Development Plan stated "the harness is openhands-sdk, locked from the Arena work," which contradicted `recipe.yaml`, `arena.yaml`, and `FINAL_REPORT.md §2.4`, all of which named goose as the winning harness with 87 % cost reduction over openhands-sdk. Leon confirmed his earlier draft had conflated two separate comparisons (openhands-sdk vs opencode, which openhands-sdk won; and openhands-sdk vs goose, which goose won). ADR-006 locks goose with the citation chain in place and corrects the dev plan inline. Second case in two days of Leon's stated Arena-specific memory contradicting disk.

**Prompt-split validation gate (ADR-005).** The Revised Development Plan originally proposed byte-exact diff against the 84-line Arena-winning prompt as the split's pass/fail gate. Claude Code pushed back with Path B: regression score as the hard gate (behavior preservation is what we actually care about), byte-diff as advisory with Leon's signed annotation. Leon approved with the nuance that the advisory diff must still run and be annotated before the split is declared passed. First-run diff produced 95.4 % similarity with three replaced lines, all domain-neutral rephrasings in the universal base; treasury-specific wording preserved verbatim in the overlay. Leon signed.

**Reasoning effort (ADR-003).** Locked at `medium` because Arena's scoring formula weighted cost 20× latency, medium hit the accuracy ceiling at substantially lower cost than high, and low hung at least one Arena test.

**Regression set stratification (ADR-004).** Eight ALWAYS-PASS across retrieval patterns, eight SWING stratified across SWING-1 through SWING-5 with bias toward `failure_catalog.md` entries (F-001 through F-004), four ALWAYS-FAIL with distinct failure modes. For the fourth ALWAYS-FAIL slot the canonical termination-signal canary candidate was UID0021 (documented self-sabotage smoking gun in `session10_journey.md`), but UID0021 is SWING-4 because the v12A overwrite-gate rule moved it out of ALWAYS-FAIL. No ALWAYS-FAIL question carries a clean termination-signal diagnostic, so Leon's fallback applied: retain UID0055 (external-data canary).

**ADR-007 newline fix.** The day-1 regression surfaced three 0-second `no_answer_file_written` failures. The first diagnostic hypothesis was a concurrent-session SQLite race; the fix under that hypothesis was `--name <uuid>` plus a 300 ms settle delay. A 90-second standalone smoke test refuted the race (the failure reproduced with no neighbor goose process). A 30-second correlation check on newline count per question produced perfect segregation: all three failures had newlines in the question text, all thirteen passes had none. Root cause: goose's `--params` CLI parser treats newlines as argument terminators. Fix: collapse whitespace runs to single spaces in `Agent.ask` before passing to `--params`. The `--name` and settle-delay mitigations were retained as defense-in-depth since both cost essentially nothing.

## Methodology Principles Validated

The three cross-day principles recorded in `METHODOLOGY.md` each had a concrete day-1 case.

**Cheapest discriminating test first.** The ADR-007 diagnostic arc. The goose log shape — multiple `Recipe execution started` within 15-35 ms, only one `Headless session started` per log — fit a concurrent SQLite race cleanly; the 4 MB `sessions.db-wal` reinforced it. Writing the first ADR-007 draft and implementing the fix under that hypothesis took 15 minutes. The discriminating test was 90 seconds: one standalone rerun. The race hypothesis was refuted inside a single interactive loop. The correlation check that found the real root cause took 30 seconds. Lesson: when multiple hypotheses fit the evidence shape, the cheapest discriminating observation should come before any fix is committed, not after.

**Arena artifacts are authoritative, not stated memory.** Leon's memory was wrong twice — corpus location (BLOCK-01) and harness identity (ADR-006) — and both errors were caught at gates before any implementation was built on them. In both cases the correct answer was on disk; a one-minute grep would have found it. Rule: grep before quoting, and flag the discrepancy with concrete file-and-line citations rather than silently going with the artifact. Saved as a feedback memory for cross-session persistence.

**Don't pull forward while blocked-waiting.** Every pulled-forward item piles onto the next review gate and dilutes review quality. During the audit-review window Claude Code correctly stopped at the Path-B boundary (API scaffold plus iron-rules test) rather than implementing Corpus and Agent.ask. The PyPI availability check was accepted as a clean pull-forward only because it was a 5-second curl whose outcome was trivially reversible.

## What Leon Got Wrong, What Claude Code Got Wrong

Leon's stated memory was wrong twice: corpus location (BLOCK-01) and harness identity (ADR-006). Both caught at gates rather than propagating. The corpus-location error would have cost hours if the fixture directory had been populated from an imagined path. The harness error would have produced a quiet behavioral regression because openhands-sdk averages lower accuracy than goose at substantially higher cost.

Claude Code's first diagnostic hypothesis on the three 0-second failures was wrong. The SQLite-race story was cleanly consistent with the log shape and the WAL file size; Claude Code wrote the first ADR-007 draft and implemented the `--name` plus settle-delay fix under that hypothesis before running the discriminating test. The actual root cause — newlines in `--params` — was only visible from a correlation check across inputs, not from deeper log analysis. Lesson: run the cheapest discriminating observation before writing the ADR, not after.

None of these are sprint failures. They are the sprint working correctly because every error was caught at a review or gate point rather than shipping. Naming them makes the pattern legible: Leon will misremember Arena specifics, Claude Code will occasionally commit to the wrong hypothesis when the evidence shape is compelling, and the check for both is the same — verify before building.

## Timing and Velocity Observations

Day 1 was budgeted as one calendar day of the five-day sprint. Actual Claude Code wall-clock work was roughly two hours across a single long interactive session from cold-start read through close commit. Including Leon's review turnarounds (audit, regression set, stop-and-escalate, close-out), elapsed time from Leon's side was approximately five hours.

Opus 4.7 throughput plus disciplined scratchpad hygiene plus clean cold-start is running approximately three to four times faster than the Revised Development Plan's budget assumed. The bottleneck has shifted from agent throughput to Leon's review bandwidth and external launch-window timing. This matters for day-2-through-5 planning: remaining days have material slack that can be used for more thorough testing, additional Codex cross-checks, or tighter polish — but only if the pull-forward discipline holds. The valuable use of slack is depth rather than breadth: better XBRL parser test coverage on day 2, more prompt iterations on day 3, more error-message polish on day 4.

## What Day 2 Inherits

Every `BLOCKED.md` entry is closed. The treasury corpus is in `tests/fixtures/treasury_bulletins/`. The harness is goose v1.31.0 installed via `brew install block-goose-cli` with `OPENROUTER_API_KEY` in the environment. The regression set is locked at 20 UIDs in `tests/fixtures/officeqa/regression_twenty.json` and ADR-004; gate thresholds are pass ≥ 13/20, warn at 12/20, stop below 12/20. `Agent.ask` carries a ~300 ms per-call overhead from the ADR-007 defense-in-depth settle delay.

Bootstrap order for the next session: `SPRINT_STATUS.md` → `ARCHITECTURE_DECISIONS.md` → `METHODOLOGY.md` → `BLOCKED.md` → the two Revised_TELLER docs in `arena-cohort0/` → the current `day_N_log.md`. Before any work the session confirms to Leon verbally which day we are on, what the last passing regression was, and what the next task is.

First day-2 artifact is ADR-002, the XBRL library choice between `arelle` and `python-xbrl`, with Codex as second opinion on the load-bearing tradeoff: API shape, maintenance status, segment-level fact extraction, install weight. Implementation sequence after the decision is locked: XBRL parser module, SEC EDGAR downloader (polite rate-limiting, `leon@dolores.research` user-agent), SEC domain overlay, Click CLI exposing `ask` / `download-sec` / `inspect`. Day-2 gate is the Apple smoke test: fresh-clone `pip install -e .` plus `teller download-sec AAPL --latest 10-K` plus `teller ask --corpus ./sec_data "what was Apple's revenue last fiscal year"` returning the correct answer with a page-level citation and a successful XBRL cross-check in under 30 seconds. Treasury regression must still pass ≥ 13/20 after day-2 work lands.

## Open Questions and Deferred Items

**UID0168 timeout budget.** The 600 s hard timeout is insufficient for the hardest multi-month extractions where the agent legitimately needs to traverse many bulletin files. Extending to 900 s, or introducing per-tier timeouts, is a future-ADR conversation. Changing the timeout changes the regression's cost and latency characteristics, so a re-baseline would follow.

**UID0190 stochastic variance.** "ALWAYS-PASS 6/6" in the variance matrix was derived from six Arena submissions using six different configurations, not six runs of the same config. A stricter definition (e.g., passes in five consecutive identical-config runs) would filter stochastic-variance questions from the reliable floor tier. Future-ADR conversation; do not rebaseline UID0190 without explicit approval.

**Upstream goose CLI bug.** The newline-in-`--params` issue is a goose defect Teller mitigates at the `Agent.ask` layer but does not fix upstream. Day-2 follow-up is to file a GitHub issue on `block/goose` with the two log excerpts (`20260416_155918.log`, `20260416_160918.log`) and a minimal reproducer. An upstream fix would eventually let us remove the whitespace normalization, but the workaround is stable and not on any sprint critical path.

---

*End of retrospective. Day 2 proceeds from the bootstrap order above, beginning with ADR-002 and Codex consultation on the XBRL library.*
