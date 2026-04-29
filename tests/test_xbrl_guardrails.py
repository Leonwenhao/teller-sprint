"""Unit coverage for SEC XBRL pre-validation guardrails.

These tests exercise `Agent._post_validate` without live inference. Most
cases stop before Arelle; the happy-path over-suppression case stubs the
XBRL lookup so the test verifies the guardrail boundary, not parser I/O.
"""
from __future__ import annotations

from pathlib import Path

from teller.agent import Agent
from teller.corpus import Corpus
from teller.validation.xbrl import FactLookup


def _agent_for(tmp_path: Path, ticker: str, *, with_instance: bool = False) -> Agent:
    corpus_dir = tmp_path / ticker
    corpus_dir.mkdir(parents=True)
    if with_instance:
        (corpus_dir / f"{ticker.lower()}-20251231.htm").write_text("x" * 1200)
    return Agent(domain="sec_filings", corpus=Corpus(corpus_dir))


def test_non_numeric_answer_skips_validation(tmp_path):
    agent = _agent_for(tmp_path, "AAPL")

    xv = agent._post_validate(
        "What is Apple's expected revenue for fiscal year 2026?",
        "NOT_IN_FILING",
    )

    assert xv.performed is False
    assert xv.agreed is None
    assert xv.reason == "non_numeric_answer"


def test_comma_separated_list_answer_skips_validation(tmp_path):
    agent = _agent_for(tmp_path, "XOM")

    xv = agent._post_validate(
        "What were ExxonMobil's total assets in fiscal years 2024 and 2025?",
        "448980,453475",
    )

    assert xv.performed is False
    assert xv.reason == "non_numeric_answer"


def test_entity_mismatch_skips_validation(tmp_path):
    agent = _agent_for(tmp_path, "XOM")

    xv = agent._post_validate(
        "What was Apple's revenue in fiscal year 2025?",
        "416161",
    )

    assert xv.performed is False
    assert xv.agreed is None
    assert xv.reason == "entity_mismatch"
    assert "question entity=AAPL" in (xv.note or "")
    assert "corpus entity=XOM" in (xv.note or "")


def test_entity_unspecified_skips_validation(tmp_path):
    agent = _agent_for(tmp_path, "AAPL")

    xv = agent._post_validate("What was revenue in fiscal year 2025?", "416161")

    assert xv.performed is False
    assert xv.reason == "entity_unspecified"


def test_period_unspecified_skips_validation(tmp_path):
    agent = _agent_for(tmp_path, "AAPL")

    xv = agent._post_validate("What was Apple's revenue?", "391035")

    assert xv.performed is False
    assert xv.agreed is None
    assert xv.reason == "period_unspecified"


def test_period_mismatch_skips_validation(monkeypatch, tmp_path):
    agent = _agent_for(tmp_path, "AAPL", with_instance=True)
    monkeypatch.setattr(
        "teller.agent._extract_document_period_end",
        lambda _instance_path: "2025-09-27",
    )

    xv = agent._post_validate(
        "What was Apple's revenue in fiscal year 2024?",
        "391035",
    )

    assert xv.performed is False
    assert xv.agreed is None
    assert xv.reason == "period_mismatch"
    assert "FY2024" in (xv.note or "")
    assert "2025-09-27" in (xv.note or "")


def test_scoped_revenue_question_skips_consolidated_validation(tmp_path):
    agent = _agent_for(tmp_path, "AAPL")

    xv = agent._post_validate(
        "What was Apple's services revenue in fiscal year 2025?",
        "109158",
    )

    assert xv.performed is False
    assert xv.agreed is None
    assert xv.reason == "concept_unsupported"


def test_total_revenue_question_still_performs_validation(
    monkeypatch, tmp_path
):
    agent = _agent_for(tmp_path, "AAPL", with_instance=True)
    monkeypatch.setattr(
        "teller.agent._extract_document_period_end",
        lambda _instance_path: "2025-12-31",
    )

    def fake_lookup(instance_path, concept, period_end):
        return FactLookup(
            available=True,
            value="416161000000",
            unit="usd",
            context_ref="c-1",
            period_end=period_end,
            decimals="-6",
            concept=concept,
        )

    monkeypatch.setattr("teller.validation.xbrl.lookup_fact", fake_lookup)

    xv = agent._post_validate("What was Apple total revenue FY2025?", "416161")

    assert xv.performed is True
    assert xv.agreed is True
    assert xv.reason is None
