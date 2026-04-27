"""Iron-rules drift detection.

Ensures the three load-bearing behavioral rules from the Arena-winning
prompt are present in the rendered base template and every domain
overlay. If any anchor is missing, the test fails and CI blocks the
change.

Canonical anchors come from docs/dev/ARCHITECTURE_DECISIONS.md ADR-001:
- Rule 1 (write-answer insurance): "WRITE /app/answer.txt in EVERY Python block"
- Rule 2 (Python-only math): "ALL math in Python"
- Rule 3 (termination signal): "FINISH. Do not re-verify"

A prompt change that alters a canonical anchor requires a new ADR that
explicitly deprecates ADR-001. Silent anchor drift is forbidden.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent.parent
PROMPTS_DIR = ROOT / "src" / "teller" / "prompts"
DOMAINS_DIR = ROOT / "src" / "teller" / "domains"


# Canonical iron-rule anchors, copied verbatim from ADR-001.
IRON_RULE_ANCHORS: dict[str, str] = {
    "rule_1_write_answer_insurance": "WRITE /app/answer.txt in EVERY Python block",
    "rule_2_python_only_math": "ALL math in Python",
    "rule_3_termination_signal": "FINISH. Do not re-verify",
}


def _render_base() -> str:
    env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))
    template = env.get_template("base.j2")
    return template.render(instruction="")


def _domain_overlays() -> list[Path]:
    """Return (name, prompt_path) tuples for every domain overlay on disk."""
    if not DOMAINS_DIR.exists():
        return []
    return sorted(p for p in DOMAINS_DIR.glob("*/prompt.j2"))


def _render_domain(domain_prompt_path: Path) -> str:
    """Render a domain overlay, allowing it to extend `base.j2`."""
    env = Environment(
        loader=FileSystemLoader([str(PROMPTS_DIR), str(domain_prompt_path.parent)])
    )
    template = env.get_template("prompt.j2")
    return template.render(instruction="")


@pytest.mark.parametrize("anchor_name,anchor_phrase", list(IRON_RULE_ANCHORS.items()))
def test_base_contains_iron_rule_anchor(anchor_name: str, anchor_phrase: str) -> None:
    """The base template must contain every iron-rule anchor."""
    rendered = _render_base()
    assert anchor_phrase in rendered, (
        f"Iron rule {anchor_name!r} missing from rendered src/teller/prompts/base.j2.\n"
        f"Expected anchor: {anchor_phrase!r}\n"
        f"See docs/dev/ARCHITECTURE_DECISIONS.md ADR-001. Changes to canonical "
        f"anchors require a new ADR that explicitly deprecates ADR-001."
    )


@pytest.mark.parametrize("anchor_name,anchor_phrase", list(IRON_RULE_ANCHORS.items()))
def test_every_domain_overlay_contains_iron_rule_anchor(
    anchor_name: str, anchor_phrase: str
) -> None:
    """Every authored domain overlay must preserve every iron-rule anchor.

    Catches overlay bugs where a domain template overrides the base content
    in a way that drops an iron rule (e.g. a `{% block %}` that omits the
    header, or a domain-specific skill that replaces the rules wholesale).

    Skips cleanly on day-1 pre-audit when no overlay has been authored yet.
    """
    overlays = _domain_overlays()
    if not overlays:
        pytest.skip("no domain overlays authored yet (day-1 pre-audit)")

    for overlay_path in overlays:
        rendered = _render_domain(overlay_path)
        domain_name = overlay_path.parent.name
        assert anchor_phrase in rendered, (
            f"Iron rule {anchor_name!r} missing from rendered "
            f"domain '{domain_name}' overlay ({overlay_path}).\n"
            f"Expected anchor: {anchor_phrase!r}\n"
            f"See docs/dev/ARCHITECTURE_DECISIONS.md ADR-001."
        )
