---
name: teller
description: Use Teller to answer, classify, debug, and improve SEC-first financial QA workflows. Prefer deterministic XBRL-backed answers for supported consolidated SEC metrics, preserve named abstentions, and collect traces for failures.
---

# Teller

Teller is a self-hosted financial reasoning dev kit. v0.1 is SEC-first:
supported consolidated SEC metrics can be answered from company-reported XBRL
facts, while unsupported segment/product/geographic questions abstain.

## Core Workflow

1. Run `teller doctor` before live queries.
2. For SEC questions, use `teller download-sec <TICKER> --latest 10-K` when the
   corpus is not already present.
3. Ask with `teller ask --domain sec_filings --corpus <path> "<question>"` or
   use the Python API.
4. Inspect `answer`, `abstained`, `abstention_reason`, `xbrl_validation`, and
   `trace_path`.
5. Return only the requested answer or named abstention reason.

## SEC Rules

- Supported consolidated SEC metrics should use Teller's XBRL fast path.
- Multi-period SEC answers must be labeled: `YEAR: value, YEAR: value`.
- Segment/product/geographic questions must not be guessed. Preserve
  `segment_level_dimensional`.
- If `xbrl_validation.agreed=True`, the public answer matches the tagged fact
  within Teller's tolerance.

## Debugging

- Preserve `trace_path` for any abnormal result.
- Do not expose API keys.
- Do not claim `cost_usd` is billing telemetry. In v0.1 it is reserved and
  reports `0.0`.
- Treat Treasury/general corpus Q&A as experimental and provider-dependent.

## Good Skill Changes

When EvoSkill proposes edits, prefer instructions that improve:

- install and `doctor` flow.
- SEC/Treasury question classification.
- trace collection and failure diagnosis.
- stable answer formatting.
- abstention discipline.

Avoid edits that:

- weaken SEC abstention behavior.
- tell the agent to guess missing segment values.
- add broad prompt rules unrelated to observed failures.
- claim production/GA reliability.
