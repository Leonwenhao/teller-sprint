#!/usr/bin/env python3
"""Day-3 download phase: fetch most-recent 10-K for each test-set ticker.

Per the day-3 test-set plan, we pull the most-recent 10-K per ticker
(not a fiscal-year-locked target), read DocumentPeriodEndDate from the
XBRL, and relabel the question's `fiscal_period` to the actual fiscal
year that landed. This avoids the WMT/NVDA mixed-year problem (their
fiscal year is one ahead of calendar-year filers, so "FY2025" means
different vintages across tickers).

Writes:
    tests/fixtures/sec_filings/corpus/<TICKER>/<accession>/*
    tests/fixtures/sec_filings/corpus/manifest.json

Usage:
    PYTHONPATH=src python3 scripts/day3_download_sec.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from teller.downloaders.sec import SecDownloader  # noqa: E402

CORPUS_ROOT = REPO / "tests" / "fixtures" / "sec_filings" / "corpus"
MANIFEST_PATH = CORPUS_ROOT / "manifest.json"

TICKERS = ["AAPL", "MSFT", "WMT", "NVDA", "GOOGL", "AMZN", "JPM", "XOM", "PFE", "TSLA"]


def derive_fiscal_year(ticker: str, report_date: str) -> str:
    """Map (ticker, report_date) -> 'FY2025' etc. using ticker convention.

    Per SEC/standard convention:
      - AAPL Sep-end, MSFT Jun-end, WMT Jan-end, NVDA Jan-end:
        the fiscal-year label equals the calendar year in which the
        fiscal year ENDS.  (WMT FY2025 ended Jan-31-2025.  MSFT FY2025
        ended Jun-30-2025.  AAPL FY2025 ended Sep-27-2025.)
      - All other tickers here are calendar-year filers: FY = year of
        report_date.
    """
    year = int(report_date[:4])
    return f"FY{year}"


def main() -> int:
    CORPUS_ROOT.mkdir(parents=True, exist_ok=True)
    downloader = SecDownloader()
    manifest: dict = {
        "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tickers": {},
    }

    for ticker in TICKERS:
        print(f"[{ticker}] resolving + downloading most-recent 10-K...", flush=True)
        try:
            dest = CORPUS_ROOT / ticker
            result = downloader.download_filing(
                ticker=ticker,
                form="10-K",
                year=None,  # most recent
                dest_dir=dest,
                warm_xbrl_cache=True,
            )
        except Exception as exc:
            print(f"  ERROR {ticker}: {exc}", flush=True)
            manifest["tickers"][ticker] = {
                "status": "error",
                "error": str(exc),
            }
            continue

        fy = derive_fiscal_year(ticker, result.report_date)
        print(
            f"  ok: {result.form} {result.accession_number} "
            f"period_end={result.report_date} -> {fy} "
            f"xbrl={'yes' if result.xbrl_available else 'no'} "
            f"cache={'warmed' if result.xbrl_cache_warmed else 'cold'}",
            flush=True,
        )
        if result.notes:
            for note in result.notes:
                print(f"    note: {note}", flush=True)

        manifest["tickers"][ticker] = {
            "status": "ok",
            "cik": result.cik,
            "form": result.form,
            "accession_number": result.accession_number,
            "filing_date": result.filing_date,
            "report_date": result.report_date,
            "fiscal_year_label": fy,
            "dest_dir": str(result.dest_dir.resolve()),
            "primary_document": str(result.primary_document.resolve()),
            "xbrl_instance": str(result.xbrl_instance.resolve()) if result.xbrl_instance else None,
            "xbrl_available": result.xbrl_available,
            "xbrl_cache_warmed": result.xbrl_cache_warmed,
            "notes": result.notes,
        }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest: {MANIFEST_PATH.relative_to(REPO)}", flush=True)

    ok = sum(1 for t in manifest["tickers"].values() if t.get("status") == "ok")
    print(f"Downloaded: {ok}/{len(TICKERS)}", flush=True)
    return 0 if ok == len(TICKERS) else 1


if __name__ == "__main__":
    sys.exit(main())
