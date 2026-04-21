"""Tests for `synthesize_xbrl_validation` — FactLookup → public XBRLValidation.

Every abstention reason code the parser can produce must survive
translation into the public `Result.xbrl_validation` shape without
collapsing into a generic "not performed" that would strip the
signal Agent.ask needs for downstream abstention logic.

Five cases:
- available=True with agreement check
- available=True with disagreement
- not_tagged
- segment_level_dimensional
- xbrl_unreadable
- xbrl_taxonomy_uncached
"""
from __future__ import annotations

from teller.result import XBRLValidation
from teller.validation.xbrl import FactLookup, synthesize_xbrl_validation


# --------------------------------------------------------------------
# available=True
# --------------------------------------------------------------------


def test_available_with_agreeing_answer():
    lookup = FactLookup(
        available=True,
        value="391035000000",
        unit="USD",
        context_ref="FY2024",
        period_start="2024-01-01",
        period_end="2024-12-31",
        decimals="-6",
        concept="us-gaap:Revenues",
    )
    xv = synthesize_xbrl_validation(lookup, agent_answer="391035000000")
    assert xv.performed is True
    assert xv.agreed is True
    assert xv.gaap_concept == "us-gaap:Revenues"
    assert xv.tagged_value == "391035000000"
    assert xv.reason is None
    # note should carry context/unit/decimals for auditability
    assert "FY2024" in (xv.note or "")
    assert "USD" in (xv.note or "")


def test_available_with_disagreeing_answer_outside_tolerance():
    lookup = FactLookup(
        available=True,
        value="391035000000",
        unit="USD",
        context_ref="FY2024",
        concept="us-gaap:Revenues",
    )
    # 5 % off → outside default 1 % tolerance
    xv = synthesize_xbrl_validation(lookup, agent_answer="410000000000")
    assert xv.performed is True
    assert xv.agreed is False


def test_available_with_disagreeing_answer_inside_tolerance():
    lookup = FactLookup(
        available=True,
        value="391035000000",
        unit="USD",
        concept="us-gaap:Revenues",
    )
    # 0.2 % off → within 1 % tolerance
    xv = synthesize_xbrl_validation(lookup, agent_answer="391800000000")
    assert xv.performed is True
    assert xv.agreed is True


def test_available_without_agent_answer_leaves_agreed_none():
    """Parser may be called ahead of the LLM to check concept
    existence; in that path no agent answer exists to compare.
    """
    lookup = FactLookup(available=True, value="100", concept="us-gaap:Revenues")
    xv = synthesize_xbrl_validation(lookup, agent_answer=None)
    assert xv.performed is True
    assert xv.agreed is None
    assert xv.tagged_value == "100"


# --------------------------------------------------------------------
# Abstention codes — all four must survive translation
# --------------------------------------------------------------------


def test_not_tagged_maps_to_not_performed_with_reason():
    lookup = FactLookup(available=False, reason="not_tagged", concept="us-gaap:Revenues")
    xv = synthesize_xbrl_validation(lookup)
    assert xv.performed is False
    assert xv.agreed is None
    assert xv.tagged_value is None
    assert xv.gaap_concept == "us-gaap:Revenues"
    assert xv.reason == "not_tagged"
    assert xv.note is not None
    assert "not tagged" in xv.note.lower()


def test_segment_level_dimensional_preserves_reason():
    """The moat case: abstention signal must reach the agent intact.

    Agent.ask branches on xbrl_validation.reason == 'segment_level_dimensional'
    to decide whether to abstain or fall back to text extraction.
    """
    lookup = FactLookup(
        available=False,
        reason="segment_level_dimensional",
        concept="us-gaap:Revenues",
    )
    xv = synthesize_xbrl_validation(lookup)
    assert xv.performed is False
    assert xv.reason == "segment_level_dimensional"
    assert xv.tagged_value is None
    assert "segment" in (xv.note or "").lower()


def test_xbrl_unreadable_preserves_reason():
    lookup = FactLookup(
        available=False,
        reason="xbrl_unreadable",
        concept="us-gaap:Revenues",
    )
    xv = synthesize_xbrl_validation(lookup)
    assert xv.performed is False
    assert xv.reason == "xbrl_unreadable"


def test_xbrl_taxonomy_uncached_preserves_reason():
    """Cache-miss must surface with its own code so the CLI can tell
    the user to re-run `teller download-sec`, rather than looking like
    a corrupt-filing abstention.
    """
    lookup = FactLookup(
        available=False,
        reason="xbrl_taxonomy_uncached",
        concept="us-gaap:Revenues",
    )
    xv = synthesize_xbrl_validation(lookup)
    assert xv.performed is False
    assert xv.reason == "xbrl_taxonomy_uncached"
    assert "download-sec" in (xv.note or "")


# --------------------------------------------------------------------
# Output shape contract
# --------------------------------------------------------------------


def test_returns_public_xbrlvalidation_type():
    """Type identity matters: this is what Result.xbrl_validation holds."""
    lookup = FactLookup(available=False, reason="not_tagged")
    xv = synthesize_xbrl_validation(lookup)
    assert isinstance(xv, XBRLValidation)
