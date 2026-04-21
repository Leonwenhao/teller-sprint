# SEC Filings Test Set — Reader's Notes

**Set:** `sec_twenty_five.json` (25 questions, 10 companies, 3 tiers: 11 tier-1 / 7 tier-2 / 7 tier-3)
**Locked:** 2026-04-18 (day 3 of sprint)
**Expected values:** verified against downloaded XBRL tagged facts (see manifest.json)
**Authoritative source for the gate:** `docs/dev/ARCHITECTURE_DECISIONS.md` ADR-002 (reason codes) and `docs/dev/SPRINT_STATUS.md` day-3 scope.

## How each tier scores (scoring contract is in the JSON under `gate.scoring_contract`)

- **Tier 1 — consolidated (11 questions).** Correct iff the agent returns a numeric answer and the official OfficeQA 1% fuzzy reward scores >0 against `expected_answer`. Abstention scores 0.
- **Tier 2 — multi-period (7 questions).** Same scoring as tier-1. Combined tier-1 + tier-2 threshold: ≥15/18 (80%). (The 11/7 split vs the original 10/8 plan comes from reassigning SEC0018 — see the placeholder section below.)
- **Tier 3 — segment-abstain (7 questions).** Correct **iff** `result.abstained == true` AND `result.abstention_reason == "segment_level_dimensional"`. Returning any numeric answer scores 0. Abstaining with a different reason code (`xbrl_unreadable`, `not_tagged`, `xbrl_taxonomy_uncached`, `concept_unknown`, `xbrl_instance_not_found`, `xbrl_period_not_found`) scores 0. Threshold: ≥5/7 (60%).

The wrong-reason-code-scores-zero rule is deliberate. It rules out gaming the tier-3 gate by over-abstention or by failing in the wrong way. The metric is "correctly abstained," not "abstained."

## Important: tier-1 is not a general-accuracy metric

Tier-1 `expected_answer` values are populated by reading the same XBRL tagged consolidated fact that the validator compares the agent's answer against. This is intentional — tier-1 measures two things:

1. **Extraction.** Did the agent pull the right number out of the 10-K text?
2. **Agreement.** Did the XBRL cross-check validator agree with that number?

It does **not** measure whether the filer tagged the correct number, nor whether Teller handles XBRL-unrelated questions well. A 10/10 on tier-1 is evidence that "the agent extracts the same number the filer tagged" — not evidence of general financial-statement comprehension.

**Real accuracy evidence for day-3 lives in:**
- **Tier 2** (multi-period). These questions require the agent to reason across periods and compute deltas/series/ratios from multiple tagged facts. An LLM that just parrots one XBRL value will fail most of these.
- **Tier 3** (segment-abstain). Tests the moat: recognize that a question demands segment-level data and abstain with the right reason rather than fabricating from raw text.

Do not report "tier-1 100%" as a headline accuracy number. Report the tier-2/3 figures, and use tier-1 as a sanity check that the extraction + XBRL agreement path is wired correctly.

## Two-phase ground-truth pattern

At fixture-draft time (2026-04-18), every tier-1/2 `expected_answer` is `null` and `expected_answer_verified` is `false`. The top-level `expected_values_status` is `"pending_verification"`.

Values are populated in a second pass after the day-3 download phase by reading the actual downloaded 10-K's XBRL instance for the tagged consolidated fact matching `concept_hint` at the filing's fiscal-period end. When the pass completes, `expected_values_verified` flips on each question and `expected_values_status` goes to `"verified"`.

This pattern keeps the fixture honest — no fabricated expected values.

## Fiscal-year fallback policy

Target for every question is FY2025. For calendar-year filers (JPM, XOM, GOOGL, AMZN, TSLA, PFE), FY2025 10-Ks are filed Feb–Mar 2026 and should be available as of the fixture lock date. If a specific FY2025 filing is not yet on EDGAR when the downloader runs, that ticker's questions fall back to FY2024 and the `fiscal_period` field is updated per-question. Fallbacks are enumerated in the download-phase summary so day-3 analysis isn't confounded by mixed fiscal years.

## SEC0018 placeholder — resolved

Originally reserved for a concept-family-drift stressor. During the download + populate phase, drift surfaced organically: AAPL and MSFT tag revenue under the ASC 606 concept `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`, while WMT, NVDA, and PFE tag revenue under legacy `us-gaap:Revenues`. The existing roster (SEC0001, SEC0002, SEC0003, SEC0012, SEC0014) already exercises both families across a single test set — no standalone stressor was needed.

SEC0018 was reassigned to **PFE net income FY2025** (tier-1 consolidated), fleshing out PFE coverage beyond the SEC0014 restatement canary. This moved the tier split from 10/8/7 to 11/7/7; combined tier-1+tier-2 is still 18, so the ≥15/18 gate is unchanged. ADR-008 (concept-family normalization) stays Reserved — no filer in this corpus exhibited within-filer year-to-year rename drift that the Agent's keyword-to-concepts map can't already handle.

## Fiscal-year fast-forward for WMT and NVDA

WMT (FY ends Jan) and NVDA (FY ends Jan) had their FY2026 10-Ks already filed by the download date (2026-04-18). The "most-recent-10-K" policy picked up FY2026 for those two instead of the FY2025 target. Rather than force a fallback to the older filing, questions SEC0003, SEC0005, and SEC0012 were updated to target FY2026. This keeps fixture questions against the primary-period fact (not the comparative column) for all 10 tickers — uniform task difficulty across the set.
