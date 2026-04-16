# Treasury Bulletin Corpus — Test Fixtures

This directory contains the parsed text corpus used by Teller's treasury-domain
regression tests. It is the same corpus used to calibrate the #1 submission on
Sentient Arena Cohort 0 (71.5% accuracy, score 187.823; peak 192.046) and is
kept in-repo so that `pytest tests/` runs self-contained on a fresh clone.

## Contents

- `index.txt` — file listing with one-line summaries (format matches `/app/corpus/index.txt` inside the Arena evaluation container).
- `treasury_bulletin_YYYY_MM.txt` — one file per monthly Treasury Bulletin issue, parsed from the original PDFs to UTF-8 text with tables preserved in pipe-delimited Markdown format. Time coverage: January 1939 through early 2025. Total: 697 bulletin files plus `index.txt`.

## Provenance

These documents are **public-domain primary sources** published by the U.S. Department of the Treasury as part of its statutory reporting obligations. They were parsed from PDF to machine-readable text by Databricks as the corpus for the OfficeQA benchmark, which is the basis of the Sentient Arena evaluation.

- **Original source:** U.S. Department of the Treasury. [Treasury Bulletin archive](https://home.treasury.gov/data/treasury-bulletin).
- **Parsed text corpus:** Databricks, *OfficeQA: Grounded Reasoning Over Enterprise Documents*, 2026. arXiv [2603.08655](https://arxiv.org/abs/2603.08655).
- **Container image distributed by:** Sentient AGI, `ghcr.io/sentient-agi/harbor/officeqa-corpus:latest` (`sha256:…`, image ID `03897cd515ec` at time of export; 725 MB image, 379 MB corpus).
- **License:** U.S. government works are not subject to copyright in the United States (17 U.S.C. § 105). The parsed text derivative is redistributed under the same public-domain status.

## Why They Are In This Repo (Not Pulled At Test Time)

1. **Self-contained regression.** A fresh `git clone` plus `pip install -e .` plus `pytest tests/` runs the treasury regression without Docker, a network connection, or access to Sentient's container registry.
2. **Version-pinning.** The Arena behavior was calibrated against this exact parse. Future drift in the upstream Docker image cannot silently change what the regression is measuring.
3. **No external-infrastructure dependency.** Sentient Arena Cohort 0 is over. While the Docker image is presumably stable for now, there is no contract that keeps it alive indefinitely. The regression test should not have a failure mode tied to a third-party container registry's uptime.

## Size Notes

- Total on disk (working tree): **379 MB**.
- Git pack size (clone transfer): **~95 MB** (git uses delta compression internally).
- Per-file: average 544 KB, max 1.3 MB, min 0 bytes (some early-period issues are empty in the parse).

If repository size becomes a concern at launch, a v0.1.1 option is to switch to per-file gzip (`.txt.gz`, same ~95 MB total, transparent decompression in `Corpus.load`) or to git-lfs. Both are reversible.

## Do Not Edit These Files

This directory is treated as read-only test data. Any editing breaks the assumption that the regression measures the same behavior as the Arena-winning submission. If a parse error is discovered, the fix lives in a patch function in `src/teller/domains/treasury/` rather than as an in-place edit of the source text.
