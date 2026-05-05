from __future__ import annotations

import pytest

from teller.normalize import normalize_answer
from teller.result import Result


def test_labeled_multi_period_normalization():
    normalized = normalize_answer(
        "What were ExxonMobil total assets in fiscal years 2024 and 2025?",
        "2025 448,980; 2024 453,475",
    )

    assert normalized.answer == "2025: 448980, 2024: 453475"
    assert normalized.metadata["kind"] == "multi_period"


def test_rate_percent_normalizes_to_decimal():
    normalized = normalize_answer(
        "What was Apple's revenue growth from FY2024 to FY2025?",
        "6.43%",
    )

    assert normalized.answer == "0.0643"
    assert normalized.metadata["kind"] == "rate"


def test_xbrl_monetary_dollars_normalize_to_millions():
    normalized = normalize_answer(
        "What was Apple's revenue in fiscal year 2025?",
        "416161000000",
        tagged_value="416161000000",
    )

    assert normalized.answer == "416161"
    assert normalized.metadata["kind"] == "monetary_millions"


def test_unlabeled_multi_value_is_preserved():
    normalized = normalize_answer(
        "What were ExxonMobil total assets in fiscal years 2024 and 2025?",
        "448980, 453475",
    )

    assert normalized.answer == "448980, 453475"
    assert normalized.metadata["kind"] == "raw"


def test_result_to_dataframe_missing_pandas(monkeypatch):
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "pandas":
            raise ImportError("no pandas")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    with pytest.raises(ImportError, match="teller-agent\\[dataframe\\]"):
        Result(question="q", answer="1").to_dataframe()
