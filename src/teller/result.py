"""Result — the typed output returned by `Agent.ask`."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class Source:
    """A citation supporting an extracted value.

    Every `Result` carries a list of Source instances, one per piece of
    evidence used to answer the question. `excerpt` is the exact passage;
    `location` is a page or section reference usable for manual verification
    in the source document.
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
    """

    performed: bool
    agreed: Optional[bool] = None
    gaap_concept: Optional[str] = None
    tagged_value: Optional[str] = None
    note: Optional[str] = None


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

    def to_dict(self) -> dict:
        """Plain dict for JSON serialization."""
        return asdict(self)

    def to_dataframe(self):
        """Single-row pandas DataFrame for notebook composition.

        Flattens sources and xbrl_validation into scalar columns so rows
        can be stacked across a batch of Results with pandas.concat.
        """
        raise NotImplementedError("Result.to_dataframe is stubbed in v0.1 day-1 scaffold")
