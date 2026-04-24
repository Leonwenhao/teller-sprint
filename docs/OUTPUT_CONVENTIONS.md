# Teller Output Conventions

Reference spec for v0.1.1; v0.1 does not enforce this in the SEC prompt.
The target is a single canonical format for each value shape so downstream tools
(spreadsheets, notebooks, parsers) don't need normalization logic.

| Shape | Format | Example |
|---|---|---|
| Monetary | integer in millions | `448980` (for $448.98 B) |
| Ratios / rates / growth | decimal (not percent) | `0.0643` (for 6.43%) |
| Per-share | decimal dollars | `1.08` |
| Multi-period list | `YEAR: value, YEAR: value, ...` | `2025: 101832, 2024: 88136` |

Single-period answers are a bare number. Only multi-period questions carry year
labels. Ordering follows the filing's reporting order (typically latest-year-first);
year labels make order unambiguous for downstream consumers.

These conventions are not enforced in v0.1's SEC prompt. v0.1.1 will enforce
them via a smaller prompt change or a non-prompt normalization layer.
