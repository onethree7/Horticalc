from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

import scripts.solver_goal_model as goal  # noqa: E402
import scripts.solver_matrix as matrix  # noqa: E402
from horticalc.core import compute_solution  # noqa: E402
from horticalc.data_io import (  # noqa: E402
    Fertilizer,
    load_fertilizers,
    load_molar_masses,
    load_water_profile_data,
)
from horticalc.paths import logs_dir, resolve_water_profile_path, shipped_fertilizers_path  # noqa: E402
from horticalc.solver import SolveResult, solve_recipe_data  # noqa: E402
from horticalc.solver_config import resolve_solver_config  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_OUT_DIR = logs_dir(ROOT) / "solver_matrix" / "mass_nnls_runtime"
CALIBRATION_ELEMENTS = matrix.MACRO_KEYS | matrix.MICRO_KEYS | {"Si"}
LEGACY_34191 = {
    "solver_model": "legacy",
    "irls_max_outer_iter": 2,
    "n_form_priority_weights": {},
    "n_total_governor_enabled": True,
    "n_total_governor_weight": 1.0,
    "nitrogen_objective_mode": "n_total_only",
    "overshoot_penalty": 1.0,
    "relative_weighting": True,
    "s_objective_enabled": True,
    "scale_eps_mg_per_l": 5.0,
    "singleton_max_regress_pp": 0.0,
    "singleton_share_threshold": 0.0,
    "singleton_supplier_enabled": True,
    "singleton_underfill_enabled": False,
    "singleton_underfill_max_iter": 2,
    "singleton_underfill_share_threshold": 0.85,
}


@dataclass(frozen=True)
class ModelPolicy:
    policy_id: str
    kind: str
    goal_policy: goal.GoalPolicy | None = None
    solver_config: dict[str, Any] | None = None


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def model_policies(cases: dict[str, Any]) -> tuple[ModelPolicy, ...]:
    return (
        ModelPolicy(
            "mass_nnls",
            "production",
            solver_config=resolve_solver_config({"solver_model": "mass_nnls"}),
        ),
        ModelPolicy(
            "legacy_canonical",
            "legacy",
            solver_config=resolve_solver_config(cases.get("solver_baseline") or {}),
        ),
        ModelPolicy("legacy_34191", "legacy", solver_config=resolve_solver_config(LEGACY_34191)),
        *(ModelPolicy(item.policy_id, "goal", goal_policy=item) for item in goal.canonical_goal_policies()),
    )


def _select_ids(items: Iterable[Any], selection: str, id_attribute: str) -> list[Any]:
    values = list(items)
    if selection == "all":
        return values
    selected = {item.strip() for item in selection.split(",") if item.strip()}
    result = [item for item in values if str(getattr(item, id_attribute)) in selected]
    found = {str(getattr(item, id_attribute)) for item in result}
    missing = sorted(selected - found)
    if missing:
        raise ValueError(f"Unknown selection: {', '.join(missing)}")
    return result


def _calibration_cases(
    portfolios: Iterable[matrix.FertilizerPortfolio],
    *,
    fertilizers: dict[str, Fertilizer],
    molar_masses: dict[str, float],
    water_profile_data: dict[str, Any],
    osmosis_percent: float,
    liters: float,
) -> list[tuple[matrix.TargetProfile, matrix.FertilizerPortfolio]]:
    cases: list[tuple[matrix.TargetProfile, matrix.FertilizerPortfolio]] = []
    for portfolio in portfolios:
        if portfolio.evaluation_role != "selection" or not portfolio.reference_amounts:
            continue
        fertilizer_rows = [
            {"name": name, "grams": amount} for name, amount in portfolio.reference_amounts.items() if amount > 0.0
        ]
        calculated = compute_solution(
            {"liters": liters, "fertilizers": fertilizer_rows, "urea_as_nh4": False},
            fertilizers,
            molar_masses,
            water_profile_data.get("mg_per_l") or {},
            osmosis_percent=osmosis_percent,
        )
        targets = {
            key: float(value)
            for key, value in calculated.elements_mg_l.items()
            if key in CALIBRATION_ELEMENTS and float(value) > 0.0
        }
        cases.append(
            (
                matrix.TargetProfile(
                    profile_id=f"calibration_{portfolio.portfolio_id}",
                    name=f"Round-trip calibration: {portfolio.portfolio_id}",
                    group="calibration",
                    source=f"reference_amounts:{portfolio.portfolio_id}",
                    targets_mg_per_l=targets,
                ),
                portfolio,
            )
        )
    return cases


def _recipe(
    profile: matrix.TargetProfile,
    portfolio: matrix.FertilizerPortfolio,
    policy: ModelPolicy,
    *,
    liters: float,
    osmosis_percent: float,
) -> dict[str, Any]:
    solver_config = (
        policy.solver_config
        if policy.kind in {"legacy", "production"}
        else {
            "solver_model": "legacy",
            "nitrogen_objective_mode": "n_total_only",
            "s_objective_enabled": True,
        }
    )
    return {
        "name": f"{profile.profile_id}:{portfolio.portfolio_id}:{policy.policy_id}",
        "liters": liters,
        "osmosis_percent": osmosis_percent,
        "urea_as_nh4": False,
        "fertilizers_allowed": list(portfolio.fertilizers),
        "targets_mg_per_l": profile.targets_mg_per_l,
        "solver_config": solver_config,
    }


def _result_metrics(result: SolveResult, molar_masses: dict[str, float]) -> dict[str, Any]:
    factors = goal.error_factors(result.objective_elements, molar_masses, "mmol")
    errors_mg = {key: float(result.errors_mg_l[key]) for key in result.objective_elements}
    errors_mmol = {key: errors_mg[key] * float(factors[index]) for index, key in enumerate(result.objective_elements)}
    absolute_mg = {key: abs(value) for key, value in errors_mg.items()}
    absolute_mmol = {key: abs(value) for key, value in errors_mmol.items()}
    fertilizer_mass = sum(float(item["grams"]) for item in result.fertilizers)
    macro_errors = [value for key, value in absolute_mg.items() if key in matrix.MACRO_KEYS]
    return {
        "errors_mg_per_l": errors_mg,
        "errors_mmol_per_l": errors_mmol,
        "worst_abs_error_mg_per_l": max(absolute_mg.values(), default=0.0),
        "worst_abs_error_mmol_per_l": max(absolute_mmol.values(), default=0.0),
        "worst_underfill_mmol_per_l": max((-value for value in errors_mmol.values()), default=0.0),
        "worst_overshoot_mmol_per_l": max(errors_mmol.values(), default=0.0),
        "total_abs_error_mmol_per_l": sum(absolute_mmol.values()),
        "total_squared_error_mg_per_l2": sum(value * value for value in errors_mg.values()),
        "worst_macro_abs_error_mg_per_l": max(macro_errors, default=0.0),
        "n_total_abs_error_mg_per_l": absolute_mg.get("N_total", 0.0),
        "total_fertilizer_mass_g": fertilizer_mass,
        "used_fertilizer_count": sum(float(item["grams"]) > 1e-8 for item in result.fertilizers),
    }


def _solve_row(
    profile: matrix.TargetProfile,
    portfolio: matrix.FertilizerPortfolio,
    policy: ModelPolicy,
    *,
    phase: str,
    fertilizers: dict[str, Fertilizer],
    molar_masses: dict[str, float],
    water_profile_data: dict[str, Any],
    osmosis_percent: float,
    liters: float,
) -> dict[str, Any]:
    started = time.perf_counter()
    recipe = _recipe(profile, portfolio, policy, liters=liters, osmosis_percent=osmosis_percent)
    try:
        stage_objectives: dict[str, float] = {}
        if policy.kind == "goal":
            solved = goal.solve_goal_recipe_data(
                recipe,
                policy.goal_policy,
                ferts=matrix.fertilizers_for_portfolio(portfolio, fertilizers),
                mm=molar_masses,
                water_profile_data=water_profile_data,
            )
            result = solved.result
            dominated = solved.pareto_dominated
            pareto_improvement = solved.pareto_improvement
            stage_objectives = solved.stage_objectives
        else:
            result = solve_recipe_data(
                recipe,
                ferts=matrix.fertilizers_for_portfolio(portfolio, fertilizers),
                mm=molar_masses,
                water_profile_data=water_profile_data,
            )
            dominated = goal.audit_pareto_dominance(
                recipe,
                result,
                error_unit="mmol",
                ferts=matrix.fertilizers_for_portfolio(portfolio, fertilizers),
                mm=molar_masses,
                water_profile_data=water_profile_data,
            )
            pareto_improvement = None
        metrics = _result_metrics(result, molar_masses)
        return {
            "status": "ok",
            "phase": phase,
            "profile_id": profile.profile_id,
            "profile_group": profile.group,
            "portfolio_id": portfolio.portfolio_id,
            "portfolio_role": portfolio.evaluation_role,
            "policy_id": policy.policy_id,
            "policy_kind": policy.kind,
            "pareto_dominated": dominated,
            "pareto_improvement": pareto_improvement,
            "elapsed_seconds": time.perf_counter() - started,
            "objective_elements": result.objective_elements,
            "targets_mg_per_l": result.targets_mg_l,
            "achieved_mg_per_l": {
                key: result.achieved_elements_mg_l.get(key, 0.0) for key in result.objective_elements
            },
            "fertilizers": result.fertilizers,
            "stage_objectives": stage_objectives,
            **metrics,
        }
    except Exception as exc:  # noqa: BLE001 - matrix rows must preserve individual failures
        return {
            "status": "error",
            "phase": phase,
            "profile_id": profile.profile_id,
            "profile_group": profile.group,
            "portfolio_id": portfolio.portfolio_id,
            "portfolio_role": portfolio.evaluation_role,
            "policy_id": policy.policy_id,
            "policy_kind": policy.kind,
            "pareto_dominated": None,
            "elapsed_seconds": time.perf_counter() - started,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    return float(np.quantile(np.asarray(values, dtype=float), fraction))


def _policy_summary(rows: list[dict[str, Any]], policy: ModelPolicy) -> dict[str, Any]:
    selection = [
        row
        for row in rows
        if row["policy_id"] == policy.policy_id
        and row["status"] == "ok"
        and row["phase"] == "benchmark"
        and row["portfolio_role"] == "selection"
    ]
    diagnostics = [
        row
        for row in rows
        if row["policy_id"] == policy.policy_id
        and row["status"] == "ok"
        and row["phase"] == "benchmark"
        and row["portfolio_role"] == "diagnostic"
    ]
    calibrations = [
        row
        for row in rows
        if row["policy_id"] == policy.policy_id and row["status"] == "ok" and row["phase"] == "calibration"
    ]
    case_worst = [float(row["worst_abs_error_mmol_per_l"]) for row in selection]
    flattened = sorted(
        (abs(float(error)) for row in selection for error in row["errors_mmol_per_l"].values()),
        reverse=True,
    )
    return {
        "policy_id": policy.policy_id,
        "policy_kind": policy.kind,
        "selection_case_count": len(selection),
        "diagnostic_case_count": len(diagnostics),
        "calibration_case_count": len(calibrations),
        "failed_case_count": sum(row["policy_id"] == policy.policy_id and row["status"] != "ok" for row in rows),
        "pareto_dominated_selection_count": sum(bool(row["pareto_dominated"]) for row in selection),
        "worst_abs_error_mmol_per_l": max(case_worst, default=math.inf),
        "p95_case_worst_abs_error_mmol_per_l": _percentile(case_worst, 0.95),
        "mean_case_worst_abs_error_mmol_per_l": float(np.mean(case_worst)) if case_worst else math.inf,
        "worst_n_total_abs_error_mg_per_l": max(
            (float(row["n_total_abs_error_mg_per_l"]) for row in selection), default=math.inf
        ),
        "worst_macro_abs_error_mg_per_l": max(
            (float(row["worst_macro_abs_error_mg_per_l"]) for row in selection), default=math.inf
        ),
        "worst_total_fertilizer_mass_g": max(
            (float(row["total_fertilizer_mass_g"]) for row in selection), default=math.inf
        ),
        "mean_total_squared_error_mg_per_l2": (
            float(np.mean([float(row["total_squared_error_mg_per_l2"]) for row in selection]))
            if selection
            else math.inf
        ),
        "calibration_worst_abs_error_mmol_per_l": max(
            (float(row["worst_abs_error_mmol_per_l"]) for row in calibrations), default=math.inf
        ),
        "diagnostic_worst_abs_error_mmol_per_l": (
            max(float(row["worst_abs_error_mmol_per_l"]) for row in diagnostics) if diagnostics else None
        ),
        "lexicographic_error_vector": flattened,
    }


def _quality_gate(summaries: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    production = [item for item in summaries if item["policy_kind"] == "production"]
    legacy = [item for item in summaries if item["policy_kind"] == "legacy"]
    goals = [item for item in summaries if item["policy_kind"] == "goal"]
    if len(production) != 1:
        raise ValueError("The model matrix requires exactly one production policy")
    mass = production[0]
    legacy_reference = next(item for item in legacy if item["policy_id"] == "legacy_canonical")
    selection_rows = [
        row
        for row in rows
        if row["status"] == "ok" and row["phase"] == "benchmark" and row["portfolio_role"] == "selection"
    ]
    by_policy_case = {(row["policy_id"], row["profile_id"], row["portfolio_id"]): row for row in selection_rows}
    comparisons = []
    for key, mass_row in by_policy_case.items():
        policy_id, profile_id, portfolio_id = key
        if policy_id != "mass_nnls":
            continue
        legacy_row = by_policy_case.get(("legacy_canonical", profile_id, portfolio_id))
        if legacy_row is not None:
            comparisons.append(
                float(mass_row["total_squared_error_mg_per_l2"])
                <= float(legacy_row["total_squared_error_mg_per_l2"]) + 1e-7
            )
    checks = {
        "production_has_no_failures": mass["failed_case_count"] == 0,
        "production_is_pareto_safe": mass["pareto_dominated_selection_count"] == 0,
        "production_never_worsens_raw_mg_sse_vs_legacy": bool(comparisons) and all(comparisons),
        "production_roundtrips_reference_recipes": mass["calibration_worst_abs_error_mmol_per_l"] <= 1e-6,
        "production_outputs_finite_mass": math.isfinite(mass["worst_total_fertilizer_mass_g"]),
        "research_models_have_no_failures": all(item["failed_case_count"] == 0 for item in goals),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "production_policy": mass["policy_id"],
        "legacy_reference_policy": legacy_reference["policy_id"],
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    cases = matrix._read_yaml(args.cases)
    fertilizers = load_fertilizers(shipped_fertilizers_path(ROOT))
    molar_masses = load_molar_masses()
    profiles = matrix.load_target_profiles(cases, args.profiles)
    named = matrix.load_fertilizer_portfolios(cases, fertilizers)
    portfolios = matrix.mass_barrage_portfolios(cases, named)
    portfolios = _select_ids(portfolios, args.portfolio_ids, "portfolio_id")
    policies = _select_ids(model_policies(cases), args.policies, "policy_id")
    if not any(item.evaluation_role == "selection" for item in portfolios):
        raise ValueError("The solver-model matrix requires at least one selection-role portfolio")
    required_kinds = {"production", "goal", "legacy"}
    if not required_kinds.issubset({item.kind for item in policies}):
        raise ValueError("The quality gate requires production, goal-research, and legacy policies")
    water_profile_name = args.water_profile or str(cases.get("water_profile") or "65936")
    water_profile_data = dict(load_water_profile_data(resolve_water_profile_path(water_profile_name, ROOT)))
    osmosis_percent = float(cases.get("osmosis_percent") or 0.0)
    water_profile_data["osmosis_percent"] = osmosis_percent
    liters = float(cases.get("liters") or 10.0)
    calibration_cases = _calibration_cases(
        named.values(),
        fertilizers=fertilizers,
        molar_masses=molar_masses,
        water_profile_data=water_profile_data,
        osmosis_percent=osmosis_percent,
        liters=liters,
    )

    planned = len(policies) * (len(profiles) * len(portfolios) + len(calibration_cases))
    rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    for policy in policies:
        for profile in profiles:
            for portfolio in portfolios:
                rows.append(
                    _solve_row(
                        profile,
                        portfolio,
                        policy,
                        phase="benchmark",
                        fertilizers=fertilizers,
                        molar_masses=molar_masses,
                        water_profile_data=water_profile_data,
                        osmosis_percent=osmosis_percent,
                        liters=liters,
                    )
                )
        for profile, portfolio in calibration_cases:
            rows.append(
                _solve_row(
                    profile,
                    portfolio,
                    policy,
                    phase="calibration",
                    fertilizers=fertilizers,
                    molar_masses=molar_masses,
                    water_profile_data=water_profile_data,
                    osmosis_percent=osmosis_percent,
                    liters=liters,
                )
            )

    summaries = [_policy_summary(rows, policy) for policy in policies]
    summaries.sort(
        key=lambda item: (
            item["failed_case_count"],
            item["pareto_dominated_selection_count"],
            tuple(item["lexicographic_error_vector"]),
        )
    )
    for rank, item in enumerate(summaries, start=1):
        item["rank"] = rank
        item.pop("lexicographic_error_vector")
    quality = _quality_gate([_policy_summary(rows, policy) for policy in policies], rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    rows_path = args.out_dir / "model_matrix_rows.jsonl.gz"
    with gzip.open(rows_path, "wt", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(_json(row) + "\n")
    summary = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "cases_sha256": hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        "water_profile": water_profile_name,
        "osmosis_percent": osmosis_percent,
        "liters": liters,
        "profile_count": len(profiles),
        "portfolio_count": len(portfolios),
        "selection_portfolio_count": sum(item.evaluation_role == "selection" for item in portfolios),
        "diagnostic_portfolio_count": sum(item.evaluation_role == "diagnostic" for item in portfolios),
        "calibration_case_count": len(calibration_cases),
        "policy_count": len(policies),
        "planned_rows": planned,
        "completed_rows": len(rows),
        "failed_rows": sum(row["status"] != "ok" for row in rows),
        "elapsed_seconds": time.perf_counter() - started,
        "policies": [
            {
                "policy_id": item.policy_id,
                "kind": item.kind,
                "goal_policy": asdict(item.goal_policy) if item.goal_policy else None,
                "solver_config": item.solver_config,
            }
            for item in policies
        ],
        "ranking": summaries,
        "quality_gate": quality,
        "rows_file": str(rows_path.resolve()),
    }
    (args.out_dir / "model_matrix_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate mass NNLS against legacy and goal-research controls.")
    parser.add_argument("--cases", type=Path, default=matrix.DEFAULT_CASES_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--profiles", default="all")
    parser.add_argument("--portfolio-ids", default="all")
    parser.add_argument("--policies", default="all")
    parser.add_argument("--water-profile", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run(args)
    gate = summary["quality_gate"]
    print(
        f"Solver-model matrix: {summary['completed_rows']:,}/{summary['planned_rows']:,} rows, "
        f"{summary['failed_rows']} failures in {summary['elapsed_seconds']:.2f}s"
    )
    print(
        f"Production policy: {gate['production_policy']}; legacy reference: {gate['legacy_reference_policy']}; "
        f"quality gate: {'PASS' if gate['passed'] else 'FAIL'}"
    )
    return 0 if gate["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
