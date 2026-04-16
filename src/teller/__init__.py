"""Teller — grounded reasoning agent for enterprise document QA.

Public surface locked for v0.1:

    from teller import Agent, Corpus, Result

    corpus = Corpus("./sec_data")
    agent = Agent(domain="sec_filings", corpus=corpus)
    result = agent.ask("What was Apple's FY2023 revenue?")
"""
from teller.agent import Agent
from teller.corpus import Corpus
from teller.result import Result, Source, XBRLValidation

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "Corpus",
    "Result",
    "Source",
    "XBRLValidation",
    "__version__",
]
