"""Centralized model configuration.

Model pluggability is the compliance story (README documents this).
Swapping models is a single-line change: construct a new `ModelConfig`
and pass it to `Agent(model=...)`. The v0.1 default is MiniMax M2.5 via
OpenRouter — the model that won Sentient Arena Cohort 0.

`reasoning_effort = "medium"` is locked by ADR-003 in
docs/dev/ARCHITECTURE_DECISIONS.md. Any future change requires a new
ADR citing cost/accuracy evidence from the target domain.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    """Immutable model configuration.

    Attributes:
        name: Provider/model identifier (e.g. "openrouter/minimax/minimax-m2.5").
        endpoint: Inference endpoint URL.
        reasoning_effort: "low" | "medium" | "high". ADR-003 locks the
            default at "medium" for `MINIMAX_M2_5`.
        max_iterations: Hard cap on harness tool-use iterations per query.
    """

    name: str
    endpoint: str
    reasoning_effort: str
    max_iterations: int = 100


MINIMAX_M2_5 = ModelConfig(
    name="openrouter/minimax/minimax-m2.5",
    endpoint="https://openrouter.ai/api/v1",
    reasoning_effort="medium",
    max_iterations=100,
)


CLAUDE_SONNET_4_5 = ModelConfig(
    name="openrouter/anthropic/claude-sonnet-4.5",
    endpoint="https://openrouter.ai/api/v1",
    reasoning_effort="medium",
    max_iterations=100,
)


GPT_4_1_MINI = ModelConfig(
    name="openrouter/openai/gpt-4.1-mini",
    endpoint="https://openrouter.ai/api/v1",
    reasoning_effort="medium",
    max_iterations=100,
)


DEFAULT_MODEL: ModelConfig = MINIMAX_M2_5
