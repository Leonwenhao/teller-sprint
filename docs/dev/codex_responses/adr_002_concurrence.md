# Codex Response — ADR-002 Second Opinion

**Date:** 2026-04-17
**ADR:** ADR-002 (XBRL library choice — `arelle-release==2.39.6`)
**Outcome:** Concurrence with substantive docstring caveats. ADR locked as Accepted.

Preserved verbatim for audit. Summarized and folded into ADR-002 in `docs/dev/ARCHITECTURE_DECISIONS.md`.

---

## Concurrence

I concur with arelle-release==2.39.6; none of the three probes surfaced a disqualifier, so ADR-002 can move to Accepted. On probe 1, Arelle 2.39.6 matches XBRL Dimensions semantics: qnameDims contains only reported dimensions, omitted explicit dimensions can resolve to inferred default members, typed dimensions are distinct and cannot have defaults, and SEC 10-K/10-Q guidance treats "total/consolidated" along an axis as the context with no member rather than an explicit "Total" member. That makes your qnameDims == {} predicate the right conservative test for a consolidated/default-member fact. On probe 2, the real multi-year risk is not Arelle inconsistency but exact-QName drift: factsByQname is a literal QName index, while FASB keeps existing element names stable where possible but still adds/deprecates concepts and publishes replacement/deprecation metadata, so cross-period normalization belongs in Teller's concept-family layer, not in the parser library. On probe 3, Arelle does produce structured error signals and unrecoverable loads fail loudly, but recoverable XML/XBRL errors can still leave a partially populated ModelXbrl; that is acceptable only if Teller treats any non-clean load/validation log as fail-closed and abstains with xbrl_unreadable rather than trusting the surviving facts.

## Parser Module Docstring Caveats

- qnameDims == {} means "no reported dimensions," not "no semantic defaulted explicit dimensions." That is still the correct consolidated/default-member predicate for SEC filings.
- Typed dimensions need separate handling: they appear in qnameDims, but dimMemberQname() is only meaningful for explicit dimensions. For typed dimensions, inspect isTyped and typedMember.
- factsByQname is exact-QName only. Do not expect Arelle to bridge deprecated/replacement concepts or year-to-year taxonomy changes for multi-period questions.
- Do not trust a non-empty fact set by itself. Gate usage on clean Arelle logs/errors; otherwise abstain with xbrl_unreadable rather than trusting the surviving facts.
- If you later see edge false positives, inspect segNonDimValues and scenNonDimValues in addition to qnameDims. I would not block the ADR on that for v0.1.

## Non-blocking Observation

- factsByQname[qname] returns a set, not an ordered list. Selection must be deterministic after filtering; never rely on iteration order.

## Sources

- Arelle 2.39.6 Session: https://github.com/Arelle/Arelle/blob/2.39.6/arelle/api/Session.py
- Arelle 2.39.6 ModelXbrl / factsByQname / errors: https://github.com/Arelle/Arelle/blob/2.39.6/arelle/ModelXbrl.py
- Arelle 2.39.6 ModelContext / ModelDimensionValue: https://github.com/Arelle/Arelle/blob/2.39.6/arelle/ModelInstanceObject.py
- Arelle 2.39.6 load/discovery behavior: https://github.com/Arelle/Arelle/blob/2.39.6/arelle/ModelDocument.py
- Arelle 2.39.6 dimension validation/defaults: https://github.com/Arelle/Arelle/blob/2.39.6/arelle/ValidateXbrlDimensions.py
- XBRL Dimensions 1.0 spec: https://www.xbrl.org/specification/dimensions/per-2011-11-20/dimensions-per-2011-11-20.html
- SEC EDGAR XBRL Guide, March 2026: https://www.sec.gov/files/edgar/xbrl-guide.pdf
- FASB 2025 GAAP Taxonomies Release Notes: https://xbrl.fasb.org/resources/annualrelease/2025/GAAP_Financial_Reporting_Taxonomy_Release_Notes.pdf
- FASB 2026 GAAP Taxonomies Release Notes: https://xbrl.fasb.org/resources/annualrelease/2026/GAAP_Financial_Reporting_Taxonomy_Release_Notes.pdf
