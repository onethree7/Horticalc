from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np

from .core import (
    OTHER_ELEMENT_FORMS,
    OXIDE_ELEMENT_FORMS,
    _form_to_element,
    _oxide_to_element,
    compute_solution,
)
from .data_io import (
    Fertilizer,
    load_fertilizers,
    load_molar_masses,
    load_recipe,
    load_water_profile_data,
)
from .paths import resolve_water_profile_path


IGNORED_TARGETS = {"S", "SO4", "NA", "CL"}


@dataclass
class SolveResult:
    liters: float
    fertilizers: List[Dict[str, float]]
    objective_elements: List[str]
    targets_mg_l: Dict[str, float]
    achieved_elements_mg_l: Dict[str, float]
    errors_mg_l: Dict[str, float]
    errors_percent: Dict[str, float]

    def to_dict(self) -> dict:
        return {
            "liters": self.liters,
            "fertilizers": self.fertilizers,
            "objective_elements": self.objective_elements,
            "targets_mg_per_l": self.targets_mg_l,
            "achieved_elements_mg_per_l": self.achieved_elements_mg_l,
            "errors_mg_per_l": self.errors_mg_l,
            "errors_percent": self.errors_percent,
        }


def _nnls(A: np.ndarray, b: np.ndarray, tol: float = 1e-10, max_iter: int = 500) -> np.ndarray:
    m, n = A.shape
    x = np.zeros(n)
    passive = np.zeros(n, dtype=bool)
    w = A.T @ (b - A @ x)
    iters = 0
    while np.any(w > tol) and iters < max_iter:
        t = int(np.argmax(w))
        passive[t] = True
        while True:
            Ap = A[:, passive]
            if Ap.size == 0:
                break
            z = np.zeros(n)
            z_passive, *_ = np.linalg.lstsq(Ap, b, rcond=None)
            z[passive] = z_passive
            if np.all(z[passive] > tol):
                x = z
                break
            negative = (z <= tol) & passive
            alpha = np.min(x[negative] / (x[negative] - z[negative]))
            x = x + alpha * (z - x)
            passive[(np.abs(x) <= tol) & passive] = False
        w = A.T @ (b - A @ x)
        iters += 1
    return x


def _normalize_targets(targets: Dict[str, float]) -> Dict[str, float]:
    cleaned: Dict[str, float] = {}
    for key, value in (targets or {}).items():
        if key is None:
            continue
        cleaned[str(key)] = float(value)
    return cleaned


def _objective_keys(targets: Dict[str, float], *, allow_n_total_with_forms: bool = True) -> List[str]:
    keys = []
    for key, val in targets.items():
        if val == 0:
            continue
        if key.upper() in IGNORED_TARGETS:
            continue
        keys.append(key)
    if (
        not allow_n_total_with_forms
        and "N_total" in keys
        and any(k in keys for k in ("N_NH4", "N_NO3", "N_UREA"))
    ):
        keys = [key for key in keys if key != "N_total"]
    return keys


def _fertilizer_element_contrib_per_g(fert: Fertilizer, mm: Dict[str, float]) -> Dict[str, float]:
    elements: Dict[str, float] = {}
    wf = float(fert.weight_factor or 1.0)

    def add(key: str, value: float) -> None:
        if value == 0:
            return
        elements[key] = elements.get(key, 0.0) + value

    for form, frac in fert.comp.items():
        mg_per_g = float(frac) * 1000.0 * wf
        if form in ("NH4", "NO3", "UREA"):
            add("N_total", mg_per_g)
            if form == "NH4":
                add("N_NH4", mg_per_g)
            elif form == "NO3":
                add("N_NO3", mg_per_g)
            else:
                add("N_UREA", mg_per_g)
            continue
        if form in OXIDE_ELEMENT_FORMS:
            element, mg_el = _oxide_to_element(mg_per_g, mm, form)
            add(element, mg_el)
            continue
        if form in OTHER_ELEMENT_FORMS:
            element, mg_el = _form_to_element(mg_per_g, mm, form)
            add(element, mg_el)
            continue

    return elements


def _build_row_scales(
    objective_keys: List[str],
    targets_raw: Dict[str, float],
    b: np.ndarray,
    *,
    eps_mg_per_l: float = 1.0,
) -> np.ndarray:
    scales = np.zeros(len(objective_keys))
    for idx, key in enumerate(objective_keys):
        target_i = abs(float(targets_raw.get(key, 0.0)))
        b_i = abs(float(b[idx]))
        scales[idx] = max(target_i, b_i, eps_mg_per_l)
    return scales


def _nnls_weighted_irls(
    A: np.ndarray,
    b: np.ndarray,
    *,
    scales: np.ndarray,
    priority_factors: np.ndarray | None,
    overshoot_only_weights: np.ndarray | None,
    overshoot_penalty: float,
    max_outer_iter: int,
    tol: float,
    rtol: float,
) -> np.ndarray:
    if A.size == 0:
        return np.array([])
    if priority_factors is None:
        priority_factors = np.ones_like(scales)
    base_w = priority_factors / np.maximum(scales, tol)
    overshoot_only = overshoot_only_weights
    if overshoot_only is None:
        overshoot_only = np.zeros_like(base_w)
    A_weighted = A * base_w[:, None]
    b_weighted = b * base_w
    x = _nnls(A_weighted, b_weighted, tol=tol)
    for _ in range(max_outer_iter - 1):
        r = A @ x - b
        w = base_w * (1.0 + overshoot_penalty * (r > 0)) + overshoot_only * (r > 0)
        A_weighted = A * w[:, None]
        b_weighted = b * w
        x_new = _nnls(A_weighted, b_weighted, tol=tol)
        if np.max(np.abs(x_new - x)) <= rtol * max(1.0, np.max(np.abs(x))):
            x = x_new
            break
        x = x_new
    return x


def _row_priority_factors(
    objective_keys: List[str],
    *,
    priority_groups: List[List[str]],
    priority_group_weights: List[float],
) -> np.ndarray:
    weights = np.ones(len(objective_keys), dtype=float)
    if not priority_groups:
        return weights
    for idx, key in enumerate(objective_keys):
        for group_idx, group in enumerate(priority_groups):
            if key in group:
                weights[idx] = max(1.0, float(priority_group_weights[group_idx]))
                break
    return weights


def _build_matrix(
    fertilizers: List[Fertilizer],
    mm: Dict[str, float],
    keys: List[str],
    liters: float,
) -> np.ndarray:
    matrix = np.zeros((len(keys), len(fertilizers)))
    for col, fert in enumerate(fertilizers):
        contrib = _fertilizer_element_contrib_per_g(fert, mm)
        for row, key in enumerate(keys):
            matrix[row, col] = contrib.get(key, 0.0) / liters
    return matrix


def _solve_weights(
    A: np.ndarray,
    b: np.ndarray,
    fixed: np.ndarray,
    variable_mask: np.ndarray,
    *,
    relative_weighting: bool = False,
    objective_keys: List[str] | None = None,
    targets_raw: Dict[str, float] | None = None,
    macro_priority_enabled: bool = True,
    priority_groups: List[List[str]] | None = None,
    priority_group_weights: List[float] | None = None,
    n_form_priority_weights: Dict[str, float] | None = None,
    n_total_governor_enabled: bool = False,
    n_total_governor_weight: float = 1.0,
    overshoot_penalty: float = 1.0,
    irls_max_outer_iter: int = 4,
    scale_eps_mg_per_l: float = 1.0,
) -> np.ndarray:
    if A.size == 0:
        return np.array([])
    if fixed.size:
        b = b - A @ fixed
    A_var = A[:, variable_mask]
    if A_var.size == 0:
        return np.zeros(int(variable_mask.sum()))
    if not relative_weighting:
        return _nnls(A_var, b)
    if objective_keys is None or targets_raw is None:
        raise ValueError("objective_keys and targets_raw are required when relative_weighting is enabled")
    scales = _build_row_scales(objective_keys, targets_raw, b, eps_mg_per_l=scale_eps_mg_per_l)
    priority_factors = None
    if macro_priority_enabled:
        priority_factors = _row_priority_factors(
            objective_keys,
            priority_groups=priority_groups or [],
            priority_group_weights=priority_group_weights or [],
        )
    base_priority = priority_factors
    if base_priority is None:
        base_priority = np.ones(len(objective_keys), dtype=float)
    if n_form_priority_weights:
        for idx, key in enumerate(objective_keys):
            if key in n_form_priority_weights:
                base_priority[idx] *= max(0.0, float(n_form_priority_weights[key]))
    n_total_priority = None
    for idx, key in enumerate(objective_keys):
        if key == "N_total":
            n_total_priority = base_priority[idx]
            break
    if n_total_priority is not None:
        for idx, key in enumerate(objective_keys):
            if key in ("N_NO3", "N_NH4", "N_UREA"):
                base_priority[idx] = min(base_priority[idx], n_total_priority)
    overshoot_only_weights = None
    if n_total_governor_enabled:
        overshoot_only_weights = np.zeros(len(objective_keys), dtype=float)
        for idx, key in enumerate(objective_keys):
            if key == "N_total":
                scale = max(scales[idx], 1e-12)
                overshoot_only_weights[idx] = (base_priority[idx] / scale) * max(
                    0.0, float(n_total_governor_weight)
                )
    return _nnls_weighted_irls(
        A_var,
        b,
        scales=scales,
        priority_factors=base_priority,
        overshoot_only_weights=overshoot_only_weights,
        overshoot_penalty=overshoot_penalty,
        max_outer_iter=irls_max_outer_iter,
        tol=1e-10,
        rtol=1e-6,
    )


def _max_abs_percent_error(
    objective_keys: List[str],
    targets_raw: Dict[str, float],
    achieved_elements: Dict[str, float],
) -> float:
    max_error = 0.0
    for key in objective_keys:
        target = float(targets_raw.get(key, 0.0))
        if target == 0:
            continue
        achieved_val = float(achieved_elements.get(key, 0.0))
        max_error = max(max_error, abs((achieved_val - target) / target * 100.0))
    return max_error


def _score_by_priority_groups(
    objective_keys: List[str],
    targets_raw: Dict[str, float],
    achieved_elements: Dict[str, float],
    *,
    priority_groups: List[List[str]],
) -> tuple[float, ...]:
    all_grouped_keys = {key for group in priority_groups for key in group}
    other_keys = [key for key in objective_keys if key not in all_grouped_keys]
    groups = list(priority_groups) + [other_keys]

    scores: list[float] = []
    for group in groups:
        max_error = 0.0
        for key in group:
            if key not in objective_keys:
                continue
            target = float(targets_raw.get(key, 0.0))
            if target == 0:
                continue
            achieved_val = float(achieved_elements.get(key, 0.0))
            max_error = max(max_error, abs((achieved_val - target) / target * 100.0))
        scores.append(max_error)
    return tuple(scores)


def _build_stage_groups(
    objective_keys: List[str],
    priority_groups: List[List[str]],
) -> List[List[str]]:
    if not priority_groups:
        return [list(objective_keys)]
    grouped_keys = {key for group in priority_groups for key in group}
    other_keys = [key for key in objective_keys if key not in grouped_keys]
    stage_groups: List[List[str]] = []
    for group in priority_groups:
        stage_group = [key for key in group if key in objective_keys]
        if stage_group:
            stage_groups.append(stage_group)
    if other_keys:
        stage_groups.append(other_keys)
    return stage_groups


def _stage_regression_budget_mg_l(
    target: float,
    *,
    stage_regression_pp: float,
    stage_regression_mg_l: float,
) -> float:
    budget_percent = abs(float(target)) * max(0.0, stage_regression_pp) / 100.0
    return max(budget_percent, max(0.0, stage_regression_mg_l))


def _apply_stage_regression_budget(
    prev_x: np.ndarray,
    prev_achieved: Dict[str, float],
    new_x: np.ndarray,
    new_achieved: Dict[str, float],
    prev_keys: List[str],
    targets_raw: Dict[str, float],
    *,
    stage_regression_pp: float,
    stage_regression_mg_l: float,
) -> tuple[np.ndarray, float]:
    if not prev_keys:
        return new_x, 1.0
    if stage_regression_pp <= 0 and stage_regression_mg_l <= 0:
        return new_x, 1.0
    t_max = 1.0
    for key in prev_keys:
        prev_val = float(prev_achieved.get(key, 0.0))
        new_val = float(new_achieved.get(key, 0.0))
        delta = new_val - prev_val
        if delta == 0:
            continue
        budget = _stage_regression_budget_mg_l(
            targets_raw.get(key, 0.0),
            stage_regression_pp=stage_regression_pp,
            stage_regression_mg_l=stage_regression_mg_l,
        )
        if budget <= 0:
            continue
        if abs(delta) > budget:
            t_max = min(t_max, budget / abs(delta))
    if t_max >= 1.0:
        return new_x, 1.0
    blended = prev_x + t_max * (new_x - prev_x)
    return blended, t_max


def _singleton_supplier_pass(
    *,
    A: np.ndarray,
    x_full: np.ndarray,
    variable_mask_full: np.ndarray,
    objective_keys: List[str],
    targets_raw: Dict[str, float],
    achieved_elements: Dict[str, float],
    liters: float,
    share_threshold: float,
    max_regress_pp: float,
    macro_regress_pp: float,
    priority_groups: List[List[str]],
    skip_keys: set[str] | None,
    recompute_achieved_fn: callable,
) -> np.ndarray:
    adjusted = x_full.copy()
    skip = skip_keys or set()
    for row, key in enumerate(objective_keys):
        if key in skip:
            continue
        contrib_row = A[row, :] * adjusted
        sum_row = float(np.sum(contrib_row))
        if sum_row <= 0:
            continue
        j_star = int(np.argmax(contrib_row))
        share = contrib_row[j_star] / sum_row
        if share < share_threshold:
            continue
        if not variable_mask_full[j_star]:
            continue
        if A[row, j_star] <= 0:
            continue
        overshoot_mg_l = float(achieved_elements.get(key, 0.0) - targets_raw.get(key, 0.0))
        if overshoot_mg_l <= 0:
            continue
        delta_g = overshoot_mg_l / A[row, j_star]
        if delta_g <= 0:
            continue
        proposed = adjusted.copy()
        proposed[j_star] = max(0.0, adjusted[j_star] - delta_g)
        achieved_new = recompute_achieved_fn(proposed)
        old_score = _score_by_priority_groups(
            objective_keys,
            targets_raw,
            achieved_elements,
            priority_groups=priority_groups,
        )
        new_score = _score_by_priority_groups(
            objective_keys,
            targets_raw,
            achieved_new,
            priority_groups=priority_groups,
        )
        if (
            achieved_new.get(key, 0.0) <= achieved_elements.get(key, 0.0)
            and new_score[0] <= old_score[0] + macro_regress_pp
            and new_score[-1] <= old_score[-1] + max_regress_pp
        ):
            adjusted = proposed
            achieved_elements = achieved_new
    return adjusted


def _resolve_water_profile(
    recipe: dict,
    water_profile_data: dict | None,
    water_profile_path: Path | None,
) -> dict:
    if water_profile_data is not None:
        return water_profile_data
    if water_profile_path is not None:
        return load_water_profile_data(water_profile_path)
    water_profile_value = recipe.get("water_profile")
    if isinstance(water_profile_value, dict):
        return water_profile_value
    if not water_profile_value:
        water_profile_value = "default"
    return load_water_profile_data(resolve_water_profile_path(str(water_profile_value)))


def solve_recipe_data(
    recipe: dict,
    *,
    ferts: Dict[str, Fertilizer] | None = None,
    mm: Dict[str, float] | None = None,
    water_profile_data: dict | None = None,
    water_profile_path: Path | None = None,
) -> SolveResult:
    fertilizers = ferts or load_fertilizers()
    molar_masses = mm or load_molar_masses()

    liters = float(recipe.get("liters") or 10.0)
    water_profile = _resolve_water_profile(recipe, water_profile_data, water_profile_path)
    osmosis_percent = float(recipe.get("osmosis_percent", water_profile.get("osmosis_percent", 0.0)))
    # compute_solution() applies osmosis_mix; do not pre-mix here.
    water_mg_l = water_profile.get("mg_per_l") or {}
    target_raw = _normalize_targets(
        recipe.get("targets")
        or recipe.get("targets_mg_per_l")
        or recipe.get("water_elements_mg_per_l")
        or {}
    )
    solver_config = recipe.get("solver_config") or {}
    relative_weighting = bool(solver_config.get("relative_weighting", True))
    overshoot_penalty = float(solver_config.get("overshoot_penalty", 1.0))
    irls_max_outer_iter = int(solver_config.get("irls_max_outer_iter", 4))
    scale_eps_mg_per_l = float(solver_config.get("scale_eps_mg_per_l", 1.0))
    singleton_supplier_enabled = bool(solver_config.get("singleton_supplier_enabled", True))
    singleton_share_threshold = float(solver_config.get("singleton_share_threshold", 0.85))
    singleton_max_regress_pp = float(solver_config.get("singleton_max_regress_pp", 0.25))
    macro_priority_enabled = bool(solver_config.get("macro_priority_enabled", True))
    macro_regress_pp = float(solver_config.get("macro_regress_pp", 0.25))
    stage_optimization_enabled = bool(solver_config.get("stage_optimization_enabled", True))
    stage_regression_pp = float(solver_config.get("stage_regression_pp", 5.0))
    stage_regression_mg_l = float(solver_config.get("stage_regression_mg_l", 5.0))
    n_total_governor_enabled = bool(solver_config.get("n_total_governor_enabled", False))
    n_total_governor_weight = float(solver_config.get("n_total_governor_weight", 1.0))
    n_form_priority_weights = solver_config.get("n_form_priority_weights") or {}
    default_priority_groups = [
        ["N_total"],
        ["N_NO3", "N_NH4", "N_UREA"],
        ["K"],
        ["P"],
        ["Ca"],
        ["Mg"],
    ]
    default_priority_group_weights = [3.5, 3.0, 2.5, 2.0, 1.5, 1.5]
    priority_groups_override = solver_config.get("priority_groups")
    priority_group_weights_override = solver_config.get("priority_group_weights")
    priority_groups = priority_groups_override or default_priority_groups
    if priority_group_weights_override is None:
        if priority_groups_override is None:
            priority_group_weights = default_priority_group_weights
        else:
            priority_group_weights = [1.0] * len(priority_groups)
    else:
        priority_group_weights = priority_group_weights_override
    if len(priority_groups) != len(priority_group_weights):
        raise ValueError("priority_groups and priority_group_weights must have the same length")
    if not macro_priority_enabled:
        priority_groups = []
    objective_keys = _objective_keys(target_raw, allow_n_total_with_forms=True)
    if not objective_keys:
        raise ValueError("No solvable targets defined (S/SO4/Na/Cl are ignored).")

    allowed_names = [str(name) for name in recipe.get("fertilizers_allowed", [])]
    if not allowed_names:
        raise ValueError("fertilizers_allowed must list at least one fertilizer")

    allowed = []
    for name in allowed_names:
        if name not in fertilizers:
            raise KeyError(f"Unbekannter Dünger in fertilizers_allowed: '{name}'")
        allowed.append(fertilizers[name])

    fixed_grams = {str(k): float(v) for k, v in (recipe.get("fixed_grams") or {}).items()}
    fixed_weights = np.array([fixed_grams.get(fert.name, 0.0) for fert in allowed], dtype=float)
    variable_mask = np.array([fert.name not in fixed_grams for fert in allowed], dtype=bool)

    water_only_recipe = {
        "liters": liters,
        "fertilizers": [],
        "urea_as_nh4": bool(recipe.get("urea_as_nh4", False)),
        "phosphate_species": recipe.get("phosphate_species", "H2PO4"),
    }
    water_only = compute_solution(
        water_only_recipe,
        fertilizers,
        molar_masses,
        water_mg_l,
        osmosis_percent=osmosis_percent,
    )
    water_elements = water_only.elements_mg_l

    b = np.array([target_raw.get(key, 0.0) - water_elements.get(key, 0.0) for key in objective_keys], dtype=float)
    A = _build_matrix(allowed, molar_masses, objective_keys, liters)

    def build_full_weights(solved: np.ndarray) -> np.ndarray:
        combined = fixed_weights.copy()
        var_idx_inner = 0
        for idx in range(len(allowed)):
            if variable_mask[idx]:
                if solved.size:
                    combined[idx] += float(solved[var_idx_inner])
                var_idx_inner += 1
        return combined

    def build_solution_for_weights(weights: np.ndarray) -> tuple[list[dict[str, float]], dict[str, float], dict]:
        ferts_out: list[dict[str, float]] = []
        for idx, fert in enumerate(allowed):
            grams = float(weights[idx])
            if grams > 0:
                ferts_out.append({"name": fert.name, "grams": grams})
        recipe_payload = {
            "liters": liters,
            "fertilizers": ferts_out,
            "urea_as_nh4": bool(recipe.get("urea_as_nh4", False)),
            "phosphate_species": recipe.get("phosphate_species", "H2PO4"),
        }
        achieved_solution = compute_solution(
            recipe_payload,
            fertilizers,
            molar_masses,
            water_mg_l,
            osmosis_percent=osmosis_percent,
        )
        return ferts_out, achieved_solution.elements_mg_l, recipe_payload

    key_to_index = {key: idx for idx, key in enumerate(objective_keys)}

    def solve_for_keys(stage_keys: List[str]) -> tuple[np.ndarray, list[dict[str, float]], dict[str, float], dict]:
        stage_indices = [key_to_index[key] for key in stage_keys]
        A_stage = A[stage_indices, :]
        b_stage = b[stage_indices]
        solve_weights = _solve_weights(
            A_stage,
            b_stage,
            fixed_weights,
            variable_mask,
            relative_weighting=relative_weighting,
            objective_keys=stage_keys,
            targets_raw=target_raw,
            macro_priority_enabled=macro_priority_enabled,
            priority_groups=priority_groups,
            priority_group_weights=priority_group_weights,
            n_form_priority_weights=n_form_priority_weights,
            n_total_governor_enabled=n_total_governor_enabled,
            n_total_governor_weight=n_total_governor_weight,
            overshoot_penalty=overshoot_penalty,
            irls_max_outer_iter=irls_max_outer_iter,
            scale_eps_mg_per_l=scale_eps_mg_per_l,
        )
        x_full_stage = build_full_weights(solve_weights)
        fertilizers_out, achieved_elements, full_recipe = build_solution_for_weights(x_full_stage)
        if relative_weighting and not (n_total_governor_enabled or n_form_priority_weights):
            solve_weights_unweighted = _solve_weights(A_stage, b_stage, fixed_weights, variable_mask)
            x_full_unweighted = build_full_weights(solve_weights_unweighted)
            ferts_unweighted, achieved_unweighted, recipe_unweighted = build_solution_for_weights(x_full_unweighted)
            weighted_score = _score_by_priority_groups(
                stage_keys,
                target_raw,
                achieved_elements,
                priority_groups=priority_groups,
            )
            unweighted_score = _score_by_priority_groups(
                stage_keys,
                target_raw,
                achieved_unweighted,
                priority_groups=priority_groups,
            )
            if unweighted_score < weighted_score:
                x_full_stage = x_full_unweighted
                fertilizers_out = ferts_unweighted
                achieved_elements = achieved_unweighted
                full_recipe = recipe_unweighted
        return x_full_stage, fertilizers_out, achieved_elements, full_recipe

    stage_groups = (
        _build_stage_groups(objective_keys, priority_groups) if stage_optimization_enabled else [objective_keys]
    )
    x_full = np.zeros_like(fixed_weights)
    fertilizers_out: list[dict[str, float]] = []
    achieved_elements: dict[str, float] = {}
    full_recipe: dict[str, float] = {}
    prev_x_full: np.ndarray | None = None
    prev_achieved: dict[str, float] | None = None
    prev_keys: List[str] = []

    for stage_idx, stage_group in enumerate(stage_groups):
        stage_key_set = {key for group in stage_groups[: stage_idx + 1] for key in group}
        stage_keys = [key for key in objective_keys if key in stage_key_set]
        if not stage_keys:
            continue
        x_full_candidate, ferts_candidate, achieved_candidate, recipe_candidate = solve_for_keys(stage_keys)
        if prev_x_full is not None and prev_achieved is not None:
            adjusted_x, blend_factor = _apply_stage_regression_budget(
                prev_x_full,
                prev_achieved,
                x_full_candidate,
                achieved_candidate,
                prev_keys,
                target_raw,
                stage_regression_pp=stage_regression_pp,
                stage_regression_mg_l=stage_regression_mg_l,
            )
            if blend_factor < 1.0:
                x_full_candidate = adjusted_x
                ferts_candidate, achieved_candidate, recipe_candidate = build_solution_for_weights(x_full_candidate)
        x_full = x_full_candidate
        fertilizers_out = ferts_candidate
        achieved_elements = achieved_candidate
        full_recipe = recipe_candidate
        prev_x_full = x_full_candidate
        prev_achieved = achieved_candidate
        prev_keys = stage_keys

    if singleton_supplier_enabled:
        singleton_skip_keys = {"N_total"} if n_total_governor_enabled else None

        def recompute_achieved_fn(new_x_full: np.ndarray) -> Dict[str, float]:
            updated_fertilizers = []
            for idx, fert in enumerate(allowed):
                grams = float(new_x_full[idx])
                if grams > 0:
                    updated_fertilizers.append({"name": fert.name, "grams": grams})
            updated_recipe = {
                "liters": liters,
                "fertilizers": updated_fertilizers,
                "urea_as_nh4": bool(recipe.get("urea_as_nh4", False)),
                "phosphate_species": recipe.get("phosphate_species", "H2PO4"),
            }
            updated_solution = compute_solution(
                updated_recipe,
                fertilizers,
                molar_masses,
                water_mg_l,
                osmosis_percent=osmosis_percent,
            )
            return updated_solution.elements_mg_l

        x_full_updated = _singleton_supplier_pass(
            A=A,
            x_full=x_full,
            variable_mask_full=variable_mask,
            objective_keys=objective_keys,
            targets_raw=target_raw,
            achieved_elements=achieved_elements,
            liters=liters,
            share_threshold=singleton_share_threshold,
            max_regress_pp=singleton_max_regress_pp,
            macro_regress_pp=macro_regress_pp,
            priority_groups=priority_groups,
            skip_keys=singleton_skip_keys,
            recompute_achieved_fn=recompute_achieved_fn,
        )
        if np.any(np.abs(x_full_updated - x_full) > 1e-12):
            x_full = x_full_updated
            fertilizers_out = []
            for idx, fert in enumerate(allowed):
                grams = float(x_full[idx])
                if grams > 0:
                    fertilizers_out.append({"name": fert.name, "grams": grams})
            full_recipe["fertilizers"] = fertilizers_out
            achieved = compute_solution(
                full_recipe,
                fertilizers,
                molar_masses,
                water_mg_l,
                osmosis_percent=osmosis_percent,
            )
            achieved_elements = achieved.elements_mg_l

    errors_mg_l = {}
    errors_percent = {}
    for key in objective_keys:
        target = target_raw.get(key, 0.0)
        achieved_val = achieved_elements.get(key, 0.0)
        errors_mg_l[key] = achieved_val - target
        errors_percent[key] = 0.0 if target == 0 else (achieved_val - target) / target * 100.0

    return SolveResult(
        liters=liters,
        fertilizers=fertilizers_out,
        objective_elements=objective_keys,
        targets_mg_l=target_raw,
        achieved_elements_mg_l=achieved_elements,
        errors_mg_l=errors_mg_l,
        errors_percent=errors_percent,
    )


def solve_recipe(recipe_path: Path, water_profile_path: Path | None = None) -> SolveResult:
    recipe = load_recipe(recipe_path)
    return solve_recipe_data(recipe, water_profile_path=water_profile_path)
