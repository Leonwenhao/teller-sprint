# Teller Production Runbook

## Install

Use the wheel/PyPI package path as the production path:

```bash
pip install teller-agent
brew install block-goose-cli
export OPENROUTER_API_KEY=<your-openrouter-key>
teller doctor
```

`teller doctor` must pass before live queries. It verifies Python, package
import, packaged recipes, goose, the OpenRouter key, and trace-directory
writability.

## First Query

```bash
teller download-sec AAPL --latest 10-K
teller ask --corpus ./sec_data/AAPL --domain sec_filings \
  "What was Apple's revenue in fiscal year 2025?"
```

For Treasury:

```bash
teller ask --corpus ./tests/fixtures/treasury_bulletins --domain treasury \
  "What were federal VA expenditures in FY 1934?"
```

## Traces

Every `Agent.ask()` call writes `.teller/traces/<trace_id>.json` unless
`TELLER_TRACE_DISABLED=1` is set. Use `TELLER_TRACE_DIR=/path/to/traces` to
store traces elsewhere.

Traces include per-attempt subprocess diagnostics, latency, result summary,
model config, package version, Python version, goose path/version, and XBRL
validation summary. They must not include `OPENROUTER_API_KEY`.

When reporting failures, include:

- the trace JSON file.
- the command used.
- stdout/stderr captured with `2>&1 | tee teller.log`.
- `teller doctor --json` output.

## Failure Modes

- `timeout_600s`: one or both model attempts timed out.
- `provider_stream_error`: provider/stream/decode signature appeared and no answer file was written.
- `goose_nonzero_exit`: goose exited non-zero and no answer file was written.
- `no_answer_file_written`: goose exited without an answer file and without provider-error signatures.
- `empty_answer_file`: answer file existed but was empty.
- XBRL `reason`: `non_numeric_answer`, `entity_mismatch`, `period_mismatch`, `concept_unsupported`, `xbrl_instance_not_found`, `xbrl_taxonomy_uncached`, or `xbrl_unreadable`.

## Release Checks

Non-live:

```bash
python -m build
python scripts/release_check.py
```

Wheel-path:

```bash
python3.12 -m venv /tmp/teller-wheel-ga
/tmp/teller-wheel-ga/bin/python -m pip install dist/teller_agent-*.whl
/tmp/teller-wheel-ga/bin/teller --help
/tmp/teller-wheel-ga/bin/teller doctor
/tmp/teller-wheel-ga/bin/python -c "from teller import Agent, Corpus, Result; print('ok')"
```

Live gates require `OPENROUTER_API_KEY` and must save logs under
`docs/dev/test_logs/` or `results/`.
