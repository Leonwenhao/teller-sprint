#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required"
  exit 1
fi

if [ -d ".git" ]; then
  echo "EvoSkill example repo already initialized: $SCRIPT_DIR"
  exit 0
fi

cat > .evoskill/state.json <<'JSON'
{"original_branch": "main"}
JSON

git init -q
git add .
git commit -q -m "Initialize Teller EvoSkill example"

echo "Initialized isolated EvoSkill repo in $SCRIPT_DIR"
echo ""
echo "Next:"
echo "  export ANTHROPIC_API_KEY=<your-anthropic-key>"
echo "  evoskill run --verbose"
echo ""
echo "Or with OpenRouter:"
echo "  export OPENROUTER_API_KEY=<your-openrouter-key>"
echo "  evoskill run --verbose --config .evoskill/config.openrouter.toml"
