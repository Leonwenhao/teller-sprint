#!/usr/bin/env python3
"""Non-live GA release checks for Teller.

This script intentionally avoids OpenRouter and SEC network calls. It verifies
the installed package, CLI, package data, and unit suite from the current
environment. Run live smoke/regression gates separately with an explicit
OPENROUTER_API_KEY.
"""
from __future__ import annotations

import argparse
import importlib.resources as resources
import subprocess
import sys


def run(cmd: list[str]) -> int:
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    from teller import Agent, Corpus, Result  # noqa: F401

    root = resources.files("teller")
    required = [
        "recipes/treasury.yaml",
        "recipes/sec_filings.yaml",
        "prompts/base.j2",
        "domains/treasury/prompt.j2",
        "domains/sec_filings/prompt.j2",
    ]
    missing = [rel for rel in required if not (root / rel).is_file()]
    if missing:
        print(f"missing package data: {missing}", file=sys.stderr)
        return 1

    if run([sys.executable, "-m", "teller.cli", "--help"]) != 0:
        return 1

    if not args.skip_tests and run([sys.executable, "-m", "pytest"]) != 0:
        return 1

    print("release_check: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
