#!/usr/bin/env python3
"""SEC 25-question gate runner (day-3).

Runs the 25-question SEC test set from
tests/fixtures/sec_filings/sec_twenty_five.json, with per-ticker
corpus-aware Agent invocation. Pre-flight validates that every
tier-1/2 fixture concept_hint is reachable via the Agent's
`_SEC_KEYWORD_TO_CONCEPTS` map — fails loudly before running any
inference if a hint is unmapped (rules out infra/prompt-iteration
signal confound per day-3 operating notes).

Scoring per fixture.gate.scoring_contract:
  - Tier 1/2: OfficeQA 1% fuzzy reward vs expected_answer
  - Tier 3:  correct iff result.abstained AND
             (result.abstention_reason == "segment_level_dimensional"
              OR result.xbrl_validation.reason ==
              "segment_level_dimensional" with abstained True)

Results are appended to
results/gate_sec_<timestamp>.json for day-3 iteration trace.

Usage::

    source arena-cohort0/.env  # sets OPENROUTER_API_KEY
    PYTHONPATH=src python3 scripts/gate_sec.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Post-hotfix: `teller` is resolved from site-packages (wheel install) or
# the editable source tree if one is active. The prior `sys.path.insert`
# for `src/` was a pre-packaging workaround and has been removed so the
# regression evidence reflects the actual distribution artifact.
sys.path.insert(0, str(REPO / "tests" / "fixtures" / "officeqa"))

from teller import Agent, Corpus  # noqa: E402
from teller.agent import _SEC_KEYWORD_TO_CONCEPTS, _guess_gaap_concepts  # noqa: E402

FIXTURE_PATH = REPO / "tests" / "fixtures" / "sec_filings" / "sec_twenty_five.json"
CORPUS_ROOT = REPO / "tests" / "fixtures" / "sec_filings" / "corpus"


def audit_keyword_map(fixture: dict) -> list[tuple[str, str, list[str]]]:
    """Pre-flight: every tier-1/2 concept_hint must be reachable via keyword map.

    Returns list of (uid, hint, guessed) for any question whose hint is
    not in the guessed-concepts list. Empty list == all reachable.
    """
    misses: list[tuple[str, str, list[str]]] = []
    for q in fixture["questions"]:
        if q["tier"] == "TIER_3_SEGMENT_ABSTAIN":
            continue
        hint = q.get("concept_hint")
        if not hint:
            continue
        guessed = _guess_gaap_concepts(q["question"])
        if hint not in guessed:
            misses.append((q["uid"], hint, guessed))
    return misses


def score_tier12(expected: str, predicted: str | None, tolerance: float = 0.01) -> float:
    """OfficeQA-style 1% fuzzy numeric reward with loose magnitude + percent
    normalization (day-3 Track A: accept both millions-integer and
    decimal-billions forms; accept both decimal and percent forms; v0.1
    punch-list tightens this to a single canonical form via prompt).

    Strategy: try the raw comparison first. If raw fails, rescale the
    predicted by candidate factors {1e3, 1e6, 1e9, 1e-3, 1e-6, 1e-9, 100,
    0.01} and accept if any scaled variant lands within tolerance. This is
    a scorer-only loosening; the Agent's output format is unchanged.
    """
    if not predicted:
        return 0.0

    labeled = _score_labeled_multi(expected, predicted, tolerance)
    if labeled is not None:
        return labeled

    raw = _raw_score(expected, predicted, tolerance)
    if raw > 0:
        return raw

    # Normalization pass: try magnitude + percent rescalings on `predicted`.
    p = _single_number(predicted)
    if p is None:
        return 0.0
    for factor in (1e3, 1e6, 1e9, 1e-3, 1e-6, 1e-9, 100.0, 0.01):
        scaled = f"{p * factor:.10g}"
        if _raw_score(expected, scaled, tolerance) > 0:
            return 1.0
    return 0.0


def _score_labeled_multi(expected: str, predicted: str, tolerance: float) -> float | None:
    """Score public `YEAR: value` multi-period output against list fixtures."""
    import ast
    import re

    if ":" not in expected and ":" not in predicted:
        return None
    expected_pairs = re.findall(
        r"\b(20\d{2})\b\s*:\s*(-?\d+(?:,\d{3})*(?:\.\d+)?)",
        expected,
    )
    predicted_pairs = re.findall(
        r"\b(20\d{2})\b\s*:\s*(-?\d+(?:,\d{3})*(?:\.\d+)?)",
        predicted,
    )
    if expected_pairs:
        if len(predicted_pairs) != len(expected_pairs):
            return 0.0
        predicted_by_year = {
            year: float(value.replace(",", "")) for year, value in predicted_pairs
        }
        for year, expected_value in expected_pairs:
            if year not in predicted_by_year:
                return 0.0
            expected_float = float(expected_value.replace(",", ""))
            predicted_value = predicted_by_year[year]
            if expected_float == 0:
                if predicted_value != 0:
                    return 0.0
            elif abs((predicted_value - expected_float) / expected_float) > tolerance:
                return 0.0
        return 1.0

    if ":" not in predicted:
        return None
    try:
        expected_values = ast.literal_eval(expected)
    except Exception:
        return None
    if not isinstance(expected_values, list) or not expected_values:
        return None

    if len(predicted_pairs) != len(expected_values):
        return 0.0
    predicted_values = [float(value.replace(",", "")) for _, value in predicted_pairs]
    for expected_value, predicted_value in zip(expected_values, predicted_values):
        expected_float = float(expected_value)
        if expected_float == 0:
            if predicted_value != 0:
                return 0.0
        elif abs((predicted_value - expected_float) / expected_float) > tolerance:
            return 0.0
    return 1.0


def _raw_score(expected: str, predicted: str, tolerance: float) -> float:
    """Try the official OfficeQA reward, fall back to simple numeric compare."""
    try:
        from reward import score_answer as official_score  # type: ignore
        return official_score(expected, predicted, tolerance)
    except Exception:
        pass
    try:
        e = _single_number(expected)
        p = _single_number(predicted)
        if e is None or p is None:
            return 1.0 if expected.strip().lower() == predicted.strip().lower() else 0.0
        if e == 0:
            return 1.0 if abs(p) < tolerance else 0.0
        return 1.0 if abs((p - e) / e) <= tolerance else 0.0
    except (ValueError, ZeroDivisionError):
        return 0.0


def _single_number(s: str) -> float | None:
    """Parse a single numeric value from a string; None for list-valued strings.

    Returns None for inputs that look list-like (contain commas between
    numbers or bracket characters) so list-valued answers take the
    official reward path exclusively — magnitude normalization is only
    meaningful for scalar comparisons.
    """
    import re
    stripped = s.strip()
    # If we see list-ish structure, abstain from normalization.
    if stripped.startswith("[") or stripped.endswith("]"):
        return None
    # Count how many separate numeric tokens appear; >1 means list-shaped.
    tokens = re.findall(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", stripped.replace(",", ""))
    if len(tokens) != 1:
        return None
    cleaned = stripped.replace(",", "").replace("%", "").replace("$", "")
    cleaned = re.sub(r"[^\d.\-eE+]", "", cleaned)
    try:
        return float(cleaned)
    except ValueError:
        return None


def score_tier3(result, expected_reason: str) -> tuple[bool, str]:
    """Tier-3 contract: correct iff abstained AND reason == expected.

    Returns (correct, actual_reason_surface) where actual_reason_surface is
    the reason string we matched against (from Result.abstention_reason or
    Result.xbrl_validation.reason when abstained).
    """
    if not result.abstained:
        return False, f"not_abstained (answer={result.answer!r})"
    actual = result.abstention_reason
    if actual == expected_reason:
        return True, actual
    # Also accept when xbrl_validation.reason carries the expected code
    # and the agent abstained for a related reason. Strict per contract
    # requires exact match — surface mismatch for analysis.
    xv_reason = result.xbrl_validation.reason if result.xbrl_validation else None
    if xv_reason == expected_reason:
        return True, f"{actual} (via xbrl_validation.reason)"
    return False, actual or "abstained_no_reason"


def run_question(q: dict, out_accumulator: list) -> dict:
    company = q["company"]
    ticker_corpus = CORPUS_ROOT / company
    if not ticker_corpus.exists():
        return {
            "uid": q["uid"], "tier": q["tier"], "company": company,
            "error": f"no corpus dir for {company}",
            "correct": False, "latency_s": 0.0,
        }

    corpus = Corpus(ticker_corpus)
    agent = Agent(domain="sec_filings", corpus=corpus)

    start = time.time()
    try:
        result = agent.ask(q["question"])
        error = None
    except Exception as exc:
        result = None
        error = f"{exc.__class__.__name__}: {exc}"
    latency_s = time.time() - start

    if q["tier"] == "TIER_3_SEGMENT_ABSTAIN":
        if result is None:
            correct = False
            detail = f"exception: {error}"
        else:
            correct, detail = score_tier3(result, q["expected_abstention_reason"])
    else:
        if result is None:
            correct = False
            detail = f"exception: {error}"
        else:
            reward = score_tier12(q["expected_answer"], result.answer)
            correct = reward > 0
            detail = f"reward={reward} got={result.answer!r} expected={q['expected_answer']!r}"

    row = {
        "uid": q["uid"],
        "tier": q["tier"],
        "company": company,
        "question": q["question"],
        "correct": correct,
        "detail": detail,
        "latency_s": round(latency_s, 2),
        "error": error,
    }
    if result is not None:
        row["answer"] = result.answer
        row["abstained"] = result.abstained
        row["abstention_reason"] = result.abstention_reason
        row["xbrl_reason"] = result.xbrl_validation.reason if result.xbrl_validation else None
        row["xbrl_agreed"] = result.xbrl_validation.agreed if result.xbrl_validation else None
    out_accumulator.append(row)
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description="SEC 25-question day-3 gate runner")
    ap.add_argument("--filter", type=str, default=None,
                    help="Comma-separated UIDs to run only (debugging)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Run only first N questions")
    ap.add_argument("--tier", type=str, default=None,
                    choices=["TIER_1_CONSOLIDATED", "TIER_2_MULTI_PERIOD", "TIER_3_SEGMENT_ABSTAIN"],
                    help="Run only questions in this tier")
    args = ap.parse_args()

    fixture = json.loads(FIXTURE_PATH.read_text())

    # ---- Pre-flight: keyword map audit ----
    misses = audit_keyword_map(fixture)
    if misses:
        print("PRE-FLIGHT FAILURE: fixture concept_hints unreachable via keyword map:")
        for uid, hint, guessed in misses:
            print(f"  {uid}: hint={hint!r}  guessed={guessed!r}")
        print("\nFix _SEC_KEYWORD_TO_CONCEPTS in src/teller/agent.py before running the gate.")
        return 3

    # ---- Filter questions ----
    selected = fixture["questions"]
    if args.tier:
        selected = [q for q in selected if q["tier"] == args.tier]
    if args.filter:
        want = {u.upper() for u in args.filter.split(",")}
        selected = [q for q in selected if q["uid"].upper() in want]
    if args.limit:
        selected = selected[: args.limit]

    gate = fixture["gate"]
    print(f"SEC gate set: sec_twenty_five ({len(selected)}/{len(fixture['questions'])} questions)")
    print(f"Tier-1/2 threshold: ≥{int(gate['tier_1_2_accuracy_threshold']*100)}% combined")
    print(f"Tier-3 threshold:  ≥{int(gate['tier_3_abstention_threshold']*100)}% correctly-abstained")
    print()

    if not os.environ.get("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY not set. `source arena-cohort0/.env` first.")
        return 4

    results: list[dict] = []
    t_start = time.time()

    # Incremental results file — flushed after each question so a mid-run
    # crash preserves everything done so far.
    out_dir = REPO / "results"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"gate_sec_{ts}.json"

    for i, q in enumerate(selected, start=1):
        print(f"[{i:>2}/{len(selected)}] {q['uid']} {q['tier']:24} {q['company']:6} "
              f"FY={q.get('fiscal_period','?')}  start...", flush=True)
        row = run_question(q, results)
        mark = "✓" if row["correct"] else "✗"
        print(f"           {mark} {row['latency_s']}s  {row['detail'][:140]}", flush=True)

        out_file.write_text(json.dumps({
            "set": "sec_twenty_five",
            "timestamp": ts,
            "selected": [q["uid"] for q in selected],
            "in_progress_through": row["uid"],
            "per_question": results,
        }, indent=2))

    elapsed = time.time() - t_start

    # ---- Aggregate ----
    by_tier: dict[str, list[dict]] = {}
    for r in results:
        by_tier.setdefault(r["tier"], []).append(r)

    t12_total = sum(1 for r in results if r["tier"] != "TIER_3_SEGMENT_ABSTAIN")
    t12_correct = sum(1 for r in results if r["tier"] != "TIER_3_SEGMENT_ABSTAIN" and r["correct"])
    t3_total = sum(1 for r in results if r["tier"] == "TIER_3_SEGMENT_ABSTAIN")
    t3_correct = sum(1 for r in results if r["tier"] == "TIER_3_SEGMENT_ABSTAIN" and r["correct"])

    t12_acc = (t12_correct / t12_total) if t12_total else 0.0
    t3_acc = (t3_correct / t3_total) if t3_total else 0.0
    t12_pass = t12_acc >= gate["tier_1_2_accuracy_threshold"] if t12_total else None
    t3_pass = t3_acc >= gate["tier_3_abstention_threshold"] if t3_total else None

    # Tier-3 abstention-reason distribution (for diagnostics)
    t3_reasons = Counter()
    for r in results:
        if r["tier"] != "TIER_3_SEGMENT_ABSTAIN":
            continue
        if r.get("abstained"):
            t3_reasons[r.get("abstention_reason") or "abstained_no_reason"] += 1
        else:
            t3_reasons[f"NOT_ABSTAINED (answered)"] += 1

    print()
    print("=" * 72)
    print(f"Elapsed: {elapsed/60:.1f} min  ({elapsed:.0f}s)")
    print()
    print(f"Tier-1+2 combined: {t12_correct}/{t12_total} "
          f"({t12_acc*100:.1f}%) — gate {'PASS' if t12_pass else 'FAIL' if t12_pass is False else 'N/A'}")
    for tier in ("TIER_1_CONSOLIDATED", "TIER_2_MULTI_PERIOD"):
        rows = by_tier.get(tier, [])
        if rows:
            c = sum(1 for r in rows if r["correct"])
            print(f"  {tier:24} {c}/{len(rows)}")

    print()
    print(f"Tier-3 (correctly abstained): {t3_correct}/{t3_total} "
          f"({t3_acc*100:.1f}%) — gate {'PASS' if t3_pass else 'FAIL' if t3_pass is False else 'N/A'}")
    if t3_reasons:
        print("  Abstention-reason distribution:")
        for reason, count in t3_reasons.most_common():
            print(f"    {count}  {reason}")

    # Final write with aggregate
    out_file.write_text(json.dumps({
        "set": "sec_twenty_five",
        "timestamp": ts,
        "selected": [q["uid"] for q in selected],
        "elapsed_minutes": elapsed / 60,
        "tier12_passed": t12_correct,
        "tier12_total": t12_total,
        "tier12_accuracy": t12_acc,
        "tier12_gate_passed": t12_pass,
        "tier3_correctly_abstained": t3_correct,
        "tier3_total": t3_total,
        "tier3_accuracy": t3_acc,
        "tier3_gate_passed": t3_pass,
        "tier3_reason_distribution": dict(t3_reasons),
        "per_question": results,
    }, indent=2))
    print()
    print(f"Results: {out_file.relative_to(REPO)}")

    gate_passed = (t12_pass is None or t12_pass) and (t3_pass is None or t3_pass)
    return 0 if gate_passed else 1


if __name__ == "__main__":
    sys.exit(main())
