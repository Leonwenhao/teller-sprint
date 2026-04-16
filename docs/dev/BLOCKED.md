# Active Blockers

Blockers only. When resolved, move the entry to the end of the file under `## Resolved` with a resolution note.

---

## BLOCK-01 — Treasury corpus location

**Opened:** 2026-04-16 Day 1 afternoon
**Status:** Open
**Blocks:** Day-1 Corpus abstraction validation; day-1 evening 20-question regression; every subsequent daily regression.
**Owner:** Leon decision required.

### Question

Where do the parsed Treasury Bulletin TXT files live, and how do we make them available to `tests/fixtures/treasury_bulletins/` for the self-contained regression?

### Context

Your Tier-1 answer: *"The parsed Treasury Bulletin TXT files are in the arena-cohort0/ repo under the data directory used during Arena iteration. Copy them into the new teller/ repo under `tests/fixtures/treasury_bulletins/` and commit them."*

Repo state as of 2026-04-16 afternoon: zero `treasury_bulletin_*.txt` files in `arena-cohort0/`. No `data/`, `corpus/`, or similar directory. The file `arena-cohort0/scripts/standalone_eval.py:40` defines `CORPUS_IMAGE = "ghcr.io/sentient-agi/harbor/officeqa-corpus:latest"`; the Arena harness mounts that image at `/app/corpus/` inside the task container at runtime. The corpus was never a repo artifact.

### Options

| Option | Approach | Repo size delta | Self-contained on fresh clone? |
|---|---|---|---|
| **A** (recommended) | Pull the Docker image once, extract 697 TXT files, commit to `tests/fixtures/treasury_bulletins/` | +80-150 MB | Yes |
| **B** | Commit only the TXT files covering the 20 regression questions | +small | Yes for regression; no for `Corpus.describe()` behavior |
| **C** | Provide `scripts/pull_corpus.sh`; no corpus in repo | 0 | No — requires Docker on first run |
| **Middle** | Stratified ~80-file subset (roughly one per year + retrospective bulletins) exercises retrieval-pattern space at ~15 MB | +15 MB | Yes for most regression paths |

### Recommendation

Option A unless 80-150 MB is a dealbreaker for a launch repo, in which case the stratified ~80-file middle path. Options B and C both fail the self-contained-regression goal explicitly stated in your Tier-1 answer.

### What Unblocks

Leon's choice among A / B / C / middle, and (if A or middle) approval to extract from the Sentient-hosted Docker image for redistribution in this open-source repo. (Public-domain Treasury Bulletins, already text; redistribution is legal; README credits the Sentient Arena parsing.)

---

## Resolved

_(None yet.)_
