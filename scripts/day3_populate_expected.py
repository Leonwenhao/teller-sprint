#!/usr/bin/env python3
"""Day-3 phase 2: populate expected_answer from downloaded 10-Ks.

Reads tests/fixtures/sec_filings/sec_twenty_five.json and the download
manifest, then for each tier-1/2 question opens the filing's XBRL
instance offline (cache was warmed in phase 1), enumerates all
consolidated facts matching concept_hint, and picks the correct one(s)
based on question pattern. Writes expected_answer back into the fixture.

Format conventions (must match what the Agent will output to be
scorable by the OfficeQA 1% fuzzy reward):

  - Monetary values: in millions, as an integer string ("416161")
  - Per-share values: raw (e.g. "3.15")
  - Percentages: as decimals ("0.02" for 2%)
  - Multi-period lists: "[val1, val2, ...]" most-recent-first

Usage:
    PYTHONPATH=src python3 scripts/day3_populate_expected.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

FIXTURE = REPO / "tests" / "fixtures" / "sec_filings" / "sec_twenty_five.json"
MANIFEST = REPO / "tests" / "fixtures" / "sec_filings" / "corpus" / "manifest.json"


def load_consolidated_facts(instance_path: Path, concept_qname: str) -> list[dict]:
    """Enumerate consolidated facts for a concept across all reported periods.

    Returns list of dicts with period_start, period_end, value, unit,
    decimals, context_id. Duration contexts preferred over instant when
    both exist for the same period (flow concepts like Revenues).
    """
    from arelle.api.Session import Session
    from arelle.ModelValue import qname
    from arelle.RuntimeOptions import RuntimeOptions

    session = Session()
    try:
        opts = RuntimeOptions(
            entrypointFile=str(instance_path),
            internetConnectivity="offline",
            keepOpen=True,
            logLevel="error",
        )
        ok = session.run(opts)
        if not ok:
            return []
        model_xbrl = session.get_models()[0]
        target = qname(concept_qname, model_xbrl.prefixedNamespaces)
        if target is None:
            return []
        matching = model_xbrl.factsByQname.get(target, set())

        results = []
        for fact in matching:
            ctx = fact.context
            if ctx.qnameDims:
                continue
            try:
                if ctx.isInstantPeriod:
                    period_start = None
                    period_end = ctx.instantDate.isoformat()
                elif ctx.isStartEndPeriod:
                    period_start = ctx.startDatetime.date().isoformat() if ctx.startDatetime else None
                    period_end = ctx.endDate.isoformat()
                else:
                    continue
            except Exception:
                continue

            value = None
            try:
                if fact.xValid and fact.xValue is not None:
                    value = float(fact.xValue)
                elif fact.value is not None:
                    value = float(str(fact.value).replace(",", ""))
            except (ValueError, TypeError):
                continue
            if value is None:
                continue

            results.append({
                "period_start": period_start,
                "period_end": period_end,
                "value": value,
                "unit": str(fact.unitID) if fact.unitID else None,
                "decimals": str(fact.decimals) if fact.decimals is not None else None,
                "context_id": fact.contextID,
                "is_duration": ctx.isStartEndPeriod,
            })
        return results
    finally:
        try:
            session.close()
        except Exception:
            pass


def dedupe_periods(facts: list[dict]) -> list[dict]:
    """Collapse duplicate (period_start, period_end) with duration-over-instant tiebreak."""
    by_period: dict[tuple, dict] = {}
    for f in facts:
        key = (f["period_start"], f["period_end"])
        existing = by_period.get(key)
        if existing is None:
            by_period[key] = f
        else:
            # Prefer duration over instant if both present
            if f["is_duration"] and not existing["is_duration"]:
                by_period[key] = f
    return sorted(by_period.values(), key=lambda f: f["period_end"], reverse=True)


def to_millions(value: float, decimals: str | None) -> int:
    """Express a monetary value in millions. Uses decimals when useful."""
    return int(round(value / 1_000_000))


def format_monetary(value: float, decimals: str | None) -> str:
    return str(to_millions(value, decimals))


def format_per_share(value: float) -> str:
    return f"{value:.2f}"


def format_percent(value: float) -> str:
    return f"{value:.4f}"


def pick_period(facts: list[dict], fiscal_year: int, fiscal_month: int) -> dict | None:
    """Find the duration (or instant) whose period_end matches (year, month±1)."""
    for f in facts:
        end = f["period_end"]
        y = int(end[:4])
        m = int(end[5:7])
        if y == fiscal_year and abs(m - fiscal_month) <= 1:
            return f
    return None


TICKER_FY_MONTH = {
    "AAPL": 9, "MSFT": 6, "WMT": 1, "NVDA": 1,
    "GOOGL": 12, "AMZN": 12, "JPM": 12, "XOM": 12, "PFE": 12, "TSLA": 12,
}


def fiscal_year_to_calendar_year_end(ticker: str, fy_label: str) -> int:
    """FY2026 for WMT (Jan-end) means calendar-year 2026 (Jan 2026 end).
    FY2025 for AAPL (Sep-end) means calendar-year 2025 (Sep 2025 end).
    All companies in this set: fy_label year == calendar year in which FY ends.
    """
    return int(fy_label.replace("FY", ""))


def populate_question(q: dict, manifest: dict) -> tuple[str | None, str | None]:
    """Return (expected_answer_str, note) or (None, error)."""
    company = q["company"]
    if company == "TBD":
        return None, "placeholder — awaiting SEC0018 resolution"

    ticker_info = manifest["tickers"].get(company)
    if not ticker_info or ticker_info.get("status") != "ok":
        return None, f"no manifest entry for {company}"

    instance_path = Path(ticker_info["xbrl_instance"])
    concept = q.get("concept_hint")
    if not concept:
        return None, "no concept_hint"

    facts = dedupe_periods(load_consolidated_facts(instance_path, concept))
    if not facts:
        return None, f"no consolidated facts for {concept}"

    fy_year = fiscal_year_to_calendar_year_end(company, q["fiscal_period"])
    fy_month = TICKER_FY_MONTH[company]
    primary = pick_period(facts, fy_year, fy_month)

    if primary is None:
        return None, f"no fact matched FY={q['fiscal_period']} (month~{fy_month}) in {[f['period_end'] for f in facts[:5]]}"

    uid = q["uid"]
    concept_lower = concept.lower()
    is_per_share = "earningspershare" in concept_lower or "pershare" in concept_lower

    # Single-period tier-1 questions
    if q["tier"] == "TIER_1_CONSOLIDATED":
        if is_per_share:
            return format_per_share(primary["value"]), None
        return format_monetary(primary["value"], primary["decimals"]), None

    # Tier-2 patterns
    if q["tier"] == "TIER_2_MULTI_PERIOD":
        if uid in ("SEC0011", "SEC0012"):
            # YoY percent: (primary - prior) / prior
            prior_year = fy_year - 1
            prior = pick_period(facts, prior_year, fy_month)
            if prior is None:
                return None, f"no prior-period fact for YoY"
            pct = (primary["value"] - prior["value"]) / prior["value"]
            return format_percent(pct), None
        if uid == "SEC0013":
            # 3-year series: pick most-recent 3 durations
            durations = [f for f in facts if f["is_duration"]][:3]
            if len(durations) < 3:
                return None, f"only {len(durations)} duration periods"
            vals = [to_millions(f["value"], f["decimals"]) for f in durations]
            return "[" + ", ".join(str(v) for v in vals) + "]", None
        if uid == "SEC0014":
            # PFE restatement canary: single-period FY25 revenue
            return format_monetary(primary["value"], primary["decimals"]), None
        if uid == "SEC0015":
            # Cash delta: primary - prior
            prior = pick_period(facts, fy_year - 1, fy_month)
            if prior is None:
                return None, "no prior-period fact for delta"
            delta = to_millions(primary["value"] - prior["value"], primary["decimals"])
            return str(delta), None
        if uid in ("SEC0016", "SEC0017"):
            # 2-year instant list
            prior = pick_period(facts, fy_year - 1, fy_month)
            if prior is None:
                return None, "no prior-period fact"
            vals = [to_millions(primary["value"], primary["decimals"]),
                    to_millions(prior["value"], prior["decimals"])]
            return "[" + ", ".join(str(v) for v in vals) + "]", None
        if uid == "SEC0018":
            return None, "placeholder — to resolve"

    return None, f"unhandled uid {uid}"


def main() -> int:
    fixture = json.loads(FIXTURE.read_text())
    manifest = json.loads(MANIFEST.read_text())

    resolved = 0
    unresolved = 0
    for q in fixture["questions"]:
        if q["tier"] == "TIER_3_SEGMENT_ABSTAIN":
            continue
        uid = q["uid"]
        print(f"{uid} [{q['company']} {q['fiscal_period']}] {q.get('concept_hint','?')}", flush=True)
        try:
            expected, note = populate_question(q, manifest)
        except Exception as exc:
            expected, note = None, f"exception: {exc.__class__.__name__}: {exc}"

        if expected is not None:
            q["expected_answer"] = expected
            q["expected_answer_verified"] = True
            print(f"  -> {expected}" + (f"   ({note})" if note else ""), flush=True)
            resolved += 1
        else:
            q["expected_answer"] = None
            q["expected_answer_verified"] = False
            q["populate_error"] = note or "unknown"
            print(f"  UNRESOLVED: {note}", flush=True)
            unresolved += 1

    if unresolved == 0:
        fixture["expected_values_status"] = "verified"

    FIXTURE.write_text(json.dumps(fixture, indent=2))
    print(f"\nResolved: {resolved} / Unresolved: {unresolved}", flush=True)
    return 0 if unresolved == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
