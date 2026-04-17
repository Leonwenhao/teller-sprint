"""Corpus — thin abstraction over a directory of text documents."""
from __future__ import annotations

import re
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
        self.path = Path(path).resolve()
        self.pattern = pattern

    def describe(self) -> dict:
        """Summary for the `teller inspect` CLI command.

        Reports file count, aggregate size, filename-encoded date range
        where applicable, a small sample of file paths, and whether an
        `index.txt` file is present.
        """
        if not self.path.exists():
            return {
                "path": str(self.path),
                "pattern": self.pattern,
                "exists": False,
                "error": "corpus path does not exist",
            }

        files = sorted(f for f in self.path.glob(self.pattern) if f.is_file())
        total_bytes = sum(f.stat().st_size for f in files)
        index_file = self.path / "index.txt"

        # Try to infer a date range from YYYY or YYYY_MM patterns in filenames.
        years: set[int] = set()
        year_month_re = re.compile(r"(\d{4})(?:[_-](\d{2}))?")
        for f in files:
            match = year_month_re.search(f.stem)
            if match:
                year = int(match.group(1))
                if 1900 <= year <= 2100:
                    years.add(year)
        date_range = (min(years), max(years)) if years else None

        sample = [f.name for f in files[:5]]

        return {
            "path": str(self.path),
            "pattern": self.pattern,
            "exists": True,
            "file_count": len(files),
            "total_bytes": total_bytes,
            "total_mb": round(total_bytes / 1024 / 1024, 1),
            "date_range": date_range,
            "has_index": index_file.exists(),
            "sample_files": sample,
        }

    def index(self) -> list[str]:
        """Return the list of filenames in the corpus.

        If `index.txt` exists in the corpus directory, returns the filenames
        parsed from it (handles both relative basenames and absolute paths,
        normalizing to basenames). Otherwise returns filenames from a glob.

        Matches the shape of the Arena-winning corpus's `/app/corpus/index.txt`,
        which is a plain list of file paths.
        """
        index_file = self.path / "index.txt"
        if index_file.exists():
            names: list[str] = []
            for line in index_file.read_text().splitlines():
                line = line.strip()
                if not line:
                    continue
                name = Path(line).name
                if name and name != "index.txt":
                    names.append(name)
            if names:
                return names

        return sorted(f.name for f in self.path.glob(self.pattern) if f.is_file())
