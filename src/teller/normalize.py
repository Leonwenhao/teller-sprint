"""Answer normalization helpers for public output conventions."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NormalizedAnswer:
    answer: str
    metadata: dict = field(default_factory=dict)


def normalize_answer(question: str, answer: str, tagged_value: Optional[str] = None) -> NormalizedAnswer:
    """Normalize answer text when the conversion is unambiguous.

    The function is intentionally conservative. It never guesses missing
    years, never reorders unlabeled multi-value answers, and leaves the
    original answer untouched when it cannot prove the intended shape.
    """
    original = answer.strip()
    q = question.lower()

    multi = _normalize_labeled_multi_period(original)
    if multi is not None:
        return NormalizedAnswer(multi, {"changed": multi != original, "kind": "multi_period"})

    if _asks_for_rate(q):
        rate = _normalize_rate(original)
        if rate is not None:
            return NormalizedAnswer(rate, {"changed": rate != original, "kind": "rate"})

    if tagged_value is not None and _is_numeric(original):
        monetary = _normalize_monetary_millions(original, tagged_value)
        if monetary is not None:
            return NormalizedAnswer(
                monetary,
                {"changed": monetary != original, "kind": "monetary_millions"},
            )

    return NormalizedAnswer(original, {"changed": False, "kind": "raw"})


def _normalize_labeled_multi_period(answer: str) -> Optional[str]:
    matches = re.findall(
        r"\b(20\d{2})\b\s*[:=\-]?\s*\$?\s*(-?\d+(?:,\d{3})*(?:\.\d+)?)",
        answer,
    )
    if len(matches) < 2:
        return None
    parts = []
    for year, value in matches:
        parts.append(f"{year}: {_clean_number(value)}")
    return ", ".join(parts)


def _asks_for_rate(question: str) -> bool:
    terms = ("rate", "ratio", "growth", "percent", "percentage", "change")
    return any(term in question for term in terms)


def _normalize_rate(answer: str) -> Optional[str]:
    stripped = answer.strip()
    match = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*%", stripped)
    if match:
        return f"{float(match.group(1)) / 100:.10g}"
    if _is_numeric(stripped):
        return _clean_number(stripped)
    return None


def _normalize_monetary_millions(answer: str, tagged_value: str) -> Optional[str]:
    try:
        answer_num = float(_clean_number(answer))
        tagged_num = float(_clean_number(tagged_value))
    except ValueError:
        return None
    if tagged_num == 0:
        return "0" if answer_num == 0 else None

    tagged_millions = tagged_num / 1_000_000
    if _close(answer_num, tagged_millions):
        return str(int(round(tagged_millions)))
    if _close(answer_num, tagged_num):
        return str(int(round(tagged_millions)))
    return None


def _is_numeric(value: str) -> bool:
    return bool(re.fullmatch(r"[+-]?(?:\d+(?:,\d{3})*|\d+)(?:\.\d+)?", value.strip()))


def _clean_number(value: str) -> str:
    cleaned = value.strip().replace(",", "").replace("$", "")
    if re.fullmatch(r"-?\d+\.0+", cleaned):
        return str(int(float(cleaned)))
    return cleaned


def _close(a: float, b: float, tolerance: float = 0.01) -> bool:
    if b == 0:
        return a == 0
    return abs(a - b) / abs(b) <= tolerance
