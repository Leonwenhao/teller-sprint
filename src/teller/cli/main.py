"""Click entry point for `teller` — see `teller.cli` package docstring."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click

from teller.agent import Agent
from teller.corpus import Corpus
from teller.downloaders import SecDownloader


# --------------------------------------------------------------------
# Domain inference
# --------------------------------------------------------------------


def _infer_domain(corpus_path: Path) -> str:
    """Heuristic domain detection from a corpus directory.

    - Treasury: `treasury_bulletin_YYYY_MM.txt` filenames present.
    - SEC filings: any `.htm` / `.html` files present (iXBRL).
    - Otherwise: "unknown".

    This exists so `teller ask` works without an explicit --domain flag
    for the two v0.1 domains. An explicit --domain override is always
    available for the edge cases.
    """
    if not corpus_path.exists():
        return "unknown"
    # Treasury first — if both are somehow present, prefer treasury
    # because it was the v0.1 regression canary.
    for f in corpus_path.glob("treasury_bulletin_*.txt"):
        return "treasury"
    for pattern in ("**/*.htm", "**/*.html"):
        for f in corpus_path.glob(pattern):
            if f.is_file():
                return "sec_filings"
    return "unknown"


def _corpus_pattern_for(domain: str) -> str:
    """Return the glob pattern matching the files the domain reads."""
    if domain == "treasury":
        return "*.txt"
    if domain == "sec_filings":
        return "**/*.htm"
    return "*"


# --------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------


@click.group()
@click.version_option(package_name="teller-agent", prog_name="teller")
def main() -> None:
    """Teller — grounded reasoning agent for SEC filings and enterprise docs."""


@main.command("download-sec")
@click.argument("ticker")
@click.option(
    "--latest",
    "form_latest",
    default=None,
    type=str,
    help="Fetch the latest filing of this form type (e.g. 10-K, 10-Q). Default: 10-K.",
)
@click.option(
    "--year",
    type=int,
    default=None,
    help="Fetch the filing from this filing year (YYYY). Mutually exclusive with --latest.",
)
@click.option(
    "--dest",
    "dest_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Destination directory. Defaults to ./sec_data/<TICKER>/<accession>/.",
)
@click.option(
    "--no-warm-xbrl",
    is_flag=True,
    default=False,
    help="Skip taxonomy cache pre-population. The first `teller ask` against this "
         "filing will have to populate the cache — typically adds 10–30 s on first "
         "query. Use when you have no network post-download.",
)
def download_sec(
    ticker: str,
    form_latest: Optional[str],
    year: Optional[int],
    dest_dir: Optional[Path],
    no_warm_xbrl: bool,
) -> None:
    """Download a 10-K or 10-Q from EDGAR, plus the XBRL instance."""
    if form_latest is not None and year is not None:
        click.echo(
            "error: --latest and --year are mutually exclusive.", err=True
        )
        sys.exit(2)
    form = form_latest or "10-K"

    dl = SecDownloader()
    try:
        result = dl.download_filing(
            ticker=ticker,
            form=form,
            year=year,
            dest_dir=dest_dir,
            warm_xbrl_cache=not no_warm_xbrl,
        )
    except Exception as exc:
        click.echo(f"error: {exc}", err=True)
        sys.exit(1)

    click.echo(f"Downloaded {result.ticker} {result.form} (filed {result.filing_date}, "
               f"period {result.report_date})")
    click.echo(f"  primary document : {result.primary_document}")
    if result.xbrl_instance is not None:
        click.echo(f"  XBRL instance    : {result.xbrl_instance}")
        click.echo(f"  XBRL available   : yes")
    else:
        click.echo(f"  XBRL available   : no (text-only extraction will be fallback)")
    click.echo(f"  cache warmed     : {'yes' if result.xbrl_cache_warmed else 'no'}")
    if result.notes:
        for note in result.notes:
            click.echo(f"  note: {note}")


@main.command("ask")
@click.argument("question")
@click.option(
    "--corpus",
    "corpus_dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to the corpus directory.",
)
@click.option(
    "--domain",
    default=None,
    type=str,
    help="Force domain selection (treasury, sec_filings). Auto-detected if omitted.",
)
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Emit the full Result as JSON instead of a human summary.",
)
def ask(
    question: str,
    corpus_dir: Path,
    domain: Optional[str],
    as_json: bool,
) -> None:
    """Run a grounded Q&A against the corpus."""
    if not question.strip():
        click.echo("error: question must not be empty.", err=True)
        sys.exit(2)

    domain = domain or _infer_domain(corpus_dir)
    if domain == "unknown":
        click.echo(
            "error: could not infer domain from corpus directory. "
            "Use --domain treasury or --domain sec_filings to override.",
            err=True,
        )
        sys.exit(2)

    pattern = _corpus_pattern_for(domain)
    corpus = Corpus(path=corpus_dir, pattern=pattern)
    agent = Agent(domain=domain, corpus=corpus)
    result = agent.ask(question)

    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2, default=str))
        return

    click.echo(f"Q: {result.question}")
    if result.abstained:
        click.echo(f"A: [abstained] reason={result.abstention_reason}")
    else:
        click.echo(f"A: {result.answer}")
    xv = result.xbrl_validation
    if xv.performed:
        agreed = "agreed" if xv.agreed else "disagreed"
        click.echo(f"   XBRL cross-check: {agreed} (concept={xv.gaap_concept}, tagged={xv.tagged_value})")
        if xv.note:
            click.echo(f"     {xv.note}")
    elif xv.reason:
        click.echo(f"   XBRL cross-check: not performed (reason={xv.reason})")
        if xv.note:
            click.echo(f"     {xv.note}")
    click.echo(f"   latency: {result.latency_ms} ms")


@main.command("inspect")
@click.argument(
    "corpus_dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
def inspect(corpus_dir: Path) -> None:
    """Describe a corpus directory: files, size, inferred domain, XBRL availability."""
    domain = _infer_domain(corpus_dir)
    pattern = _corpus_pattern_for(domain)
    corpus = Corpus(path=corpus_dir, pattern=pattern)
    described = corpus.describe()

    # For SEC, the default glob misses nested .htm files (they live in
    # an accession-number subdirectory). Count recursively for accuracy.
    if domain == "sec_filings":
        htm_files = [p for p in corpus_dir.rglob("*.htm") if p.is_file()]
        htm_files += [p for p in corpus_dir.rglob("*.html") if p.is_file()]
        described["file_count"] = len(htm_files)
        described["total_bytes"] = sum(p.stat().st_size for p in htm_files)
        described["total_mb"] = round(described["total_bytes"] / 1024 / 1024, 1)
        described["sample_files"] = [p.name for p in htm_files[:5]]

    xbrl_available = domain == "sec_filings" and described.get("file_count", 0) > 0

    click.echo(f"corpus         : {corpus_dir}")
    click.echo(f"inferred domain: {domain}")
    click.echo(f"file count     : {described.get('file_count', 0)}")
    click.echo(f"total size     : {described.get('total_mb', 0)} MB")
    if described.get("date_range"):
        dr = described["date_range"]
        click.echo(f"date range     : {dr[0]}–{dr[1]}")
    click.echo(f"XBRL validation: {'yes' if xbrl_available else 'no'}")
    if described.get("sample_files"):
        click.echo("sample files   : " + ", ".join(described["sample_files"]))


if __name__ == "__main__":  # pragma: no cover
    main()
