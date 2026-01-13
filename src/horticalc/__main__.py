from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import run_recipe, solve_recipe


def main(argv: list[str] | None = None) -> None:
    args_list = list(argv) if argv is not None else None
    if args_list is None:
        import sys

        args_list = sys.argv[1:]

    if args_list and args_list[0] == "solve":
        parser = argparse.ArgumentParser(
            prog="horticalc solve",
            description="Horticalc Solver – Solver Recipe to Nutrient Solution",
        )
        parser.add_argument(
            "recipe",
            help="Path to a Solver Recipe (YAML), e.g. recipes/solve_golden.yml",
        )
        parser.add_argument(
            "--out",
            help="Optional: JSON Ergebnis in Datei schreiben",
            default=None,
        )
        parser.add_argument(
            "--pretty",
            help="JSON hübsch formatieren",
            action="store_true",
        )
        args = parser.parse_args(args_list[1:])
        recipe_path = Path(args.recipe).expanduser().resolve()
        result = solve_recipe(recipe_path)
    else:
        parser = argparse.ArgumentParser(
            prog="horticalc",
            description="Horticalc Nutrient Solution – Recipe to Solution Output",
        )
        parser.add_argument(
            "recipe",
            help="Path to a Recipe (YAML), e.g. recipes/golden.yml",
        )
        parser.add_argument(
            "--out",
            help="Optional: JSON Ergebnis in Datei schreiben",
            default=None,
        )
        parser.add_argument(
            "--pretty",
            help="JSON hübsch formatieren",
            action="store_true",
        )
        args = parser.parse_args(args_list)
        recipe_path = Path(args.recipe).expanduser().resolve()
        result = run_recipe(recipe_path)

    if args.pretty:
        text = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        text = json.dumps(result, ensure_ascii=False)

    print(text)

    if args.out:
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
