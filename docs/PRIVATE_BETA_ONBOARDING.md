# Teller v0.1 — private beta

You're receiving Teller v0.1 because you asked questions about 10-Ks out loud often enough that we finally built the thing. Teller answers quantitative questions about SEC filings and Treasury bulletins by reading the source document, running its own retrieval and extraction, and (for SEC) cross-checking the answer against the filing's XBRL-tagged facts. You get back the number and, where applicable, an agreement signal against the company's own tagging.

This is private beta. You're the first person other than us running it. We want your feedback more than we want your silence.

## Install

Requires Python ≥ 3.10 (tested on 3.12).

```
pip install teller-agent
export OPENROUTER_API_KEY=sk-or-v1-...       # https://openrouter.ai/keys
```

Goose is a prerequisite. macOS: `brew install block-goose-cli`. Linux: `curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash`. Verify with `goose --version`.

## First queries

Treasury bulletins (included with the package for the beta):

```
teller ask --corpus ./treasury_bulletins "What were federal VA expenditures in FY 1934?"
```

SEC filings — you pick the company:

```
teller download-sec AAPL --latest 10-K
teller ask --corpus ./sec_data "What was Apple's revenue in fiscal year 2025?"
```

Typical query: 60–120 seconds. Worst case under normal conditions: about 3 minutes. See "latency tail" below for the exception.

## Please capture stderr

Run everything with `2>&1 | tee teller.log`:

```
teller ask --corpus ./sec_data "..." 2>&1 | tee teller.log
```

Teller emits operational signals to stderr that we find valuable in the first weeks. Email `teller.log` back whenever something surprises you.

## Known v0.1 limitations

Three things we know about. Naming them up front is cheaper than you discovering them.

**1. Multi-year list answers come back in reporting order, not question order.** For questions like "total assets at the end of each of fiscal years 2024 and 2025," Teller emits the values in the order the filing reports them — typically latest-year-first — which is the opposite of the natural English order in the question. Both values are correct; the order may surprise your downstream parser. Addressed in v0.1.1 via explicit year labels on list answers.

**2. Latency tail — occasional queries exceed 3 minutes.** About 5 % of queries will see a first-attempt stall, trigger an automatic retry, and return at 2–3× typical latency. You'll see exactly one stderr line: `teller: model timed out after 600s, retrying (attempt 2/2)...`. In day-4 regression both observed retries recovered; treat the returned answer normally and inspect XBRL/citations before relying on it. This is a known pattern of MiniMax M2.5 tail latency, not a Teller bug; we built the retry specifically for it.

**3. Rare double-stall — both retry attempts time out.** We've seen this once in our regression testing. Real-world rate is unknown. When it happens you'll see `abstained=True, abstention_reason="timeout_600s"` on the Result. The honest answer today: we can't tell you why it stalled. Reasoning-trace persistence that would let us debug this is the first v0.1.1 item; target is 10 days from v0.1 tag. If you hit a double-stall, save the log file and send it over. It's the first data point we'd like to have.

## What we want back

One email, any length, when something surprises you. "Worked as expected on N questions" is also valuable data. We're not asking for a survey; we're asking for the ten minutes between when you notice something and when you forget you noticed.

## Contact

Leon Liu — leon@dolores.research
