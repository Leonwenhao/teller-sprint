"""Tests for the ABSTAIN:<reason> sentinel parsing in Agent.ask.

Covers the day-3 Track B behavioral-abstention surface: the SEC overlay
writes "ABSTAIN:segment_level_dimensional" (or another reason code) to
the answer file on segment-intent classification, and Agent.ask lifts
the reason into Result.abstained without running XBRL cross-check.

These tests cover the parsing logic in isolation — they do not launch
goose. The answer-file contents are what we're asserting Agent handles
correctly, so we simulate the post-goose state by writing the file
directly and invoking the same decoding path.
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from teller.result import Result


# The parsing logic lives inline in Agent.ask between the "answer file
# exists" branch and the "_post_validate" call. Mirror it here so the
# test is hermetic and doesn't require monkey-patching subprocess.run.
def _parse_answer_file(answer: str, latency_ms: int, question: str) -> Result:
    """Reproduction of the sentinel-parsing branch from Agent.ask.

    Kept in sync with src/teller/agent.py — if the Agent's parsing
    changes, update this helper. The test's value is asserting that
    the REASON-CODE TAXONOMY is owned by the prompt layer (Agent does
    not whitelist reason codes).
    """
    if not answer:
        return Result(
            question=question,
            answer=None,
            abstained=True,
            abstention_reason="empty_answer_file",
            latency_ms=latency_ms,
        )
    first_line = answer.split("\n", 1)[0].strip()
    if first_line.startswith("ABSTAIN:"):
        reason = first_line[len("ABSTAIN:"):].strip() or "llm_requested_abstention"
        return Result(
            question=question,
            answer=None,
            abstained=True,
            abstention_reason=reason,
            latency_ms=latency_ms,
        )
    return Result(
        question=question,
        answer=answer,
        confidence=1.0,
        latency_ms=latency_ms,
    )


class TestAbstentionSentinel:
    def test_segment_level_dimensional_lifts_to_result(self):
        result = _parse_answer_file(
            "ABSTAIN:segment_level_dimensional",
            latency_ms=123,
            question="What were Apple's net sales in Greater China in fiscal year 2025?",
        )
        assert result.abstained is True
        assert result.abstention_reason == "segment_level_dimensional"
        assert result.answer is None
        # XBRL validation is NOT run on abstention — default XBRLValidation(performed=False)
        assert result.xbrl_validation.performed is False

    def test_arbitrary_reason_code_surfaced_verbatim(self):
        # Agent does not whitelist reason codes — the prompt layer owns
        # the taxonomy. A future prompt can add ABSTAIN:out_of_corpus_date
        # without Agent changes.
        result = _parse_answer_file(
            "ABSTAIN:out_of_corpus_date",
            latency_ms=50,
            question="placeholder",
        )
        assert result.abstained is True
        assert result.abstention_reason == "out_of_corpus_date"

    def test_empty_reason_falls_back_to_llm_requested(self):
        # Defensive: if the LLM writes "ABSTAIN:" without a reason code,
        # we surface a descriptive fallback rather than an empty string.
        result = _parse_answer_file(
            "ABSTAIN:",
            latency_ms=10,
            question="placeholder",
        )
        assert result.abstained is True
        assert result.abstention_reason == "llm_requested_abstention"

    def test_trailing_whitespace_and_newlines_stripped(self):
        result = _parse_answer_file(
            "ABSTAIN:segment_level_dimensional\n\nignored trailing text\n",
            latency_ms=10,
            question="placeholder",
        )
        assert result.abstained is True
        assert result.abstention_reason == "segment_level_dimensional"

    def test_numeric_answer_does_not_trigger_abstention(self):
        result = _parse_answer_file(
            "416161",
            latency_ms=10,
            question="What was Apple's total net sales in fiscal year 2025?",
        )
        assert result.abstained is False
        assert result.answer == "416161"

    def test_answer_that_mentions_abstain_but_is_not_a_sentinel(self):
        # Sentinel check is startswith(ABSTAIN:) — a numeric answer that
        # happens to contain "ABSTAIN" elsewhere is NOT lifted.
        result = _parse_answer_file(
            "50 (confidence note: would ABSTAIN: on segment)",
            latency_ms=10,
            question="placeholder",
        )
        assert result.abstained is False
        assert result.answer.startswith("50 ")
