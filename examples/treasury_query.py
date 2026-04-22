"""Ask a single question against the Treasury Bulletin corpus.

Run after `pip install teller-agent` (see docs/PRIVATE_BETA_ONBOARDING.md).
Expects OPENROUTER_API_KEY in the environment and `goose` on PATH.

Usage:
    python examples/treasury_query.py
"""
from teller import Agent, Corpus

corpus = Corpus("./tests/fixtures/treasury_bulletins")
agent = Agent(domain="treasury", corpus=corpus)

result = agent.ask("What were federal VA expenditures in FY 1934?")

print(f"Answer:      {result.answer}")
print(f"Latency:     {result.latency_ms / 1000:.1f}s")
if result.abstained:
    print(f"Abstained:   {result.abstention_reason}")
