from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.optimize import linprog

from horticalc import solver
from horticalc.data_io import Fertilizer

N_KEYS = {"N_total", "N_NH4", "N_NO3", "N_UREA"}
ERROR_UNITS = {"mg", "mmol"}
DIRECTION_MODES = {"symmetric", "under_first"}


@dataclass(frozen=True)
class GoalPolicy:
    policy_id: str
    error_unit: str
    direction_mode: str
    underfill_factor: float = 1.0

    def __post_init__(self) -> None:
        if self.error_unit not in ERROR_UNITS:
            raise ValueError(f"Unknown goal error unit: {self.error_unit}")
        if self.direction_mode not in DIRECTION_MODES:
            raise ValueError(f"Unknown goal direction mode: {self.direction_mode}")
        if not np.isfinite(self.underfill_factor) or self.underfill_factor < 1.0:
            raise ValueError("underfill_factor must be finite and >= 1")


@dataclass(frozen=True)
class GoalSolveResult:
    result: solver.SolveResult
    policy: GoalPolicy
    stage_objectives: dict[str, float]
    errors_in_policy_unit: dict[str, float]
    pareto_dominated: bool
    pareto_improvement: float


def canonical_goal_policies() -> tuple[GoalPolicy, ...]:
    return (
        GoalPolicy("goal_mmol_symmetric", "mmol", "symmetric"),
        GoalPolicy("goal_mmol_under_x2", "mmol", "symmetric", 2.0),
        GoalPolicy("goal_mmol_under_x4", "mmol", "symmetric", 4.0),
        GoalPolicy("goal_mmol_under_x10", "mmol", "symmetric", 10.0),
        GoalPolicy("goal_mg_symmetric", "mg", "symmetric"),
    )


def _molar_mass_key(element: str) -> str:
    return "N" if element in N_KEYS else element


def error_factors(
    objective_keys: list[str],
    molar_masses: dict[str, float],
    error_unit: str,
) -> np.ndarray:
    if error_unit == "mg":
        return np.ones(len(objective_keys), dtype=float)
    if error_unit != "mmol":
        raise ValueError(f"Unknown goal error unit: {error_unit}")
    factors = []
    for key in objective_keys:
        mass_key = _molar_mass_key(key)
        if mass_key not in molar_masses:
            raise KeyError(f"Molar mass missing for goal element {key!r} ({mass_key!r})")
        factors.append(1.0 / float(molar_masses[mass_key]))
    return np.asarray(factors, dtype=float)


def _freeze_tolerance(value: float, *, relaxed: bool = False) -> float:
    floor = 1e-6 if relaxed else 1e-9
    return max(floor, abs(float(value)) * 1e-8)


def _linprog_bounds(upper_bounds: np.ndarray, row_count: int) -> list[tuple[float, float | None]]:
    fertilizer_bounds = [(0.0, None if np.isinf(value) else float(value)) for value in upper_bounds]
    return [*fertilizer_bounds, *([(0.0, None)] * (2 * row_count + 2))]


def _solve_stage(
    objective: np.ndarray,
    *,
    A_eq: np.ndarray,
    b_eq: np.ndarray,
    inequalities: list[np.ndarray],
    limits: list[float],
    bounds: list[tuple[float, float | None]],
) -> np.ndarray:
    result = linprog(
        objective,
        A_ub=np.asarray(inequalities, dtype=float) if inequalities else None,
        b_ub=np.asarray(limits, dtype=float) if limits else None,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
        options={
            "presolve": True,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
            "ipm_optimality_tolerance": 1e-10,
        },
    )
    if not result.success or result.x is None:
        raise ValueError(f"Goal LP failed: {result.message}")
    return np.asarray(result.x, dtype=float)


def solve_goal_weights(
    matrix: np.ndarray,
    remaining_targets: np.ndarray,
    upper_bounds: np.ndarray,
    row_factors: np.ndarray,
    direction_mode: str,
    underfill_factor: float = 1.0,
) -> tuple[np.ndarray, dict[str, float]]:
    if direction_mode not in DIRECTION_MODES:
        raise ValueError(f"Unknown goal direction mode: {direction_mode}")
    if not np.isfinite(underfill_factor) or underfill_factor < 1.0:
        raise ValueError("underfill_factor must be finite and >= 1")
    A = np.asarray(matrix, dtype=float) * np.asarray(row_factors, dtype=float)[:, None]
    b = np.asarray(remaining_targets, dtype=float) * np.asarray(row_factors, dtype=float)
    rows, columns = A.shape
    if b.shape != (rows,) or upper_bounds.shape != (columns,):
        raise ValueError("Goal LP inputs have incompatible dimensions")

    under_start = columns
    over_start = columns + rows
    t_under = columns + 2 * rows
    t_over = t_under + 1
    variable_count = t_over + 1

    A_eq = np.zeros((rows, variable_count), dtype=float)
    A_eq[:, :columns] = A
    A_eq[:, under_start:over_start] = np.eye(rows)
    A_eq[:, over_start:t_under] = -np.eye(rows)
    bounds = _linprog_bounds(np.asarray(upper_bounds, dtype=float), rows)
    inequalities: list[np.ndarray] = []
    limits: list[float] = []
    stages: dict[str, float] = {}

    if direction_mode == "symmetric":
        for index in range(rows):
            constraint = np.zeros(variable_count, dtype=float)
            constraint[under_start + index] = underfill_factor
            constraint[over_start + index] = 1.0
            constraint[t_under] = -1.0
            inequalities.append(constraint)
            limits.append(0.0)
        objective = np.zeros(variable_count, dtype=float)
        objective[t_under] = 1.0
        solution = _solve_stage(
            objective,
            A_eq=A_eq,
            b_eq=b,
            inequalities=inequalities,
            limits=limits,
            bounds=bounds,
        )
        stages["worst_absolute_error"] = float(solution[t_under])
        freeze = np.zeros(variable_count, dtype=float)
        freeze[t_under] = 1.0
        inequalities.append(freeze)
        limits.append(stages["worst_absolute_error"] + _freeze_tolerance(stages["worst_absolute_error"]))
    else:
        for index in range(rows):
            under_constraint = np.zeros(variable_count, dtype=float)
            under_constraint[under_start + index] = 1.0
            under_constraint[t_under] = -1.0
            inequalities.append(under_constraint)
            limits.append(0.0)
            over_constraint = np.zeros(variable_count, dtype=float)
            over_constraint[over_start + index] = 1.0
            over_constraint[t_over] = -1.0
            inequalities.append(over_constraint)
            limits.append(0.0)

        objective = np.zeros(variable_count, dtype=float)
        objective[t_under] = 1.0
        solution = _solve_stage(
            objective,
            A_eq=A_eq,
            b_eq=b,
            inequalities=inequalities,
            limits=limits,
            bounds=bounds,
        )
        stages["worst_underfill"] = float(solution[t_under])
        freeze_under = np.zeros(variable_count, dtype=float)
        freeze_under[t_under] = 1.0
        inequalities.append(freeze_under)
        limits.append(stages["worst_underfill"] + _freeze_tolerance(stages["worst_underfill"], relaxed=True))

        objective = np.zeros(variable_count, dtype=float)
        objective[t_over] = 1.0
        solution = _solve_stage(
            objective,
            A_eq=A_eq,
            b_eq=b,
            inequalities=inequalities,
            limits=limits,
            bounds=bounds,
        )
        stages["worst_overshoot"] = float(solution[t_over])
        freeze_over = np.zeros(variable_count, dtype=float)
        freeze_over[t_over] = 1.0
        inequalities.append(freeze_over)
        limits.append(stages["worst_overshoot"] + _freeze_tolerance(stages["worst_overshoot"], relaxed=True))

    total_error_objective = np.zeros(variable_count, dtype=float)
    total_error_objective[under_start:over_start] = underfill_factor
    total_error_objective[over_start:t_under] = 1.0
    solution = _solve_stage(
        total_error_objective,
        A_eq=A_eq,
        b_eq=b,
        inequalities=inequalities,
        limits=limits,
        bounds=bounds,
    )
    stages["total_absolute_error"] = float(total_error_objective @ solution)
    stages["variable_fertilizer_mass_g"] = float(solution[:columns].sum())
    return np.maximum(solution[:columns], 0.0), stages


def _pareto_improvement(
    matrix: np.ndarray,
    remaining_targets: np.ndarray,
    upper_bounds: np.ndarray,
    row_factors: np.ndarray,
    candidate_errors: np.ndarray,
) -> float:
    A = np.asarray(matrix, dtype=float) * row_factors[:, None]
    b = np.asarray(remaining_targets, dtype=float) * row_factors
    cap = np.abs(np.asarray(candidate_errors, dtype=float))
    rows, columns = A.shape
    under_start = columns
    over_start = columns + rows
    variable_count = columns + 2 * rows
    A_eq = np.zeros((rows, variable_count), dtype=float)
    A_eq[:, :columns] = A
    A_eq[:, under_start:over_start] = np.eye(rows)
    A_eq[:, over_start:] = -np.eye(rows)
    A_ub = np.zeros((rows, variable_count), dtype=float)
    A_ub[:, under_start:over_start] = np.eye(rows)
    A_ub[:, over_start:] = np.eye(rows)
    objective = np.zeros(variable_count, dtype=float)
    objective[under_start:] = 1.0
    bounds = [
        *[(0.0, None if np.isinf(value) else float(value)) for value in upper_bounds],
        *([(0.0, None)] * (2 * rows)),
    ]
    result = linprog(
        objective,
        A_ub=A_ub,
        b_ub=cap,
        A_eq=A_eq,
        b_eq=b,
        bounds=bounds,
        method="highs",
        options={
            "presolve": True,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
            "ipm_optimality_tolerance": 1e-10,
        },
    )
    if not result.success or result.fun is None:
        return 0.0
    candidate_sum = float(np.abs(candidate_errors).sum())
    return max(0.0, candidate_sum - float(result.fun))


def solve_goal_recipe_data(
    recipe: dict[str, Any],
    policy: GoalPolicy,
    *,
    ferts: dict[str, Fertilizer] | None = None,
    mm: dict[str, float] | None = None,
    water_profile_data: dict[str, Any] | None = None,
) -> GoalSolveResult:
    problem = solver._prepare_solve_problem(
        recipe,
        ferts=ferts,
        mm=mm,
        water_profile_data=water_profile_data,
        water_profile_path=None,
    )
    row_factors = error_factors(problem.objective_keys, problem.molar_masses, policy.error_unit)
    remaining = problem.remaining_targets - problem.matrix @ problem.fixed_weights
    variable_weights, stages = solve_goal_weights(
        problem.matrix[:, problem.variable_mask],
        remaining,
        problem.upper_bounds[problem.variable_mask],
        row_factors,
        policy.direction_mode,
        policy.underfill_factor,
    )
    weights = problem.fixed_weights.copy()
    weights[problem.variable_mask] += variable_weights
    weights[np.abs(weights) < 1e-8] = 0.0
    variant_result = solver._VariantRunner(problem)._build_solution_for_weights(weights)
    solve_result = solver._build_solve_result(problem, variant_result)
    policy_errors = {
        key: float(solve_result.errors_mg_l[key]) * float(row_factors[index])
        for index, key in enumerate(problem.objective_keys)
    }
    pareto_improvement = _pareto_improvement(
        problem.matrix[:, problem.variable_mask],
        remaining,
        problem.upper_bounds[problem.variable_mask],
        row_factors,
        np.asarray([policy_errors[key] for key in problem.objective_keys], dtype=float),
    )
    candidate_sum = sum(abs(value) for value in policy_errors.values())
    dominated = pareto_improvement > max(1e-5, candidate_sum * 1e-5)
    return GoalSolveResult(
        result=solve_result,
        policy=policy,
        stage_objectives=stages,
        errors_in_policy_unit=policy_errors,
        pareto_dominated=dominated,
        pareto_improvement=pareto_improvement,
    )


def audit_pareto_dominance(
    recipe: dict[str, Any],
    solve_result: solver.SolveResult,
    *,
    error_unit: str = "mmol",
    ferts: dict[str, Fertilizer] | None = None,
    mm: dict[str, float] | None = None,
    water_profile_data: dict[str, Any] | None = None,
) -> bool:
    problem = solver._prepare_solve_problem(
        recipe,
        ferts=ferts,
        mm=mm,
        water_profile_data=water_profile_data,
        water_profile_path=None,
    )
    factors = error_factors(problem.objective_keys, problem.molar_masses, error_unit)
    remaining = problem.remaining_targets - problem.matrix @ problem.fixed_weights
    errors = np.asarray([solve_result.errors_mg_l[key] for key in problem.objective_keys], dtype=float) * factors
    improvement = _pareto_improvement(
        problem.matrix[:, problem.variable_mask],
        remaining,
        problem.upper_bounds[problem.variable_mask],
        factors,
        errors,
    )
    candidate_sum = float(np.abs(errors).sum())
    return improvement > max(1e-5, candidate_sum * 1e-5)
