"""Downloaders fetch external documents into a local working directory.

Each downloader is responsible for polite rate-limiting against its
upstream source and for surfacing a `DownloadResult` that the Agent
and the CLI can consume without knowing the transport details.
"""

from teller.downloaders.sec import DownloadResult, SecDownloader

__all__ = ["DownloadResult", "SecDownloader"]
