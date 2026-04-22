"""Download a 10-K from EDGAR and ask a question with XBRL cross-check.

Run after `pip install teller-agent` (see docs/PRIVATE_BETA_ONBOARDING.md).
Expects OPENROUTER_API_KEY in the environment and `goose` on PATH.

The first call to `teller download-sec` warms a local cache under
./sec_data/<TICKER>/; subsequent runs against the same ticker are offline.

Usage:
    teller download-sec AAPL --latest 10-K
    python examples/sec_query.py
"""
from teller import Agent, Corpus

corpus = Corpus("./sec_data/AAPL")
agent = Agent(domain="sec_filings", corpus=corpus)

result = agent.ask("What was Apple's revenue in fiscal year 2025?")

print(f"Answer:      {result.answer}")
print(f"Latency:     {result.latency_ms / 1000:.1f}s")

if result.abstained:
    print(f"Abstained:   {result.abstention_reason}")
elif result.xbrl_validation.performed:
    v = result.xbrl_validation
    mark = "agreed" if v.agreed else "disagreed"
    print(f"XBRL:        {mark} (tagged value: {v.tagged_value})")
else:
    print(f"XBRL:        not performed ({result.xbrl_validation.reason})")
