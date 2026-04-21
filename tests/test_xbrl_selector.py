"""Pure-unit tests for the moat predicate in `teller.validation.xbrl`.

`_select_consolidated_fact` is the core classification logic behind
XBRL cross-validation: it decides whether a set of matching facts
yields a consolidated hit, a segment-level abstention, or a period
miss. Bugs here propagate directly to the abstention contract — a
confident-wrong answer on a segment-only concept is the launch-day
catastrophe named in `Revised_TELLER_STRATEGY.md §11`.

These tests build fact-like mocks with `SimpleNamespace` so the
classification is exercised without an arelle load or any taxonomy
cache dependency. Integration coverage comes from the day-2 Apple
10-K smoke test, which exercises real US-GAAP dimensional contexts
end-to-end.
"""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from teller.validation.xbrl import _select_consolidated_fact


def _mock_context(
    *,
    qname_dims: dict | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    instant: str | None = None,
) -> SimpleNamespace:
    """Build a fact.context duck-typed for the selector.

    Exposes exactly the attributes `_select_consolidated_fact` and its
    date helpers touch: `qnameDims`, `isStartEndPeriod`,
    `isInstantPeriod`, `startDatetime`, `endDate`, `instantDate`.
    """
    if instant is not None:
        d = datetime.fromisoformat(instant).date()
        return SimpleNamespace(
            qnameDims=dict(qname_dims or {}),
            isStartEndPeriod=False,
            isInstantPeriod=True,
            startDatetime=None,
            endDate=None,
            instantDate=d,
        )
    return SimpleNamespace(
        qnameDims=dict(qname_dims or {}),
        isStartEndPeriod=True,
        isInstantPeriod=False,
        startDatetime=datetime.fromisoformat(period_start),
        endDate=datetime.fromisoformat(period_end).date(),
        instantDate=None,
    )


def _mock_fact(
    *, context_id: str, context: SimpleNamespace, value: str = "0"
) -> SimpleNamespace:
    return SimpleNamespace(
        contextID=context_id,
        context=context,
        value=value,
        unitID="USD",
        decimals="-6",
    )


# --------------------------------------------------------------------
# Branch 1 — empty input
# --------------------------------------------------------------------


def test_empty_input_returns_not_tagged():
    fact, reason = _select_consolidated_fact([], "2024-12-31")
    assert fact is None
    assert reason == "not_tagged"


# --------------------------------------------------------------------
# Branch 2 — segment-only
# --------------------------------------------------------------------


def test_only_dimensional_facts_abstains_as_segment_level():
    """Moat predicate: qnameDims == {} is the consolidated test.

    When every fact carries at least one reported dimension, there is
    no consolidated reading and the selector must refuse to pick a
    segment value as a consolidated answer.
    """
    product_segment = _mock_fact(
        context_id="FY2024_Products",
        context=_mock_context(
            qname_dims={"us-gaap:SegmentAxis": "us-gaap:ProductsMember"},
            period_start="2024-01-01",
            period_end="2024-12-31",
        ),
        value="250000000000",
    )
    services_segment = _mock_fact(
        context_id="FY2024_Services",
        context=_mock_context(
            qname_dims={"us-gaap:SegmentAxis": "us-gaap:ServicesMember"},
            period_start="2024-01-01",
            period_end="2024-12-31",
        ),
        value="100000000000",
    )
    fact, reason = _select_consolidated_fact(
        [product_segment, services_segment], "2024-12-31"
    )
    assert fact is None
    assert reason == "segment_level_dimensional"


def test_consolidated_chosen_over_segments_when_both_present():
    """Mixed facts: selector must pick the consolidated fact.

    A typical 10-K reports Revenues both consolidated and broken down
    by segment. Empty-qnameDims fact is the one we want; segment
    facts are ignored.
    """
    consolidated = _mock_fact(
        context_id="FY2024",
        context=_mock_context(
            qname_dims={},
            period_start="2024-01-01",
            period_end="2024-12-31",
        ),
        value="391035000000",
    )
    product_segment = _mock_fact(
        context_id="FY2024_Products",
        context=_mock_context(
            qname_dims={"us-gaap:SegmentAxis": "us-gaap:ProductsMember"},
            period_start="2024-01-01",
            period_end="2024-12-31",
        ),
        value="250000000000",
    )
    fact, reason = _select_consolidated_fact(
        [product_segment, consolidated], "2024-12-31"
    )
    assert reason is None
    assert fact is consolidated
    assert fact.value == "391035000000"


# --------------------------------------------------------------------
# Branch 3 — period miss
# --------------------------------------------------------------------


def test_consolidated_fact_for_wrong_period_is_not_tagged():
    consolidated_2023 = _mock_fact(
        context_id="FY2023",
        context=_mock_context(
            qname_dims={},
            period_start="2023-01-01",
            period_end="2023-12-31",
        ),
        value="383285000000",
    )
    fact, reason = _select_consolidated_fact([consolidated_2023], "2024-12-31")
    assert fact is None
    assert reason == "not_tagged"


# --------------------------------------------------------------------
# Branch 4 — hit; determinism and duration-over-instant tiebreak
# --------------------------------------------------------------------


def test_duration_preferred_over_instant_for_same_period():
    """Flow concepts tag both period (flow) and period-end (stock) in
    some filers. The selector must return the duration fact for a
    flow concept like Revenues.
    """
    duration = _mock_fact(
        context_id="D2024",
        context=_mock_context(
            qname_dims={},
            period_start="2024-01-01",
            period_end="2024-12-31",
        ),
        value="391035000000",
    )
    instant = _mock_fact(
        context_id="I2024",
        context=_mock_context(qname_dims={}, instant="2024-12-31"),
        value="391035999999",
    )
    fact, reason = _select_consolidated_fact([instant, duration], "2024-12-31")
    assert reason is None
    assert fact is duration


def test_instant_fact_chosen_when_only_instant_available():
    """Balance-sheet concepts (Assets) only have instant contexts.

    The duration-preference logic must fall back to instant when no
    duration exists so balance concepts work.
    """
    instant = _mock_fact(
        context_id="I2024",
        context=_mock_context(qname_dims={}, instant="2024-12-31"),
        value="352583000000",
    )
    fact, reason = _select_consolidated_fact([instant], "2024-12-31")
    assert reason is None
    assert fact is instant


def test_sort_is_deterministic_across_iteration_orders():
    """factsByQname returns a set; selector must return the same fact
    regardless of iteration order. Given two duration facts with the
    same (period_start, period_end), the one with the
    lexicographically earlier contextID wins.
    """
    fact_a = _mock_fact(
        context_id="C001",
        context=_mock_context(
            qname_dims={},
            period_start="2024-01-01",
            period_end="2024-12-31",
        ),
        value="100",
    )
    fact_b = _mock_fact(
        context_id="C002",
        context=_mock_context(
            qname_dims={},
            period_start="2024-01-01",
            period_end="2024-12-31",
        ),
        value="200",
    )
    picked_1, _ = _select_consolidated_fact([fact_a, fact_b], "2024-12-31")
    picked_2, _ = _select_consolidated_fact([fact_b, fact_a], "2024-12-31")
    assert picked_1.contextID == "C001"
    assert picked_2.contextID == "C001"
