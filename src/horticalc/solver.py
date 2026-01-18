from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
import yaml

from .core import (
    OTHER_ELEMENT_FORMS,
    OXIDE_ELEMENT_FORMS,
    _form_to_element,
    _oxide_to_element,
    apply_osmosis_mix,
    compute_solution,
)
from .data_io import Fertilizer, load_fertilizers, load_molar_masses, load_water_profile_data, repo_root


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


def _objective_keys(targets: Dict[str, float]) -> List[str]:
    keys = []
    for key, val in targets.items():
        if val == 0:
            continue
        if key.upper() in IGNORED_TARGETS:
            continue
        keys.append(key)
    if "N_total" in keys and any(k in keys for k in ("N_NH4", "N_NO3", "N_UREA")):
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
        if form in ("NH4", "NO3", "Ur-N"):
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
    overshoot_penalty: float,
    max_outer_iter: int,
    tol: float,
    rtol: float,
) -> np.ndarray:
    if A.size == 0:
        return np.array([])
    base_w = 1.0 / np.maximum(scales, tol)
    A_weighted = A * base_w[:, None]
    b_weighted = b * base_w
    x = _nnls(A_weighted, b_weighted, tol=tol)
    for _ in range(max_outer_iter - 1):
        r = A @ x - b
        w = base_w * (1.0 + overshoot_penalty * (r > 0))
        A_weighted = A * w[:, None]
        b_weighted = b * w
        x_new = _nnls(A_weighted, b_weighted, tol=tol)
        if np.max(np.abs(x_new - x)) <= rtol * max(1.0, np.max(np.abs(x))):
            x = x_new
            break
        x = x_new
    return x


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
    overshoot_penalty: float = 1.0,
    irls_max_outer_iter: int = 4,
    scale_eps_mg_per_l: float = 1.0,
) -> np.ndarray:
    if A.size == 0:
        return np.array([])
    if fixed.size:
        b = b - A @ fixed
    b = np.maximum(b, 0.0)
    A_var = A[:, variable_mask]
    if A_var.size == 0:
        return np.zeros(int(variable_mask.sum()))
    if not relative_weighting:
        return _nnls(A_var, b)
    if objective_keys is None or targets_raw is None:
        raise ValueError("objective_keys and targets_raw are required when relative_weighting is enabled")
    scales = _build_row_scales(objective_keys, targets_raw, b, eps_mg_per_l=scale_eps_mg_per_l)
    return _nnls_weighted_irls(
        A_var,
        b,
        scales=scales,
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
    recompute_achieved_fn: callable,
) -> np.ndarray:
    adjusted = x_full.copy()
    for row, key in enumerate(objective_keys):
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
        old_max = _max_abs_percent_error(objective_keys, targets_raw, achieved_elements)
        new_max = _max_abs_percent_error(objective_keys, targets_raw, achieved_new)
        if achieved_new.get(key, 0.0) <= achieved_elements.get(key, 0.0) and new_max <= old_max + max_regress_pp:
            adjusted = proposed
            achieved_elements = achieved_new
    return adjusted


def _load_solver_recipe(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def _resolve_water_profile(recipe: dict, water_profile_data: dict | None) -> dict:
    if water_profile_data is not None:
        return water_profile_data
    water_profile_value = recipe.get("water_profile")
    if isinstance(water_profile_value, dict):
        return water_profile_value
    if not water_profile_value:
        water_profile_value = "default"
    wp_path = repo_root() / "data" / "water_profiles" / f"{water_profile_value}.yml"
    return load_water_profile_data(wp_path)


def solve_recipe_data(
    recipe: dict,
    *,
    ferts: Dict[str, Fertilizer] | None = None,
    mm: Dict[str, float] | None = None,
    water_profile_data: dict | None = None,
) -> SolveResult:
    fertilizers = ferts or load_fertilizers()
    molar_masses = mm or load_molar_masses()

    liters = float(recipe.get("liters") or 10.0)
    water_profile = _resolve_water_profile(recipe, water_profile_data)
    osmosis_percent = float(recipe.get("osmosis_percent", water_profile.get("osmosis_percent", 0.0)))
    water_mg_l = apply_osmosis_mix(water_profile.get("mg_per_l") or {}, osmosis_percent)
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
    objective_keys = _objective_keys(target_raw)
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
    solve_weights = _solve_weights(
        A,
        b,
        fixed_weights,
        variable_mask,
        relative_weighting=relative_weighting,
        objective_keys=objective_keys,
        targets_raw=target_raw,
        overshoot_penalty=overshoot_penalty,
        irls_max_outer_iter=irls_max_outer_iter,
        scale_eps_mg_per_l=scale_eps_mg_per_l,
    )

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

    x_full = build_full_weights(solve_weights)
    fertilizers_out, achieved_elements, full_recipe = build_solution_for_weights(x_full)
    if relative_weighting:
        solve_weights_unweighted = _solve_weights(A, b, fixed_weights, variable_mask)
        x_full_unweighted = build_full_weights(solve_weights_unweighted)
        ferts_unweighted, achieved_unweighted, recipe_unweighted = build_solution_for_weights(x_full_unweighted)
        weighted_error = _max_abs_percent_error(objective_keys, target_raw, achieved_elements)
        unweighted_error = _max_abs_percent_error(objective_keys, target_raw, achieved_unweighted)
        if unweighted_error < weighted_error:
            x_full = x_full_unweighted
            fertilizers_out = ferts_unweighted
            achieved_elements = achieved_unweighted
            full_recipe = recipe_unweighted

    if singleton_supplier_enabled:

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


def solve_recipe(recipe_path: Path) -> SolveResult:
    recipe = _load_solver_recipe(recipe_path)
    return solve_recipe_data(recipe)
