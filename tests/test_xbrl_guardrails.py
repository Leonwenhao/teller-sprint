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


def test_sec_xbrl_fast_path_answers_multi_period_without_goose(
    monkeypatch, tmp_path
):
    agent = _agent_for(tmp_path, "JPM", with_instance=True)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("TELLER_TRACE_DIR", str(tmp_path / "traces"))
    monkeypatch.setattr("teller.agent.shutil.which", lambda _name: None)
    monkeypatch.setattr(
        Agent,
        "_find_xbrl_instance",
        lambda self, preferred_entity=None: self.corpus.path / "jpm-20251231.htm",
    )

    def fake_lookup(instance_path, concept, fiscal_years):
        assert concept == "us-gaap:Assets"
        values = {2024: "4002814000000", 2025: "4424900000000"}
        return {
            year: FactLookup(
                available=True,
                value=values[year],
                unit="usd",
                context_ref=f"FY{year}",
                period_end=f"{year}-12-31",
                decimals="-6",
                concept=concept,
            )
            for year in fiscal_years
        }

    monkeypatch.setattr("teller.validation.xbrl.lookup_facts_by_fiscal_years", fake_lookup)

    result = agent.ask(
        "What were JPMorgan Chase's total assets at the end of each of "
        "fiscal years 2024 and 2025?"
    )

    assert result.answer == "2024: 4002814, 2025: 4424900"
    assert result.xbrl_validation.performed is True
    assert result.xbrl_validation.agreed is True
    assert result.normalization["source"] == "sec_xbrl_fast_path"
    assert result.trace_path is not None


def test_sec_segment_fast_path_abstains_without_goose(monkeypatch, tmp_path):
    agent = _agent_for(tmp_path, "AAPL", with_instance=True)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("TELLER_TRACE_DIR", str(tmp_path / "traces"))
    monkeypatch.setattr("teller.agent.shutil.which", lambda _name: None)

    result = agent.ask("What were Apple's net sales in Greater China in fiscal year 2025?")

    assert result.abstained is True
    assert result.abstention_reason == "segment_level_dimensional"
    assert result.xbrl_validation.reason == "segment_level_dimensional"
    assert result.normalization["kind"] == "segment_abstention"
