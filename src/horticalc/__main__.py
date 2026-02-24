from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import run_recipe, solve_recipe
from .paths import resolve_recipe_path, resolve_water_profile_path


def _solve_diag_summary(payload: dict) -> str | None:
    diagnostics = payload.get("diagnostics") or {}
    if not isinstance(diagnostics, dict):
        return None
    active = []
    for key in (
        "n_split_conflict",
        "n_form_infeasible_with_basis",
        "co_delivery_pressure_P",
        "co_delivery_pressure_Ca",
        "n_failsafe_triggered",
    ):
        if diagnostics.get(key):
            active.append(key)
    if not active:
        return None
    dominant = diagnostics.get("dominant_n_fertilizers") or []
    dominant_text = f" dominant_n={','.join(dominant)}" if dominant else ""
    return f"[solve diagnostics] {';'.join(active)}{dominant_text}"


def main(argv: list[str] | None = None) -> None:
    import sys

    args_list = list(argv) if argv is not None else sys.argv[1:]

    if args_list and args_list[0] == "solve":
        parser = argparse.ArgumentParser(
            prog="horticalc solve",
            description="Horticalc Solver – Solver Recipe to Nutrient Solution",
        )
        parser.add_argument(
            "recipe",
            nargs="?",
            help="Path to a Solver Recipe (YAML), e.g. recipes/solve_golden.yml",
        )
        parser.add_argument(
            "--load-recipe",
            help="Optional: Recipe-Datei explizit laden (überschreibt positional)",
            default=None,
        )
        parser.add_argument(
            "--load-water",
            help="Optional: Wasserprofil-Datei (z.B. 65936.yml oder Pfad)",
            default=None,
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
        recipe_arg = args.load_recipe or args.recipe
        if not recipe_arg:
            parser.error("Recipe fehlt: positional oder --load-recipe angeben.")
        recipe_path = resolve_recipe_path(recipe_arg)
        water_profile_path = None
        if args.load_water:
            water_profile_path = resolve_water_profile_path(args.load_water)
        result = solve_recipe(recipe_path, water_profile_path=water_profile_path)
    else:
        parser = argparse.ArgumentParser(
            prog="horticalc",
            description="Horticalc Nutrient Solution – Recipe to Solution Output",
        )
        parser.add_argument(
            "recipe",
            nargs="?",
            help="Path to a Recipe (YAML), e.g. recipes/golden.yml",
        )
        parser.add_argument(
            "--load-recipe",
            help="Optional: Recipe-Datei explizit laden (überschreibt positional)",
            default=None,
        )
        parser.add_argument(
            "--load-water",
            help="Optional: Wasserprofil-Datei (z.B. 65936.yml oder Pfad)",
            default=None,
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
        recipe_arg = args.load_recipe or args.recipe
        if not recipe_arg:
            parser.error("Recipe fehlt: positional oder --load-recipe angeben.")
        recipe_path = resolve_recipe_path(recipe_arg)
        water_profile_path = None
        if args.load_water:
            water_profile_path = resolve_water_profile_path(args.load_water)
        result = run_recipe(recipe_path, water_profile_path=water_profile_path)

    if args.pretty:
        text = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        text = json.dumps(result, ensure_ascii=False)

    print(text)

    if args_list and args_list[0] == "solve":
        result_payload = result if isinstance(result, dict) else result.to_dict()
        summary = _solve_diag_summary(result_payload)
        if summary:
            print(summary, file=sys.stderr)

    if args.out:
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
