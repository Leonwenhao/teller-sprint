"""Command-line interface for the `teller` package.

Three commands are exposed:

- `teller ask --corpus ./sec_data "<question>"` — run Agent.ask
- `teller download-sec AAPL --latest 10-K` — fetch an EDGAR filing
- `teller inspect ./sec_data` — describe a corpus directory

The CLI is a thin shell over the public Python API (`Agent`, `Corpus`,
`SecDownloader`). Everything it does can be done programmatically.
"""

from teller.cli.main import main

__all__ = ["main"]
