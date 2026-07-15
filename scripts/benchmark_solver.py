from __future__ import annotations

import argparse
import time
from pathlib import Path

from horticalc.data_io import load_fertilizers, load_molar_masses, load_nutrient_solution_data
from horticalc.paths import repo_root
from horticalc.solver import solve_recipe_data

DEFAULT_SOLUTION = repo_root() / "data" / "nutrient_solutions" / "Hoagland_Arnon_1950_Solution1_Nitrate.yml"
DEFAULT_LITERS = 10.0
DEFAULT_ITERATIONS = 3
DEFAULT_BASELINE_SECONDS = 2.0


def build_recipe(solution_path: Path) -> tuple[dict, dict, dict]:
    fertilizers = load_fertilizers()
    molar_masses = load_molar_masses()
    nutrient_solution = load_nutrient_solution_data(solution_path)
    allowed = sorted(fertilizers.keys(), key=str.casefold)
    recipe = {
        "liters": DEFAULT_LITERS,
        "water_profile": "default",
        "targets_mg_per_l": nutrient_solution["targets_mg_per_l"],
        "fertilizers_allowed": allowed,
    }
    return recipe, fertilizers, molar_masses


def run_benchmark(recipe: dict, fertilizers: dict, molar_masses: dict, iterations: int) -> float:
    start = time.perf_counter()
    for _ in range(iterations):
        solve_recipe_data(recipe, ferts=fertilizers, mm=molar_masses)
    end = time.perf_counter()
    return end - start


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark solver with all fertilizers enabled.")
    parser.add_argument(
        "--solution",
        type=Path,
        default=DEFAULT_SOLUTION,
        help="Path to a nutrient solution definition YAML.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help="Number of timed solver runs.",
    )
    parser.add_argument(
        "--baseline-seconds",
        type=float,
        default=DEFAULT_BASELINE_SECONDS,
        help="Baseline average seconds for regression checks.",
    )
    args = parser.parse_args()

    recipe, fertilizers, molar_masses = build_recipe(args.solution)
    solve_recipe_data(recipe, ferts=fertilizers, mm=molar_masses)
    elapsed = run_benchmark(recipe, fertilizers, molar_masses, args.iterations)
    avg = elapsed / max(1, args.iterations)

    print("Solver benchmark (all fertilizers allowed)")
    print(f"  solution: {args.solution}")
    print(f"  fertilizers: {len(fertilizers)}")
    print(f"  iterations: {args.iterations}")
    print(f"  total_seconds: {elapsed:.6f}")
    print(f"  avg_seconds: {avg:.6f}")
    print(f"  baseline_threshold_seconds: {args.baseline_seconds:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
