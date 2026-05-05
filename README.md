# Teller

Self-hosted financial reasoning dev kit for building traceable SEC filing
agents. MIT-licensed.

[![Sentient Arena Cohort 0 — highest accuracy on OfficeQA (71.5%)](https://img.shields.io/badge/Sentient_Arena_Cohort_0-71.5%25_on_OfficeQA_%7C_highest_accuracy-blue)](docs/research/final_report.md)

**Teller v0.1 is a public developer preview.** It is SEC-first: supported
consolidated filing questions can be answered directly from company-reported
XBRL facts, while unsupported segment/product/geographic questions abstain
instead of guessing. LLM-backed paths remain available for experimentation and
write local traces so failures are debuggable.

Use Teller as a CLI, a Python package, or an installable skill for coding
agents such as Codex, Claude Code, Hermes, and similar tools.

Teller originated from **Sentient Arena Cohort 0**, where its default agent
strategy won the OfficeQA benchmark track. The repo now includes an
**EvoSkill-compatible integration** so builders can use Sentient's EvoSkill loop
to evolve Teller agent skills from real financial-QA failures.

v0.1 includes:

- **SEC filings**: 10-K / 10-Q download, local XBRL parsing, deterministic
  answers for mapped consolidated metrics, stable multi-year output, and named
  abstentions for unsupported segment questions.
- **Experimental corpus Q&A**: Treasury-style document Q&A through goose plus an
  OpenRouter model. This path is useful for development, but still has provider
  latency and variance.
- **Developer observability**: `teller doctor`, local JSON traces, named failure
  classes, and a small `Result` object for notebooks or downstream tools.
- **Sentient ecosystem path**: an EvoSkill example that evolves Teller skills
  across Claude Code, Codex, OpenCode, OpenHands, Goose, and other supported
  agent runtimes.

---

## Install

Requires Python 3.10+ (tested on 3.12). Goose is needed for LLM fallback paths.
The SEC XBRL fast path can answer supported filing questions without invoking a
provider, but `teller doctor` expects the full local runtime for live use.

```bash
# macOS
brew install block-goose-cli
# Linux
curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash

pip install teller-agent
export OPENROUTER_API_KEY=<your-openrouter-key>    # https://openrouter.ai/keys
```

Verify:

```bash
teller --help
teller doctor
python -c "from teller import Agent, Corpus, Result; print('ok')"
```

## Quickstart — SEC filing

```bash
teller download-sec AAPL --latest 10-K    # caches to ./sec_data/AAPL/
teller ask --domain sec_filings --corpus ./sec_data/AAPL \
  "What was Apple's revenue in fiscal year 2025?"
```

```python
from teller import Agent, Corpus

agent = Agent(domain="sec_filings", corpus=Corpus("./sec_data/AAPL"))
result = agent.ask("What was Apple's revenue in fiscal year 2025?")

print(result.answer)                        # e.g. "416161"
print(result.xbrl_validation.agreed)        # True / False / None
print(result.xbrl_validation.tagged_value)  # the company's own XBRL-reported value
print(result.trace_path)                    # local JSON trace for debugging
```

For supported consolidated SEC metrics, Teller can answer from tagged XBRL facts
directly and set `xbrl_validation.agreed=True`. If the question asks for a
segment/product/geographic breakdown that v0.1 does not support, Teller returns
`abstained=True` with `abstention_reason="segment_level_dimensional"` instead
of inventing a value.

Multi-period SEC answers are labeled for downstream parsing:

```text
2024: 4002814, 2025: 4424900
```

## Use Teller As An Agent Skill

The repo includes an installable skill for coding agents:

- [skills/teller/SKILL.md](skills/teller/SKILL.md)

For Codex-style local skills:

```bash
mkdir -p ~/.codex/skills
cp -R skills/teller ~/.codex/skills/teller
```

For project-local use, keep `skills/teller/SKILL.md` in the repo and tell your
agent:

```text
Use the Teller skill at skills/teller/SKILL.md to install, run, debug, or extend Teller.
```

For Claude Code, Hermes, or another skill-aware agent, copy the `skills/teller`
folder into that agent's configured skills directory. The skill teaches the
agent the safe install flow, `teller doctor`, SEC first query, trace collection,
result interpretation, and contribution checks.

## Evolve Teller Skills With EvoSkill

Teller includes a first-class
[EvoSkill](https://github.com/sentient-agi/EvoSkill) example:

- [examples/evoskill_teller/](examples/evoskill_teller/)

EvoSkill is Sentient's toolkit for automatically discovering and improving
agent skills from benchmark failures. Teller uses it as an ecosystem integration,
not a runtime dependency: the core `teller-agent` package stays small and
deterministic, while EvoSkill can evolve the surrounding agent workflows.

```bash
cd examples/evoskill_teller
bash setup.sh

# Claude Code path
export ANTHROPIC_API_KEY=<your-anthropic-key>
evoskill run --verbose

# OpenRouter path
export OPENROUTER_API_KEY=<your-openrouter-key>
evoskill run --verbose --config .evoskill/config.openrouter.toml
```

Use this path to improve Teller's install flow, SEC/Treasury question
classification, trace handling, stable answer formatting, and abstention
discipline. Good EvoSkill discoveries should be ported back into
[skills/teller/SKILL.md](skills/teller/SKILL.md).

## Experimental — Treasury Bulletin

```python
from teller import Agent, Corpus

agent = Agent(domain="treasury", corpus=Corpus("./tests/fixtures/treasury_bulletins"))
result = agent.ask("What were federal VA expenditures in FY 1934?")

print(result.answer)      # e.g. "507"
print(result.latency_ms)
```

Treasury/general corpus Q&A is included for builders to inspect and improve, but
it is not the primary v0.1 launch promise. Expect provider latency and variance
on this path.

## What you get back

Every call returns a `Result`:

- `answer` — the extracted value (string-typed to preserve format).
- `abstained`, `abstention_reason` — set when the agent determined the question was not answerable from available evidence.
- `xbrl_validation` — SEC domain only. Fields: `performed`, `agreed`, `tagged_value`, `reason`. For non-SEC calls, `performed=False`.
- `latency_ms` — end-to-end, inclusive of any retry.
- `sources` — reserved citation field; v0.1 carries the auditable tagged fact via `xbrl_validation` for supported SEC metrics.
- `trace_id`, `trace_path` — local diagnostics for each `Agent.ask()` call. Set `TELLER_TRACE_DIR` to choose the directory, or `TELLER_TRACE_DISABLED=1` to disable local trace files. Traces do not persist `OPENROUTER_API_KEY`.
- `cost_usd` — reserved for future billing integration. v0.1 reports `0.0`; use OpenRouter billing for authoritative cost.

## Empirical characteristics

**Latency.** Recent SEC fast-path measurements against the fixture gate answer
supported consolidated metrics in roughly 1-3 seconds per question on a local
Mac. Segment abstentions are near-instant. LLM fallback paths remain dominated
by goose/provider latency and can take minutes.

| Case | Time |
|---|---|
| Supported SEC XBRL fast path | ~1-3 s |
| SEC segment abstention | <1 s |
| Download phase (10-K + XBRL files) | ~5 s in prior smoke runs |
| LLM fallback path | provider-dependent; minutes are possible |

The core v0.1 launch path is SEC-first because it avoids provider latency for
mapped consolidated metrics.

**Accuracy.** Single-run results, honestly reported:

- **SEC:** the current SEC fixture gate passes through deterministic fast paths:
  18/18 tier-1+2 and 7/7 tier-3 abstention in the latest local validation.
- **Treasury:** prior live regression passed the project threshold, but this
  remains an experimental LLM-backed path for v0.1 developer-preview users.

**Provider failures.** Teller classifies provider/stream failures, retries once
on provider-class failures, and records the evidence in the trace. This improves
debuggability; it is not a guarantee that provider-backed answers will always
recover.

## Operations

Run `teller doctor` before the first live query. It checks Python, package data, goose, `OPENROUTER_API_KEY`, and trace-directory writability.

Every `Agent.ask()` writes a local JSON trace by default. On abnormal CLI results, Teller prints the trace path. Include that trace when reporting failures.

## Known v0.1 limitations

**1. Developer preview, not hosted GA.** v0.1 is a self-hosted dev kit. There is
no hosted API or SLA.

**2. SEC fast path is intentionally scoped.** It covers mapped consolidated
metrics. Segment/product/geographic questions abstain unless a future
contribution adds audited support.

**3. Treasury/general corpus Q&A is experimental.** It uses the LLM fallback path
and can have provider latency, timeouts, or answer variance.

**4. `cost_usd` is not billing telemetry.** v0.1 reports `0.0`; use provider
billing dashboards for authoritative cost.

See `docs/PRIVATE_BETA_ONBOARDING.md` for the full known-issue list and `docs/dev/ARCHITECTURE_DECISIONS.md` for the decision log.

## Swap the model

Defaults live in `src/teller/config.py`. To swap at call time:

```python
from teller import Agent, Corpus
from teller.config import CLAUDE_SONNET_4_5

agent = Agent(
    domain="sec_filings",
    corpus=Corpus("./sec_data/AAPL"),
    model=CLAUDE_SONNET_4_5,
)
```

Built-in configs: `MINIMAX_M2_5` (default), `CLAUDE_SONNET_4_5`, `GPT_4_1_MINI`. Add your own `ModelConfig` for any OpenRouter-served model. For compliance-sensitive deployments that cannot use MiniMax, this is the swap point.

No regression evidence yet on non-default models; v0.2 will publish comparative accuracy for at least one alternative.

## Roadmap

- **v0.1 (now):** public developer preview, SEC XBRL fast path, trace
  persistence, agent skill, CLI/Python package.
- **v0.2:** shape set by first-wave builder feedback. Candidates include broader
  SEC concept-family coverage, real cost telemetry, more provider adapters, and
  comparative model evidence.
- **v0.3:** a second vertical. Candidates include earnings-call transcripts and proxy / DEF 14A filings; picked based on who asks.
- **Hosted product:** out of scope for v0.1. Self-host remains the supported path.

## Evidence

The upstream methodology — how the default MiniMax M2.5 configuration was tuned — is documented separately. Sentient Arena Cohort 0 result: **highest accuracy in the competition on the 246-question OfficeQA benchmark (71.5%, 176/246 correct)**, MiniMax M2.5 via goose. Full report: `docs/research/final_report.md`.

Neither the Arena credential nor Teller alone carries the full argument. The pair is the claim that the performance gap on grounded enterprise reasoning is behavioral, not capability-based.

## Project structure

```
src/teller/           # package
src/teller/prompts/   # Jinja templates (base + domain overlays), shipped with the wheel
src/teller/recipes/   # rendered goose recipes, shipped with the wheel
examples/             # minimal scripts for each domain
examples/evoskill_teller/ # Sentient EvoSkill integration for evolving Teller skills
docs/research/        # Arena methodology + final report
docs/dev/             # ADRs, sprint notes, retrospectives
docs/pitch/           # concise product overview deck
skills/teller/        # installable agent skill
tests/                # unit suite (pytest)
```

## License

MIT, see `LICENSE`. Bundled dependencies retain their own licenses; see `NOTICE`.

## Contact

Leon Liu — leon@dolores.research
GitHub issues and contributions welcome.
