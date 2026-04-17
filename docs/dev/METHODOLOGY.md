# Sprint Methodology Notes

Cross-day working principles for Teller v0.1. Add entries when a principle is demonstrated in-session and carries forward. Keep each entry to a rule + a concrete case + the application scope.

---

## Cheapest Discriminating Test First

**Rule.** When multiple hypotheses fit the shape of the evidence, run the cheapest test that discriminates between them before committing to the fix for any single hypothesis. Cheap is measured in minutes to execute, not in how principled the test feels.

**Case (2026-04-17 — ADR-007 diagnosis).** Day-1 regression produced three 0-second `no_answer_file_written` failures in a cluster. The goose log shape — multiple `Recipe execution started` within 15–35 ms, only one `Headless session started` each time — fit a concurrent-session SQLite race hypothesis cleanly. The 4 MB `sessions.db-wal` and 32 KB `sessions.db-shm` files after the run reinforced the story. Writing ADR-007 and implementing `--name <uuid>` + 300 ms settle delay took ~15 minutes.

**The discriminating test was 90 seconds long.** Standalone re-run of ONE failed question (UID0190). If the failure was a concurrent-process race, a single goose process with no neighbor could not reproduce it. The standalone run still failed in 0.4 s. Hypothesis refuted.

The actual root cause — newlines in the `--params` CLI argument — was then found via a 30-second correlation check: count newlines in failed vs passed questions. Perfect segregation (all 3 failures had newlines, all 13 passes did not). Total diagnosis time from refuted hypothesis to correct fix: ~5 minutes.

**Application scope.**

- Day-3 SEC prompt iteration when a refactor regresses: is the drop on a specific UID, or on many UIDs? Check that distribution before blaming the refactor.
- Any "my harness is flaky" hypothesis: re-run once standalone before blaming the harness.
- Any "the model is wrong" hypothesis: check whether a re-run produces the same wrong answer or a different wrong answer. Same = systematic. Different = stochastic, which changes the fix.
- Any "multiple questions are failing together" hypothesis: check whether they share a structural property (length, newlines, specific year ranges, specific formulas). Correlation across inputs is cheaper than inspection of a single input's trace.

**Anti-pattern.** Writing the ADR for a hypothesis before running the discriminating test. The ADR is load-bearing documentation; writing it implies commitment. Commit after the evidence narrows to one hypothesis, not before.

---

## Arena Artifacts Are Authoritative, Not Stated Memory

**Rule.** For any Arena-specific fact — harness, model config, corpus location, per-question results, scoring formula — the repo artifacts in `arena-cohort0/` are ground truth. Stated memory from either party should be verified against disk before it is built upon.

**Case (2026-04-16).** Two cases in two days:
1. BLOCK-01 corpus location. Stated: "in arena-cohort0 under a data directory." Disk: only in the Docker image `ghcr.io/sentient-agi/harbor/officeqa-corpus:latest`.
2. ADR-006 harness. Stated: "openhands-sdk, locked from the Arena work." Disk: `recipe.yaml` and `arena.yaml` both declare `harness_name: goose`; `FINAL_REPORT.md §2.4` explicitly names goose as the 192.046 winner with 87 % cost reduction over openhands-sdk.

**Application scope.**

- When quoting or citing an Arena fact in ADR, scratchpad, or user communication, `grep` the referenced file first and cite `file:line`.
- When the stated fact contradicts the artifact, name the discrepancy concretely (path + line + actual text) rather than silently going with the artifact. The correction matters.
- Saved as a feedback memory in `~/.claude/projects/.../memory/feedback_arena_artifacts_authoritative.md` for cross-session persistence.

---

## When Blocked-Waiting, Don't Pull Forward

**Rule.** Waiting on a review gate is not an invitation to implement day-N+1 work. Each pulled-forward item adds to the reviewer's surface area at the next gate and dilutes review quality. Use waiting windows for scratchpad updates, daily logs, drafting the ADR for the next decision we know is coming, or documenting the day in progress — not new implementation.

**Case (2026-04-16).** During Leon's audit review window, Claude Code considered implementing Corpus + Agent.ask concurrently. Correct call was to stop at the Path-B boundary (scaffold + iron-rules test) and update scratchpads during the wait. Post-approval, implementation started fresh and proceeded cleanly.

**Application scope.**

- Day-2 XBRL library review: do not start the parser implementation while Leon reviews ADR-002.
- Day-3 25-question SEC test construction: do not iterate the prompt while Leon reviews the test set.
- Day-4 private beta recipient list: do not draft the beta message while Leon reviews polish deliverables.

**Exceptions (reversible, pre-approved).** Explicitly flag when something is pulled forward and why it is reversible. PyPI availability check is the canonical example — 5-second curl, zero-cost if the name turns out to be taken, reversible.
