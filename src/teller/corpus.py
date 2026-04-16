"""Corpus — thin abstraction over a directory of text documents."""
from __future__ import annotations

from pathlib import Path


class Corpus:
    """A directory of text files exposed as a grep-indexed corpus.

    Retrieval is grep-based, matching the pattern used by the Arena-winning
    agent on the Treasury Bulletin corpus. No embeddings, no vector search,
    no RAG. A future release may add semantic retrieval as an alternative;
    that is a v0.3+ concern.

    Example::

        from teller import Corpus

        corpus = Corpus("./sec_data")
        info = corpus.describe()
        # {'path': './sec_data', 'file_count': 4, 'pattern': '*.txt', ...}
    """

    def __init__(self, path: str | Path, pattern: str = "*.txt") -> None:
        self.path = Path(path)
        self.pattern = pattern

    def describe(self) -> dict:
        """Summary for the `teller inspect` CLI command.

        Reports file count, aggregate size, filename-encoded date range
        where applicable, a small sample of file paths, and whether an
        `index.txt` file is present. Implements the corpus-introspection
        leap from the v0.1 strategy synthesis (Revised_TELLER_STRATEGY.md
        Section 4).
        """
        raise NotImplementedError("Corpus.describe is stubbed in v0.1 day-1 scaffold")

    def index(self) -> dict[str, str]:
        """Return a filename → one-line summary index.

        Matches the format used by the Arena-winning agent's `index.txt`
        in the Treasury Bulletin corpus at `/app/corpus/index.txt`.
        """
        raise NotImplementedError("Corpus.index is stubbed in v0.1 day-1 scaffold")
