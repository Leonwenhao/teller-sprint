---
name: teller
description: Use when a user wants an AI coding agent to install, run, debug, extend, or build on Teller, the self-hosted financial reasoning dev kit for SEC filings and Treasury-style corpus Q&A. Covers wheel install, doctor checks, SEC download/query flow, trace collection, result interpretation, and safe contribution workflows.
---

# Teller

Teller is a self-hosted financial reasoning dev kit. Treat v0.1 as SEC-first:
supported consolidated SEC metrics can be answered directly from XBRL-backed
facts; other paths may use goose plus an OpenRouter model and can have provider
latency or failures.

## Operating Rules

- Do not print or persist `OPENROUTER_API_KEY`.
- Prefer wheel/PyPI install for user validation; use editable install only for
  development inside the repo.
- Run `teller doctor` before live queries.
- Save traces and command output when debugging failures.
- Do not market `cost_usd` as billing telemetry. v0.1 reports `0.0`.
- Treat Treasury/general corpus Q&A as experimental unless local regression
  evidence says otherwise.

## Install And Verify

```bash
python3 -m venv .venv-teller
. .venv-teller/bin/activate
pip install --upgrade pip
pip install teller-agent

# macOS
brew install block-goose-cli

# Linux
curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash

export OPENROUTER_API_KEY=<your-openrouter-key>
teller doctor
teller --help
python -c "from teller import Agent, Corpus, Result; print('ok')"
```

If working from a cloned repo:

```bash
python -m build
python3 -m venv /tmp/teller-wheel-check
/tmp/teller-wheel-check/bin/python -m pip install dist/teller_agent-*.whl
/tmp/teller-wheel-check/bin/teller doctor
```

## First SEC Query

```bash
teller download-sec AAPL --latest 10-K
teller ask --domain sec_filings --corpus ./sec_data/AAPL \
  "What was Apple's revenue in fiscal year 2025?"
```

Expected shape for supported consolidated SEC metrics:

- `answer`: string value, usually integer millions for USD whole-dollar XBRL facts.
- `xbrl_validation.performed`: `True`.
- `xbrl_validation.agreed`: `True` when the returned value matches the tagged fact.
- `trace_path`: local JSON trace unless tracing is disabled.

Segment/product/geographic questions should abstain rather than guess:

```bash
teller ask --domain sec_filings --corpus ./sec_data/AAPL \
  "What were Apple's net sales in Greater China in fiscal year 2025?"
```

Expected abstention reason: `segment_level_dimensional`.

## Python API

```python
from teller import Agent, Corpus

agent = Agent(domain="sec_filings", corpus=Corpus("./sec_data/AAPL"))
result = agent.ask("What was Apple's revenue in fiscal year 2025?")

print(result.answer)
print(result.abstained, result.abstention_reason)
print(result.xbrl_validation)
print(result.trace_path)
```

## Trace Workflow

By default, traces are written to `.teller/traces/<trace_id>.json`.

Useful environment variables:

```bash
export TELLER_TRACE_DIR=./teller-traces
export TELLER_TRACE_DISABLED=1
```

For bug reports, collect:

```bash
teller doctor --json > doctor.json
teller ask --domain sec_filings --corpus ./sec_data/AAPL "..." 2>&1 | tee teller.log
```

Attach `doctor.json`, `teller.log`, and the trace JSON. Check first that no
secret appears in the artifacts.

## Result Interpretation

Primary fields:

- `answer`: the answer string, or `None` when abstained.
- `abstained`: whether Teller refused to answer.
- `abstention_reason`: named reason such as `segment_level_dimensional`,
  `timeout_600s`, `provider_stream_error`, or `no_answer_file_written`.
- `xbrl_validation`: SEC validation summary.
- `latency_ms`: end-to-end runtime.
- `trace_path`: local diagnostic file.
- `cost_usd`: reserved; not real billing telemetry in v0.1.

Multi-period SEC answers should be stable and labeled:

```text
2024: 4002814, 2025: 4424900
```

## Debugging Decision Tree

1. If `teller doctor` fails, fix the environment first.
2. If the query is SEC and asks for a supported consolidated metric, inspect
   `xbrl_validation` and trace metadata before changing prompts.
3. If `abstention_reason` is `segment_level_dimensional`, the question is asking
   for segment/product/geographic detail that v0.1 intentionally does not answer.
4. If `abstention_reason` is `provider_stream_error` or `timeout_600s`, preserve
   the trace and rerun once before changing code.
5. If there is no trace, check `TELLER_TRACE_DISABLED` and trace directory
   permissions.

## Contribution Workflow

For code changes:

```bash
python -m pytest
python scripts/release_check.py
python -m build
```

For SEC changes, also run:

```bash
OPENROUTER_API_KEY=dummy TELLER_TRACE_DISABLED=1 python scripts/gate_sec.py
```

A good contribution is narrow, tested, and code-true in docs. Common extension
areas: new SEC concept mappings, additional deterministic XBRL fast paths,
provider adapters, real cost telemetry, and new domain-specific corpora.
