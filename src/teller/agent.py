"""Agent — the public entry point for asking grounded questions against a corpus."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from importlib.resources import files as _resource_files
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from teller.config import DEFAULT_MODEL, ModelConfig
from teller.result import Result, XBRLValidation

if TYPE_CHECKING:
    from teller.corpus import Corpus


# v0.1 keyword → candidate GAAP concept map for SEC XBRL cross-check.
# Tried in order; first available fact wins. This is a narrow heuristic
# sized for the day-2 Apple smoke test and Tier-1 direct-line-item
# questions in the day-3 SEC test set. Cross-period concept
# normalization (e.g. deprecated-concept fallback across taxonomy years)
# is deferred to a future concept-family layer — see placeholder ADR-008
# in SPRINT_STATUS.md.
_SEC_KEYWORD_TO_CONCEPTS: dict[str, list[str]] = {
    "revenue": [
        "us-gaap:Revenues",
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    ],
    "net sales": [
        "us-gaap:Revenues",
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    ],
    "sales": [
        "us-gaap:Revenues",
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    ],
    "net income": ["us-gaap:NetIncomeLoss"],
    "diluted earnings per share": ["us-gaap:EarningsPerShareDiluted"],
    "earnings per share": [
        "us-gaap:EarningsPerShareDiluted",
        "us-gaap:EarningsPerShareBasic",
    ],
    "diluted eps": ["us-gaap:EarningsPerShareDiluted"],
    "earnings": ["us-gaap:NetIncomeLoss"],
    "total assets": ["us-gaap:Assets"],
    "assets": ["us-gaap:Assets"],
    "cash": ["us-gaap:CashAndCashEquivalentsAtCarryingValue"],
}

_SEC_ENTITY_ALIASES: dict[str, str] = {
    "aapl": "AAPL",
    "apple": "AAPL",
    "apple inc": "AAPL",
    "msft": "MSFT",
    "microsoft": "MSFT",
    "microsoft corporation": "MSFT",
    "wmt": "WMT",
    "walmart": "WMT",
    "walmart inc": "WMT",
    "nvda": "NVDA",
    "nvidia": "NVDA",
    "nvidia corporation": "NVDA",
    "googl": "GOOGL",
    "alphabet": "GOOGL",
    "google": "GOOGL",
    "alphabet inc": "GOOGL",
    "amzn": "AMZN",
    "amazon": "AMZN",
    "amazon.com": "AMZN",
    "jpm": "JPM",
    "jpmorgan": "JPM",
    "jpmorgan chase": "JPM",
    "xom": "XOM",
    "exxon": "XOM",
    "exxon mobil": "XOM",
    "exxonmobil": "XOM",
    "pfe": "PFE",
    "pfizer": "PFE",
    "tsla": "TSLA",
    "tesla": "TSLA",
}

_SEC_TICKERS = frozenset(_SEC_ENTITY_ALIASES.values())

_SCOPED_REVENUE_TERMS = (
    "services",
    "service",
    "iphone",
    "ipad",
    "mac",
    "wearables",
    "product",
    "products",
    "segment",
    "geographic",
    "region",
    "americas",
    "europe",
    "greater china",
    "japan",
    "rest of asia pacific",
)


class GooseNotFoundError(RuntimeError):
    """Raised when the goose CLI is not on PATH.

    The message names what happened, why it happened, and what the user
    can do next — per the error-messages-are-first-class rule.
    """

    def __init__(self) -> None:
        super().__init__(
            "goose CLI not found on PATH. Teller's default harness is goose "
            "(per ADR-006). Install with `brew install block-goose-cli` (macOS) "
            "or `curl -fsSL https://github.com/block/goose/releases/download/"
            "stable/download_cli.sh | bash`. After installing, ensure `goose` is "
            "on PATH and re-run."
        )


class MissingAPIKeyError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "OPENROUTER_API_KEY is not set. Teller defaults to MiniMax M2.5 via "
            "OpenRouter (ADR-003). Get a key at https://openrouter.ai/keys and "
            "`export OPENROUTER_API_KEY=sk-or-v1-...` before calling Agent.ask. "
            "To use a different provider, construct a ModelConfig and pass it "
            "as `model=` to Agent()."
        )


class Agent:
    """A grounded reasoning agent bound to a domain and a corpus.

    Each `ask` call runs a retrieve → extract → compute → validate pipeline
    against the bound corpus. Results are typed (`Result`) with page-level
    citations and, for supported domains (SEC filings on day 2+), XBRL
    cross-validation against the company's own tagged facts.

    Under the hood, `ask` wraps the `goose` CLI via subprocess (per ADR-006),
    following the Arena-winning pattern. The recipe for the bound domain is
    shipped inside the `teller` package at `teller/recipes/<domain>.yaml` and
    resolved via `importlib.resources`; absolute corpus paths in the recipe
    are substituted at call time so Teller works on any filesystem.

    Example::

        from teller import Agent, Corpus

        corpus = Corpus("./treasury_bulletins")
        agent = Agent(domain="treasury", corpus=corpus)
        result = agent.ask("What were federal expenditures in February 1938?")
        print(result.answer)
    """

    TIMEOUT_SECONDS = 600

    # ADR-007 — post-exit settle window to let goose's SQLite WAL flush before
    # the next Agent.ask call acquires the session DB. Prevents the
    # observed-day-1 concurrent-invocation race where two sequential goose
    # processes contend on ~/.local/share/goose/sessions/sessions.db and the
    # loser exits 0 without starting a session or writing an answer file.
    SESSION_SETTLE_SECONDS = 0.3

    # ADR-012 — single same-model retry on subprocess.TimeoutExpired only.
    # Class attribute (not public kwarg) so tests can patch to False when
    # they need to assert single-attempt behavior. Do not extend the retry
    # trigger beyond TimeoutExpired without a new ADR (see ADR-012 Change
    # Policy).
    RETRY_ON_TIMEOUT: bool = True

    def __init__(
        self,
        domain: str,
        corpus: "Corpus",
        model: Optional[ModelConfig] = None,
    ) -> None:
        self.domain = domain
        self.corpus = corpus
        self.model = model or DEFAULT_MODEL

    def ask(self, question: str) -> Result:
        """Answer a question against the bound corpus.

        Returns a Result with answer, confidence, sources, xbrl_validation,
        and abstention status. If goose writes no answer file, the Result
        is abstained with reason `no_answer_file_written`.

        ADR-012 — on `subprocess.TimeoutExpired` of the first attempt, a
        single same-model retry fires. `latency_ms` accumulates both
        attempts. No retry on other failure classes (see ADR-012 trigger
        scope).
        """
        if shutil.which("goose") is None:
            raise GooseNotFoundError()
        if not os.environ.get("OPENROUTER_API_KEY"):
            raise MissingAPIKeyError()

        recipe_src = self._recipe_path(self.domain)
        if not recipe_src.exists():
            raise FileNotFoundError(
                f"No recipe for domain {self.domain!r} at {recipe_src}. "
                f"Expected a goose recipe file with embedded prompt and the "
                f"`instruction` parameter hook."
            )

        # ADR-007 — goose's --params CLI parser treats newlines in the
        # value as argument terminators. Normalize whitespace once for
        # both attempts.
        instruction_arg = " ".join(question.split())

        start = time.time()
        result = self._run_once(question, instruction_arg, recipe_src, start)
        if result is not None:
            return result

        # First attempt timed out. ADR-012 — single same-model retry with
        # fresh tempdir + fresh uuid session. Emit one stderr line before
        # the retry. `RETRY_ON_TIMEOUT=False` disables retry (test-patch
        # hook; no public kwarg).
        if not self.RETRY_ON_TIMEOUT:
            latency_ms = int((time.time() - start) * 1000)
            return Result(
                question=question,
                answer=None,
                abstained=True,
                abstention_reason=f"timeout_{self.TIMEOUT_SECONDS}s",
                latency_ms=latency_ms,
            )

        print(
            f"teller: model timed out after {self.TIMEOUT_SECONDS}s, "
            f"retrying (attempt 2/2)...",
            file=sys.stderr,
            flush=True,
        )

        result = self._run_once(question, instruction_arg, recipe_src, start)
        if result is not None:
            return result

        # Retry also timed out. Reason stays `timeout_<N>s` for data
        # continuity; semantic shift to "both attempts timed out" is
        # documented in ADR-012.
        latency_ms = int((time.time() - start) * 1000)
        return Result(
            question=question,
            answer=None,
            abstained=True,
            abstention_reason=f"timeout_{self.TIMEOUT_SECONDS}s",
            latency_ms=latency_ms,
        )

    def _run_once(
        self,
        question: str,
        instruction_arg: str,
        recipe_src: Path,
        start: float,
    ) -> Optional[Result]:
        """Execute one goose invocation.

        Returns a `Result` on any terminal outcome (success, empty answer,
        abstention sentinel, no answer file written). Returns `None` on
        `subprocess.TimeoutExpired` to signal the caller that retry is
        permitted per ADR-012. Non-timeout outcomes never trigger retry.

        `latency_ms` is always measured cumulatively from `start` so the
        caller sees true wall-clock across attempts.
        """
        with tempfile.TemporaryDirectory(prefix="teller-run-") as workdir:
            workspace = Path(workdir)
            answer_path = workspace / "answer.txt"

            # Substitute absolute Arena paths with local workspace paths.
            # The recipe's embedded prompt references /app/corpus/ for retrieval
            # and /app/answer.txt for the termination-signal write. Both are
            # rebased so goose runs correctly on any filesystem without
            # requiring root-owned /app to exist.
            recipe_text = recipe_src.read_text()
            recipe_text = recipe_text.replace("/app/answer.txt", str(answer_path))
            recipe_text = recipe_text.replace("/app/corpus", str(self.corpus.path))

            temp_recipe = workspace / "recipe.yaml"
            temp_recipe.write_text(recipe_text)

            env = {
                **os.environ,
                "GOOSE_PROVIDER": "openrouter",
                "GOOSE_MODEL": self.model.name.replace("openrouter/", ""),
            }

            # ADR-007 — unique session name per invocation (defense-in-depth
            # against goose session-name collisions).
            session_name = f"teller-{uuid.uuid4().hex[:10]}"

            try:
                subprocess.run(
                    [
                        "goose",
                        "run",
                        "--recipe",
                        str(temp_recipe),
                        "--name",
                        session_name,
                        "--params",
                        f"instruction={instruction_arg}",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=self.TIMEOUT_SECONDS,
                    env=env,
                    cwd=str(workspace),
                )
            except subprocess.TimeoutExpired:
                # Settle before returning so the next attempt (or the next
                # Agent.ask call) does not race against goose's SQLite WAL
                # from the timed-out process.
                time.sleep(self.SESSION_SETTLE_SECONDS)
                return None

            # ADR-007 — post-exit settle window.
            time.sleep(self.SESSION_SETTLE_SECONDS)

            latency_ms = int((time.time() - start) * 1000)

            if answer_path.exists():
                answer = answer_path.read_text().strip()
                if not answer:
                    return Result(
                        question=question,
                        answer=None,
                        abstained=True,
                        abstention_reason="empty_answer_file",
                        latency_ms=latency_ms,
                    )
                # Prompt-level abstention sentinel (ADR-010 day-3 behavioral
                # abstention). The SEC overlay writes "ABSTAIN:<reason_code>"
                # to the answer file when it classifies a question as
                # segment-intent (or any other unanswerable class). Lift the
                # reason into Result.abstained without running XBRL cross-
                # check — there's no numeric value to validate against a
                # tagged fact. The reason string after the colon is surfaced
                # verbatim, so the prompt layer owns the reason-code taxonomy
                # without requiring Agent changes.
                first_line = answer.split("\n", 1)[0].strip()
                if first_line.startswith("ABSTAIN:"):
                    reason = first_line[len("ABSTAIN:"):].strip() or "llm_requested_abstention"
                    return Result(
                        question=question,
                        answer=None,
                        abstained=True,
                        abstention_reason=reason,
                        latency_ms=latency_ms,
                    )
                xbrl_validation = self._post_validate(question, answer)
                return Result(
                    question=question,
                    answer=answer,
                    confidence=1.0,
                    xbrl_validation=xbrl_validation,
                    latency_ms=latency_ms,
                )

            # ADR-007 contract — goose exited without writing an answer
            # file. This is diagnostic of a structural bug (not a flake).
            # ADR-012 explicitly excludes this class from retry: the
            # signal must stay loud.
            return Result(
                question=question,
                answer=None,
                abstained=True,
                abstention_reason="no_answer_file_written",
                latency_ms=latency_ms,
            )

    @staticmethod
    def _recipe_path(domain: str) -> Path:
        """Return the path to the packaged recipe YAML for `domain`.

        Uses `importlib.resources` so the lookup works for both editable
        source-tree installs and wheel installs. Returns a `pathlib.Path`
        (the file is always unpacked on disk for both install paths).
        """
        return Path(str(_resource_files("teller") / "recipes" / f"{domain}.yaml"))

    # ------------------------------------------------------------------
    # Post-validation (XBRL cross-check for SEC filings)
    # ------------------------------------------------------------------

    def _post_validate(self, question: str, answer: str) -> XBRLValidation:
        """Run the domain's post-hoc validation against a raw LLM answer.

        Treasury and other non-XBRL domains always return
        `XBRLValidation(performed=False)` — no tagged ground truth
        exists. The SEC domain attempts a literal-QName lookup against
        the filing's iXBRL instance per ADR-002, guessing the GAAP
        concept from question keywords.

        Missing filing, missing concept, or an answer that is not a
        parseable number all fall through to `performed=False` with a
        structured reason. This mirrors the abstention-first design
        from the strategy doc: the agent never invents agreement it
        cannot verify.
        """
        if self.domain != "sec_filings":
            return XBRLValidation(performed=False)

        if not _is_numeric_scalar(answer):
            return XBRLValidation(
                performed=False,
                reason="non_numeric_answer",
                note=(
                    "answer is not a single numeric scalar; XBRL comparison "
                    "would be ambiguous"
                ),
            )

        question_entity = _extract_question_entity(question)
        if question_entity is None:
            return XBRLValidation(
                performed=False,
                reason="entity_unspecified",
                note=(
                    "question does not name a supported company or ticker; "
                    "XBRL comparison skipped"
                ),
            )

        corpus_entity = _infer_corpus_entity(self.corpus.path, question_entity)
        if corpus_entity is not None and corpus_entity != question_entity:
            return XBRLValidation(
                performed=False,
                reason="entity_mismatch",
                note=(
                    f"question entity={question_entity}; "
                    f"corpus entity={corpus_entity}"
                ),
            )

        requested_period = _extract_question_fiscal_year(question)
        if requested_period is None:
            return XBRLValidation(
                performed=False,
                reason="period_unspecified",
                note=(
                    "question does not specify a fiscal period; XBRL comparison "
                    "would default to the filing period"
                ),
            )

        if _has_scoped_revenue_request(question):
            return XBRLValidation(
                performed=False,
                reason="concept_unsupported",
                note=(
                    "question asks for a scoped revenue line; v0.1 XBRL "
                    "validation only checks supported consolidated concepts"
                ),
            )

        # Lazy import — avoids the ~2 s arelle import cost for callers
        # that never hit the SEC path.
        from teller.validation.xbrl import (
            FactLookup,
            lookup_fact,
            synthesize_xbrl_validation,
        )

        instance_path = self._find_xbrl_instance(question_entity)
        if instance_path is None:
            return XBRLValidation(
                performed=False,
                reason="xbrl_instance_not_found",
                note=(
                    "no .htm inline-XBRL filing found under the corpus "
                    "directory; re-run `teller download-sec` to populate it"
                ),
            )

        concepts = _guess_gaap_concepts(question)
        if not concepts:
            return XBRLValidation(
                performed=False,
                reason="concept_unknown",
                note=(
                    "no GAAP concept mapping for this question in v0.1; "
                    "concept-family normalization is tracked under "
                    "placeholder ADR-008"
                ),
            )

        period_end = _extract_document_period_end(instance_path)
        if period_end is None:
            return XBRLValidation(
                performed=False,
                reason="xbrl_period_not_found",
                note="could not determine DocumentPeriodEndDate from the filing",
            )
        filing_fiscal_year = _fiscal_year_from_period_end(period_end)
        if isinstance(requested_period, int) and filing_fiscal_year != requested_period:
            return XBRLValidation(
                performed=False,
                reason="period_mismatch",
                note=(
                    f"question fiscal year=FY{requested_period}; "
                    f"filing period end={period_end}"
                ),
            )

        last_lookup: Optional[FactLookup] = None
        for concept in concepts:
            lookup = lookup_fact(instance_path, concept, period_end)
            last_lookup = lookup
            if lookup.available:
                return synthesize_xbrl_validation(
                    lookup,
                    agent_answer=_normalize_numeric(answer, lookup.value),
                )

        # None of the candidate concepts produced an available fact.
        # Surface the last lookup's reason (most informative — e.g.
        # segment_level_dimensional) rather than collapsing to not_tagged.
        if last_lookup is not None:
            return synthesize_xbrl_validation(last_lookup)
        return XBRLValidation(performed=False, reason="concept_unknown")

    def _find_xbrl_instance(
        self, preferred_entity: Optional[str] = None
    ) -> Optional[Path]:
        """Find a single .htm iXBRL instance under `self.corpus.path`.

        When `preferred_entity` is supplied and the corpus is a parent
        directory like ./sec_data, prefer that ticker's subdirectory.
        Otherwise return the first `.htm` / `.html` file found recursively.
        """
        root = self.corpus.path
        search_roots = []
        if preferred_entity is not None:
            if root.name.upper() == preferred_entity:
                search_roots.append(root)
            if root.exists():
                search_roots.extend(
                    p
                    for p in root.rglob("*")
                    if p.is_dir() and p.name.upper() == preferred_entity
                )
        search_roots.append(root)

        seen: set[Path] = set()
        for search_root in search_roots:
            if search_root in seen:
                continue
            seen.add(search_root)
            for pattern in ("**/*.htm", "**/*.html"):
                for candidate in search_root.glob(pattern):
                    if candidate.is_file() and candidate.stat().st_size > 1000:
                        return candidate
        return None


def _guess_gaap_concepts(question: str) -> list[str]:
    """Return candidate GAAP concepts for a natural-language question."""
    q = question.lower()
    # Match longest keyword first (e.g. "net sales" before "sales").
    for keyword in sorted(_SEC_KEYWORD_TO_CONCEPTS.keys(), key=len, reverse=True):
        if keyword in q:
            return list(_SEC_KEYWORD_TO_CONCEPTS[keyword])
    return []


def _is_numeric_scalar(answer: str) -> bool:
    """Return True when `answer` is one numeric value, not text or a list."""
    stripped = answer.strip()
    if "," in stripped:
        thousands = r"[+-]?\d{1,3}(?:,\d{3})+(?:\.\d*)?"
        if not re.fullmatch(thousands, stripped):
            return False
    normalized = stripped.replace(",", "")
    return bool(re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", normalized))


def _extract_question_entity(question: str) -> Optional[str]:
    """Infer a supported SEC fixture ticker from the question text."""
    q = question.lower()
    aliases = sorted(
        _SEC_ENTITY_ALIASES.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    for alias, ticker in aliases:
        if re.search(rf"\b{re.escape(alias)}\b", q):
            return ticker
    return None


def _infer_corpus_entity(
    corpus_path: Path, requested_entity: Optional[str] = None
) -> Optional[str]:
    """Infer corpus ticker from path components or downloaded SEC filenames."""
    candidates = list(corpus_path.parts)
    if corpus_path.exists():
        candidates.extend(p.stem for p in corpus_path.rglob("*") if p.is_file())
    found: set[str] = set()
    for candidate in candidates:
        for token in re.split(r"[^A-Za-z0-9]+", candidate):
            ticker = token.upper()
            if ticker in _SEC_TICKERS:
                found.add(ticker)
    if requested_entity in found:
        return requested_entity
    if len(found) == 1:
        return next(iter(found))
    if corpus_path.name.upper() in _SEC_TICKERS:
        return corpus_path.name.upper()
    return None


def _extract_question_fiscal_year(question: str) -> Optional[int | str]:
    """Return explicit target fiscal year, 'latest', or None if unspecified."""
    q = question.lower()
    years = [int(y) for y in re.findall(r"\b(?:fy|fiscal year)\s*'?(\d{2,4})\b", q)]
    if not years:
        years = [int(y) for y in re.findall(r"\b(20\d{2})\b", q)]
    if years:
        normalized = [2000 + y if y < 100 else y for y in years]
        return max(normalized)
    latest_phrases = (
        "last fiscal year",
        "latest fiscal year",
        "most recent fiscal year",
        "last year",
        "most recent year",
        "latest year",
    )
    if any(phrase in q for phrase in latest_phrases):
        return "latest"
    return None


def _fiscal_year_from_period_end(period_end: str) -> Optional[int]:
    try:
        return int(period_end.split("-", 1)[0])
    except (TypeError, ValueError):
        return None


def _has_scoped_revenue_request(question: str) -> bool:
    """Detect revenue questions that ask for a segment/product line."""
    q = question.lower()
    metric = r"(?:revenue|sales|net sales)"
    for term in _SCOPED_REVENUE_TERMS:
        scoped = re.escape(term)
        if re.search(rf"\b{scoped}\s+{metric}\b", q):
            return True
        if re.search(rf"\b{metric}\s+(?:from|for|in)\s+{scoped}\b", q):
            return True
    return False


def _extract_document_period_end(instance_path: Path) -> Optional[str]:
    """Read `dei:DocumentPeriodEndDate` from an iXBRL instance.

    Every SEC filing tags this DEI concept with the period-of-report
    date. Using the DEI tag is more reliable than inferring from
    filename conventions or from the largest-range context.
    """
    from teller.validation.xbrl import lookup_fact

    # DocumentPeriodEndDate is an instant-type string fact, not a
    # numeric monetaryItemType — our lookup_fact still works for it
    # because the predicate (consolidated context, period match) only
    # checks the context shape, not the fact type. We do not have a
    # period_end to match against yet, so we read the raw instance and
    # return the first consolidated DocumentPeriodEndDate we see.
    from arelle.api.Session import Session
    from arelle.ModelValue import qname
    from arelle.RuntimeOptions import RuntimeOptions

    session = Session()
    try:
        options = RuntimeOptions(
            entrypointFile=str(instance_path),
            internetConnectivity="offline",
            keepOpen=True,
            logLevel="error",
        )
        try:
            session.run(options)
        except Exception:
            return None
        models = session.get_models()
        if not models:
            return None
        m = models[0]
        dei_concept = qname("dei:DocumentPeriodEndDate", m.prefixedNamespaces)
        if dei_concept is None:
            return None
        facts = m.factsByQname.get(dei_concept, set())
        for fact in facts:
            if not fact.context.qnameDims:
                value = fact.value
                if value:
                    return str(value).strip()
        return None
    finally:
        try:
            session.close()
        except Exception:
            pass


def _normalize_numeric(agent_answer: str, tagged_value: Optional[str]) -> Optional[str]:
    """Scale the agent's answer so it compares cleanly to `tagged_value`.

    The iron rules force the LLM to write a bare number to answer.txt
    with no unit. For a 10-K revenue question, the LLM typically
    writes the value in the table's reporting unit (millions):
    `391035`. The XBRL fact stores the full dollar amount:
    `391035000000`. Direct comparison is off by 10^6 / 10^9.

    This helper tries the agent's answer as-is and scaled by 10^3 / 10^6
    / 10^9, returning the candidate closest to `tagged_value`. If none
    agree within 1 %, returns the raw answer and
    `synthesize_xbrl_validation` will mark `agreed=False` — which is
    also the right signal.
    """
    if tagged_value is None:
        return agent_answer
    try:
        agent_f = float(agent_answer)
        tagged_f = float(tagged_value)
    except (TypeError, ValueError):
        return agent_answer
    if tagged_f == 0:
        return agent_answer
    candidates = [
        agent_f,
        agent_f * 1_000,
        agent_f * 1_000_000,
        agent_f * 1_000_000_000,
    ]
    best = min(candidates, key=lambda x: abs(x - tagged_f) / abs(tagged_f))
    return str(best)
