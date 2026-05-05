# Changelog

All notable changes to Teller are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Local JSON trace persistence for every `Agent.ask()` call, with `trace_id` and `trace_path` on `Result`.
- `teller doctor` runtime diagnostics for Python, package data, goose, OpenRouter key, and trace directory.
- Conservative output normalization for labeled multi-period answers, rates, and SEC monetary values.
- `Result.to_dataframe()` with optional `pandas` support via `teller-agent[dataframe]`.
- `scripts/release_check.py` for non-live GA release checks.

### Changed
- Suppressed normal user-facing Arelle diagnostic noise while preserving diagnostics for debug/trace inspection.
- Updated package metadata to SPDX license syntax and added the `dataframe` optional extra.

### Fixed
- Provider stream/decode failures are now distinguishable from generic `no_answer_file_written` when stderr contains provider signatures.

## [0.1.0] — 2026-04-22

### Added
- Two domains: **SEC filings** (10-K / 10-Q with XBRL cross-validation) and **U.S. Treasury Bulletins** (1939–present).
- XBRL cross-check for SEC queries: compares the model-extracted figure against the filing's XBRL-tagged value; surfaces agreement/disagreement or abstains on questions not answerable from tagged facts.
- Public API: `Agent`, `Corpus`, `Result` (with `XBRLValidation` and `Source` sub-structures).
- CLI: `teller ask`, `teller download-sec`, `teller inspect`, `teller --help`.
- Goose-backed execution with `reasoning_effort="medium"` locked per ADR-003.
- Single same-model retry on subprocess timeout per ADR-012; cumulative `latency_ms` across both attempts; one stderr line on retry.
- Behavioral abstention on questions not answerable from available evidence; named `abstention_reason`.
- Examples: `examples/treasury_query.py`, `examples/sec_query.py`.
- Private-beta onboarding guide: `docs/PRIVATE_BETA_ONBOARDING.md`.
- Output conventions spec: `docs/OUTPUT_CONVENTIONS.md` (v0.1.1 will enforce in the SEC overlay).

### Measurements (single-run, honest)
- Treasury: 13/20 on the ADR-004 honest baseline; ±2-pass MiniMax variance band documented.
- SEC tier-1+2: 17/18 (94.4%) on the day-4 gate run; gate threshold ≥80%.
- SEC tier-3 abstention: 7/7 with strict reason-code matching; gate threshold ≥60%.
- Empirical latency: 60–120 s typical end-to-end, ~180 s worst case; XBRL validation ~200 ms.
- Retry-event rate: 4.4% (2/45) on day-4 regression; both retries converted to passes.

### Known issues
- **SEC0017** — multi-year list answers emitted in filing-reporting order rather than question order. Both values correct; parser-unfriendly. v0.1.1 fix: labeled-list answer format. ≤10 days from v0.1 tag.
- **Reasoning-trace opacity on double-stall** — when both retry attempts time out, the operator cannot inspect *why*. ADR-011 trace persistence is the first v0.1.1 item.

### Architecture decisions
- ADR-001 iron rules; ADR-002 XBRL (Arelle, fail-closed narrowing); ADR-003 reasoning_effort=medium; ADR-004 regression stratification + honest baseline; ADR-005 prompt split validation gate; ADR-006 harness correction (goose, not openhands-sdk); ADR-007 newline-in-params fix; ADR-011 reasoning-trace accepted-for-v0.1.1 with re-escalation trigger; ADR-012 retry-on-timeout.

### Notes
- Default model: MiniMax M2.5 via OpenRouter. Swap via `model=` argument to `Agent(...)` using any `ModelConfig` from `teller.config`.
- Tested on Python 3.12 (fresh-clone Docker verification). Declared support: Python 3.10–3.12.
