"""CLI input validation tests for `teller ask`."""
from __future__ import annotations

import importlib

from click.testing import CliRunner

cli_main = importlib.import_module("teller.cli.main")


def test_ask_rejects_empty_question_before_agent_call(monkeypatch, tmp_path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    monkeypatch.setattr(
        cli_main,
        "Agent",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError),
    )

    result = CliRunner().invoke(
        cli_main.main,
        ["ask", "", "--corpus", str(corpus_dir), "--domain", "treasury"],
    )

    assert result.exit_code == 2
    assert "question must not be empty" in result.output


def test_ask_rejects_whitespace_question_before_agent_call(monkeypatch, tmp_path):
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    monkeypatch.setattr(
        cli_main,
        "Agent",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError),
    )

    result = CliRunner().invoke(
        cli_main.main,
        ["ask", "   ", "--corpus", str(corpus_dir), "--domain", "treasury"],
    )

    assert result.exit_code == 2
    assert "question must not be empty" in result.output
