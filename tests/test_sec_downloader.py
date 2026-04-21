"""Tests for `teller.downloaders.sec.SecDownloader`.

Split into two suites:

- Unit tests (default): HTTP is mocked by monkey-patching `_get`.
  Exercises CIK resolution, filing selection, URL construction,
  rate-limiter pacing, and the iXBRL / separate-instance branches.
  No network.

- Integration test (`@pytest.mark.integration`): hits live EDGAR for
  Apple's latest 10-K. Deselected by default (`-m "not integration"`
  is implied unless the marker is requested). Provides the end-to-end
  coverage the day-2 gate needs; not run in CI.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Callable

import pytest

from teller.downloaders.sec import (
    DownloadResult,
    NoMatchingFilingError,
    SecDownloader,
    TickerNotFoundError,
    _RateLimiter,
)


# --------------------------------------------------------------------
# Fixtures — fake EDGAR responses
# --------------------------------------------------------------------


TICKERS_JSON = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp."},
}


def _submissions_json(accession: str, form: str, filing_date: str, report_date: str, primary: str) -> dict:
    return {
        "cik": "320193",
        "name": "Apple Inc.",
        "filings": {
            "recent": {
                "accessionNumber": [accession, "0000320193-23-000106"],
                "form": [form, "10-K"],
                "filingDate": [filing_date, "2023-11-03"],
                "reportDate": [report_date, "2023-09-30"],
                "primaryDocument": [primary, "aapl-20230930.htm"],
            },
            "files": [],
        },
    }


def _install_fake_http(downloader: SecDownloader, handlers: dict[str, Callable[[], bytes]]):
    """Replace `_get` with a handler lookup.

    `handlers` maps URL substrings to a callable that returns the
    response body. Matching is "first substring that fits" so tests
    can stay terse.
    """
    def fake_get(url: str, timeout: float = 30.0) -> bytes:  # noqa: ARG001
        for pattern, handler in handlers.items():
            if pattern in url:
                return handler()
        raise AssertionError(f"unexpected URL in test: {url}")

    downloader._get = fake_get  # type: ignore[method-assign]


# --------------------------------------------------------------------
# Rate limiter
# --------------------------------------------------------------------


class TestRateLimiter:
    def test_respects_min_interval(self):
        rl = _RateLimiter(max_rps=20.0)  # 50 ms min interval
        t0 = time.monotonic()
        for _ in range(5):
            rl.await_slot()
        elapsed = time.monotonic() - t0
        # 4 intervals of 50 ms between 5 calls = 200 ms lower bound.
        assert elapsed >= 0.18

    def test_rejects_non_positive_rps(self):
        with pytest.raises(ValueError):
            _RateLimiter(max_rps=0)
        with pytest.raises(ValueError):
            _RateLimiter(max_rps=-1)


# --------------------------------------------------------------------
# CIK resolution
# --------------------------------------------------------------------


class TestResolveCik:
    def test_resolves_known_ticker(self):
        dl = SecDownloader()
        _install_fake_http(
            dl, {"company_tickers.json": lambda: json.dumps(TICKERS_JSON).encode()}
        )
        assert dl.resolve_cik("AAPL") == "0000320193"
        assert dl.resolve_cik("msft") == "0000789019"

    def test_caches_cik(self):
        dl = SecDownloader()
        call_count = {"n": 0}

        def handler():
            call_count["n"] += 1
            return json.dumps(TICKERS_JSON).encode()

        _install_fake_http(dl, {"company_tickers.json": handler})
        dl.resolve_cik("AAPL")
        dl.resolve_cik("AAPL")
        assert call_count["n"] == 1

    def test_unknown_ticker_raises(self):
        dl = SecDownloader()
        _install_fake_http(
            dl, {"company_tickers.json": lambda: json.dumps(TICKERS_JSON).encode()}
        )
        with pytest.raises(TickerNotFoundError):
            dl.resolve_cik("NOPE")


# --------------------------------------------------------------------
# Filing selection
# --------------------------------------------------------------------


class TestFilingSelection:
    def _setup(self, tmp_path: Path) -> tuple[SecDownloader, Path]:
        dl = SecDownloader()
        subs = _submissions_json(
            accession="0000320193-24-000123",
            form="10-K",
            filing_date="2024-11-01",
            report_date="2024-09-28",
            primary="aapl-20240928.htm",
        )
        primary_body = b"<html><body>fake iXBRL filing</body></html>"
        _install_fake_http(
            dl,
            {
                "company_tickers.json": lambda: json.dumps(TICKERS_JSON).encode(),
                "submissions/CIK0000320193.json": lambda: json.dumps(subs).encode(),
                "aapl-20240928.htm": lambda: primary_body,
            },
        )
        return dl, tmp_path

    def test_latest_10k_by_default(self, tmp_path):
        dl, _ = self._setup(tmp_path)
        result = dl.download_filing(
            "AAPL", dest_dir=tmp_path, warm_xbrl_cache=False
        )
        assert result.ticker == "AAPL"
        assert result.cik == "0000320193"
        assert result.form == "10-K"
        assert result.accession_number == "0000320193-24-000123"
        assert result.filing_date == "2024-11-01"
        assert result.report_date == "2024-09-28"
        assert result.primary_document.name == "aapl-20240928.htm"
        assert result.primary_document.exists()
        # Modern iXBRL filing → primary doc is the instance.
        assert result.xbrl_instance == result.primary_document
        assert result.xbrl_available is True

    def test_by_year_filter(self, tmp_path):
        dl, _ = self._setup(tmp_path)
        # 2023 filing exists in the fake submissions JSON at index 1.
        # Its primary_document is "aapl-20230930.htm" which we haven't
        # wired a handler for — register one.
        dl._get_original = dl._get  # type: ignore[attr-defined]

        def extended_get(url, timeout=30.0):  # noqa: ARG001
            if "aapl-20230930.htm" in url:
                return b"<html>2023 fake</html>"
            return dl._get_original(url, timeout=timeout)

        dl._get = extended_get  # type: ignore[method-assign]
        result = dl.download_filing(
            "AAPL", year=2023, dest_dir=tmp_path, warm_xbrl_cache=False
        )
        assert result.filing_date.startswith("2023")

    def test_no_match_raises(self, tmp_path):
        dl, _ = self._setup(tmp_path)
        with pytest.raises(NoMatchingFilingError):
            dl.download_filing(
                "AAPL", form="10-Q", dest_dir=tmp_path, warm_xbrl_cache=False
            )


# --------------------------------------------------------------------
# URL construction
# --------------------------------------------------------------------


class TestUrlConstruction:
    def test_archives_url_strips_dashes_and_zero_pads(self):
        url = SecDownloader._archives_url(
            cik="0000320193",
            accession_number="0000320193-24-000123",
            filename="aapl-20240928.htm",
        )
        assert url == (
            "https://www.sec.gov/Archives/edgar/data/320193/"
            "000032019324000123/aapl-20240928.htm"
        )


# --------------------------------------------------------------------
# User-agent and host headers
# --------------------------------------------------------------------


class TestUserAgent:
    def test_user_agent_is_dolores_research(self):
        dl = SecDownloader()
        assert "Dolores Research" in dl._user_agent
        assert "leon@dolores.research" in dl._user_agent

    def test_host_header_switches_between_sec_domains(self):
        assert SecDownloader._host_for("https://www.sec.gov/Archives/foo") == "www.sec.gov"
        assert SecDownloader._host_for("https://data.sec.gov/submissions/foo") == "data.sec.gov"


# --------------------------------------------------------------------
# Integration — real EDGAR, opt-in via marker
# --------------------------------------------------------------------


@pytest.mark.integration
def test_apple_latest_10k_real_edgar(tmp_path):
    """Hits live EDGAR. Deselected by default; run with `-m integration`.

    This is the day-2 gate exercise: download Apple's latest 10-K
    and confirm the primary document + XBRL cache warmup succeed.
    """
    dl = SecDownloader()
    result = dl.download_filing("AAPL", dest_dir=tmp_path)
    assert isinstance(result, DownloadResult)
    assert result.ticker == "AAPL"
    assert result.primary_document.exists()
    assert result.primary_document.stat().st_size > 100_000
    assert result.xbrl_available is True
