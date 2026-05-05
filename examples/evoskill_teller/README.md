# Teller + EvoSkill

This example makes Teller usable as an EvoSkill project.

Teller came out of Sentient Arena Cohort 0. EvoSkill is the natural follow-on:
it can take real financial-QA failures, propose improvements to the Teller agent
skill, evaluate those changes, and keep the best-performing skill variants as
git-versioned agent programs.

Use this example when you want to:

- evolve the Teller skill from SEC/Treasury failure cases.
- compare agent runtimes such as Claude Code, Codex, OpenCode, Goose, or OpenHands.
- build a Sentient-aligned demo around financial-agent skill evolution.
- contribute better Teller onboarding, debugging, and domain workflows without
  changing Teller's deterministic XBRL core.

## What This Example Contains

```text
examples/evoskill_teller/
├── .evoskill/
│   ├── config.toml              # Claude Code default
│   ├── config.openrouter.toml   # OpenRouter via OpenHands
│   └── task.md                  # Teller-specific agent task
├── .claude/skills/teller/
│   └── SKILL.md                 # seed skill EvoSkill can edit/evolve
├── data/
│   └── teller_evoskill_sample.csv
├── README.md
└── setup.sh
```

The sample CSV is intentionally small. It is a seed benchmark for skill
evolution, not Teller's authoritative release gate.

## Prerequisites

Install Teller from this repo or from the package:

```bash
pip install teller-agent
teller doctor
```

Install EvoSkill separately:

```bash
git clone https://github.com/sentient-agi/EvoSkill /tmp/EvoSkill
cd /tmp/EvoSkill
pip install -e .
```

Install at least one EvoSkill-supported agent runtime. Claude Code is the
simplest default; OpenRouter-backed runs can use OpenHands/OpenCode/Goose.

## Setup

From the Teller repo:

```bash
cd examples/evoskill_teller
bash setup.sh
```

This initializes an isolated git repo inside `examples/evoskill_teller` so
EvoSkill's `program/*` branches and frontier tags do not touch the Teller repo.

## Run With Claude Code

```bash
export ANTHROPIC_API_KEY=<your-anthropic-key>
evoskill run --verbose
```

## Run With OpenRouter

```bash
export OPENROUTER_API_KEY=<your-openrouter-key>
evoskill run --verbose --config .evoskill/config.openrouter.toml
```

## Inspect Results

```bash
evoskill skills
evoskill diff
evoskill logs
```

EvoSkill writes evolved skills under `.claude/skills/` and versions programs as
git branches. If a discovered skill materially improves Teller workflows, port
the relevant instructions back to the root `skills/teller/SKILL.md`.

## Design Notes

- Teller's core package does not depend on EvoSkill.
- EvoSkill should evolve agent instructions and workflows, not Teller's XBRL
  parser or SEC fast path.
- Keep generated skills concise and code-true.
- Do not persist provider API keys in traces, logs, skills, or benchmarks.
- Treat Treasury/general corpus questions as experimental; use them to discover
  useful skills, not to claim deterministic product behavior.
