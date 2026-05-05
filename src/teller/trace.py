"""Local trace persistence for Teller runs."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Optional


_MAX_STREAM_CHARS = 20_000


@dataclass
class AttemptTrace:
    attempt: int
    session_name: str
    cwd: str
    recipe_path: str
    timeout_seconds: int
    timed_out: bool = False
    returncode: Optional[int] = None
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""
    answer_file_exists: bool = False
    answer_file_bytes: int = 0
    latency_ms: int = 0
    classification: Optional[str] = None


@dataclass
class RunTrace:
    trace_id: str
    question: str
    domain: str
    corpus_path: str
    model: dict[str, Any]
    started_at_unix: float
    trace_path: Optional[str] = None
    attempts: list[AttemptTrace] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @classmethod
    def create(cls, *, question: str, domain: str, corpus_path: Path, model) -> "RunTrace":
        return cls(
            trace_id=uuid.uuid4().hex,
            question=question,
            domain=domain,
            corpus_path=str(corpus_path),
            model=asdict(model),
            started_at_unix=time.time(),
            environment=environment_diagnostics(),
        )

    @property
    def enabled(self) -> bool:
        return os.environ.get("TELLER_TRACE_DISABLED") != "1"

    def write(self) -> Optional[Path]:
        if not self.enabled:
            return None
        trace_dir = Path(os.environ.get("TELLER_TRACE_DIR", ".teller/traces")).resolve()
        trace_dir.mkdir(parents=True, exist_ok=True)
        path = trace_dir / f"{self.trace_id}.json"
        self.trace_path = str(path)
        path.write_text(json.dumps(asdict(self), indent=2, sort_keys=True))
        return path


def environment_diagnostics() -> dict[str, Any]:
    goose_path = shutil.which("goose")
    goose_version = None
    if goose_path:
        try:
            proc = subprocess.run(
                [goose_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            goose_version = (proc.stdout or proc.stderr).strip()
        except Exception as exc:  # pragma: no cover - diagnostic best effort
            goose_version = f"unavailable: {exc.__class__.__name__}"
    try:
        package_version = version("teller-agent")
    except PackageNotFoundError:
        package_version = "unknown"
    return {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "package_version": package_version,
        "goose_path": goose_path,
        "goose_version": goose_version,
    }


def excerpt(text: Optional[str], limit: int = _MAX_STREAM_CHARS) -> str:
    if not text:
        return ""
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + "\n...[truncated]...\n" + text[-half:]


def classify_stderr(stderr: str) -> Optional[str]:
    lowered = stderr.lower()
    provider_signals = (
        "stream",
        "decode",
        "provider",
        "openrouter",
        "upstream",
        "connection reset",
        "incomplete chunk",
        "unexpected eof",
    )
    if any(signal in lowered for signal in provider_signals):
        return "provider_stream_error"
    return None
