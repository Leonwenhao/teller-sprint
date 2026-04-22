# Teller

Grounded reasoning agent for SEC filings and U.S. Treasury bulletins. MIT-licensed.

[![Sentient Arena Cohort 0 — highest accuracy on OfficeQA (71.5%)](https://img.shields.io/badge/Sentient_Arena_Cohort_0-71.5%25_on_OfficeQA_%7C_highest_accuracy-blue)](docs/research/final_report.md)

**Teller cross-checks every answer against what the company reported to the SEC in XBRL. When the two disagree, Teller abstains and shows both.** The tool is built to distinguish questions it can answer from questions it can't — not to confirm that the LLM guessed right.

v0.1 does two domains: **SEC filings** (10-K / 10-Q with XBRL cross-check) and **U.S. Treasury Bulletins** (1939–present). Default model is MiniMax M2.5 via OpenRouter; one-line swap to any other OpenRouter-served model.

---

## Install

Requires Python 3.10+ (tested on 3.12). Goose is a prerequisite — Teller runs the model through it.

```bash
# macOS
brew install block-goose-cli
# Linux
curl -fsSL https://github.com/block/goose/releases/download/stable/download_cli.sh | bash

pip install teller-agent
export OPENROUTER_API_KEY=sk-or-v1-...    # https://openrouter.ai/keys
```

Verify:

```bash
teller --help
python -c "from teller import Agent, Corpus, Result; print('ok')"
```

## Quickstart — SEC filing with XBRL cross-check

```bash
teller download-sec AAPL --latest 10-K    # caches to ./sec_data/AAPL/
```

```python
from teller import Agent, Corpus

agent = Agent(domain="sec_filings", corpus=Corpus("./sec_data/AAPL"))
result = agent.ask("What was Apple's revenue in fiscal year 2025?")

print(result.answer)                        # e.g. "416161"
print(result.xbrl_validation.agreed)        # True / False / None
print(result.xbrl_validation.tagged_value)  # the company's own XBRL-reported value
```

If the extracted number and the XBRL-tagged value agree within tolerance, `agreed=True`. If they disagree, `agreed=False` and both values are surfaced. If the question isn't answerable from the XBRL facts available (e.g., a segment breakdown not tagged at that granularity), Teller sets `abstained=True` with a named `abstention_reason` — it does not guess.

## Quickstart — Treasury Bulletin

```python
from teller import Agent, Corpus

agent = Agent(domain="treasury", corpus=Corpus("./tests/fixtures/treasury_bulletins"))
result = agent.ask("What were federal VA expenditures in FY 1934?")

print(result.answer)      # e.g. "507"
print(result.latency_ms)
```

## What you get back

Every call returns a `Result`:

- `answer` — the extracted value (string-typed to preserve format).
- `abstained`, `abstention_reason` — set when the agent determined the question was not answerable from available evidence.
- `xbrl_validation` — SEC domain only. Fields: `performed`, `agreed`, `tagged_value`, `reason`. For non-SEC calls, `performed=False`.
- `latency_ms` — end-to-end, inclusive of any retry.
- `sources` — page-level citations to source documents.

## Empirical characteristics

**Latency.** Measured on MiniMax M2.5 + goose against real iXBRL 10-Ks:

| Case | Time |
|---|---|
| Typical end-to-end | 60–120 s |
| Worst case observed | ~180 s (1.5 MB 10-K) |
| Download phase (10-K + XBRL files) | ~5 s |
| XBRL validation leg | ~200 ms |

Under two minutes typical, about three minutes worst case. LLM + harness latency dominates; the XBRL leg itself is negligible.

**Accuracy.** Single-run results, honestly reported:

- **Treasury:** 13/20 on the ADR-004 honest baseline (stratified 20-question set). Single-run variance on MiniMax M2.5 is ±2 passes and is documented in `docs/dev/ARCHITECTURE_DECISIONS.md` (ADR-004). A 15/20 run on day 4 sits within that band; 13/20 is the number we ship against.
- **SEC:** 17/18 on tier-1+2 (94.4%) and 7/7 on tier-3 abstention with strict reason-code matching, in a single day-4 gate run. This is one run, not a high-water mark. The documented gate is ≥80% tier-1+2 and ≥60% tier-3.

**Retry-on-timeout.** Teller retries once on subprocess timeout (ADR-012). In day-4 regression, 2 of 45 inferences (4.4%) triggered a retry; both recovered. *Retry eliminates tail-latency failures that would be visibly flaky; accuracy is within measurement variance of prior runs.* Retry is a latency tax, not an accuracy lift.

## Known v0.1 limitations

**1. Multi-year list answers come back in reporting order, not question order.** For "total assets at the end of each of fiscal years 2024 and 2025," Teller emits values in the order the filing reports them (typically latest-year-first), which is the opposite of natural English order. Both values are correct; ordering may surprise a downstream parser. Fix committed for v0.1.1: labeled-list answer format (`2024: 448980, 2025: 453475`). **v0.1.1 calendar: within 10 days of the v0.1 tag.**

**2. Rare double-stall.** Observed once in regression; real-world rate unknown. The `Result` surfaces `abstained=True, abstention_reason="timeout_600s"`. We cannot yet tell you *why* it stalled. Reasoning-trace persistence (ADR-011) is the first v0.1.1 item.

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

- **v0.1 (now):** two domains, XBRL cross-check, retry-on-timeout, MiniMax M2.5 default.
- **v0.1.1 (≤10 days from v0.1 tag):** reasoning-trace persistence (ADR-011); labeled-list answer format (SEC0017 fix).
- **v0.2 (~2 weeks, user-driven):** shape set by first-wave feedback. Candidates include a sub-5 s XBRL-only fast path (ADR-009) and comparative accuracy on alternative models.
- **v0.3:** a second vertical. Candidates include earnings-call transcripts and proxy / DEF 14A filings; picked based on who asks.
- **v0.4:** hosted waitlist opens. Self-host remains the supported path.

## Evidence

The upstream methodology — how the default MiniMax M2.5 configuration was tuned — is documented separately. Sentient Arena Cohort 0 result: **highest accuracy in the competition on the 246-question OfficeQA benchmark (71.5%, 176/246 correct)**, MiniMax M2.5 via goose. Full report: `docs/research/final_report.md`.

Neither the Arena credential nor Teller alone carries the full argument. The pair is the claim that the performance gap on grounded enterprise reasoning is behavioral, not capability-based.

## Project structure

```
src/teller/         # package
prompts/            # Jinja templates (base + domain overlays)
recipes/            # rendered goose recipes
examples/           # minimal scripts for each domain
docs/research/      # Arena methodology + final report
docs/dev/           # ADRs, sprint notes, retrospectives
tests/              # unit suite (pytest)
```

## License

MIT, see `LICENSE`. Bundled dependencies retain their own licenses; see `NOTICE`.

## Contact

Leon Liu — leon@dolores.research
GitHub issues welcome. Private beta feedback: email directly.
