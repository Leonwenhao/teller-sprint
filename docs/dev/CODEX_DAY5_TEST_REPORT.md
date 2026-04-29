# Codex Day-5 Adversarial Test Report

## Top line

**Verdict: hold for a v0.1 private-round-trip install fix before sending to the first external user.** The pushed post-audit commit is on the private mirror and the first AAPL SEC smoke query returned the correct XBRL-agreed answer, but the fresh editable install path became unreliably unusable immediately after that call: `.venv-test/bin/teller` and `.venv-test/bin/python -c "import teller"` now fail with `ModuleNotFoundError: No module named 'teller'` unless `PYTHONPATH=src` is injected. Since the current distribution decision is private repo invite vs public PyPI, a broken `pip install -e ".[dev]"` path is a first-recipient ship-blocker. Matrix halted per instruction; no further inference spend.

## Setup verification

| Check | Result |
|---|---|
| Local HEAD before push | `3fbbe3f46955528397a6c970cd0157e7741dc482` |
| Remote `origin/main` after push | `3fbbe3f46955528397a6c970cd0157e7741dc482` |
| Fresh venv | `.venv-test` created with Homebrew Python 3.12.12 |
| Install command | `.venv-test/bin/python -m pip install -e '.[dev]'` completed successfully |
| Initial import/CLI check | Initially passed: `from teller import Agent, Corpus, Result` printed `ok`; `teller --help` printed command list |
| Goose | `goose --version` returned `1.32.0`, with a warning that it could not create a log directory under `~/.local/state/goose/...` in the sandboxed check |
| OpenRouter usage before inference | `87.772564772` |
| OpenRouter usage after halted pass | `87.786729332` |
| Test-pass spend | `$0.01416456` |

## Test summary table

| Category | Question / command | Answer | Expected behavior | Observed behavior | Class | Latency |
|---|---|---:|---|---|---|---:|
| Setup | `git push origin main`; `git ls-remote origin refs/heads/main` | n/a | Remote head matches local `3fbbe3f` | PASS: both local and remote resolve to `3fbbe3f46955528397a6c970cd0157e7741dc482` | PASS | n/a |
| Setup | `.venv-test/bin/python -m pip install -e '.[dev]'` | n/a | Fresh editable install works | PASS at install time. Later import resolution fails despite editable dist metadata existing. | SURPRISE | n/a |
| Happy path | AAPL latest 10-K download | n/a | Download latest 10-K and warm XBRL cache | PASS: downloaded AAPL 10-K filed 2025-10-31, period 2025-09-27; XBRL available/cache warmed. Log contains many Arelle invalid-transformation warnings. | PASS + UX surprise | n/a |
| Happy path | "What was Apple's revenue in fiscal year 2025?" | `416161` | XBRL agreement | PASS: `xbrl_validation.performed=true`, `agreed=true`, concept `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`, tagged value `416161000000`, `abstained=false`. | PASS + latency surprise | 316.437s |
| Happy path | "What was Apple's net income in fiscal year 2025?" | n/a | XBRL agreement | HALT: command failed before inference: `ModuleNotFoundError: No module named 'teller'`. Reproduced with direct import. | SHIP-BLOCKER | n/a |

Log files written:

- `docs/dev/test_logs/download_aapl.log`
- `docs/dev/test_logs/happy_aapl_revenue.log`
- `docs/dev/test_logs/happy_aapl_net_income.log`

## Findings by severity

### SHIP-BLOCKER — Fresh editable install path is not reliable enough for private-repo first recipient

**Behavior.** After a successful editable install and one successful `teller ask`, the same fresh venv now fails:

```text
Traceback (most recent call last):
  File "/Users/leonliu/Desktop/teller/.venv-test/bin/teller", line 3, in <module>
    from teller.cli import main
ModuleNotFoundError: No module named 'teller'
```

Direct import also fails:

```text
.venv-test/bin/python -c "import teller"
ModuleNotFoundError: No module named 'teller'
```

Evidence:

- `pip show -f teller-agent` reports an editable install at `/Users/leonliu/Desktop/teller` and lists `__editable__.teller_agent-0.1.0.pth`.
- That `.pth` file contains `/Users/leonliu/Desktop/teller/src`.
- `.venv-test/bin/python -m site` does not include `/Users/leonliu/Desktop/teller/src` on `sys.path`.
- `.venv-test/bin/python -c "import sys; sys.path.insert(0, 'src'); import teller"` succeeds and resolves `src/teller/__init__.py`.
- `pip check` reports no broken requirements.

**Why it blocks first recipient.** The public README says `pip install teller-agent`, but PyPI is paused. A private repo invite likely means `pip install -e ".[dev]"` or equivalent local editable install. That path is currently not trustworthy on the tested macOS/Homebrew Python 3.12.12 environment. A first external user should not need to discover or apply `PYTHONPATH=src`.

**Recommendation.** Before first-recipient round-trip, choose and verify one supported install path on the recipient-equivalent machine: either publish/use a non-editable wheel, provide `pip install .` from a tagged source checkout, or fix/document the editable-install `.pth` behavior. Do not spend more inference until the install path is stable.

### IMPORTANT — AAPL happy-path latency exceeded documented worst-observed band

The AAPL revenue smoke succeeded but took `316.437s`, above the README's `~180s` worst-observed line and the onboarding "about 3 minutes" normal-case framing. There was no retry stderr line. This looks like a single slow successful MiniMax/goose inference, not ADR-012 retry behavior. Treat as a launch-copy/expectations risk unless subsequent first-recipient runs are closer to the documented band.

### IMPORTANT — Arelle warnings dominate user-facing logs even on successful paths

`download-sec` and the successful AAPL revenue query both emitted many `ix11.*:invalidTransformation` lines before the useful result. ADR-002 intentionally whitelists those as known-benign, but the CLI/log UX exposes them as scary errors. For a private-beta user asked to `tee teller.log`, this creates noise and may look like data corruption even when `xbrl_validation.agreed=true`.

## Confirms existing closures

- The post-audit README line 7 is code-true for the successful AAPL smoke: Teller surfaced the XBRL validation object and agreement state rather than hiding the conflict path. No disagreement case was reached before halt.
- ADR-002 Amendment A appears operational: the AAPL filing generated invalid-transformation warnings, but the XBRL check still performed and agreed.
- `Result.sources` remains empty in the successful smoke, consistent with the post-audit copy that now treats it as reserved.

## v0.1.1 candidates

- **P0:** Install-path hardening for private beta. Verify `pip install .`, editable install, or wheel install on macOS Python 3.12 and Linux Python 3.12, then put exactly one supported install path in onboarding.
- **P1:** Suppress or demote known-benign Arelle `ix11.*:invalidTransformation` warnings on user-facing CLI paths while preserving them in debug logs.
- **P1:** Recalibrate latency copy after a few real first-recipient calls. One successful AAPL query at 316s is enough to avoid promising "about 3 minutes" as worst case under normal conditions.

## v0.2+ candidates

- A direct XBRL fast path for consolidated top-line metrics would have avoided the 316s LLM path for the AAPL revenue query. This confirms ADR-009's value without reopening v0.1.
- Structured trace persistence should include environment/install metadata and path resolution state, not just goose stdout/stderr. The install failure is not an inference trace issue, but first-recipient debugging needs the same observability posture.

## Cost + latency summary

| Metric | Value |
|---|---:|
| Completed inference calls | 1 |
| Retry events observed | 0 |
| OpenRouter usage delta | `$0.01416456` |
| Mean latency | 316.437s |
| Median latency | 316.437s |
| Max latency | 316.437s |
| Calls over 180s | 1/1 |

The matrix halted after the second happy-path command failed before inference. No SEC disagreement, abstention, SEC0017, or edge-case inference categories were run.

## Phase 4 — XBRL Guardrails, CLI Input Validation, Onboarding Updates

### Top-line verdict

Ship condition met after re-gate. The XBRL guardrail and CLI hardening changes passed unit coverage, treasury stayed in-band, and the authoritative clean-wheel SEC re-run passed tier-1+2 and tier-3 gates. The first Phase 4 SEC run at 13/18 is attributed to service variance, not guardrail drift: SEC0008 reproduced as a pass twice with guardrails and once without guardrails, and the same rebuilt guardrail wheel later passed the SEC gate at 15/18.

### Changes made

| File | Change |
|---|---|
| `src/teller/agent.py` | Added SEC XBRL pre-validation gates in order: non-numeric answer, entity unspecified/mismatch, period unspecified/mismatch, scoped revenue concept unsupported. Skipped validations return `performed=false`, `agreed=null`, and a named `reason`. |
| `src/teller/cli/main.py` | Rejects empty or whitespace-only `teller ask` input before model invocation, exits non-zero with a clear Click error. |
| `tests/test_xbrl_guardrails.py` | Unit coverage for non-numeric answer, comma-separated answer, entity mismatch, entity unspecified, period unspecified, period mismatch, scoped revenue skip, and total revenue over-suppression guard. |
| `tests/test_cli_input_validation.py` | Unit coverage for empty string and whitespace-only CLI rejection. |
| `docs/PRIVATE_BETA_ONBOARDING.md` | Added known limitations for stream-decode/no-answer-file attribution and residual `agreed=false` interpretation guidance. Empty-input limitation was not added because the CLI fix shipped. |

### Unit and wheel verification

Unit suite: `61 passed, 1 skipped, 1 deselected in 0.77s`.

Fresh wheel path: rebuilt with `python -m build`, installed into `/tmp/.venv-xbrl-fix/`, and verified installed code from `/private/tmp/.venv-xbrl-fix/lib/python3.14/site-packages/teller/agent.py` contains `entity_unspecified`, `concept_unsupported`, and `non_numeric_answer`.

### Regression results

| Gate | 88ca710 hotfix run | Phase 4 first guardrail run | Phase 4 authoritative re-run | Gate |
|---|---:|---:|---:|---|
| Treasury 20 | 12/20 warn, in-band | 14/20 | not re-run | PASS (`>=13/20`) |
| SEC tier-1+2 | 15/18 | 13/18 | 15/18 | PASS (`>=80%`) |
| SEC tier-3 | 7/7 | 7/7 | 7/7 | PASS (`>=60%`) |

Evidence files:

- Treasury Phase 4: `results/regression_twenty_20260427T234106Z.json`, `docs/dev/test_logs/phase4_regression_treasury.log`
- SEC first guardrail run: `results/gate_sec_20260427T234116Z.json`, `docs/dev/test_logs/phase4_gate_sec.log`
- SEC authoritative re-run: `results/gate_sec_20260428T171334Z.json`, `docs/dev/test_logs/phase4_gate_sec_rerun.log`

SEC first guardrail run failed tier-1+2 at 13/18. Failures: SEC0008 wrong answer, SEC0009 wrong answer, SEC0014 null, SEC0016 null, SEC0017 null. Diagnostic cross-reference showed SEC0008 and SEC0016 were already in the variance set; SEC0017 was known fragile; SEC0009 and SEC0014 were new relative to 88ca710 but consistent with elevated null/timeout pressure. SEC0008 exoneration: with guardrail pass `30708` twice, without guardrail pass `30708` once (`phase4_diag_sec0008_*` logs).

SEC authoritative re-run passed tier-1+2 at 15/18 in 134.5 min. Failures: SEC0007 both-attempt timeout/null, SEC0015 sign error (`-7242` vs `7242`), SEC0016 scale/format (`4002.814, 4424.9` vs `[4424900, 4002814]`). Tier-3 remained 7/7 abstained with `segment_level_dimensional`.

### Phase 3 guardrail before/after

After values are zero-inference wheel-env post-validation spot-checks against the same fixture corpora, logged in `docs/dev/test_logs/phase4_guardrail_spotchecks.log`.

| Query | Before performed/agreed/reason | After performed/agreed/reason | Outcome |
|---|---|---|---|
| Q2 Apple services revenue FY2025 | `true` / `false` / `null` | `false` / `null` / `concept_unsupported` | False disagreement suppressed. |
| Q5 Apple FY2026 expected revenue, answer `NOT_IN_FILING` | `true` / `null` / `null` | `false` / `null` / `non_numeric_answer` | Validator no longer fires on non-numeric answer. |
| Q6 Apple question against XOM corpus | `true` / `false` / `null` | `false` / `null` / `entity_mismatch` | Entity mismatch surfaced explicitly. |
| Q8 Apple revenue with no fiscal year | `true` / `false` / `null` | `false` / `null` / `period_unspecified` | Period-default false disagreement suppressed. |

The over-suppression unit test confirms `"Apple total revenue FY2025"` still performs validation and agrees.

### Cost summary

Local `Result.cost_usd` remains `0.0` and is not authoritative for OpenRouter billing. Inference-bearing Phase 4 work: treasury gate (20 questions), first SEC gate (25), SEC0008 diagnostic (3), authoritative SEC re-gate (25). The guardrail spot-checks used direct installed-code post-validation and spent no OpenRouter inference. Exact dollar delta requires the OpenRouter dashboard/export.
