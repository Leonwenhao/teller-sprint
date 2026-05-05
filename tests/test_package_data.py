from __future__ import annotations

import importlib.resources as resources


def test_required_package_data_is_available():
    root = resources.files("teller")

    required = [
        "recipes/treasury.yaml",
        "recipes/sec_filings.yaml",
        "prompts/base.j2",
        "prompts/_source_goose_prompt.j2",
        "domains/treasury/prompt.j2",
        "domains/sec_filings/prompt.j2",
    ]

    for rel in required:
        assert (root / rel).is_file(), rel
