from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
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
from horticalc.solver_config import resolve_solver_config  # noqa: E402

DEFAULT_CASES_PATH = Path(__file__).with_name("solver_matrix_cases.yml")
DEFAULT_OUT_DIR = logs_dir(ROOT) / "solver_matrix" / "dev"
MACRO_KEYS = {"N_total", "P", "K", "Ca", "Mg", "S", "Si"}
N_FORM_KEYS = {"N_NH4", "N_NO3", "N_UREA"}
MICRO_KEYS = {"Fe", "Mn", "Cu", "Zn", "B", "Mo"}
CSV_FIELDS = (
    "run_id",
    "profile_id",
    "profile_name",
    "profile_group",
    "profile_source",
    "preset",
    "phase",
    "portfolio_id",
    "portfolio_source",
    "omitted_fertilizer",
    "nitrogen_objective_mode",
    "subset_size",
    "fertilizers_allowed",
    "experiment_id",
    "config_id",
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
    "objective_elements",
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
    group: str
    source: str
    targets_mg_per_l: dict[str, float]


@dataclass(frozen=True)
class FertilizerPortfolio:
    portfolio_id: str
    source: str
    fertilizers: tuple[str, ...]
    omitted_fertilizer: str = ""


@dataclass(frozen=True)
class SolverConfigCase:
    experiment_id: str
    config_id: str
    name: str
    values: dict[str, Any]
    varied_keys: tuple[str, ...]


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
    """Score only solver-declared objectives, including S when it is enabled."""
    objective_set = set(objective_elements)
    grouped: dict[str, list[float]] = {
        "macro": [],
        "n_form": [],
        "micro": [],
        "other": [],
        "ignored": [],
    }
    element_scores: dict[str, dict[str, Any]] = {}

    for key, target_value in targets_mg_per_l.items():
        target = float(target_value)
        achieved = float(achieved_mg_per_l.get(key, 0.0))
        error = achieved - target
        category = _target_category(key) if key in objective_set else "ignored"
        if target == 0.0:
            percent_error = None
            normalized_score = abs(error) / _zero_target_tolerance(key) * 100.0
        else:
            percent_error = error / target * 100.0
            normalized_score = abs(percent_error)
        grouped[category].append(normalized_score)
        element_scores[key] = {
            "target": target,
            "achieved": achieved,
            "error_mg_per_l": error,
            "error_percent": percent_error,
            "score": normalized_score,
            "category": category,
            "optimized": key in objective_set,
        }

    scores = {
        "macro_score": _score_rms(grouped["macro"]),
        "n_form_score": _score_rms(grouped["n_form"]),
        "micro_score": _score_rms(grouped["micro"]),
        "other_score": _score_rms(grouped["other"]),
        "ignored_score": _score_rms(grouped["ignored"]),
    }
    scores["composite_score"] = (
        3.0 * scores["macro_score"]
        + 3.0 * scores["n_form_score"]
        + 1.5 * scores["micro_score"]
        + 0.5 * scores["other_score"]
    )
    scored_items = [
        (details["score"], key) for key, details in element_scores.items() if details["category"] != "ignored"
    ]
    max_score, max_key = max(scored_items, default=(0.0, ""))
    return {
        **scores,
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
        if name in resolved:
            errors.append(f"Duplicate fertilizer {name!r}.")
            continue
        if name in available_names:
            resolved.append(name)
            continue
        stripped = name.strip()
        if stripped in available_names:
            errors.append(f"{name!r} is not an exact fertilizer name. Use {stripped!r} without surrounding whitespace.")
            continue
        matches = get_close_matches(stripped, sorted(available_names), n=3, cutoff=0.55)
        suffix = f" Did you mean: {', '.join(repr(match) for match in matches)}?" if matches else ""
        errors.append(f"Unknown fertilizer {name!r}.{suffix}")

    if errors:
        raise ValueError("Invalid allowed fertilizers:\n- " + "\n- ".join(errors))
    if not resolved:
        raise ValueError("At least one allowed fertilizer is required")
    return resolved


def load_target_profiles(cases: dict[str, Any], selection: str) -> list[TargetProfile]:
    entries = cases.get("benchmark_profiles") or []
    if not isinstance(entries, list) or not entries:
        raise ValueError("benchmark_profiles must be a non-empty YAML list")
    selected = None if selection == "all" else {item.strip() for item in selection.split(",") if item.strip()}
    profiles: list[TargetProfile] = []

    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("id"):
            raise ValueError("benchmark_profiles entries must contain an id")
        profile_id = str(entry["id"])
        if selected is not None and profile_id not in selected:
            continue
        if entry.get("recipe"):
            path = ROOT / str(entry["recipe"])
            data = _read_yaml(path)
            source = str(path.relative_to(ROOT)).replace("\\", "/")
        elif entry.get("targets_mg_per_l"):
            data = entry
            source = str(entry.get("source") or "inline benchmark profile")
        else:
            path = shipped_nutrient_solutions_dir(ROOT) / f"{profile_id}.yml"
            data = load_nutrient_solution_data(path)
            source = str(path.relative_to(ROOT)).replace("\\", "/")
        profiles.append(
            TargetProfile(
                profile_id=profile_id,
                name=str(data.get("name") or profile_id),
                group=str(entry.get("group") or "scientific"),
                source=source,
                targets_mg_per_l=_float_targets(data.get("targets_mg_per_l") or {}),
            )
        )

    if selected is not None:
        found = {profile.profile_id for profile in profiles}
        missing = sorted(selected - found)
        if missing:
            raise ValueError(f"No configured benchmark profile matched: {', '.join(missing)}")
    if not profiles:
        raise ValueError("No target profiles selected")
    return profiles


def load_fertilizer_portfolios(
    cases: dict[str, Any],
    fertilizers: dict[str, Fertilizer],
) -> dict[str, FertilizerPortfolio]:
    portfolios: dict[str, FertilizerPortfolio] = {}
    for entry in cases.get("fertilizer_portfolios") or []:
        if not isinstance(entry, dict) or not entry.get("id"):
            raise ValueError("fertilizer_portfolios entries must contain an id")
        portfolio_id = str(entry["id"])
        if portfolio_id in portfolios:
            raise ValueError(f"Duplicate fertilizer portfolio: {portfolio_id}")
        portfolios[portfolio_id] = FertilizerPortfolio(
            portfolio_id=portfolio_id,
            source=str(entry.get("source") or ""),
            fertilizers=tuple(resolve_allowed_fertilizers(entry.get("fertilizers") or [], fertilizers)),
        )
    primary_id = str(cases.get("primary_portfolio") or "")
    if primary_id not in portfolios:
        raise ValueError(f"Unknown primary_portfolio: {primary_id}")
    return portfolios


def mass_barrage_portfolios(
    cases: dict[str, Any],
    portfolios: dict[str, FertilizerPortfolio],
) -> list[FertilizerPortfolio]:
    spec = cases.get("mass_barrage") or {}
    selected: list[FertilizerPortfolio] = []
    for portfolio_id in spec.get("named_portfolios") or []:
        key = str(portfolio_id)
        if key not in portfolios:
            raise ValueError(f"Unknown mass-barrage portfolio: {key}")
        selected.append(portfolios[key])
    if spec.get("leave_one_out_primary"):
        primary = portfolios[str(cases["primary_portfolio"])]
        for index, omitted in enumerate(primary.fertilizers, start=1):
            selected.append(
                FertilizerPortfolio(
                    portfolio_id=f"loo_{index:02d}",
                    source=f"{primary.portfolio_id} without {omitted}",
                    fertilizers=tuple(name for name in primary.fertilizers if name != omitted),
                    omitted_fertilizer=omitted,
                )
            )
    return selected


def _config_label(values: dict[str, Any], keys: Iterable[str]) -> str:
    return ",".join(f"{key}={_json(values[key])}" for key in keys)


def _config_case(
    baseline: dict[str, Any],
    experiment_id: str,
    config_id: str,
    changes: dict[str, Any],
) -> SolverConfigCase:
    values = resolve_solver_config({**baseline, **changes})
    if values["nitrogen_objective_mode"] != "n_total_only":
        raise ValueError("The canonical matrix requires nitrogen_objective_mode=n_total_only")
    if values["s_objective_enabled"] is not True:
        raise ValueError("The canonical matrix requires s_objective_enabled=true")
    varied_keys = tuple(changes)
    label = _config_label(values, varied_keys) if varied_keys else "canonical"
    return SolverConfigCase(
        experiment_id=experiment_id,
        config_id=config_id,
        name=f"{experiment_id}:{label}",
        values=values,
        varied_keys=varied_keys,
    )


def solver_config_cases(cases: dict[str, Any], preset: str) -> list[SolverConfigCase]:
    baseline = resolve_solver_config(cases.get("solver_baseline") or {})
    configs = [_config_case(baseline, "baseline", "canonical", {})]
    if preset == "quick":
        return configs

    for experiment in cases.get("solver_experiments") or []:
        if not isinstance(experiment, dict) or not experiment.get("id"):
            raise ValueError("solver_experiments entries must contain an id")
        experiment_id = str(experiment["id"])
        for index, control in enumerate(experiment.get("controls") or [], start=1):
            if not isinstance(control, dict):
                raise ValueError(f"{experiment_id}.controls entries must be objects")
            configs.append(_config_case(baseline, experiment_id, f"control_{index}", control))

        for index, variant in enumerate(experiment.get("variants") or [], start=1):
            if not isinstance(variant, dict) or not variant:
                raise ValueError(f"{experiment_id}.variants entries must be non-empty objects")
            configs.append(_config_case(baseline, experiment_id, f"variant_{index}", variant))

        grid = experiment.get("grid") or {}
        if not isinstance(grid, dict) or not grid:
            continue
        keys = tuple(str(key) for key in grid)
        options = []
        for key in keys:
            values = grid[key]
            if not isinstance(values, list) or not values:
                raise ValueError(f"{experiment_id}.grid.{key} must be a non-empty list")
            options.append(values)
        for values in itertools.product(*options):
            changes = dict(zip(keys, values, strict=True))
            config_id = _config_label(changes, keys)
            configs.append(_config_case(baseline, experiment_id, config_id, changes))
    return configs


class MatrixAggregate:
    def __init__(self) -> None:
        self.total_runs = 0
        self.failed_runs = 0
        self.best_by_profile: dict[str, dict[str, Any]] = {}
        self.config_scores: dict[tuple[str, str], dict[str, Any]] = {}

    def update(self, row: dict[str, Any]) -> None:
        self.total_runs += 1
        if row["status"] != "ok":
            self.failed_runs += 1
            return
        score = float(row["composite_score"])
        profile_id = str(row["profile_id"])
        current = self.best_by_profile.get(profile_id)
        if current is None or score < float(current["composite_score"]):
            self.best_by_profile[profile_id] = dict(row)
        if row["phase"] == "settings":
            key = (str(row["experiment_id"]), str(row["config_id"]))
            stats = self.config_scores.setdefault(
                key,
                {
                    "experiment_id": key[0],
                    "config_id": key[1],
                    "config_name": row["config_name"],
                    "solver_config": json.loads(row["solver_config"]),
                    "score_sum": 0.0,
                    "elapsed_sum": 0.0,
                    "runs": 0,
                },
            )
            stats["score_sum"] += score
            stats["elapsed_sum"] += float(row["elapsed_seconds"])
            stats["runs"] += 1

    def summary(self) -> dict[str, Any]:
        ranking = []
        for stats in self.config_scores.values():
            count = int(stats["runs"])
            ranking.append(
                {key: value for key, value in stats.items() if key not in {"score_sum", "elapsed_sum"}}
                | {
                    "avg_composite_score": stats["score_sum"] / max(1, count),
                    "avg_elapsed_seconds": stats["elapsed_sum"] / max(1, count),
                }
            )
        ranking.sort(key=lambda item: float(item["avg_composite_score"]))
        return {
            "total_runs": self.total_runs,
            "failed_runs": self.failed_runs,
            "best_by_profile": self.best_by_profile,
            "global_config_ranking": ranking,
        }


def _run_id(
    phase: str,
    profile: TargetProfile,
    portfolio: FertilizerPortfolio,
    config: SolverConfigCase,
) -> str:
    payload = _json([phase, profile.profile_id, portfolio.portfolio_id, config.experiment_id, config.config_id])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def solve_case(
    *,
    profile: TargetProfile,
    portfolio: FertilizerPortfolio,
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
        "run_id": _run_id(phase, profile, portfolio, config),
        "profile_id": profile.profile_id,
        "profile_name": profile.name,
        "profile_group": profile.group,
        "profile_source": profile.source,
        "preset": preset,
        "phase": phase,
        "portfolio_id": portfolio.portfolio_id,
        "portfolio_source": portfolio.source,
        "omitted_fertilizer": portfolio.omitted_fertilizer,
        "nitrogen_objective_mode": str(config.values["nitrogen_objective_mode"]),
        "subset_size": len(portfolio.fertilizers),
        "fertilizers_allowed": _json(list(portfolio.fertilizers)),
        "experiment_id": config.experiment_id,
        "config_id": config.config_id,
        "config_name": config.name,
        "solver_config": _json(config.values),
    }
    try:
        recipe = {
            "liters": liters,
            "water_profile": water_profile_name,
            "osmosis_percent": osmosis_percent,
            "targets_mg_per_l": profile.targets_mg_per_l,
            "fertilizers_allowed": list(portfolio.fertilizers),
            "solver_config": config.values,
        }
        result = solve_recipe_data(
            recipe,
            ferts=fertilizers,
            mm=molar_masses,
            water_profile_data=water_profile_data,
        )
        score = score_solution(
            result.targets_mg_l,
            result.achieved_elements_mg_l,
            result.objective_elements,
        )
        ignored_targets = {
            key: details for key, details in score["elements"].items() if details["category"] == "ignored"
        }
        row.update(
            {
                "status": "ok",
                "elapsed_seconds": time.perf_counter() - start,
                **{
                    key: score[key]
                    for key in (
                        "composite_score",
                        "macro_score",
                        "n_form_score",
                        "micro_score",
                        "other_score",
                        "ignored_score",
                        "max_error_key",
                        "max_error_score",
                    )
                },
                "total_grams": sum(float(item["grams"]) for item in result.fertilizers),
                "used_fertilizer_count": len(result.fertilizers),
                "used_fertilizers": _json(result.fertilizers),
                "objective_elements": _json(result.objective_elements),
                "achieved_elements_mg_per_l": _json(result.achieved_elements_mg_l),
                "errors_mg_per_l": _json(result.errors_mg_l),
                "errors_percent": _json(result.errors_percent),
                "ignored_targets": _json(ignored_targets),
                "error": "",
            }
        )
    except Exception as exc:  # noqa: BLE001 - a benchmark must preserve failed rows.
        row.update(
            {
                "status": "error",
                "elapsed_seconds": time.perf_counter() - start,
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
                "objective_elements": "[]",
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


def _manifest(
    args: argparse.Namespace,
    cases: dict[str, Any],
    profiles: list[TargetProfile],
    named_portfolios: dict[str, FertilizerPortfolio],
    barrage_portfolios: list[FertilizerPortfolio],
    configs: list[SolverConfigCase],
    planned_runs: int,
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cases_file": str(args.cases.resolve()),
        "cases_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        "preset": args.preset,
        "primary_portfolio": args.primary_portfolio or cases["primary_portfolio"],
        "planned_runs": planned_runs,
        "max_runs": args.max_runs,
        "profiles": [asdict(profile) for profile in profiles],
        "named_portfolios": [asdict(portfolio) for portfolio in named_portfolios.values()],
        "mass_barrage_portfolios": [asdict(portfolio) for portfolio in barrage_portfolios],
        "solver_configs": [asdict(config) for config in configs],
        "solver_baseline": resolve_solver_config(cases.get("solver_baseline") or {}),
        "unresolved_profiles": cases.get("unresolved_profiles") or [],
    }


def run_matrix(args: argparse.Namespace) -> dict[str, Any]:
    cases = _read_yaml(args.cases)
    if int(cases.get("schema_version") or 0) != 2:
        raise ValueError("solver matrix cases must use schema_version: 2")
    fertilizers = load_fertilizers()
    molar_masses = load_molar_masses()
    profiles = load_target_profiles(cases, args.profiles)
    if args.max_profiles:
        profiles = profiles[: args.max_profiles]

    named_portfolios = load_fertilizer_portfolios(cases, fertilizers)
    primary_id = str(args.primary_portfolio or cases["primary_portfolio"])
    if primary_id not in named_portfolios:
        raise ValueError(f"Unknown primary portfolio override: {primary_id}")
    primary = named_portfolios[primary_id]
    configs = solver_config_cases(cases, args.preset)
    if args.max_configs:
        configs = configs[: args.max_configs]
    barrage_portfolios = mass_barrage_portfolios(cases, named_portfolios) if args.preset == "deep" else []

    water_profile_name = args.water_profile or str(cases.get("water_profile") or "65936")
    osmosis_percent = float(args.osmosis_percent if args.osmosis_percent is not None else cases["osmosis_percent"])
    liters = float(args.liters if args.liters is not None else cases.get("liters") or 10.0)
    water_profile_data = dict(load_water_profile_data(resolve_water_profile_path(water_profile_name, ROOT)))
    water_profile_data["osmosis_percent"] = osmosis_percent

    planned_settings = len(profiles) * len(configs)
    planned_barrage = len(profiles) * len(barrage_portfolios)
    planned_runs = planned_settings + planned_barrage
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    results_csv = out_dir / "results.csv"
    results_jsonl = out_dir / "results.jsonl"
    summary_json = out_dir / "summary.json"
    manifest_json = out_dir / "run_manifest.json"
    manifest_json.write_text(
        json.dumps(
            _manifest(args, cases, profiles, named_portfolios, barrage_portfolios, configs, planned_runs),
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    aggregate = MatrixAggregate()
    stopped_early = False

    def at_cap() -> bool:
        return bool(args.max_runs and args.max_runs > 0 and aggregate.total_runs >= args.max_runs)

    def execute(
        writer: csv.DictWriter,
        jsonl_handle: Any,
        *,
        phase: str,
        profile: TargetProfile,
        portfolio: FertilizerPortfolio,
        config: SolverConfigCase,
    ) -> bool:
        nonlocal stopped_early
        if at_cap():
            stopped_early = True
            return False
        row = solve_case(
            profile=profile,
            portfolio=portfolio,
            config=config,
            preset=args.preset,
            phase=phase,
            liters=liters,
            water_profile_name=water_profile_name,
            osmosis_percent=osmosis_percent,
            water_profile_data=water_profile_data,
            fertilizers=fertilizers,
            molar_masses=molar_masses,
        )
        write_row(writer, jsonl_handle, row)
        aggregate.update(row)
        return True

    with (
        results_csv.open("w", encoding="utf-8", newline="") as csv_handle,
        results_jsonl.open("w", encoding="utf-8") as jsonl_handle,
    ):
        writer = csv.DictWriter(csv_handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        # Config-first ordering keeps capped runs balanced across profiles.
        for config in configs:
            for profile in profiles:
                if not execute(
                    writer,
                    jsonl_handle,
                    phase="settings",
                    profile=profile,
                    portfolio=primary,
                    config=config,
                ):
                    break
            if stopped_early:
                break
        if not stopped_early:
            baseline = configs[0]
            for portfolio in barrage_portfolios:
                for profile in profiles:
                    if not execute(
                        writer,
                        jsonl_handle,
                        phase="mass_barrage",
                        profile=profile,
                        portfolio=portfolio,
                        config=baseline,
                    ):
                        break
                if stopped_early:
                    break

    summary = aggregate.summary()
    summary.update(
        {
            "schema_version": 2,
            "preset": args.preset,
            "profiles": [profile.profile_id for profile in profiles],
            "profile_groups": {profile.profile_id: profile.group for profile in profiles},
            "water_profile": water_profile_name,
            "osmosis_percent": osmosis_percent,
            "liters": liters,
            "primary_portfolio": primary.portfolio_id,
            "allowed_fertilizers": list(primary.fertilizers),
            "config_count": len(configs),
            "mass_barrage_portfolio_count": len(barrage_portfolios),
            "planned_runs": planned_runs,
            "max_runs": args.max_runs,
            "stopped_early": stopped_early,
            "results_csv": str(results_csv),
            "results_jsonl": str(results_jsonl),
            "run_manifest": str(manifest_json),
        }
    )
    summary_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run controlled Horticalc solver-setting benchmarks.")
    parser.add_argument("--preset", choices=("quick", "matrix", "deep"), default="quick")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--profiles", default="all", help="all configured cases, or comma-separated profile ids")
    parser.add_argument(
        "--primary-portfolio",
        default=None,
        help="Named fertilizer portfolio used for the setting matrix (defaults to the cases file).",
    )
    parser.add_argument("--water-profile", default=None)
    parser.add_argument("--osmosis-percent", type=float, default=None)
    parser.add_argument("--liters", type=float, default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--max-profiles", type=int, default=None, help="Limit profiles for smoke tests.")
    parser.add_argument("--max-configs", type=int, default=None, help="Limit setting configs for smoke tests.")
    parser.add_argument(
        "--max-runs",
        type=int,
        default=100_000,
        help="Stop after this many rows. Use 0 to disable the safety cap.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_matrix(args)
    print(f"Solver matrix complete: {summary['total_runs']} runs, {summary['failed_runs']} failures")
    print(f"Planned rows: {summary['planned_runs']}")
    if summary["stopped_early"]:
        print(f"Stopped early at --max-runs {summary['max_runs']}")
    print(f"Results CSV: {summary['results_csv']}")
    print(f"Results JSONL: {summary['results_jsonl']}")
    print(f"Run manifest: {summary['run_manifest']}")
    print(f"Summary JSON: {args.out_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
