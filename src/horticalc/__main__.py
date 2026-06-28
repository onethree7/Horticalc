from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import run_recipe, solve_recipe
from .paths import resolve_recipe_path, resolve_water_profile_path
from .solver_config import add_solver_config_arguments, solver_config_overrides_from_args


def _add_common_arguments(parser: argparse.ArgumentParser, recipe_help: str) -> None:
    parser.add_argument("recipe", nargs="?", help=recipe_help)
    parser.add_argument(
        "--load-recipe",
        help="Optional: load a recipe file explicitly (overrides the positional argument)",
        default=None,
    )
    parser.add_argument(
        "--load-water",
        help="Optional: water profile file (for example, 65936.yml or a path)",
        default=None,
    )
    parser.add_argument(
        "--out",
        help="Optional: write the JSON result to a file",
        default=None,
    )
    parser.add_argument(
        "--pretty",
        help="Pretty-print the JSON output",
        action="store_true",
    )


def _resolve_cli_paths(args: argparse.Namespace, parser: argparse.ArgumentParser) -> tuple[Path, Path | None]:
    recipe_arg = args.load_recipe or args.recipe
    if not recipe_arg:
        parser.error("Recipe missing: provide a positional argument or --load-recipe.")
    recipe_path = resolve_recipe_path(recipe_arg)
    water_profile_path = resolve_water_profile_path(args.load_water) if args.load_water else None
    return recipe_path, water_profile_path


def _write_result(result: dict, args: argparse.Namespace) -> None:
    text = json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False)
    print(text)
    if args.out:
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    import sys

    args_list = list(argv) if argv is not None else sys.argv[1:]

    if args_list and args_list[0] == "solve":
        parser = argparse.ArgumentParser(
            prog="horticalc solve",
            description="Horticalc Solver – Solver Recipe to Nutrient Solution",
        )
        _add_common_arguments(parser, "Path to a Solver Recipe (YAML), e.g. recipes/solve_golden.yml")
        add_solver_config_arguments(parser)
        args = parser.parse_args(args_list[1:])
        recipe_path, water_profile_path = _resolve_cli_paths(args, parser)
        try:
            solver_config_overrides = solver_config_overrides_from_args(args)
        except (json.JSONDecodeError, ValueError) as exc:
            parser.error(str(exc))
        result = solve_recipe(
            recipe_path,
            water_profile_path=water_profile_path,
            solver_config_overrides=solver_config_overrides,
        )
    else:
        parser = argparse.ArgumentParser(
            prog="horticalc",
            description="Horticalc Nutrient Solution – Recipe to Solution Output",
        )
        _add_common_arguments(parser, "Path to a Recipe (YAML), e.g. recipes/golden.yml")
        args = parser.parse_args(args_list)
        recipe_path, water_profile_path = _resolve_cli_paths(args, parser)
        result = run_recipe(recipe_path, water_profile_path=water_profile_path)

    _write_result(result, args)


if __name__ == "__main__":
    main()
