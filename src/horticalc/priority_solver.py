from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
from scipy.optimize import linprog

MIN_PRIORITY = 1
MAX_PRIORITY = 4
REPORT_ONLY_PRIORITY = 0
DEFAULT_PRIORITY = 3


@dataclass(frozen=True)
class PriorityStageResult:
    priority: int
    max_error_mg_per_l: float
    total_error_mg_per_l: float


@dataclass(frozen=True)
class HierarchicalSolveResult:
    doses: np.ndarray
    stages: tuple[PriorityStageResult, ...]


def _positive_tolerance(value: float, tolerance: float) -> float:
    return max(tolerance, tolerance * max(1.0, abs(float(value))))


def _solve_lp(
    objective: np.ndarray,
    *,
    equality_matrix: np.ndarray,
    equality_targets: np.ndarray,
    upper_rows: list[np.ndarray],
    upper_targets: list[float],
    bounds: list[tuple[float, float | None]],
) -> np.ndarray:
    result = linprog(
        objective,
        A_ub=np.asarray(upper_rows, dtype=float) if upper_rows else None,
        b_ub=np.asarray(upper_targets, dtype=float) if upper_targets else None,
        A_eq=equality_matrix,
        b_eq=equality_targets,
        bounds=bounds,
        method="highs",
        options={
            "dual_feasibility_tolerance": 1e-9,
            "primal_feasibility_tolerance": 1e-9,
        },
    )
    if not result.success or result.x is None:
        raise ValueError(f"Hierarchical solver failed: {result.message}")
    if not np.all(np.isfinite(result.x)):
        raise ValueError("Hierarchical solver produced a non-finite result")
    return np.asarray(result.x, dtype=float)


def solve_hierarchical_priorities(
    matrix: np.ndarray,
    targets: np.ndarray,
    upper_bounds: np.ndarray,
    priorities: Sequence[tuple[int, int]],
    effective_mass_factors: np.ndarray,
    *,
    tolerance: float = 1e-7,
) -> HierarchicalSolveResult:
    """Solve strict under/over priority tiers without nutrient concentration bounds.

    Each tier first minimizes its worst directional residual in raw mg/L, then
    minimizes the tier's total residual without worsening that optimum. Lower
    tiers retain both optima. Effective product mass is the final deterministic
    tie-break and cannot worsen any nutrient-priority result.
    """

    matrix = np.asarray(matrix, dtype=float)
    targets = np.asarray(targets, dtype=float)
    upper_bounds = np.asarray(upper_bounds, dtype=float)
    mass_factors = np.asarray(effective_mass_factors, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    row_count, dose_count = matrix.shape
    if targets.shape != (row_count,):
        raise ValueError("targets must match the number of matrix rows")
    if upper_bounds.shape != (dose_count,):
        raise ValueError("upper_bounds must match the number of fertilizer columns")
    if mass_factors.shape != (dose_count,):
        raise ValueError("effective_mass_factors must match the number of fertilizer columns")
    if not np.all(np.isfinite(matrix)) or not np.all(np.isfinite(targets)):
        raise ValueError("matrix and targets must be finite")
    if np.any(np.isnan(upper_bounds)) or np.any(upper_bounds < 0.0):
        raise ValueError("upper_bounds must be non-negative")
    if not np.all(np.isfinite(mass_factors)) or np.any(mass_factors <= 0.0):
        raise ValueError("effective_mass_factors must be finite and positive")
    if not np.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")

    normalized_priorities: list[tuple[int, int]] = []
    for pair in priorities:
        if len(pair) != 2:
            raise ValueError("each priority row must define under and over")
        under, over = pair
        if (
            not isinstance(under, int)
            or isinstance(under, bool)
            or not isinstance(over, int)
            or isinstance(over, bool)
            or under < REPORT_ONLY_PRIORITY
            or under > MAX_PRIORITY
            or over < REPORT_ONLY_PRIORITY
            or over > MAX_PRIORITY
        ):
            raise ValueError("priorities must be integers from 0 through 4")
        normalized_priorities.append((under, over))
    if len(normalized_priorities) != row_count:
        raise ValueError("priorities must match the number of matrix rows")
    if not any(under > 0 or over > 0 for under, over in normalized_priorities):
        raise ValueError("at least one under or over priority must be active")

    if dose_count == 0:
        under_errors = np.maximum(targets, 0.0)
        over_errors = np.maximum(-targets, 0.0)
        stages = []
        for level in range(MIN_PRIORITY, MAX_PRIORITY + 1):
            values = [
                error
                for index, pair in enumerate(normalized_priorities)
                for error, direction_priority in (
                    (under_errors[index], pair[0]),
                    (over_errors[index], pair[1]),
                )
                if direction_priority == level
            ]
            if values:
                stages.append(PriorityStageResult(level, float(max(values)), float(sum(values))))
        return HierarchicalSolveResult(np.zeros(0, dtype=float), tuple(stages))

    base_variable_count = dose_count + 2 * row_count
    under_offset = dose_count
    over_offset = dose_count + row_count
    equality_matrix = np.zeros((row_count, base_variable_count), dtype=float)
    equality_matrix[:, :dose_count] = matrix
    for index in range(row_count):
        equality_matrix[index, under_offset + index] = 1.0
        equality_matrix[index, over_offset + index] = -1.0

    bounds: list[tuple[float, float | None]] = [
        (0.0, None if np.isinf(value) else float(value)) for value in upper_bounds
    ]
    bounds.extend([(0.0, None)] * (2 * row_count))
    retained_rows: list[np.ndarray] = []
    retained_targets: list[float] = []
    stages: list[PriorityStageResult] = []

    for level in range(MIN_PRIORITY, MAX_PRIORITY + 1):
        residual_indices: list[int] = []
        for index, (under_priority, over_priority) in enumerate(normalized_priorities):
            if under_priority == level:
                residual_indices.append(under_offset + index)
            if over_priority == level:
                residual_indices.append(over_offset + index)
        if not residual_indices:
            continue

        max_variable_index = base_variable_count
        max_objective = np.zeros(base_variable_count + 1, dtype=float)
        max_objective[max_variable_index] = 1.0
        max_rows = [np.pad(row, (0, 1)) for row in retained_rows]
        max_targets = list(retained_targets)
        for residual_index in residual_indices:
            row = np.zeros(base_variable_count + 1, dtype=float)
            row[residual_index] = 1.0
            row[max_variable_index] = -1.0
            max_rows.append(row)
            max_targets.append(0.0)
        max_solution = _solve_lp(
            max_objective,
            equality_matrix=np.pad(equality_matrix, ((0, 0), (0, 1))),
            equality_targets=targets,
            upper_rows=max_rows,
            upper_targets=max_targets,
            bounds=[*bounds, (0.0, None)],
        )
        max_error = max(0.0, float(max_solution[max_variable_index]))
        max_limit = max_error + _positive_tolerance(max_error, tolerance)
        for residual_index in residual_indices:
            row = np.zeros(base_variable_count, dtype=float)
            row[residual_index] = 1.0
            retained_rows.append(row)
            retained_targets.append(max_limit)

        total_objective = np.zeros(base_variable_count, dtype=float)
        total_objective[residual_indices] = 1.0
        total_solution = _solve_lp(
            total_objective,
            equality_matrix=equality_matrix,
            equality_targets=targets,
            upper_rows=retained_rows,
            upper_targets=retained_targets,
            bounds=bounds,
        )
        total_error = max(0.0, float(total_objective @ total_solution))
        total_row = np.zeros(base_variable_count, dtype=float)
        total_row[residual_indices] = 1.0
        retained_rows.append(total_row)
        retained_targets.append(total_error + _positive_tolerance(total_error, tolerance))
        stages.append(PriorityStageResult(level, max_error, total_error))

    mass_objective = np.zeros(base_variable_count, dtype=float)
    mass_objective[:dose_count] = mass_factors
    final_solution = _solve_lp(
        mass_objective,
        equality_matrix=equality_matrix,
        equality_targets=targets,
        upper_rows=retained_rows,
        upper_targets=retained_targets,
        bounds=bounds,
    )
    doses = np.clip(final_solution[:dose_count], 0.0, upper_bounds)
    return HierarchicalSolveResult(doses, tuple(stages))
