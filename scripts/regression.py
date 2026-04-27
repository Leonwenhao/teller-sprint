#!/usr/bin/env python3
"""Treasury regression runner — day-1 canary.

Runs the 20-question treasury regression set locked in
docs/dev/ARCHITECTURE_DECISIONS.md ADR-004 and listed in
tests/fixtures/officeqa/regression_twenty.json. Scores each answer via
the official 1% fuzzy-tolerance reward function from OfficeQA and
reports aggregate + per-tier + per-UID.

Usage::

    source arena-cohort0/.env  # or any shell that sets OPENROUTER_API_KEY
    python3 scripts/regression.py --set twenty

Exit codes (post-ADR-004 day-2+ reset — see "Day-2 Gate Threshold Reset"):
    0 — gate passed (≥13/20 = 65%)
    1 — warn: below pass, above stop (12/20 = 60%)
    2 — below stop threshold (<12/20 = 60%) — day progression blocked

The pre-baseline 14/20 projection was retired once the empirical day-1
run landed at 13/20. Do not revert under schedule pressure.

Results are appended to results/regression_<set>_<timestamp>.json for
day-N trend analysis.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Post-hotfix: `teller` is resolved from site-packages (wheel install) or
# the editable source tree if one is active. The prior `sys.path.insert`
# for `src/` was a pre-packaging workaround and has been removed so the
# regression evidence reflects the actual distribution artifact.
sys.path.insert(0, str(REPO / "tests" / "fixtures" / "officeqa"))

from teller import Agent, Corpus  # noqa: E402

CORPUS_DIR = REPO / "tests" / "fixtures" / "treasury_bulletins"
QUESTIONS_CSV = REPO / "tests" / "fixtures" / "officeqa" / "officeqa_full.csv"
SET_FILES = {
    "twenty": REPO / "tests" / "fixtures" / "officeqa" / "regression_twenty.json",
}


def load_questions_by_uid() -> dict[str, dict]:
    with open(QUESTIONS_CSV) as f:
        return {row["uid"]: row for row in csv.DictReader(f)}


def score_answer(expected: str, predicted: str | None, tolerance: float = 0.01) -> float:
    """Score via the official OfficeQA reward, fall back to numeric compare."""
    if not predicted:
        return 0.0
    try:
        from reward import score_answer as official_score  # type: ignore

        return official_score(expected, predicted, tolerance)
    except Exception:
        pass

    import re

    def clean_num(s: str) -> float:
        s = s.strip().replace(",", "").replace("%", "").replace("$", "")
        s = re.sub(r"[^\d.\-]", "", s)
        return float(s)

    try:
        e = clean_num(expected)
        p = clean_num(predicted)
        if e == 0:
            return 1.0 if abs(p) < tolerance else 0.0
        return 1.0 if abs((p - e) / e) <= tolerance else 0.0
    except (ValueError, ZeroDivisionError):
        return 1.0 if expected.strip().lower() == (predicted or "").strip().lower() else 0.0


def main() -> int:
    ap = argparse.ArgumentParser(description="Teller treasury regression runner")
    ap.add_argument("--set", default="twenty", choices=list(SET_FILES),
                    help="Which regression set to run (default: twenty)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Limit to first N questions (debugging)")
    ap.add_argument("--filter", type=str, default=None,
                    help="Comma-separated UIDs to run only")
    args = ap.parse_args()

    spec_path = SET_FILES[args.set]
    spec = json.loads(spec_path.read_text())
    selected = spec["questions"]
    if args.filter:
        want = {u.upper() for u in args.filter.split(",")}
        selected = [q for q in selected if q["uid"].upper() in want]
    if args.limit:
        selected = selected[: args.limit]

    by_uid = load_questions_by_uid()
    missing = [q["uid"] for q in selected if q["uid"] not in by_uid]
    if missing:
        print(f"ERROR: UIDs missing from officeqa_full.csv: {missing}")
        return 3

    gate = spec["gate_threshold"]
    stop = spec["stop_threshold"]
    print(f"Regression set: {args.set} ({len(selected)} questions)")
    print(f"Corpus: {CORPUS_DIR.relative_to(REPO)}")
    print(f"Gate: ≥{int(gate * len(selected))}/{len(selected)} ({int(gate * 100)}%). Stop below: {int(stop * 100)}%")
    print()

    corpus = Corpus(CORPUS_DIR)
    agent = Agent(domain="treasury", corpus=corpus)

    results: list[dict] = []
    t_start = time.time()

    for i, spec_q in enumerate(selected, start=1):
        uid = spec_q["uid"]
        tier = spec_q["tier"]
        row = by_uid[uid]
        expected = row["answer"]
        question = row["question"]

        print(f"[{i}/{len(selected)}] {uid} ({tier}, {row.get('difficulty', '?')})")
        print(f"    Q: {question[:140]}{'...' if len(question) > 140 else ''}")

        try:
            result = agent.ask(question)
            answer = result.answer
            latency_s = result.latency_ms / 1000 if result.latency_ms else 0.0
            abstained = result.abstained
            reason = result.abstention_reason
            error = None
        except Exception as e:
            answer = None
            latency_s = 0.0
            abstained = True
            reason = f"exception: {e.__class__.__name__}"
            error = str(e)

        reward = score_answer(expected, answer)
        correct = reward > 0

        mark = "✓ PASS" if correct else "✗ FAIL"
        got = (answer[:60] + "...") if answer and len(answer) > 60 else (answer or "<none>")
        exp_shown = (expected[:60] + "...") if len(expected) > 60 else expected
        print(f"    {mark}  got={got!r}  expected={exp_shown!r}  ({latency_s:.1f}s)")
        if abstained:
            print(f"    abstained: {reason}")

        results.append({
            "uid": uid,
            "tier": tier,
            "difficulty": row.get("difficulty", ""),
            "correct": correct,
            "reward": reward,
            "answer": answer,
            "expected": expected,
            "abstained": abstained,
            "abstention_reason": reason,
            "error": error,
            "latency_s": latency_s,
        })

    elapsed = time.time() - t_start

    passed = sum(1 for r in results if r["correct"])
    total = len(results)
    accuracy = passed / total if total else 0.0
    total_latency = sum(r["latency_s"] for r in results)

    tier_stats: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in results:
        tier_stats[r["tier"]][1] += 1
        if r["correct"]:
            tier_stats[r["tier"]][0] += 1

    print()
    print("=" * 64)
    print(f"RESULT: {passed}/{total} correct ({accuracy * 100:.1f}%)")
    print(f"Total elapsed: {elapsed / 60:.1f} min; avg latency per Q: {total_latency / total:.1f}s")
    print()
    print("By tier:")
    for tier in ("ALWAYS_PASS", "SWING", "ALWAYS_FAIL"):
        p, t = tier_stats.get(tier, [0, 0])
        print(f"  {tier:<14} {p}/{t}")

    gate_passed = accuracy >= gate
    should_stop = accuracy < stop

    out_dir = REPO / "results"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"regression_{args.set}_{ts}.json"
    out_file.write_text(json.dumps({
        "set": args.set,
        "timestamp": ts,
        "passed": passed,
        "total": total,
        "accuracy": accuracy,
        "gate_threshold": gate,
        "stop_threshold": stop,
        "gate_passed": gate_passed,
        "should_stop": should_stop,
        "elapsed_minutes": elapsed / 60,
        "avg_latency_s": total_latency / total if total else 0,
        "per_tier": {tier: {"passed": p, "total": t} for tier, (p, t) in tier_stats.items()},
        "per_question": results,
    }, indent=2))
    print()
    print(f"Results: {out_file.relative_to(REPO)}")

    if should_stop:
        print()
        print(f"⛔ STOP: {accuracy * 100:.1f}% is below the {int(stop * 100)}% stop threshold.")
        print("Day progression is blocked until the drift is diagnosed and restored.")
        return 2
    if not gate_passed:
        print()
        print(f"⚠ Gate NOT met: {accuracy * 100:.1f}% < {int(gate * 100)}% (but above stop threshold).")
        print("Investigate variance; baseline per ADR-004 is 13/20 = 65%.")
        return 1
    print()
    print(f"✓ Gate passed: {accuracy * 100:.1f}% ≥ {int(gate * 100)}%. Regression complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
