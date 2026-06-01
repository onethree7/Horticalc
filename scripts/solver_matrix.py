from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from horticalc.data_io import (  # noqa: E402
    Fertilizer,
    load_fertilizers,
    load_molar_masses,
    load_nutrient_solution_data,
    load_water_profile_data,
)
from horticalc.paths import logs_dir, resolve_water_profile_path, shipped_nutrient_solutions_dir  # noqa: E402
from horticalc.solver import solve_recipe_data  # noqa: E402


DEFAULT_CASES_PATH = Path(__file__).with_name("solver_matrix_cases.yml")
DEFAULT_OUT_DIR = logs_dir(ROOT) / "solver_matrix" / "dev"
BOOLEAN_SOLVER_KEYS = (
    "relative_weighting",
    "singleton_supplier_enabled",
    "singleton_underfill_enabled",
    "n_total_governor_enabled",
)
BOOLEAN_DEFAULTS = {
    "relative_weighting": False,
    "singleton_supplier_enabled": False,
    "singleton_underfill_enabled": True,
    "n_total_governor_enabled": False,
}
IGNORED_OPTIMIZATION_TARGETS = {"S", "SO4", "NA", "CL"}
MACRO_KEYS = {"N_total", "P", "K", "Ca", "Mg", "Si"}
N_FORM_KEYS = {"N_NH4", "N_NO3", "N_UREA"}
MICRO_KEYS = {"Fe", "Mn", "Cu", "Zn", "B", "Mo"}
CSV_FIELDS = (
    "profile_id",
    "profile_name",
    "preset",
    "phase",
    "nitrogen_objective_mode",
    "subset_size",
    "fertilizers_allowed",
    "config_name",
    "solver_config",
    "status",
    "elapsed_seconds",
    "composite_score",
    "macro_score",
    "n_form_score",
    "micro_score",
    "other_score",
    "ignored_score",
    "max_error_key",
    "max_error_score",
    "total_grams",
    "used_fertilizer_count",
    "used_fertilizers",
    "achieved_elements_mg_per_l",
    "errors_mg_per_l",
    "errors_percent",
    "ignored_targets",
    "error",
)


@dataclass(frozen=True)
class TargetProfile:
    profile_id: str
    name: str
    source: str
    targets_mg_per_l: dict[str, float]


@dataclass(frozen=True)
class SolverConfigCase:
    name: str
    values: dict[str, Any]


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML object")
    return data


def _float_targets(data: dict[str, Any]) -> dict[str, float]:
    return {str(key): float(value) for key, value in (data or {}).items()}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _score_rms(values: list[float]) -> float:
    if not values:
        return 0.0
    return math.sqrt(sum(value * value for value in values) / len(values))


def _zero_target_tolerance(key: str) -> float:
    if key in MICRO_KEYS:
        return 0.05
    if key in N_FORM_KEYS:
        return 1.0
    if key in MACRO_KEYS:
        return 2.0
    return 1.0


def _target_category(key: str) -> str:
    upper = key.upper()
    if upper in IGNORED_OPTIMIZATION_TARGETS:
        return "ignored"
    if key in N_FORM_KEYS:
        return "n_form"
    if key in MACRO_KEYS:
        return "macro"
    if key in MICRO_KEYS:
        return "micro"
    return "other"


def score_solution(
    targets_mg_per_l: dict[str, float],
    achieved_mg_per_l: dict[str, float],
    objective_elements: Iterable[str],
) -> dict[str, Any]:
    objective_set = set(objective_elements)
    grouped: dict[str, list[float]] = {
        "macro": [],
        "n_form": [],
        "micro": [],
        "other": [],
        "ignored": [],
    }
    element_scores: dict[str, dict[str, Any]] = {}

    for key, target in targets_mg_per_l.items():
        target = float(target)
        achieved = float(achieved_mg_per_l.get(key, 0.0))
        abs_error = achieved - target
        category = _target_category(key) if key in objective_set else "ignored"
        if target == 0.0:
            percent_error = None
            normalized_score = abs(abs_error) / _zero_target_tolerance(key) * 100.0
        else:
            percent_error = abs_error / target * 100.0
            normalized_score = abs(percent_error)
        grouped[category].append(normalized_score)
        element_scores[key] = {
            "target": target,
            "achieved": achieved,
            "error_mg_per_l": abs_error,
            "error_percent": percent_error,
            "score": normalized_score,
            "category": category,
            "optimized": key in objective_set,
        }

    macro_score = _score_rms(grouped["macro"])
    n_form_score = _score_rms(grouped["n_form"])
    micro_score = _score_rms(grouped["micro"])
    other_score = _score_rms(grouped["other"])
    ignored_score = _score_rms(grouped["ignored"])
    composite_score = (
        3.0 * macro_score
        + 3.0 * n_form_score
        + 1.5 * micro_score
        + 0.5 * other_score
    )
    scored_items = [
        (details["score"], key)
        for key, details in element_scores.items()
        if details["category"] != "ignored"
    ]
    max_score, max_key = max(scored_items, default=(0.0, ""))
    return {
        "composite_score": composite_score,
        "macro_score": macro_score,
        "n_form_score": n_form_score,
        "micro_score": micro_score,
        "other_score": other_score,
        "ignored_score": ignored_score,
        "max_error_key": max_key,
        "max_error_score": max_score,
        "elements": element_scores,
    }


def resolve_allowed_fertilizers(
    configured_names: Iterable[str],
    fertilizers: dict[str, Fertilizer],
) -> list[str]:
    available_names = set(fertilizers)
    resolved: list[str] = []
    errors: list[str] = []
    for raw_name in configured_names:
        name = str(raw_name)
        if name in available_names:
            resolved.append(name)
            continue
        stripped = name.strip()
        if stripped in available_names:
            errors.append(
                f"{name!r} is not an exact fertilizer name. Use {stripped!r} "
                "without surrounding whitespace."
            )
            continue
        matches = get_close_matches(stripped, sorted(available_names), n=3, cutoff=0.55)
        suffix = f" Did you mean: {', '.join(repr(match) for match in matches)}?" if matches else ""
        errors.append(f"Unknown fertilizer {name!r}.{suffix}")

    if errors:
        raise ValueError("Invalid allowed_fertilizers:\n- " + "\n- ".join(errors))
    return resolved


def load_target_profiles(cases: dict[str, Any], selection: str) -> list[TargetProfile]:
    profiles: list[TargetProfile] = []
    if selection == "all":
        selected_tokens: set[str] | None = None
    else:
        selected_tokens = {token.strip() for token in selection.split(",") if token.strip()}

    for path in sorted(shipped_nutrient_solutions_dir(ROOT).glob("*.yml")):
        data = load_nutrient_solution_data(path)
        profile = TargetProfile(
            profile_id=path.stem,
            name=str(data["name"]),
            source=str(data.get("source") or ""),
            targets_mg_per_l=_float_targets(data["targets_mg_per_l"]),
        )
        if selected_tokens is None or path.stem in selected_tokens or path.name in selected_tokens:
            profiles.append(profile)

    for entry in cases.get("custom_profiles") or []:
        if not isinstance(entry, dict):
            raise ValueError("custom_profiles entries must be YAML objects")
        profile_id = str(entry.get("id") or entry.get("name") or "custom_profile")
        profile = TargetProfile(
            profile_id=profile_id,
            name=str(entry.get("name") or profile_id),
            source=str(entry.get("source") or ""),
            targets_mg_per_l=_float_targets(entry.get("targets_mg_per_l") or {}),
        )
        if selected_tokens is None or profile_id in selected_tokens:
            profiles.append(profile)

    if selected_tokens is not None:
        found = {profile.profile_id for profile in profiles}
        missing = sorted(selected_tokens - found - {Path(token).name for token in selected_tokens})
        if missing:
            raise ValueError(f"No target profile matched: {', '.join(missing)}")
    if not profiles:
        raise ValueError("No target profiles selected")
    return profiles


def fertilizer_subsets(allowed: list[str], preset: str) -> list[tuple[str, ...]]:
    if preset == "quick":
        return [tuple(allowed)]
    subsets: list[tuple[str, ...]] = []
    for size in range(1, len(allowed) + 1):
        subsets.extend(itertools.combinations(allowed, size))
    return subsets


def sample_subsets_for_cap(
    subsets: list[tuple[str, ...]],
    limit: int,
    *,
    seed: int | None = None,
) -> list[tuple[str, ...]]:
    if limit >= len(subsets):
        return subsets
    if limit <= 0:
        raise ValueError("subset sample limit must be positive")
    if limit == 1:
        return [subsets[-1]]

    if seed is not None:
        rng = random.Random(seed)
        full_subset = subsets[-1]
        indexed = list(enumerate(subsets[:-1]))
        sampled = rng.sample(indexed, k=limit - 1)
        sampled.append((len(subsets) - 1, full_subset))
        return [subset for _, subset in sorted(sampled, key=lambda item: item[0])]

    last_index = len(subsets) - 1
    positions = {
        round(index * last_index / (limit - 1))
        for index in range(limit)
    }
    while len(positions) < limit:
        for index in range(last_index + 1):
            positions.add(index)
            if len(positions) == limit:
                break
    return [subsets[index] for index in sorted(positions)]


def nitrogen_objective_modes(cases: dict[str, Any], override: str | None) -> list[str]:
    raw_modes: Any
    if override:
        raw_modes = [mode.strip() for mode in override.split(",") if mode.strip()]
    else:
        raw_modes = cases.get("nitrogen_objective_modes") or ["as_targets"]
    modes = [str(mode) for mode in raw_modes]
    allowed = {"as_targets", "n_total_only", "n_forms_only"}
    unknown = [mode for mode in modes if mode not in allowed]
    if unknown:
        raise ValueError(f"Unknown nitrogen objective mode(s): {', '.join(unknown)}")
    if not modes:
        raise ValueError("At least one nitrogen objective mode is required")
    return modes


def boolean_solver_configs(nitrogen_modes: list[str]) -> list[SolverConfigCase]:
    value_options = []
    for key in BOOLEAN_SOLVER_KEYS:
        default = BOOLEAN_DEFAULTS[key]
        value_options.append((default, not default))

    configs: list[SolverConfigCase] = []
    for nitrogen_mode in nitrogen_modes:
        for values in itertools.product(*value_options):
            config = dict(zip(BOOLEAN_SOLVER_KEYS, values))
            config["nitrogen_objective_mode"] = nitrogen_mode
            changed_parts = [
                f"{key}={str(value).lower()}"
                for key, value in config.items()
                if key in BOOLEAN_DEFAULTS and value != BOOLEAN_DEFAULTS[key]
            ]
            name = f"n_mode={nitrogen_mode}"
            if changed_parts:
                name = f"{name}," + ",".join(changed_parts)
            configs.append(SolverConfigCase(name=name, values=config))
    return configs


def deep_refinement_configs(base: SolverConfigCase) -> list[SolverConfigCase]:
    variants: list[SolverConfigCase] = []
    numeric_mutations: list[tuple[str, Any]] = [
        ("overshoot_penalty", 0.0),
        ("overshoot_penalty", 0.25),
        ("overshoot_penalty", 3.0),
        ("overshoot_penalty", 10.0),
        ("scale_eps_mg_per_l", 0.1),
        ("scale_eps_mg_per_l", 5.0),
        ("irls_max_outer_iter", 1),
        ("irls_max_outer_iter", 8),
        ("singleton_share_threshold", 0.65),
        ("singleton_share_threshold", 0.95),
        ("singleton_underfill_share_threshold", 0.65),
        ("singleton_underfill_share_threshold", 0.95),
        ("n_total_governor_weight", 0.01),
        ("n_total_governor_weight", 0.1),
        ("n_total_governor_weight", 5.0),
    ]
    for key, value in numeric_mutations:
        values = dict(base.values)
        values[key] = value
        if key == "n_total_governor_weight":
            values["n_total_governor_enabled"] = True
        variants.append(SolverConfigCase(name=f"{base.name};{key}={value}", values=values))

    combo = dict(base.values)
    combo.update({"overshoot_penalty": 3.0, "scale_eps_mg_per_l": 0.1, "irls_max_outer_iter": 8})
    variants.append(SolverConfigCase(name=f"{base.name};tight_weighting_combo", values=combo))
    return variants


def base_run_budget(args: argparse.Namespace, profiles: list[TargetProfile], configs: list[SolverConfigCase]) -> int | None:
    if args.max_runs is None or args.max_runs <= 0:
        return None
    if args.preset != "deep" or not configs:
        return args.max_runs
    refinement_variants = len(deep_refinement_configs(configs[0]))
    max_refinement_rows = len(profiles) * args.top_n * refinement_variants
    refinement_reserve = min(max_refinement_rows, args.max_runs // 10)
    return max(1, args.max_runs - refinement_reserve)


def _run_key(profile_id: str, subset: tuple[str, ...], config: SolverConfigCase) -> str:
    payload = [profile_id, list(subset), config.values]
    return _json(payload)


class MatrixAggregate:
    def __init__(self, allowed_fertilizers: list[str], top_n: int) -> None:
        self.allowed_fertilizers = allowed_fertilizers
        self.top_n = top_n
        self.total_runs = 0
        self.failed_runs = 0
        self.best_by_profile: dict[str, dict[str, Any]] = {}
        self.top_by_profile: dict[str, list[dict[str, Any]]] = {}
        self.config_scores: dict[str, dict[str, float]] = {}
        self.fertilizer_scores: dict[str, dict[str, float]] = {
            name: {"present_sum": 0.0, "present_count": 0, "absent_sum": 0.0, "absent_count": 0}
            for name in allowed_fertilizers
        }

    def update(self, row: dict[str, Any], subset: tuple[str, ...], config: SolverConfigCase) -> None:
        self.total_runs += 1
        if row["status"] != "ok":
            self.failed_runs += 1
            return

        score = float(row["composite_score"])
        profile_id = str(row["profile_id"])
        current = self.best_by_profile.get(profile_id)
        if current is None or score < float(current["composite_score"]):
            self.best_by_profile[profile_id] = dict(row)

        top_rows = self.top_by_profile.setdefault(profile_id, [])
        candidate = {
            "profile_id": profile_id,
            "subset": subset,
            "config": config,
            "composite_score": score,
        }
        top_rows.append(candidate)
        top_rows.sort(key=lambda item: float(item["composite_score"]))
        del top_rows[self.top_n :]

        config_stats = self.config_scores.setdefault(config.name, {"sum": 0.0, "count": 0})
        config_stats["sum"] += score
        config_stats["count"] += 1

        subset_set = set(subset)
        for fertilizer_name, stats in self.fertilizer_scores.items():
            if fertilizer_name in subset_set:
                stats["present_sum"] += score
                stats["present_count"] += 1
            else:
                stats["absent_sum"] += score
                stats["absent_count"] += 1

    def summary(self) -> dict[str, Any]:
        config_ranking = []
        for name, stats in self.config_scores.items():
            count = int(stats["count"])
            config_ranking.append(
                {
                    "config_name": name,
                    "avg_composite_score": stats["sum"] / max(1, count),
                    "runs": count,
                }
            )
        config_ranking.sort(key=lambda item: item["avg_composite_score"])

        fertilizer_impact = []
        for name, stats in self.fertilizer_scores.items():
            present_count = int(stats["present_count"])
            absent_count = int(stats["absent_count"])
            present_avg = stats["present_sum"] / present_count if present_count else None
            absent_avg = stats["absent_sum"] / absent_count if absent_count else None
            fertilizer_impact.append(
                {
                    "fertilizer": name,
                    "avg_when_present": present_avg,
                    "avg_when_absent": absent_avg,
                    "omission_delta": None
                    if present_avg is None or absent_avg is None
                    else absent_avg - present_avg,
                    "present_runs": present_count,
                    "absent_runs": absent_count,
                }
            )
        fertilizer_impact.sort(
            key=lambda item: float("-inf") if item["omission_delta"] is None else -float(item["omission_delta"])
        )

        return {
            "total_runs": self.total_runs,
            "failed_runs": self.failed_runs,
            "best_by_profile": self.best_by_profile,
            "global_config_ranking": config_ranking,
            "fertilizer_omission_impact": fertilizer_impact,
        }


def solve_case(
    *,
    profile: TargetProfile,
    subset: tuple[str, ...],
    config: SolverConfigCase,
    preset: str,
    phase: str,
    liters: float,
    water_profile_name: str,
    osmosis_percent: float,
    water_profile_data: dict[str, Any],
    fertilizers: dict[str, Fertilizer],
    molar_masses: dict[str, float],
) -> dict[str, Any]:
    start = time.perf_counter()
    row: dict[str, Any] = {
        "profile_id": profile.profile_id,
        "profile_name": profile.name,
        "preset": preset,
        "phase": phase,
        "nitrogen_objective_mode": str(config.values.get("nitrogen_objective_mode", "as_targets")),
        "subset_size": len(subset),
        "fertilizers_allowed": _json(list(subset)),
        "config_name": config.name,
        "solver_config": _json(config.values),
    }
    try:
        recipe = {
            "liters": liters,
            "water_profile": water_profile_name,
            "osmosis_percent": osmosis_percent,
            "targets_mg_per_l": profile.targets_mg_per_l,
            "fertilizers_allowed": list(subset),
            "solver_config": config.values,
        }
        result = solve_recipe_data(
            recipe,
            ferts=fertilizers,
            mm=molar_masses,
            water_profile_data=water_profile_data,
        )
        elapsed = time.perf_counter() - start
        score = score_solution(
            result.targets_mg_l,
            result.achieved_elements_mg_l,
            result.objective_elements,
        )
        ignored_targets = {
            key: details
            for key, details in score["elements"].items()
            if details["category"] == "ignored"
        }
        total_grams = sum(float(item["grams"]) for item in result.fertilizers)
        row.update(
            {
                "status": "ok",
                "elapsed_seconds": elapsed,
                "composite_score": score["composite_score"],
                "macro_score": score["macro_score"],
                "n_form_score": score["n_form_score"],
                "micro_score": score["micro_score"],
                "other_score": score["other_score"],
                "ignored_score": score["ignored_score"],
                "max_error_key": score["max_error_key"],
                "max_error_score": score["max_error_score"],
                "total_grams": total_grams,
                "used_fertilizer_count": len(result.fertilizers),
                "used_fertilizers": _json(result.fertilizers),
                "achieved_elements_mg_per_l": _json(result.achieved_elements_mg_l),
                "errors_mg_per_l": _json(result.errors_mg_l),
                "errors_percent": _json(result.errors_percent),
                "ignored_targets": _json(ignored_targets),
                "error": "",
            }
        )
    except Exception as exc:  # noqa: BLE001 - benchmark rows should capture solver failures.
        elapsed = time.perf_counter() - start
        row.update(
            {
                "status": "error",
                "elapsed_seconds": elapsed,
                "composite_score": math.inf,
                "macro_score": math.inf,
                "n_form_score": math.inf,
                "micro_score": math.inf,
                "other_score": math.inf,
                "ignored_score": math.inf,
                "max_error_key": "",
                "max_error_score": math.inf,
                "total_grams": 0.0,
                "used_fertilizer_count": 0,
                "used_fertilizers": "[]",
                "achieved_elements_mg_per_l": "{}",
                "errors_mg_per_l": "{}",
                "errors_percent": "{}",
                "ignored_targets": "{}",
                "error": str(exc),
            }
        )
    return row


def write_row(csv_writer: csv.DictWriter, jsonl_handle: Any, row: dict[str, Any]) -> None:
    csv_writer.writerow({field: row.get(field, "") for field in CSV_FIELDS})
    jsonl_handle.write(_json(row) + "\n")


def run_matrix(args: argparse.Namespace) -> dict[str, Any]:
    cases = _read_yaml(args.cases)
    fertilizers = load_fertilizers()
    molar_masses = load_molar_masses()
    allowed_fertilizers = resolve_allowed_fertilizers(cases["allowed_fertilizers"], fertilizers)

    profiles = load_target_profiles(cases, args.profiles)
    if args.max_profiles:
        profiles = profiles[: args.max_profiles]

    water_profile_name = args.water_profile or str(cases.get("water_profile") or "65936")
    osmosis_percent = float(args.osmosis_percent if args.osmosis_percent is not None else cases["osmosis_percent"])
    liters = float(args.liters if args.liters is not None else cases.get("liters") or 10.0)
    water_profile_data = load_water_profile_data(resolve_water_profile_path(water_profile_name, ROOT))
    water_profile_data = dict(water_profile_data)
    water_profile_data["osmosis_percent"] = osmosis_percent

    subsets = fertilizer_subsets(allowed_fertilizers, args.preset)
    if args.max_subsets:
        subsets = subsets[: args.max_subsets]

    nitrogen_modes = nitrogen_objective_modes(cases, args.nitrogen_modes)
    configs = boolean_solver_configs(nitrogen_modes)
    if args.max_configs:
        configs = configs[: args.max_configs]
    original_subset_count = len(subsets)
    budget = base_run_budget(args, profiles, configs)
    sampled_subsets = False
    if budget is not None:
        base_grid_runs = len(profiles) * len(subsets) * len(configs)
        if base_grid_runs > budget:
            subset_limit = max(1, budget // max(1, len(profiles) * len(configs)))
            if subset_limit < len(subsets):
                subsets = sample_subsets_for_cap(subsets, subset_limit, seed=args.seed)
                sampled_subsets = True

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    results_csv = out_dir / "results.csv"
    results_jsonl = out_dir / "results.jsonl"
    summary_json = out_dir / "summary.json"

    aggregate = MatrixAggregate(allowed_fertilizers, top_n=args.top_n)
    seen: set[str] = set()
    stopped_early = False

    def max_runs_reached() -> bool:
        return args.max_runs is not None and args.max_runs > 0 and aggregate.total_runs >= args.max_runs

    with results_csv.open("w", encoding="utf-8", newline="") as csv_handle, results_jsonl.open(
        "w", encoding="utf-8"
    ) as jsonl_handle:
        writer = csv.DictWriter(csv_handle, fieldnames=CSV_FIELDS)
        writer.writeheader()

        for profile in profiles:
            if stopped_early:
                break
            for subset in subsets:
                if stopped_early:
                    break
                for config in configs:
                    if max_runs_reached():
                        stopped_early = True
                        break
                    key = _run_key(profile.profile_id, subset, config)
                    if key in seen:
                        continue
                    seen.add(key)
                    row = solve_case(
                        profile=profile,
                        subset=subset,
                        config=config,
                        preset=args.preset,
                        phase="base",
                        liters=liters,
                        water_profile_name=water_profile_name,
                        osmosis_percent=osmosis_percent,
                        water_profile_data=water_profile_data,
                        fertilizers=fertilizers,
                        molar_masses=molar_masses,
                    )
                    write_row(writer, jsonl_handle, row)
                    aggregate.update(row, subset, config)

        if args.preset == "deep" and not stopped_early:
            refinement_candidates = [
                candidate
                for candidates in aggregate.top_by_profile.values()
                for candidate in candidates
            ]
            if args.seed is not None:
                random.Random(args.seed).shuffle(refinement_candidates)
            for candidate in refinement_candidates:
                profile = next(
                    item for item in profiles if item.profile_id == candidate["profile_id"]
                )
                subset = candidate["subset"]
                refinement_configs = deep_refinement_configs(candidate["config"])
                if args.seed is not None:
                    random.Random(f"{args.seed}:{profile.profile_id}:{candidate['composite_score']}").shuffle(
                        refinement_configs
                    )
                for config in refinement_configs:
                    if max_runs_reached():
                        stopped_early = True
                        break
                    key = _run_key(profile.profile_id, subset, config)
                    if key in seen:
                        continue
                    seen.add(key)
                    row = solve_case(
                        profile=profile,
                        subset=subset,
                        config=config,
                        preset=args.preset,
                        phase="refine",
                        liters=liters,
                        water_profile_name=water_profile_name,
                        osmosis_percent=osmosis_percent,
                        water_profile_data=water_profile_data,
                        fertilizers=fertilizers,
                        molar_masses=molar_masses,
                    )
                    write_row(writer, jsonl_handle, row)
                    aggregate.update(row, subset, config)
                if stopped_early:
                    break

    summary = aggregate.summary()
    summary.update(
        {
            "preset": args.preset,
            "profiles": [profile.profile_id for profile in profiles],
            "water_profile": water_profile_name,
            "osmosis_percent": osmosis_percent,
            "liters": liters,
            "allowed_fertilizers": allowed_fertilizers,
            "nitrogen_objective_modes": nitrogen_modes,
            "max_runs": args.max_runs,
            "stopped_early": stopped_early,
            "sampled_subsets_for_cap": sampled_subsets,
            "original_subset_count": original_subset_count,
            "subset_count": len(subsets),
            "base_run_budget": budget,
            "results_csv": str(results_csv),
            "results_jsonl": str(results_jsonl),
        }
    )
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a solver quality matrix for Horticalc.")
    parser.add_argument("--preset", choices=("quick", "matrix", "deep"), default="quick")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--profiles", default="all", help="all, or comma-separated profile ids/stems")
    parser.add_argument("--water-profile", default=None)
    parser.add_argument("--osmosis-percent", type=float, default=None)
    parser.add_argument("--liters", type=float, default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--seed", type=int, default=None, help="Seed for reproducible deep refinement ordering.")
    parser.add_argument(
        "--nitrogen-modes",
        default=None,
        help="Comma-separated nitrogen objective modes: as_targets,n_total_only,n_forms_only.",
    )
    parser.add_argument("--top-n", type=int, default=20, help="Top base rows per profile refined by deep preset.")
    parser.add_argument("--max-profiles", type=int, default=None, help="Limit profiles for smoke tests.")
    parser.add_argument("--max-subsets", type=int, default=None, help="Limit fertilizer subsets for smoke tests.")
    parser.add_argument("--max-configs", type=int, default=None, help="Limit solver configs for smoke tests.")
    parser.add_argument(
        "--max-runs",
        type=int,
        default=100_000,
        help="Stop after this many attempted solver rows. Use 0 to disable the safety cap.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    summary = run_matrix(args)
    best_count = len(summary["best_by_profile"])
    print(f"Solver matrix complete: {summary['total_runs']} runs, {summary['failed_runs']} failures")
    if summary.get("stopped_early"):
        print(f"Stopped early at --max-runs {summary['max_runs']}")
    if summary.get("sampled_subsets_for_cap"):
        print(
            "Sampled fertilizer subsets for --max-runs cap: "
            f"{summary['subset_count']} of {summary['original_subset_count']}"
        )
    print(f"Best profile rows: {best_count}")
    print(f"Results CSV: {summary['results_csv']}")
    print(f"Results JSONL: {summary['results_jsonl']}")
    print(f"Summary JSON: {args.out_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
