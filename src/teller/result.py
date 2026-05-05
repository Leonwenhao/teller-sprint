"""Result — the typed output returned by `Agent.ask`."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class Source:
    """An optional citation supporting an extracted value.

    `sources` is reserved for evidence records when a domain can provide
    them. v0.1's SEC path carries its auditable tagged fact through
    `xbrl_validation`; callers must not assume every `Result` has sources.
    """

    file: str
    location: str
    excerpt: str


@dataclass
class XBRLValidation:
    """Cross-validation against XBRL-tagged facts in a filing.

    When `performed` is False, no XBRL cross-check was attempted — either
    the corpus is not XBRL-tagged (Treasury Bulletin), or the metric is
    not covered by the GAAP taxonomy (segment-level figures), or the
    domain does not support XBRL at all. When `performed` is True,
    `agreed` indicates whether the LLM-extracted value matches the
    tagged fact within tolerance.

    `reason` carries a machine-readable code when `performed=False` so
    the agent and downstream callers can branch on the abstention class
    (segment-level vs malformed filing vs uncached taxonomy) without
    string-matching on `note`.
    """

    performed: bool
    agreed: Optional[bool] = None
    gaap_concept: Optional[str] = None
    tagged_value: Optional[str] = None
    note: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class Result:
    """Structured answer returned by `Agent.ask`.

    Every field below is part of the locked v0.1 public surface. Downstream
    tools (notebooks, dashboards, future hosted UIs) rely on this contract.
    Add new fields in future releases; do not rename or repurpose existing
    ones.
    """

    question: str
    answer: Optional[str]
    unit: Optional[str] = None
    currency: Optional[str] = None
    confidence: float = 0.0
    sources: list[Source] = field(default_factory=list)
    xbrl_validation: XBRLValidation = field(
        default_factory=lambda: XBRLValidation(performed=False)
    )
    abstained: bool = False
    abstention_reason: Optional[str] = None
    cost_usd: float = 0.0
    latency_ms: int = 0
    trace_id: Optional[str] = None
    trace_path: Optional[str] = None
    normalization: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Plain dict for JSON serialization."""
        return asdict(self)

    def to_dataframe(self):
        """Single-row pandas DataFrame for notebook composition.

        Flattens sources and xbrl_validation into scalar columns so rows
        can be stacked across a batch of Results with pandas.concat.
        """
        try:
            import pandas as pd
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ImportError(
                "Result.to_dataframe() requires pandas. Install with "
                "`pip install teller-agent[dataframe]`."
            ) from exc

        row = self.to_dict()
        xv = row.pop("xbrl_validation", {}) or {}
        for key, value in xv.items():
            row[f"xbrl_validation.{key}"] = value
        sources = row.pop("sources", [])
        row["sources.count"] = len(sources)
        row["sources"] = sources
        return pd.DataFrame([row])
