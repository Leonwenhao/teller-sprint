"""Tests for ADR-012 retry-on-timeout in Agent.ask.

Covers the six test cases enumerated in ADR-012:
(a) first-attempt timeout, second-attempt success → Result.answer populated,
    latency cumulative
(b) both attempts timeout → abstention_reason=f"timeout_{TIMEOUT_SECONDS}s",
    single _run_once call counted as two attempts
(c) first-attempt returns no_answer_file_written → no retry, no stderr line
(d) ABSTAIN: sentinel on first attempt → no retry
(e) stderr line text matches spec exactly (ADR-012 wording)
(f) RETRY_ON_TIMEOUT=False class-patch disables retry

These tests stub `Agent._run_once` directly rather than mocking subprocess.
The retry loop is a property of `Agent.ask`; the helper's internals (goose
subprocess, tempdir lifecycle) are covered separately in other suites.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pytest

from teller.agent import Agent
from teller.corpus import Corpus
from teller.result import Result


@pytest.fixture
def fake_environment(monkeypatch, tmp_path):
    """Satisfy Agent.ask's preflight checks (goose on PATH, API key, recipe)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test")
    monkeypatch.setattr("teller.agent.shutil.which", lambda _name: "/usr/local/bin/goose")

    # Agent resolves recipe at <repo_root>/recipes/<domain>.yaml. The real
    # repo already ships recipes/treasury.yaml; point _repo_root at a tmp
    # tree so we don't depend on the real recipe's contents during these
    # retry-loop tests.
    repo_root = tmp_path / "repo"
    (repo_root / "recipes").mkdir(parents=True)
    (repo_root / "recipes" / "treasury.yaml").write_text("# stub recipe for retry tests\n")

    monkeypatch.setattr(Agent, "_repo_root", staticmethod(lambda: repo_root))

    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "stub.txt").write_text("")
    return corpus_dir


def _make_agent(corpus_dir: Path) -> Agent:
    corpus = Corpus(corpus_dir)
    return Agent(domain="treasury", corpus=corpus)


class _RunOnceStub:
    """Programmable _run_once replacement.

    `outcomes` is a list of per-attempt return values (Result or None).
    Each invocation consumes the next element. Raises if the list is
    exhausted — catches any test that expects more attempts than it set up.
    """

    def __init__(self, outcomes):
        self._outcomes = list(outcomes)
        self.calls = 0

    def __call__(self, agent, question, instruction_arg, recipe_src, start):
        if not self._outcomes:
            raise AssertionError(
                f"_run_once called {self.calls + 1} time(s) but only "
                f"{self.calls} outcome(s) were programmed"
            )
        self.calls += 1
        return self._outcomes.pop(0)


def _install_stub(monkeypatch, stub: _RunOnceStub) -> None:
    def _bound(self, question, instruction_arg, recipe_src, start):
        return stub(self, question, instruction_arg, recipe_src, start)

    monkeypatch.setattr(Agent, "_run_once", _bound)


class TestRetryOnTimeout:
    def test_a_first_timeout_then_success(self, monkeypatch, fake_environment, capsys):
        """First attempt times out, retry succeeds — answer returned, retry counted."""
        success = Result(
            question="q",
            answer="42",
            confidence=1.0,
            latency_ms=700_000,  # cumulative (mock value)
        )
        stub = _RunOnceStub([None, success])
        _install_stub(monkeypatch, stub)

        agent = _make_agent(fake_environment)
        result = agent.ask("what is the answer")

        assert stub.calls == 2
        assert result.answer == "42"
        assert result.abstained is False
        captured = capsys.readouterr()
        assert "timed out" in captured.err
        assert "attempt 2/2" in captured.err

    def test_b_both_attempts_timeout(self, monkeypatch, fake_environment, capsys):
        """Both attempts time out — final abstention with timeout_600s."""
        stub = _RunOnceStub([None, None])
        _install_stub(monkeypatch, stub)

        agent = _make_agent(fake_environment)
        result = agent.ask("what is the answer")

        assert stub.calls == 2
        assert result.abstained is True
        assert result.abstention_reason == f"timeout_{Agent.TIMEOUT_SECONDS}s"
        assert result.answer is None
        captured = capsys.readouterr()
        # One retry line (before the second attempt), not two.
        assert captured.err.count("retrying (attempt 2/2)") == 1

    def test_c_no_answer_file_written_does_not_retry(
        self, monkeypatch, fake_environment, capsys
    ):
        """no_answer_file_written preserves ADR-007 loud-signal contract."""
        loud = Result(
            question="q",
            answer=None,
            abstained=True,
            abstention_reason="no_answer_file_written",
            latency_ms=500,
        )
        stub = _RunOnceStub([loud])
        _install_stub(monkeypatch, stub)

        agent = _make_agent(fake_environment)
        result = agent.ask("what is the answer")

        assert stub.calls == 1
        assert result.abstention_reason == "no_answer_file_written"
        captured = capsys.readouterr()
        assert "retrying" not in captured.err

    def test_d_abstain_sentinel_does_not_retry(
        self, monkeypatch, fake_environment, capsys
    ):
        """Prompt-layer abstention (ADR-010) is deliberate, not a flake."""
        abstain = Result(
            question="q",
            answer=None,
            abstained=True,
            abstention_reason="segment_level_dimensional",
            latency_ms=8_000,
        )
        stub = _RunOnceStub([abstain])
        _install_stub(monkeypatch, stub)

        agent = _make_agent(fake_environment)
        result = agent.ask("what were net sales in Greater China")

        assert stub.calls == 1
        assert result.abstention_reason == "segment_level_dimensional"
        captured = capsys.readouterr()
        assert "retrying" not in captured.err

    def test_e_stderr_line_matches_adr_wording_exactly(
        self, monkeypatch, fake_environment, capsys
    ):
        """ADR-012 specifies the exact launch-audience wording."""
        success = Result(question="q", answer="1", confidence=1.0, latency_ms=100)
        stub = _RunOnceStub([None, success])
        _install_stub(monkeypatch, stub)

        agent = _make_agent(fake_environment)
        agent.ask("what is the answer")

        expected = (
            f"teller: model timed out after {Agent.TIMEOUT_SECONDS}s, "
            f"retrying (attempt 2/2)..."
        )
        captured = capsys.readouterr()
        assert expected in captured.err
        # No mention of "goose" — launch-audience vocabulary per ADR-012.
        assert "goose" not in captured.err

    def test_f_retry_disabled_via_class_attribute(
        self, monkeypatch, fake_environment, capsys
    ):
        """RETRY_ON_TIMEOUT=False preserves single-attempt behavior for tests."""
        stub = _RunOnceStub([None])
        _install_stub(monkeypatch, stub)
        monkeypatch.setattr(Agent, "RETRY_ON_TIMEOUT", False)

        agent = _make_agent(fake_environment)
        result = agent.ask("what is the answer")

        assert stub.calls == 1
        assert result.abstention_reason == f"timeout_{Agent.TIMEOUT_SECONDS}s"
        captured = capsys.readouterr()
        assert "retrying" not in captured.err
