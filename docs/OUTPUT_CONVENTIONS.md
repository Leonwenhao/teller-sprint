# Teller Output Conventions

Teller answers follow a single canonical format for each value shape so downstream
tools (spreadsheets, notebooks, parsers) don't need normalization logic. The SEC
domain prompt overlay enforces these; treasury and future domains may override.

| Shape | Format | Example |
|---|---|---|
| Monetary | integer in millions | `448980` (for $448.98 B) |
| Ratios / rates / growth | decimal (not percent) | `0.0643` (for 6.43%) |
| Per-share | decimal dollars | `1.08` |
| Multi-period list | `YEAR: value, YEAR: value, ...` | `2025: 101832, 2024: 88136` |

Single-period answers are a bare number. Only multi-period questions carry year
labels. Ordering follows the filing's reporting order (typically latest-year-first);
year labels make order unambiguous for downstream consumers.

These conventions are enforced in `src/teller/domains/sec_filings/prompt.j2`
(`domain_output_format` block) and referenced by the README quickstart at launch.
