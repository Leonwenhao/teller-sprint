"""SEC EDGAR downloader for 10-K / 10-Q filings.

Fetches the primary document (inline-XBRL `.htm` for modern filings)
and, when available, the separate XBRL instance document, and stores
them to a working directory for downstream consumption by
`teller.validation.xbrl.lookup_fact` and the LLM agent.

Rate-limit policy. SEC EDGAR enforces a 10-request-per-second cap per
user-agent. This module enforces the cap locally via monotonic
spacing so a single `teller download-sec` invocation cannot trip the
limit even under multi-filing batch work. The user-agent header
identifies Dolores Research (Leon's contact) per SEC's stated
requirement; a missing or generic user-agent is the fastest path to
being hard-rate-limited and is not attempted.

Taxonomy cache pre-population (ADR-002). After a successful download,
this module optionally triggers arelle ONCE in online mode to
discover and cache the filing's referenced taxonomies. That is the
only place online XBRL I/O happens; the ask-path parser
(`lookup_fact`) runs arelle in offline mode and never fetches mid-
inference. Failure to pre-warm the cache is non-fatal: downstream
`lookup_fact` will surface `reason="xbrl_taxonomy_uncached"` on a
cache miss so the user can re-run the download.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

__all__ = ["DownloadResult", "SecDownloader", "TickerNotFoundError", "NoMatchingFilingError"]

_LOG = logging.getLogger("teller.downloaders.sec")


USER_AGENT = "Dolores Research (leon@dolores.research)"
SEC_BASE = "https://www.sec.gov"
SEC_DATA = "https://data.sec.gov"
TICKER_CIK_URL = f"{SEC_BASE}/files/company_tickers.json"
DEFAULT_RATE_LIMIT_RPS = 10.0


class TickerNotFoundError(LookupError):
    """Raised when a ticker does not resolve to any SEC CIK."""


class NoMatchingFilingError(LookupError):
    """Raised when no filing matches the form/year constraints."""


@dataclass
class FilingMeta:
    """One filing row from the SEC submissions JSON."""

    accession_number: str  # e.g. "0000320193-24-000123"
    form: str              # "10-K", "10-Q", "10-K/A", ...
    filing_date: str       # ISO
    report_date: str       # ISO — period covered
    primary_document: str  # relative filename, e.g. "aapl-20240928.htm"


@dataclass
class DownloadResult:
    """Outcome of a single `download_filing` call.

    `xbrl_instance` points at the primary document for modern inline-
    XBRL filings (iXBRL embeds the instance in the .htm). When a
    filing predates iXBRL or otherwise ships a separate .xml instance,
    this field may diverge from `primary_document`. `xbrl_available`
    is the honest signal for the agent: if False, text-only extraction
    is the fallback path per the dev-plan §day-2 scope.
    """

    ticker: str
    cik: str
    form: str
    filing_date: str
    report_date: str
    accession_number: str
    dest_dir: Path
    primary_document: Path
    xbrl_instance: Optional[Path]
    xbrl_available: bool
    xbrl_cache_warmed: bool
    notes: list[str] = field(default_factory=list)


class _RateLimiter:
    """Monotonic-clock rate limiter with per-instance thread safety.

    `await_slot()` blocks until at least `1 / max_rps` seconds have
    elapsed since the previous call. Shared across threads via a
    lock so a single SecDownloader instance respects the cap even if
    a caller parallelizes downloads.
    """

    def __init__(self, max_rps: float) -> None:
        if max_rps <= 0:
            raise ValueError("max_rps must be positive")
        self._min_interval = 1.0 / max_rps
        self._last = 0.0
        self._lock = threading.Lock()

    def await_slot(self) -> None:
        with self._lock:
            now = time.monotonic()
            wait = self._min_interval - (now - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()


class SecDownloader:
    """Polite EDGAR client for 10-K / 10-Q + XBRL instance retrieval."""

    def __init__(
        self,
        rate_limit_rps: float = DEFAULT_RATE_LIMIT_RPS,
        user_agent: str = USER_AGENT,
    ) -> None:
        self._rate_limiter = _RateLimiter(rate_limit_rps)
        self._user_agent = user_agent
        self._cik_cache: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download_filing(
        self,
        ticker: str,
        form: str = "10-K",
        year: Optional[int] = None,
        dest_dir: Optional[Path] = None,
        warm_xbrl_cache: bool = True,
    ) -> DownloadResult:
        """Fetch one filing and its XBRL instance into `dest_dir`.

        Args:
            ticker: company ticker, e.g. `"AAPL"`. Case-insensitive.
            form: form type, default `"10-K"`. `"10-Q"` also supported.
                Matches `.startswith(form)` so amendments like
                `"10-K/A"` also match.
            year: optional filing year (calendar year of filing, not
                fiscal year). If None, picks the most recent filing.
            dest_dir: directory to write the downloaded files into.
                Created if missing. Defaults to
                `./sec_data/<ticker>/<accession_number>/`.
            warm_xbrl_cache: when True (default), trigger arelle in
                online mode once to pre-populate the taxonomy cache.
                Required for `teller ask` to run offline later.

        Returns:
            `DownloadResult` with paths to the primary document and
            (when available) XBRL instance, plus a `xbrl_cache_warmed`
            flag indicating whether the cache pre-population
            succeeded.
        """
        ticker_upper = ticker.upper()
        cik = self.resolve_cik(ticker_upper)
        filings = self._list_recent_filings(cik)
        chosen = self._pick_filing(filings, form=form, year=year)

        dest_dir = self._resolve_dest_dir(dest_dir, ticker_upper, chosen)
        dest_dir.mkdir(parents=True, exist_ok=True)

        primary_path = self._download_document(
            cik=cik,
            accession_number=chosen.accession_number,
            filename=chosen.primary_document,
            dest_dir=dest_dir,
        )

        xbrl_instance, xbrl_available, notes = self._resolve_xbrl_instance(
            primary_path=primary_path,
            cik=cik,
            accession_number=chosen.accession_number,
            dest_dir=dest_dir,
        )

        warmed = False
        if warm_xbrl_cache and xbrl_instance is not None:
            warmed = self._warm_xbrl_cache(xbrl_instance)

        return DownloadResult(
            ticker=ticker_upper,
            cik=cik,
            form=chosen.form,
            filing_date=chosen.filing_date,
            report_date=chosen.report_date,
            accession_number=chosen.accession_number,
            dest_dir=dest_dir,
            primary_document=primary_path,
            xbrl_instance=xbrl_instance,
            xbrl_available=xbrl_available,
            xbrl_cache_warmed=warmed,
            notes=notes,
        )

    def resolve_cik(self, ticker: str) -> str:
        """Return the 10-digit zero-padded CIK for `ticker`.

        Caches results in memory for the lifetime of the
        `SecDownloader` instance. The ticker table is small (~10 k
        rows) so a single fetch per session is fine.
        """
        ticker = ticker.upper()
        if ticker in self._cik_cache:
            return self._cik_cache[ticker]
        body = self._get(TICKER_CIK_URL)
        table = json.loads(body)
        for row in table.values():
            if row.get("ticker", "").upper() == ticker:
                cik_int = int(row["cik_str"])
                cik_padded = f"{cik_int:010d}"
                self._cik_cache[ticker] = cik_padded
                return cik_padded
        raise TickerNotFoundError(
            f"Ticker '{ticker}' not found in SEC company tickers JSON"
        )

    # ------------------------------------------------------------------
    # Filing discovery
    # ------------------------------------------------------------------

    def _list_recent_filings(self, cik: str) -> list[FilingMeta]:
        """Parse the `recent` block of the submissions JSON.

        For v0.1 we only read the `recent` inline block (approximately
        the last 1000 filings per company). Companies with deep
        filing histories have overflow files pointed to by
        `filings.files[]`, but for 10-K / 10-Q needs of our target
        use case (last-few-years earnings-season work), `recent` is
        always sufficient. Paging is a v0.2 backlog item.
        """
        url = f"{SEC_DATA}/submissions/CIK{cik}.json"
        body = self._get(url)
        data = json.loads(body)
        recent = data.get("filings", {}).get("recent", {})
        accs = recent.get("accessionNumber", [])
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        primary_docs = recent.get("primaryDocument", [])
        n = min(len(accs), len(forms), len(filing_dates), len(primary_docs))
        return [
            FilingMeta(
                accession_number=accs[i],
                form=forms[i],
                filing_date=filing_dates[i],
                report_date=report_dates[i] if i < len(report_dates) else "",
                primary_document=primary_docs[i],
            )
            for i in range(n)
        ]

    def _pick_filing(
        self,
        filings: list[FilingMeta],
        form: str,
        year: Optional[int],
    ) -> FilingMeta:
        """Pick the target filing by form + optional filing year."""
        matches = [f for f in filings if f.form.startswith(form)]
        if year is not None:
            matches = [f for f in matches if f.filing_date.startswith(str(year))]
        if not matches:
            raise NoMatchingFilingError(
                f"No {form} filing found"
                + (f" for filing year {year}" if year else " in recent filings")
            )
        # Filings are already in reverse-chronological order in the
        # submissions JSON, but sort defensively.
        matches.sort(key=lambda f: f.filing_date, reverse=True)
        return matches[0]

    # ------------------------------------------------------------------
    # Document fetching
    # ------------------------------------------------------------------

    def _download_document(
        self,
        cik: str,
        accession_number: str,
        filename: str,
        dest_dir: Path,
    ) -> Path:
        """Fetch one document from the filing archive into `dest_dir`."""
        url = self._archives_url(cik, accession_number, filename)
        body = self._get(url)
        out = dest_dir / filename
        out.write_bytes(body)
        return out

    def _resolve_xbrl_instance(
        self,
        primary_path: Path,
        cik: str,
        accession_number: str,
        dest_dir: Path,
    ) -> tuple[Optional[Path], bool, list[str]]:
        """Locate the XBRL instance document and its support files.

        Modern 10-K / 10-Q filings (post-2019 for 10-K) embed XBRL
        inline within the primary `.htm` document (iXBRL). For those
        filings, `primary_path` *is* the instance. However, arelle
        still needs the company's taxonomy extension files colocated
        on disk — the company-specific `.xsd` schema and the four
        standard linkbases (`_cal.xml`, `_def.xml`, `_lab.xml`,
        `_pre.xml`). Without them arelle reports
        `ix11.12.1.2:missingReferences` on every us-gaap concept and
        `factsByQname` returns an empty set.

        This method fetches the XBRL support files for both iXBRL and
        separate-instance layouts, returning the instance path and a
        success flag.
        """
        notes: list[str] = []
        stem = primary_path.stem  # e.g. "aapl-20250927"
        support_files = [
            f"{stem}.xsd",
            f"{stem}_cal.xml",
            f"{stem}_def.xml",
            f"{stem}_lab.xml",
            f"{stem}_pre.xml",
        ]

        missing_support: list[str] = []
        for filename in support_files:
            try:
                self._download_document(
                    cik=cik,
                    accession_number=accession_number,
                    filename=filename,
                    dest_dir=dest_dir,
                )
            except Exception as exc:
                missing_support.append(f"{filename}: {exc}")

        if missing_support:
            notes.append(
                "some XBRL support files could not be fetched; arelle "
                "may fall back to online taxonomy resolution: "
                + "; ".join(missing_support[:3])
            )

        if primary_path.suffix.lower() in {".htm", ".html"}:
            return primary_path, True, notes

        # Older filings: inspect filing index for a separate .xml instance.
        index_url = self._archives_url(cik, accession_number, "index.json")
        try:
            index_body = self._get(index_url)
            index = json.loads(index_body)
        except Exception as exc:
            notes.append(f"filing index not available: {exc}")
            return None, False, notes

        items = index.get("directory", {}).get("item", [])
        candidates = [
            it["name"]
            for it in items
            if isinstance(it.get("name"), str)
            and it["name"].lower().endswith(".xml")
            and "_htm" in it["name"].lower()
        ]
        if not candidates:
            notes.append(
                "no separate XBRL instance found in filing archive; "
                "text-only extraction will be the fallback path"
            )
            return None, False, notes

        instance_name = candidates[0]
        path = self._download_document(
            cik=cik,
            accession_number=accession_number,
            filename=instance_name,
            dest_dir=dest_dir,
        )
        return path, True, notes

    # ------------------------------------------------------------------
    # XBRL cache warm-up (ADR-002)
    # ------------------------------------------------------------------

    def _warm_xbrl_cache(self, instance_path: Path) -> bool:
        """Pre-populate arelle's taxonomy cache for `instance_path`.

        Runs arelle ONCE in online mode. Any exception is swallowed
        and logged: the downloader's contract is "filing is on disk,"
        not "XBRL validation is guaranteed to work." A subsequent
        `teller ask` on a filing with an uncached taxonomy will
        abstain with `reason="xbrl_taxonomy_uncached"` and prompt
        the user to re-run download-sec.
        """
        try:
            # Lazy import — keeps the downloader usable when arelle
            # is not installed (future optional-extra path).
            from arelle.api.Session import Session
            from arelle.RuntimeOptions import RuntimeOptions
            from teller.validation.xbrl import _run_arelle_session
        except Exception as exc:  # pragma: no cover
            _LOG.warning("arelle unavailable; skipping XBRL cache warm: %s", exc)
            return False

        cache_dir = os.environ.get("TELLER_XBRL_CACHE_DIR")
        session = Session()
        try:
            options = RuntimeOptions(
                entrypointFile=str(instance_path),
                internetConnectivity="online",
                keepOpen=False,
                logLevel="warning",
                cacheDirectory=cache_dir,
            )
            ok = _run_arelle_session(session, options)
            if not ok:
                _LOG.warning(
                    "XBRL cache warm-up reported not-ok for %s", instance_path
                )
            return bool(ok)
        except Exception as exc:
            _LOG.warning("XBRL cache warm-up failed for %s: %s", instance_path, exc)
            return False
        finally:
            try:
                session.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _get(self, url: str, timeout: float = 30.0) -> bytes:
        """Rate-limited HTTP GET with SEC-required user-agent."""
        self._rate_limiter.await_slot()
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self._user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": self._host_for(url),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return _read_maybe_gzipped(resp)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"SEC request failed with HTTP {exc.code} for {url}: {exc.reason}"
            ) from exc

    @staticmethod
    def _host_for(url: str) -> str:
        # Kept simple; EDGAR serves from www.sec.gov and data.sec.gov.
        if "data.sec.gov" in url:
            return "data.sec.gov"
        return "www.sec.gov"

    # ------------------------------------------------------------------
    # URL + path helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _archives_url(cik: str, accession_number: str, filename: str) -> str:
        cik_int = int(cik)
        acc_nodash = accession_number.replace("-", "")
        return (
            f"{SEC_BASE}/Archives/edgar/data/{cik_int}/{acc_nodash}/{filename}"
        )

    @staticmethod
    def _resolve_dest_dir(
        dest_dir: Optional[Path],
        ticker: str,
        filing: FilingMeta,
    ) -> Path:
        if dest_dir is not None:
            return Path(dest_dir)
        return Path("sec_data") / ticker / filing.accession_number


def _read_maybe_gzipped(resp) -> bytes:
    """Decode gzip/deflate response bodies; pass plain bytes through."""
    import gzip
    import zlib

    raw = resp.read()
    encoding = resp.headers.get("Content-Encoding", "").lower()
    if "gzip" in encoding:
        return gzip.decompress(raw)
    if "deflate" in encoding:
        return zlib.decompress(raw)
    return raw
