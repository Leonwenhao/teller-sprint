"""Agent — the public entry point for asking grounded questions against a corpus."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from teller.config import ModelConfig
    from teller.corpus import Corpus
    from teller.result import Result


class Agent:
    """A grounded reasoning agent bound to a domain and a corpus.

    Each `ask` call runs a retrieve → extract → compute → validate pipeline
    against the bound corpus. Results are typed (`Result`) with page-level
    citations and, for supported domains (SEC filings on day 2+), XBRL
    cross-validation against the company's own tagged facts.

    Example::

        from teller import Agent, Corpus

        corpus = Corpus("./sec_data")
        agent = Agent(domain="sec_filings", corpus=corpus)
        result = agent.ask("What was Apple's FY2023 revenue?")

        print(result.answer)                   # '383285'
        print(result.xbrl_validation.agreed)   # True
        print([s.file for s in result.sources])
    """

    def __init__(
        self,
        domain: str,
        corpus: "Corpus",
        model: Optional["ModelConfig"] = None,
    ) -> None:
        self.domain = domain
        self.corpus = corpus
        self.model = model

    def ask(self, question: str) -> "Result":
        """Answer a question against the bound corpus.

        Returns a `Result` with answer, confidence, sources, XBRL validation
        (when applicable), and abstention status. The agent abstains with
        a structured reason rather than return a confidently-wrong answer.
        """
        raise NotImplementedError("Agent.ask is stubbed in v0.1 day-1 scaffold")
