"""XBRL fact extraction for SEC filings.

Wraps arelle 2.39.6 (ADR-002) for literal-QName fact lookup from
already-cached XBRL instance documents. This module is consumed by
`Agent.ask` during result assembly to cross-check the LLM-extracted
answer against the fact the filer tagged and submitted to the SEC.

The module always runs arelle with `internetConnectivity="offline"`.
The taxonomy cache is populated only by `teller download-sec`, never
by this module. A missing taxonomy triggers abstention with
`reason="xbrl_taxonomy_uncached"` rather than a mid-inference fetch
(ADR-002 constraint: no live fetches on the ask path).

----------------------------------------------------------------------
Parser-Module Docstring Caveats (from Codex / ADR-002 — load-bearing)
----------------------------------------------------------------------

1. `qnameDims == {}` means "no reported dimensions," not "no semantic
   defaulted explicit dimensions." This is still the correct
   consolidated / default-member predicate for SEC filings under
   XBRL Dimensions 1.0; omitted explicit dimensions are inferred as
   defaults. Do not over-engineer a default-member resolver for v0.1.

2. Typed dimensions need separate handling. They appear in `qnameDims`,
   but `dimMemberQname()` is only meaningful for explicit dimensions.
   For typed dimensions, inspect `isTyped` and `typedMember` on the
   `ModelDimensionValue`. The `qnameDims == {}` predicate still works
   for "consolidated" — it excludes typed-dimensional contexts
   correctly — but any code that walks `qnameDims` for reporting or
   abstention-reason detail must branch on `isTyped`.

3. `factsByQname` is exact-QName only. Do not expect arelle to bridge
   deprecated/replacement concepts or year-to-year taxonomy changes
   for multi-period questions. Cross-period concept normalization
   lives in Teller's concept-family layer (placeholder ADR-008),
   not in this module.

4. Do not trust a non-empty fact set by itself. Gate usage on clean
   arelle logs/errors; any ERROR or FATAL severity on
   `model_xbrl.errors` forces abstention with
   `reason="xbrl_unreadable"` regardless of whether `factsByQname`
   returned a populated set.

Non-blocking: `factsByQname[qname]` returns a set, not an ordered
list. This module sorts matches on
`(period_start, period_end, contextID)` before selecting, so results
are deterministic across runs.

Half-open interval caveat (silent-corruption class): XBRL represents
durations as half-open intervals. Arelle surfaces `endDatetime` as
the *exclusive* end (a duration ending 2024-12-31 has
`endDatetime == 2025-01-01 00:00:00`). Use `context.endDate` /
`context.instantDate` — not `endDatetime.date()` — when matching
period strings. Getting this wrong does not raise; it silently
shifts every period by one day and poisons multi-period lookups.
"""
from __future__ import annotations

import contextlib
import io
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from teller.result import XBRLValidation

FactReason = Literal[
    "not_tagged",
    "segment_level_dimensional",
    "xbrl_unreadable",
    "xbrl_taxonomy_uncached",
]


_NOTE_BY_REASON: dict[str, str] = {
    "not_tagged": "concept not tagged in this filing for the requested period",
    "segment_level_dimensional": (
        "concept reported only under segment / dimensional contexts; "
        "no consolidated fact available for cross-check"
    ),
    "xbrl_unreadable": (
        "XBRL instance document could not be parsed cleanly; "
        "surviving facts are not trusted (fail-closed)"
    ),
    "xbrl_taxonomy_uncached": (
        "referenced taxonomy is not in the local cache; "
        "re-run `teller download-sec` to populate it"
    ),
}

_LAST_ARELLE_DIAGNOSTICS = ""


def get_last_arelle_diagnostics() -> str:
    """Return raw diagnostics captured from the most recent arelle run."""
    return _LAST_ARELLE_DIAGNOSTICS


def _run_arelle_session(session, options) -> bool:
    """Run arelle while suppressing normal noisy diagnostics.

    Known-benign iXBRL warnings are still preserved in
    `_LAST_ARELLE_DIAGNOSTICS` and are printed only when
    `TELLER_DEBUG_XBRL=1` is set by the CLI.
    """
    global _LAST_ARELLE_DIAGNOSTICS
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        ok = session.run(options)
    _LAST_ARELLE_DIAGNOSTICS = stdout.getvalue() + stderr.getvalue()
    if os.environ.get("TELLER_DEBUG_XBRL") == "1" and _LAST_ARELLE_DIAGNOSTICS:
        print(_LAST_ARELLE_DIAGNOSTICS, file=sys.stderr, end="")
    return ok


@dataclass
class FactLookup:
    """Parser-module return type. Internal to `teller.validation`.

    `Agent.ask` consumes `FactLookup` and synthesizes the public
    `Result.xbrl_validation` (`XBRLValidation`) by comparing the
    LLM-extracted answer against `FactLookup.value`. Do not re-export
    this type on the public `teller` surface; it is an implementation
    detail that may evolve before `XBRLValidation` does.
    """

    available: bool
    value: Optional[str] = None
    unit: Optional[str] = None
    context_ref: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    decimals: Optional[str] = None
    concept: Optional[str] = None
    reason: Optional[FactReason] = None


def lookup_fact(
    instance_path: Path | str,
    concept: str,
    period_end: str,
) -> FactLookup:
    """Look up a consolidated fact in an XBRL instance document.

    Args:
        instance_path: Path to the XBRL instance document (`.xml` or
            inline XBRL `.htm`).
        concept: GAAP concept QName, e.g. `"us-gaap:Revenues"`.
        period_end: ISO date string for the period end, e.g.
            `"2024-09-28"`. Duration contexts (start/end) are
            preferred over instant contexts when both match.

    Returns:
        `FactLookup(available=True, ...)` when a consolidated fact
        (context with `qnameDims == {}`) exists for this concept+period,
        with `value`, `unit`, `context_ref`, `period_start`,
        `period_end`, and `decimals` populated. Otherwise
        `FactLookup(available=False, reason=...)` with one of:

        - `"not_tagged"`: concept has no facts in the filing, or none
          in the requested period.
        - `"segment_level_dimensional"`: concept is reported only in
          dimensional contexts (segment/geography/product breakdowns);
          no consolidated fact exists.
        - `"xbrl_unreadable"`: the instance document could not be
          loaded cleanly (parse error, broken linkbase, or any
          ERROR/FATAL on `model_xbrl.errors`). Fail-closed per
          ADR-002: surviving facts from a flagged load are not
          trusted.
        - `"xbrl_taxonomy_uncached"`: a referenced taxonomy is not in
          the local cache. The ask path is offline-only; cache
          pre-population is the downloader's job.

    Always runs `arelle` with `internetConnectivity="offline"`. This
    function does not perform network I/O.
    """
    # Lazy-import arelle symbols. The import cost is ~2 s (lxml, numpy,
    # pillow transitively). Keeping it local to this call means
    # `teller --help` and `teller inspect` on non-XBRL corpora do not
    # pay it. Once the first call has run, subsequent calls in the
    # same process reuse the cached module.
    from arelle.api.Session import Session
    from arelle.ModelValue import qname
    from arelle.RuntimeOptions import RuntimeOptions

    session = Session()
    try:
        options = RuntimeOptions(
            entrypointFile=str(instance_path),
            internetConnectivity="offline",
            keepOpen=True,
            logLevel="warning",
        )
        try:
            ok = _run_arelle_session(session, options)
        except Exception as e:
            return _classify_load_exception(e, concept)

        models = session.get_models()
        if not models:
            return FactLookup(
                available=False,
                reason="xbrl_unreadable",
                concept=concept,
            )
        model_xbrl = models[0]

        # Fail-closed gate (ADR-002 Consequences, Codex probe 3).
        # Any ERROR/FATAL on model_xbrl.errors → abstain regardless of
        # what factsByQname returned. We do not trust surviving facts
        # from a flagged load.
        if not ok or _has_blocking_errors(model_xbrl):
            return FactLookup(
                available=False,
                reason="xbrl_unreadable",
                concept=concept,
            )

        target = qname(concept, model_xbrl.prefixedNamespaces)
        if target is None:
            return FactLookup(
                available=False,
                reason="not_tagged",
                concept=concept,
            )

        matching = model_xbrl.factsByQname.get(target, set())
        chosen, reason = _select_consolidated_fact(matching, period_end)
        if chosen is None:
            return FactLookup(
                available=False,
                reason=reason,
                concept=concept,
            )

        return FactLookup(
            available=True,
            value=str(chosen.value) if chosen.value is not None else None,
            unit=str(chosen.unitID) if chosen.unitID else None,
            context_ref=chosen.contextID,
            period_start=_period_start_iso(chosen.context),
            period_end=_period_end_iso(chosen.context),
            decimals=str(chosen.decimals) if chosen.decimals is not None else None,
            concept=concept,
        )
    finally:
        try:
            session.close()
        except Exception:
            pass


def lookup_facts_by_fiscal_years(
    instance_path: Path | str,
    concept: str,
    fiscal_years: list[int],
) -> dict[int, FactLookup]:
    """Look up consolidated facts for explicit fiscal years.

    This powers Teller's SEC fast path for simple consolidated questions.
    It intentionally preserves the same fail-closed Arelle behavior as
    `lookup_fact`, but selects facts by fiscal year rather than a single
    filing period end so multi-period 10-K questions can be answered
    directly from tagged facts without invoking the LLM.
    """
    if not fiscal_years:
        return {}

    from arelle.api.Session import Session
    from arelle.ModelValue import qname
    from arelle.RuntimeOptions import RuntimeOptions

    wanted = list(dict.fromkeys(fiscal_years))
    session = Session()
    try:
        options = RuntimeOptions(
            entrypointFile=str(instance_path),
            internetConnectivity="offline",
            keepOpen=True,
            logLevel="warning",
        )
        try:
            ok = _run_arelle_session(session, options)
        except Exception as e:
            failed = _classify_load_exception(e, concept)
            return {year: failed for year in wanted}

        models = session.get_models()
        if not models:
            failed = FactLookup(available=False, reason="xbrl_unreadable", concept=concept)
            return {year: failed for year in wanted}
        model_xbrl = models[0]
        if not ok or _has_blocking_errors(model_xbrl):
            failed = FactLookup(available=False, reason="xbrl_unreadable", concept=concept)
            return {year: failed for year in wanted}

        target = qname(concept, model_xbrl.prefixedNamespaces)
        if target is None:
            failed = FactLookup(available=False, reason="not_tagged", concept=concept)
            return {year: failed for year in wanted}

        matching = model_xbrl.factsByQname.get(target, set())
        return {
            year: _lookup_consolidated_fact_for_year(matching, year, concept)
            for year in wanted
        }
    finally:
        try:
            session.close()
        except Exception:
            pass


# --------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------


def _select_consolidated_fact(matching_facts, period_end: str):
    """Classify a set of facts and pick the consolidated one for a period.

    The four return branches implement ADR-002's abstention taxonomy at
    the moat layer. Pure function over `(fact, context)` duck-typed
    inputs — no arelle dependency — so the classification logic is
    unit-testable without an XBRL load.

    Args:
        matching_facts: iterable of fact-like objects with `.context`,
            `.contextID`. Each `.context` must expose `qnameDims`
            (mapping), `isStartEndPeriod`, `isInstantPeriod`, and
            either `startDatetime`/`endDate` or `instantDate`.
        period_end: ISO date string for the period end (e.g.
            `"2024-09-28"`).

    Returns:
        `(fact, None)` — a consolidated fact matches the period.
            Selected deterministically by
            `(period_start, period_end, contextID)` sort with
            duration-over-instant tiebreak.
        `(None, "not_tagged")` — no facts at all for this concept, or
            no consolidated fact matches the requested period.
        `(None, "segment_level_dimensional")` — facts exist for this
            concept but only under dimensional (non-empty `qnameDims`)
            contexts. This is the moat predicate: we abstain rather
            than return a segment value when the user asked for
            consolidated.
    """
    matching = list(matching_facts)
    if not matching:
        return None, "not_tagged"

    # Caveat 1 (ADR-002 / Codex): qnameDims == {} is the conservative
    # consolidated predicate. Omitted explicit dimensions default-
    # resolve; we do not walk defaults for v0.1.
    consolidated = [f for f in matching if not f.context.qnameDims]
    if not consolidated:
        return None, "segment_level_dimensional"

    period_matches = [
        f for f in consolidated if _period_end_iso(f.context) == period_end
    ]
    if not period_matches:
        return None, "not_tagged"

    # Deterministic sort — factsByQname returns a set and iteration
    # order is not stable across runs.
    period_matches.sort(
        key=lambda f: (
            _period_start_iso(f.context) or "",
            _period_end_iso(f.context) or "",
            f.contextID or "",
        )
    )

    # Prefer duration (start/end) contexts over instant for flow
    # concepts (Revenues, NetIncomeLoss). Balance concepts (Assets)
    # only have instant contexts, so the fallback picks them up.
    durations = [f for f in period_matches if f.context.isStartEndPeriod]
    chosen = durations[0] if durations else period_matches[0]
    return chosen, None


def _lookup_consolidated_fact_for_year(
    matching_facts,
    fiscal_year: int,
    concept: str,
) -> FactLookup:
    matching = list(matching_facts)
    if not matching:
        return FactLookup(available=False, reason="not_tagged", concept=concept)

    consolidated = [f for f in matching if not f.context.qnameDims]
    if not consolidated:
        return FactLookup(
            available=False,
            reason="segment_level_dimensional",
            concept=concept,
        )

    period_matches = [
        f for f in consolidated
        if _fiscal_year_from_context(f.context) == fiscal_year
    ]
    if not period_matches:
        return FactLookup(available=False, reason="not_tagged", concept=concept)

    durations = [f for f in period_matches if f.context.isStartEndPeriod]
    if durations:
        durations.sort(
            key=lambda f: (
                _duration_days(f.context),
                _period_end_iso(f.context) or "",
                f.contextID or "",
            ),
            reverse=True,
        )
        chosen = durations[0]
    else:
        period_matches.sort(
            key=lambda f: (
                _period_end_iso(f.context) or "",
                f.contextID or "",
            ),
            reverse=True,
        )
        chosen = period_matches[0]

    return FactLookup(
        available=True,
        value=str(chosen.value) if chosen.value is not None else None,
        unit=str(chosen.unitID) if chosen.unitID else None,
        context_ref=chosen.contextID,
        period_start=_period_start_iso(chosen.context),
        period_end=_period_end_iso(chosen.context),
        decimals=str(chosen.decimals) if chosen.decimals is not None else None,
        concept=concept,
    )


def _fiscal_year_from_context(context) -> Optional[int]:
    period_end = _period_end_iso(context)
    if period_end is None:
        return None
    try:
        return int(period_end.split("-", 1)[0])
    except ValueError:
        return None


def _duration_days(context) -> int:
    start = getattr(context, "startDatetime", None)
    end = getattr(context, "endDate", None)
    if start is None or end is None:
        return 0
    try:
        return (end - start.date()).days
    except Exception:
        return 0


_NON_BLOCKING_ERROR_CODES = frozenset({
    # iXBRL text-transformation namespace codes. These appear on
    # nearly every modern SEC 10-K / 10-Q because filers still use
    # the pre-2020 inline-XBRL transformation registry (ix-2015-08-31)
    # which arelle 2.39.6 does not recognize by default. They flag a
    # *formatting* concern on non-numeric facts (e.g. date-string
    # transformation), not a correctness concern on the us-gaap
    # numeric facts this module extracts. Allowing them through is a
    # narrow, documented relaxation of the ADR-002 fail-closed rule.
    # If this list grows beyond two entries, write an ADR amendment.
    "ix11.11.1.2:invalidTransformation",
    "ix11.10.1.2:invalidTransformation",
})


def _has_blocking_errors(model_xbrl) -> bool:
    """Fail-closed check on arelle's accumulated error log.

    Caveat 4: we do not trust a non-empty fact set from a flagged
    load. In arelle 2.39.6, `model_xbrl.errors` is a list of error
    message codes populated when any ERROR or FATAL-severity log
    record is emitted during load, schema discovery, or validation.

    The strict ADR-002 rule is "any ERROR or FATAL → abstain."
    `_NON_BLOCKING_ERROR_CODES` narrows this for a small set of
    iXBRL text-transformation codes that are known-benign for
    numeric fact extraction on SEC filings. See the constant's
    docstring for the rationale and the documented relaxation path.
    """
    errors = getattr(model_xbrl, "errors", None) or []
    blocking = [e for e in errors if e not in _NON_BLOCKING_ERROR_CODES]
    return bool(blocking)


def _classify_load_exception(exc: Exception, concept: str) -> FactLookup:
    """Map an exception from `Session.run` to a `FactLookup` reason.

    Offline mode raises when a referenced taxonomy is not in the
    local cache; we distinguish that case so the agent can surface
    `xbrl_taxonomy_uncached` to the user with a clear remediation
    ("re-run `teller download-sec`"). All other load failures are
    `xbrl_unreadable`.
    """
    msg = str(exc).lower()
    cache_signals = ("cache", "offline", "not found", "no such", "connection")
    if any(signal in msg for signal in cache_signals):
        return FactLookup(
            available=False,
            reason="xbrl_taxonomy_uncached",
            concept=concept,
        )
    return FactLookup(
        available=False,
        reason="xbrl_unreadable",
        concept=concept,
    )


def synthesize_xbrl_validation(
    lookup: FactLookup,
    agent_answer: Optional[str] = None,
    tolerance: float = 0.01,
) -> XBRLValidation:
    """Translate an internal `FactLookup` into the public `XBRLValidation`.

    `Agent.ask` calls this after running the parser and, for domains
    that produce a numeric answer, passes the LLM-extracted value as
    `agent_answer` to populate `agreed`.

    Args:
        lookup: result from `lookup_fact`.
        agent_answer: optional numeric string extracted by the LLM. When
            provided and `lookup.available`, `agreed` is True iff
            `|agent - tagged| / |tagged| <= tolerance`.
        tolerance: fractional tolerance for numeric agreement. Matches
            the Arena-era `reward.py` 1 % default.

    Returns:
        `XBRLValidation` with `performed=True` only when a consolidated
        fact was extracted. For every abstention reason, `performed` is
        False, `reason` carries the machine-readable code, and `note`
        carries the human-readable explanation.
    """
    if not lookup.available:
        return XBRLValidation(
            performed=False,
            agreed=None,
            gaap_concept=lookup.concept,
            tagged_value=None,
            note=_NOTE_BY_REASON.get(lookup.reason or "", None),
            reason=lookup.reason,
        )

    agreed: Optional[bool] = None
    if agent_answer is not None and lookup.value is not None:
        agreed = _within_tolerance(agent_answer, lookup.value, tolerance)

    note_parts = []
    if lookup.context_ref:
        note_parts.append(f"contextRef={lookup.context_ref}")
    if lookup.unit:
        note_parts.append(f"unit={lookup.unit}")
    if lookup.decimals:
        note_parts.append(f"decimals={lookup.decimals}")
    note = " ".join(note_parts) if note_parts else None

    return XBRLValidation(
        performed=True,
        agreed=agreed,
        gaap_concept=lookup.concept,
        tagged_value=lookup.value,
        note=note,
        reason=None,
    )


def _within_tolerance(a: str, b: str, tolerance: float) -> Optional[bool]:
    """Return True if |a - b| / |b| <= tolerance. None on parse failure."""
    try:
        fa = float(a)
        fb = float(b)
    except (TypeError, ValueError):
        return None
    if fb == 0.0:
        return fa == 0.0
    return abs(fa - fb) / abs(fb) <= tolerance


def _period_end_iso(context) -> Optional[str]:
    """ISO date string for a context's end date (duration) or instant date.

    XBRL represents durations as half-open intervals: `endDatetime` is the
    exclusive end (one day after the human-readable end date). Use `endDate`
    / `instantDate` for the XBRL-spec date so `period_end="2024-12-31"`
    matches a context ending 2024-12-31 as a human reads it.
    """
    if getattr(context, "isInstantPeriod", False):
        d = getattr(context, "instantDate", None)
        return d.isoformat() if d else None
    if getattr(context, "isStartEndPeriod", False):
        d = getattr(context, "endDate", None)
        return d.isoformat() if d else None
    return None


def _period_start_iso(context) -> Optional[str]:
    """ISO date string for a duration context's start; None otherwise.

    `startDatetime` is already an inclusive start; `.date()` gives the
    correct ISO value.
    """
    if getattr(context, "isStartEndPeriod", False):
        dt = getattr(context, "startDatetime", None)
        return dt.date().isoformat() if dt else None
    return None
