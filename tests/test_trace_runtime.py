from __future__ import annotations

import json
import subprocess
from pathlib import Path

from teller.agent import Agent
from teller.corpus import Corpus


def _agent(tmp_path: Path, monkeypatch) -> Agent:
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-secret-test")
    monkeypatch.setattr("teller.agent.shutil.which", lambda _name: "/usr/local/bin/goose")
    monkeypatch.setattr(
        "teller.trace.environment_diagnostics",
        lambda: {
            "python_version": "3.12",
            "platform": "test",
            "package_version": "test",
            "goose_path": "/usr/local/bin/goose",
            "goose_version": "test",
        },
    )
    recipe_dir = tmp_path / "recipes"
    recipe_dir.mkdir()
    (recipe_dir / "treasury.yaml").write_text("write /app/answer.txt from /app/corpus")
    monkeypatch.setattr(
        Agent,
        "_recipe_path",
        staticmethod(lambda domain: recipe_dir / f"{domain}.yaml"),
    )
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "stub.txt").write_text("stub")
    return Agent(domain="treasury", corpus=Corpus(corpus_dir))


def test_trace_file_created_without_api_key(monkeypatch, tmp_path):
    trace_dir = tmp_path / "traces"
    monkeypatch.setenv("TELLER_TRACE_DIR", str(trace_dir))

    def fake_run(cmd, capture_output, text, timeout, env, cwd):
        Path(cwd, "answer.txt").write_text("42")
        return subprocess.CompletedProcess(cmd, 0, stdout="provider out", stderr="provider err")

    monkeypatch.setattr("teller.agent.subprocess.run", fake_run)

    result = _agent(tmp_path, monkeypatch).ask("What is the answer?")

    assert result.answer == "42"
    assert result.trace_path is not None
    trace = json.loads(Path(result.trace_path).read_text())
    assert trace["attempts"][0]["classification"] == "success"
    assert "provider out" in trace["attempts"][0]["stdout_excerpt"]
    assert "sk-or-v1-secret-test" not in Path(result.trace_path).read_text()


def test_trace_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("TELLER_TRACE_DIR", str(tmp_path / "traces"))
    monkeypatch.setenv("TELLER_TRACE_DISABLED", "1")

    def fake_run(cmd, capture_output, text, timeout, env, cwd):
        Path(cwd, "answer.txt").write_text("42")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("teller.agent.subprocess.run", fake_run)

    result = _agent(tmp_path, monkeypatch).ask("What is the answer?")

    assert result.trace_id
    assert result.trace_path is None
    assert not (tmp_path / "traces").exists()


def test_timeout_retry_trace(monkeypatch, tmp_path):
    monkeypatch.setenv("TELLER_TRACE_DIR", str(tmp_path / "traces"))
    calls = {"n": 0}

    def fake_run(cmd, capture_output, text, timeout, env, cwd):
        calls["n"] += 1
        if calls["n"] == 1:
            raise subprocess.TimeoutExpired(cmd, timeout)
        Path(cwd, "answer.txt").write_text("42")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("teller.agent.subprocess.run", fake_run)

    result = _agent(tmp_path, monkeypatch).ask("What is the answer?")
    trace = json.loads(Path(result.trace_path).read_text())

    assert result.answer == "42"
    assert [a["classification"] for a in trace["attempts"]] == ["timeout_600s", "success"]


def test_no_answer_nonzero_and_provider_classification(monkeypatch, tmp_path):
    monkeypatch.setenv("TELLER_TRACE_DIR", str(tmp_path / "traces"))
    monkeypatch.setattr(Agent, "RETRY_ON_PROVIDER_FAILURE", False)

    def fake_run(cmd, capture_output, text, timeout, env, cwd):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="OpenRouter stream decode failed")

    monkeypatch.setattr("teller.agent.subprocess.run", fake_run)

    result = _agent(tmp_path, monkeypatch).ask("What is the answer?")
    trace = json.loads(Path(result.trace_path).read_text())

    assert result.abstained is True
    assert result.abstention_reason == "provider_stream_error"
    assert trace["attempts"][0]["classification"] == "provider_stream_error"


def test_stdout_answer_recovery(monkeypatch, tmp_path):
    monkeypatch.setenv("TELLER_TRACE_DIR", str(tmp_path / "traces"))

    def fake_run(cmd, capture_output, text, timeout, env, cwd):
        return subprocess.CompletedProcess(cmd, 0, stdout="Final answer: 42\n", stderr="")

    monkeypatch.setattr("teller.agent.subprocess.run", fake_run)

    result = _agent(tmp_path, monkeypatch).ask("What is the answer?")
    trace = json.loads(Path(result.trace_path).read_text())

    assert result.answer == "42"
    assert result.abstained is False
    assert result.normalization["recovered_from_stdout"] is True
    assert trace["attempts"][0]["classification"] == "recovered_from_stdout"


def test_provider_failure_retries_once(monkeypatch, tmp_path):
    monkeypatch.setenv("TELLER_TRACE_DIR", str(tmp_path / "traces"))
    calls = {"n": 0}

    def fake_run(cmd, capture_output, text, timeout, env, cwd):
        calls["n"] += 1
        if calls["n"] == 1:
            return subprocess.CompletedProcess(
                cmd,
                1,
                stdout="",
                stderr="OpenRouter stream decode failed",
            )
        Path(cwd, "answer.txt").write_text("42")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("teller.agent.subprocess.run", fake_run)

    result = _agent(tmp_path, monkeypatch).ask("What is the answer?")
    trace = json.loads(Path(result.trace_path).read_text())

    assert result.answer == "42"
    assert calls["n"] == 2
    assert [a["classification"] for a in trace["attempts"]] == [
        "provider_stream_error",
        "success",
    ]
