# Teller v0.1 — private beta

You're receiving Teller v0.1 because you asked questions about 10-Ks out loud often enough that we finally built the thing. Teller answers quantitative questions about SEC filings and Treasury bulletins by reading the source document, running its own retrieval and extraction, and (for SEC) cross-checking the answer against the filing's XBRL-tagged facts. You get back the number and, where applicable, an agreement signal against the company's own tagging.

This is private beta. You're the first person other than us running it. We want your feedback more than we want your silence.

## Install

Requires Python ≥ 3.10 (tested on 3.12).

```
pip install teller-agent
export OPENROUTER_API_KEY=<your-openrouter-key>       # https://openrouter.ai/keys
```

Goose is a prerequisite. macOS: `brew install block-goose-cli`. Linux: `curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash`. Verify with `goose --version`.

Run `teller doctor` before your first query. It checks Python, package data, goose, your OpenRouter key, and trace-directory writability.

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

Typical query: 60–120 seconds. Long single calls around five minutes have been observed. See "latency tail" below for the exception.

## Please capture traces

Every query writes a local JSON trace under `.teller/traces/` by default. You can change the location with `TELLER_TRACE_DIR=/path/to/traces` or disable it with `TELLER_TRACE_DISABLED=1`.

Run surprising queries with stderr capture too:

```
teller ask --corpus ./sec_data "..." 2>&1 | tee teller.log
```

Email the trace JSON and `teller.log` back whenever something surprises you. Traces intentionally do not include `OPENROUTER_API_KEY`.

## Known v0.1 limitations

Five things we know about. Naming them up front is cheaper than you discovering them.

**1. Multi-year list normalization is conservative.** Teller normalizes labeled multi-period answers to `YEAR: value`. If the model emits an unlabeled list that cannot be mapped safely, Teller preserves the raw answer and records that in the trace.

**2. Latency tail — occasional queries exceed 3 minutes.** About 5 % of queries will see a first-attempt stall, trigger an automatic retry, and return at 2–3× typical latency. You'll see exactly one stderr line: `teller: model timed out after 600s, retrying (attempt 2/2)...`. In day-4 regression both observed retries recovered; treat the returned answer normally and inspect XBRL/citations before relying on it. This is a known pattern of MiniMax M2.5 tail latency, not a Teller bug; we built the retry specifically for it.

**3. Rare double-stall — both retry attempts time out.** We've seen this once in our regression testing. Real-world rate is unknown. When it happens you'll see `abstained=True, abstention_reason="timeout_600s"` on the Result. The trace records both attempts, but it may still not expose a provider-side root cause.

**4. Stream-decode-class failures are classified from provider stderr.** `provider_stream_error` means Teller saw provider/stream/decode signals and no answer file. `no_answer_file_written` means no answer file was produced without a provider signature. Send the trace either way.

**5. Treat `agreed=false` as a review signal, not a final fraud alarm.** Teller's XBRL cross-check is conservative and now skips cases where the comparison is not meaningful, but residual edge cases will remain. Before treating `agreed=false` as a real Teller-vs-company disagreement, verify three things: the answer is numeric, the company in your question matches the downloaded corpus, and the period in your question matches the period being validated. If any of those are off, send the log and Result JSON rather than relying on the disagreement flag alone.

## What we want back

One email, any length, when something surprises you. "Worked as expected on N questions" is also valuable data. We're not asking for a survey; we're asking for the ten minutes between when you notice something and when you forget you noticed.

## Contact

Leon Liu — leon@dolores.research
