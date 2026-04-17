"""Agent — the public entry point for asking grounded questions against a corpus."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from teller.config import DEFAULT_MODEL, ModelConfig
from teller.result import Result

if TYPE_CHECKING:
    from teller.corpus import Corpus


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
    following the Arena-winning pattern. The recipe for the bound domain
    lives at `recipes/<domain>.yaml`; absolute corpus paths in the recipe
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
        """
        if shutil.which("goose") is None:
            raise GooseNotFoundError()
        if not os.environ.get("OPENROUTER_API_KEY"):
            raise MissingAPIKeyError()

        repo_root = self._repo_root()
        recipe_src = repo_root / "recipes" / f"{self.domain}.yaml"
        if not recipe_src.exists():
            raise FileNotFoundError(
                f"No recipe for domain {self.domain!r} at {recipe_src}. "
                f"Expected a goose recipe file with embedded prompt and the "
                f"`instruction` parameter hook."
            )

        start = time.time()
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

            # ADR-007 — goose's --params CLI parser treats newlines in the
            # value as argument terminators: a question containing `\n`
            # causes goose to exit silently between "Recipe execution
            # started" and "Headless session started" with no error logged.
            # Normalize newlines to spaces so the full instruction reaches
            # the model intact. Semantically lossless for natural-language
            # questions.
            instruction_arg = " ".join(question.split())

            try:
                proc = subprocess.run(
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
                latency_ms = int((time.time() - start) * 1000)
                # Settle before returning so the next Agent.ask call does not
                # race against goose's SQLite WAL from the timed-out process.
                time.sleep(self.SESSION_SETTLE_SECONDS)
                return Result(
                    question=question,
                    answer=None,
                    abstained=True,
                    abstention_reason=f"timeout_{self.TIMEOUT_SECONDS}s",
                    latency_ms=latency_ms,
                )

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
                return Result(
                    question=question,
                    answer=answer,
                    confidence=1.0,
                    latency_ms=latency_ms,
                )

            return Result(
                question=question,
                answer=None,
                abstained=True,
                abstention_reason="no_answer_file_written",
                latency_ms=latency_ms,
            )

    @staticmethod
    def _repo_root() -> Path:
        """Return the teller/ repo root (two levels up from src/teller/)."""
        return Path(__file__).parent.parent.parent.resolve()
