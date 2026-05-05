from __future__ import annotations

import sys

from teller.validation.xbrl import _run_arelle_session, get_last_arelle_diagnostics


class _FakeSession:
    def run(self, options):
        print("[ix11.11.1.2:invalidTransformation] benign warning")
        print("[stderr diagnostic]", file=sys.stderr)
        return True


def test_arelle_diagnostics_suppressed_by_default(capsys, monkeypatch):
    monkeypatch.delenv("TELLER_DEBUG_XBRL", raising=False)

    ok = _run_arelle_session(_FakeSession(), object())

    captured = capsys.readouterr()
    assert ok is True
    assert captured.out == ""
    assert captured.err == ""
    assert "invalidTransformation" in get_last_arelle_diagnostics()


def test_arelle_diagnostics_printed_in_debug(capsys, monkeypatch):
    monkeypatch.setenv("TELLER_DEBUG_XBRL", "1")

    _run_arelle_session(_FakeSession(), object())

    captured = capsys.readouterr()
    assert "invalidTransformation" in captured.err
    assert "[stderr diagnostic]" in captured.err
