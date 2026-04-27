#!/usr/bin/env python3
"""Render the `prompt:` block of each domain recipe from its Jinja overlay.

Single source of truth for domain prompts is the overlay .j2 file under
`src/teller/domains/<domain>/prompt.j2` (which extends
`src/teller/prompts/base.j2`). This script re-renders each overlay and
patches the `prompt: |` block of the corresponding
`src/teller/recipes/<domain>.yaml`, leaving every other recipe field
untouched (extensions, settings, activities, parameters, etc.).

Narrow by design: the recipe YAML carries goose-specific configuration
that is not derivable from the Jinja template. A full round-trip render
would lose that information. This script only touches the prompt body.

Run after any change to `src/teller/prompts/base.j2` or a domain overlay .j2.

Currently handled:
  - sec_filings (src/teller/domains/sec_filings/prompt.j2 + src/teller/prompts/base.j2)

Treasury recipe is hand-maintained for day-3 scope — it predates the
base.j2 split and regenerating would require a treasury overlay .j2
which is future work.

Usage:
    python3 scripts/render_recipes.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RECIPES = REPO / "src" / "teller" / "recipes"


def render_sec_filings_prompt() -> str:
    """Render the SEC filings prompt from its Jinja overlay.

    Leaves `{{ instruction }}` intact so goose substitutes at run time
    via `--params instruction=...`.
    """
    from jinja2 import Environment, FileSystemLoader

    env = Environment(
        loader=FileSystemLoader([
            str(REPO / "src" / "teller" / "domains" / "sec_filings"),
            str(REPO / "src" / "teller" / "prompts"),
        ]),
        keep_trailing_newline=True,
    )
    template = env.get_template("prompt.j2")
    # The base.j2 template has `{{ instruction }}` as its last line.
    # Rendering with the literal string preserves that placeholder for
    # goose to fill in.
    return template.render(instruction="{{ instruction }}")


def patch_prompt_block(recipe_path: Path, new_prompt: str) -> None:
    """Replace the `prompt: |` block of a recipe YAML, preserving everything else.

    Assumes:
      - `prompt: |` starts the prompt block at column 0.
      - The prompt block is indented by 2 spaces on every content line.
      - The next top-level key at column 0 (alphanum followed by `:`)
        ends the prompt block.
    """
    text = recipe_path.read_text()

    # Find the `prompt: |` line
    m = re.search(r"^prompt:[ \t]*\|[ \t]*\n", text, re.MULTILINE)
    if not m:
        raise RuntimeError(f"{recipe_path}: no `prompt: |` block found")
    block_start = m.end()

    # Find the end: the next line starting with a non-whitespace, non-#
    # character at column 0. This is the start of the next top-level YAML
    # key.
    after = text[block_start:]
    end_m = re.search(r"^(?=[A-Za-z_])", after, re.MULTILINE)
    if not end_m:
        # Prompt is the last block in the file
        block_end = len(text)
    else:
        block_end = block_start + end_m.start()

    # Indent the new prompt by 2 spaces per line (matching YAML block scalar)
    indented = "\n".join("  " + line if line else "" for line in new_prompt.splitlines())
    # Ensure trailing newline before the next top-level key
    if not indented.endswith("\n"):
        indented += "\n"

    patched = text[:block_start] + indented + text[block_end:]
    recipe_path.write_text(patched)


def main() -> int:
    sec_recipe = RECIPES / "sec_filings.yaml"
    if not sec_recipe.exists():
        print(f"ERROR: {sec_recipe} does not exist — cannot patch", file=sys.stderr)
        return 1

    rendered = render_sec_filings_prompt()
    patch_prompt_block(sec_recipe, rendered)
    size = sec_recipe.stat().st_size
    print(f"Patched {sec_recipe.relative_to(REPO)}  ({size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
