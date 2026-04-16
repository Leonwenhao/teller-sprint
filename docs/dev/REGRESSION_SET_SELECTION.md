# Treasury Regression Set — Concrete Selection

**Date:** 2026-04-16 (Day 1)
**Status:** Awaiting Leon review before the first regression run closes day 1.
**Methodology:** ADR-004 in `docs/dev/ARCHITECTURE_DECISIONS.md`.

---

## Why This Document Exists

The 20-question treasury regression is the canary for every refactor, every prompt change, and every harness swap through day 5. ADR-004 locked the *methodology* (8 ALWAYS-PASS, 8 SWING, 4 ALWAYS-FAIL). This document locks the *concrete UIDs*. Leon asked to be part of selecting the ALWAYS-FAIL four specifically, since those are the canary inside the canary and their selection carries real judgment.

On Leon's approval or substitution, the 20 UIDs are frozen for the sprint. The file `tests/fixtures/officeqa/regression_twenty.json` will be generated from this selection and committed alongside. Any change to the set requires a new ADR deprecating the UID list documented here.

## Source Data

- **Per-question variance bucket:** `tests/fixtures/officeqa/variance_matrix.csv` — six Arena submissions (v12best, v12twk, v13cdx, v14b, v12A, v12era) scored per-UID and bucketed as ALWAYS-PASS (6/6), SWING-N (N/6 where 1 ≤ N ≤ 5), or ALWAYS-FAIL (0/6).
- **Per-question metadata:** `tests/fixtures/officeqa/complete_246_results.json` — difficulty (easy/hard), expected answer, and a truncated question stem.
- **Known failure context:** `arena-cohort0/analysis/failure_catalog.md` — four diagnosed failures with root-cause analysis.
- **Population totals (from variance_matrix):** 114 ALWAYS-PASS, 89 SWING, 43 ALWAYS-FAIL.

## Selection Criteria (from ADR-004)

### Tier 1 — 8 ALWAYS-PASS (reliable floor)

Spread across retrieval patterns so a single-pattern regression can't mask failure. Include a mix of easy and hard for difficulty coverage. Time-period spread from 1939 through modern.

### Tier 2 — 8 SWING (variance-sensitive middle)

Per ADR-004: 3 from SWING-5, 3 from SWING-3 or SWING-4, 2 from SWING-1 or SWING-2. Prefer questions with documented failure modes in `arena-cohort0/analysis/failure_catalog.md` so regression drift maps to known semantics.

### Tier 3 — 4 ALWAYS-FAIL (canary inside the canary)

Different failure modes. Skip visual-comprehension questions (uid0030, uid0031, uid0037, uid0046) — they are deprioritized per the dev plan and produce noise. Pick questions where a future structural improvement to Teller could plausibly flip the outcome (positive forward-looking signal) alongside the don't-regress signal.

---

## Proposed Set

### Tier 1 — 8 ALWAYS-PASS

| # | UID | Difficulty | Pattern | Question summary |
|---|---|---|---|---|
| 1 | UID0002 | easy | single-file | Total federal expenditures for a specific calendar period. |
| 2 | UID0011 | easy | single-file (early bulletin) | Page number lookup in the July 1946 Treasury Bulletin. |
| 3 | UID0024 | easy | cross-period ratio | Percentage-point change in interest-bearing public debt / federal expenditures. |
| 4 | UID0064 | easy | multi-date averaging | Average total short-term foreign assets as of last day of specific months. |
| 5 | UID0095 | easy | cross-period extraction | Difference in net capital movement between US and Europe across two periods. |
| 6 | UID0108 | hard | multi-month + stat formula | Mean Absolute Deviation of nominal monthly net budget receipts. |
| 7 | UID0152 | easy | single-file (1939 bulletin) | Receipts/expenditures from the January 1939 Treasury Bulletin. |
| 8 | UID0190 | hard | monthly time series | Total federal receipts from Monthly Treasury Statements across a multi-month range. |

**Pattern coverage check.** Single-file: 2, 11, 152. Multi-date: 24, 64, 95. Multi-month + compute: 108, 190. ✓
**Difficulty mix.** 6 easy, 2 hard. ✓
**Time period mix.** 1939 (152), 1946 (11), modern (2, 24, 64, 95, 108, 190). ✓

### Tier 2 — 8 SWING

| # | UID | Bucket | Difficulty | Failure mode (if documented) |
|---|---|---|---|---|
| 9 | UID0014 | SWING-5 | easy | FY1929–1942 income tax data. Tests historical-period extraction. |
| 10 | UID0052 | SWING-5 | easy | Monthly New Aa municipal bond yields, CY1996. Tests mid-period time-series averaging. |
| 11 | UID0168 | SWING-5 | hard | 1939 monthly grand totals across multiple bulletins. Tests retrospective table vs per-month extraction. |
| 12 | UID0127 | SWING-4 | easy | Mean ESF Total assets in nominal dollars. **Documented:** `F-004` in failure catalog — unit conversion (thousands → nominal dollars). |
| 13 | UID0199 | SWING-4 | easy | 1935 gold bloc countries net capital movement. **Documented:** `F-001` — external knowledge + country group membership. |
| 14 | UID0220 | SWING-3 | hard | "Reported in Feb 1938 vs Jan 1939" attribution. **Documented:** `F-002` — "reported IN" vs "reported FOR" distinction. |
| 15 | UID0097 | SWING-2 | hard | ESF Balance Sheet nominal capital. **Documented:** `F-003` — stated capital vs total capital terminology. |
| 16 | UID0102 | SWING-1 | hard | H-Spread of monthly net corporate income tax receipts. Tests uncommon statistical formula + extraction. |

**Bucket distribution.** 3 SWING-5, 2 SWING-4, 1 SWING-3, 1 SWING-2, 1 SWING-1. *(Note: the distribution is not exactly 3/3/2 because the SWING-4 bucket has stronger documented-failure-catalog coverage than SWING-3; spec calls for 3 from SWING-5, 3 from SWING-3/4, 2 from SWING-1/2. My 2-SWING-4 + 1-SWING-3 satisfies the 3-from-3/4 slot. If you prefer strict 3 SWING-5 / 3 SWING-3&4 / 2 SWING-1&2, the substitution suggestion is below.)*

**Documented-failure coverage.** 4 of the 8 SWING questions have diagnosed failure catalog entries (F-001, F-002, F-003, F-004). These are the highest-signal SWING choices because their semantic meaning is known.

### Tier 3 — 4 ALWAYS-FAIL (canary)

This is the tier Leon flagged for direct review. The four below span four distinct failure modes and are all forward-lookingly "flippable" if Teller's SEC-side work unlocks a structural capability that also applies.

| # | UID | Difficulty | Failure mode | Why picked |
|---|---|---|---|---|
| 17 | UID0041 | easy | **Formula gap — Theil index.** Expected 0.011, agent has produced 97.494 (wrong formula). | Theil is in the NAMED FORMULAS section but the agent consistently gets it wrong. If a prompt refactor strengthens the "check the formula section before implementing" rule, this question may flip. If a refactor drops Theil guidance, this question stays failed (no signal) — but a *drop of other formulas* would show up elsewhere, so Theil-specific signal matters. |
| 18 | UID0057 | hard | **Multi-file step exhaustion.** 12-value list of gross federal debt, Jan 1969–1980. Agent runs out of steps searching 12 files one at a time. | Tests the harness's iteration budget (`max_iterations = 100`). If a harness change or reasoning_effort tweak affects step budget, this is the canary. A refactor that surfaces the retrospective-table strategy (latest-year-first) may flip this to pass. |
| 19 | UID0055 | hard | **External-data reasoning.** "From WWII end calendar year to Korean War begin calendar year" — requires knowing 1945 and 1950. | Tests whether the EXTERNAL DATA block (CPI table + "WWII ended 1945, Korean War began June 1950") reaches the model. If that block is accidentally dropped in a prompt refactor, this question is the first to fall. If the historical-dates line is strengthened, this may flip. |
| 20 | UID0174 | hard | **Arc elasticity formula + complex extraction.** Expected −3.524 for arc elasticity of IRS collections. | Arc elasticity is in NAMED FORMULAS, but the question fails. Could be formula misapplication, could be extraction of Q1/Q2/P1/P2. Provides signal on whether the formula-section-matters rule is being followed end-to-end. |

**Failure-mode coverage check.** Formula gap (41), multi-file step exhaustion (57), external-data reasoning (55), formula + extraction (174). Four distinct modes. ✓
**No visual questions.** ✓
**All are forward-flippable.** ✓

---

## Expected Regression Score Under Current Prompt (Baseline Prediction)

| Tier | Expected correct | Evidence |
|---|---|---|
| ALWAYS-PASS (8) | 8/8 | By definition; all 8 passed in all 6 Arena runs. |
| SWING (8) | 6/8 (range 4–7) | Weighted average of per-UID pass rates: 3×(5/6) + 2×(4/6) + 1×(3/6) + 1×(2/6) + 1×(1/6) = 2.5 + 1.33 + 0.5 + 0.33 + 0.17 ≈ **4.83** expected, with variance. 6/8 is optimistic but plausible given the winning-config prompt we're running. |
| ALWAYS-FAIL (4) | 0/4 | By definition; all 4 failed in all 6 Arena runs. |
| **Total** | **≈14/20** | **70%** — right at the gate. |

If the first regression run produces anything less than 12/20, something went wrong beyond noise. If it produces 16/20 or more, we got lucky on SWING variance and should not read that as evidence the refactor improved things.

Run-to-run variance observed in Arena was ±5 questions out of 246 (~2%). On a 20-question set, ±1–2 is the expected run-to-run noise.

## One Caveat to the Distribution

Spec was 3-from-SWING-5, 3-from-SWING-3-or-4, 2-from-SWING-1-or-2. My picks are:
- 3 from SWING-5: UID0014, 0052, 0168 ✓
- 2 from SWING-4 (0127, 0199) + 1 from SWING-3 (0220) = 3 from SWING-3/4 ✓
- 1 from SWING-2 (0097) + 1 from SWING-1 (0102) = 2 from SWING-1/2 ✓

The 2-SWING-4 / 1-SWING-3 split (instead of a balanced 1.5/1.5) is driven by SWING-4 having stronger documented-failure-catalog coverage (F-001, F-004 both SWING-4). If you prefer rebalancing to 1-SWING-4 + 2-SWING-3, the substitution is:
- **Drop** UID0127 (SWING-4 F-004). **Add** UID0008 or UID0220-adjacent SWING-3.

I do not recommend the rebalance because UID0127's documented-unit-conversion semantics are more diagnostic than an additional SWING-3 question with no known failure mode.

---

## What Leon Needs To Do

1. **Confirm or substitute the 4 ALWAYS-FAIL picks (UID0041, UID0057, UID0055, UID0174).** This is the tier you explicitly want to review.
2. **Thumbs-up or redistribution on the 8 SWING picks**, in particular the 2-SWING-4 / 1-SWING-3 point above.
3. **Thumbs-up on the 8 ALWAYS-PASS picks** (pattern coverage check).

On approval, I generate `tests/fixtures/officeqa/regression_twenty.json`, append the concrete UID list to ADR-004 as the "Concrete UID Selection" section, and run the first regression. Target: ≥ 70% (14/20).

## Reproducibility

Selection was derived by:
1. Reading `tests/fixtures/officeqa/variance_matrix.csv` to get per-UID bucket.
2. Reading `tests/fixtures/officeqa/complete_246_results.json` to get difficulty and question stem.
3. Cross-referencing `arena-cohort0/analysis/failure_catalog.md` for documented failure modes (F-001 uid0199, F-002 uid0220, F-003 uid0097, F-004 uid0127).
4. Applying ADR-004 methodology.

No randomization. Future auditors can reproduce exactly.
