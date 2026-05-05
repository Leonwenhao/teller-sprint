# Teller Dev Kit

Company demo deck source. Public framing: developer preview, SEC-first,
self-hosted, traceable financial reasoning.

---

## 1. Teller

**Traceable financial Q&A agents, starting with SEC filings.**

- Self-hosted Python package and CLI
- Deterministic XBRL-backed answers for supported SEC metrics
- LLM fallback paths with local traces for debugging
- Built for developers to inspect, extend, and build on

Speaker note: Position Teller as a dev kit, not a finished hosted product. The
core idea is that financial agents need audit surfaces, not just fluent answers.

---

## 2. The Problem

Financial Q&A agents fail in ways that are hard to trust.

- Answers often lack verifiable grounding
- Provider failures look like product failures
- Segment, period, and unit mistakes are easy to miss
- Internal teams need a way to debug and extend behavior

Speaker note: The market does not need another black-box chatbot for filings.
It needs repeatable machinery for answering, abstaining, and explaining why.

---

## 3. The Product

Teller is a financial reasoning dev kit.

- `teller-agent` package
- `teller` terminal tool
- SEC downloader and local corpus format
- Result object with answer, abstention, XBRL validation, latency, and trace
- Installable agent skill for Codex, Claude Code, Hermes, and similar tools

Speaker note: The product surface is intentionally small. Developers should be
able to install it, run one SEC question, inspect the trace, and understand the
system in minutes.

---

## 4. How It Works

SEC-first pipeline:

1. Download a 10-K or 10-Q from EDGAR
2. Parse local inline XBRL facts offline
3. Answer supported consolidated metrics directly from tagged facts
4. Abstain on unsupported segment/product/geographic questions
5. Use LLM fallback where deterministic paths do not apply

Speaker note: The important shift is moving common SEC questions out of the
model path. The LLM is no longer responsible for every answer.

---

## 5. Why XBRL Matters

XBRL gives Teller an audit layer.

- Company-reported tagged facts are available locally
- Units, periods, concepts, and contexts can be inspected
- Supported answers can be cross-checked or produced directly
- Disagreements and abstentions become explicit states

Speaker note: XBRL is not just a parser detail. It is the reason Teller can make
stronger claims than a retrieval-only filing assistant.

---

## 6. What Changed Recently

The product became launchable as a dev kit.

- SEC consolidated metrics now run in seconds through a fast path
- Multi-period answers are stable: `YEAR: value`
- Segment questions abstain deterministically
- Provider failures are classified and retried once
- Clear stdout answers can be recovered when goose misses `answer.txt`
- Every run has local trace diagnostics by default

Speaker note: This is the sanity-check slide. The system moved from "interesting
agent prototype" toward "useful developer substrate."

---

## 7. Developer Experience

The happy path is short.

```bash
pip install teller-agent
teller doctor
teller download-sec AAPL --latest 10-K
teller ask --domain sec_filings --corpus ./sec_data/AAPL \
  "What was Apple's revenue in fiscal year 2025?"
```

The answer includes a trace path and XBRL validation summary.

Speaker note: This is the onboarding promise. The first user should not need to
read the codebase to get value.

---

## 8. What Users Can Build

Teller is a base layer, not just a demo.

- Filing analysis workflows
- Analyst notebooks and dashboards
- Agent skills for finance teams
- New XBRL concept families and SEC question types
- Provider/model comparisons
- Support bundles and observability for financial agents

Speaker note: GTM can talk about adoption through builders: analysts,
engineers, and AI-agent teams who want a transparent starting point.

---

## 9. Honest Boundaries

Developer preview means clear limits.

- SEC-first, not universal financial Q&A
- Fast path covers mapped consolidated metrics
- Treasury/general corpus Q&A remains experimental
- `cost_usd` is not real billing telemetry in v0.1
- No hosted API in this launch

Speaker note: This slide prevents overclaiming. It also makes the project more
credible because the boundaries are specific.

---

## 10. The Launch Narrative

Public developer preview.

- Open the repo and package for builders
- Lead with SEC/XBRL traceability
- Invite contributions around coverage, adapters, and telemetry
- Use the dev kit to learn which workflows deserve a hosted product

**Thesis:** financial agents become useful when they can prove, abstain, and
leave a trace.

Speaker note: This is the first public story. Teller is the wedge for
trustworthy financial agents, starting where the data already has structure.
