from __future__ import annotations

import importlib
import json

from click.testing import CliRunner

cli_main = importlib.import_module("teller.cli.main")


def test_doctor_json_success(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test")
    monkeypatch.setenv("TELLER_TRACE_DIR", str(tmp_path / "traces"))
    monkeypatch.setattr(
        cli_main,
        "environment_diagnostics",
        lambda: {
            "python_version": "3.12.0",
            "platform": "test",
            "package_version": "0.1.0",
            "goose_path": "/usr/local/bin/goose",
            "goose_version": "1.32.0",
        },
    )

    result = CliRunner().invoke(cli_main.main, ["doctor", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert {c["name"] for c in payload["checks"]} >= {
        "python",
        "package import",
        "goose",
        "OPENROUTER_API_KEY",
        "trace directory",
    }


def test_doctor_fails_when_api_key_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("TELLER_TRACE_DIR", str(tmp_path / "traces"))
    monkeypatch.setattr(
        cli_main,
        "environment_diagnostics",
        lambda: {
            "python_version": "3.12.0",
            "platform": "test",
            "package_version": "0.1.0",
            "goose_path": "/usr/local/bin/goose",
            "goose_version": "1.32.0",
        },
    )

    result = CliRunner().invoke(cli_main.main, ["doctor", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    key_check = next(c for c in payload["checks"] if c["name"] == "OPENROUTER_API_KEY")
    assert key_check["ok"] is False


def test_ask_prints_trace_on_abnormal_result(monkeypatch, tmp_path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()

    class FakeAgent:
        def __init__(self, *args, **kwargs):
            pass

        def ask(self, question):
            from teller.result import Result

            return Result(
                question=question,
                answer=None,
                abstained=True,
                abstention_reason="no_answer_file_written",
                trace_path="/tmp/teller-trace.json",
            )

    monkeypatch.setattr(cli_main, "Agent", FakeAgent)

    result = CliRunner().invoke(
        cli_main.main,
        ["ask", "q", "--corpus", str(corpus_dir), "--domain", "treasury"],
    )

    assert result.exit_code == 0
    assert "trace: /tmp/teller-trace.json" in result.output
