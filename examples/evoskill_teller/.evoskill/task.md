# Task

Use Teller to answer or classify financial QA tasks.

Teller is available as a self-hosted CLI/Python package for SEC filing Q&A and
experimental Treasury-style corpus Q&A. Prefer Teller's deterministic SEC/XBRL
behavior whenever the question is about a supported consolidated SEC metric.

## Expected workflow

1. Inspect the question and classify it as SEC consolidated, SEC segment/product/
   geography, Treasury/general corpus, or unsupported.
2. For SEC questions, use Teller commands or the Python API against the local or
   downloaded SEC corpus.
3. Check `Result.xbrl_validation`, `Result.abstained`,
   `Result.abstention_reason`, and `Result.trace_path`.
4. If Teller abstains, preserve the abstention reason rather than guessing.
5. Return only the expected answer string or named abstention reason.

## Output format

Return only one of:

- the answer value, such as `416161`.
- a labeled multi-period answer, such as `2024: 4002814, 2025: 4424900`.
- a named abstention reason, such as `segment_level_dimensional`.

---

# Constraints

- Do not reveal or persist API keys.
- Do not claim `cost_usd` is real billing telemetry.
- Do not answer SEC segment/product/geographic questions by guessing.
- Prefer trace inspection over prompt changes when debugging failures.
- Keep generated Teller skills concise, installable, and code-true.
