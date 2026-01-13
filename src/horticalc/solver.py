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


IGNORED_TARGETS = {"S", "SO4"}


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

    def add(key: str, value: float) -> None:
        if value == 0:
            return
        elements[key] = elements.get(key, 0.0) + value

    for form, frac in fert.comp.items():
        mg_per_g = float(frac) * 1000.0
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
) -> np.ndarray:
    if A.size == 0:
        return np.array([])
    if fixed.size:
        b = b - A @ fixed
    b = np.maximum(b, 0.0)
    A_var = A[:, variable_mask]
    if A_var.size == 0:
        return np.zeros(int(variable_mask.sum()))
    return _nnls(A_var, b)


def _load_solver_recipe(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def solve_recipe(recipe_path: Path) -> SolveResult:
    recipe = _load_solver_recipe(recipe_path)
    ferts = load_fertilizers()
    mm = load_molar_masses()

    liters = float(recipe.get("liters") or 10.0)
    wp_name = str(recipe.get("water_profile") or "default")
    wp_path = repo_root() / "data" / "water_profiles" / f"{wp_name}.yml"
    water_profile = load_water_profile_data(wp_path)
    osmosis_percent = float(recipe.get("osmosis_percent", water_profile.get("osmosis_percent", 0.0)))
    water_mg_l = apply_osmosis_mix(water_profile.get("mg_per_l") or {}, osmosis_percent)
    target_raw = _normalize_targets(recipe.get("targets_mg_per_l") or {})
    objective_keys = _objective_keys(target_raw)
    if not objective_keys:
        raise ValueError("No solvable targets defined (S/SO4 are ignored).")

    allowed_names = [str(name) for name in recipe.get("fertilizers_allowed", [])]
    if not allowed_names:
        raise ValueError("fertilizers_allowed must list at least one fertilizer")

    allowed = []
    for name in allowed_names:
        if name not in ferts:
            raise KeyError(f"Unbekannter Dünger in fertilizers_allowed: '{name}'")
        allowed.append(ferts[name])

    fixed_grams = {str(k): float(v) for k, v in (recipe.get("fixed_grams") or {}).items()}
    fixed_weights = np.array([fixed_grams.get(fert.name, 0.0) for fert in allowed], dtype=float)
    variable_mask = np.array([fert.name not in fixed_grams for fert in allowed], dtype=bool)

    water_only_recipe = {
        "liters": liters,
        "fertilizers": [],
        "urea_as_nh4": bool(recipe.get("urea_as_nh4", False)),
        "phosphate_species": recipe.get("phosphate_species", "H2PO4"),
    }
    water_only = compute_solution(water_only_recipe, ferts, mm, water_mg_l, osmosis_percent=osmosis_percent)
    water_elements = water_only.elements_mg_l

    b = np.array([target_raw.get(key, 0.0) - water_elements.get(key, 0.0) for key in objective_keys], dtype=float)
    A = _build_matrix(allowed, mm, objective_keys, liters)
    solve_weights = _solve_weights(A, b, fixed_weights, variable_mask)

    fertilizers_out = []
    var_idx = 0
    for idx, fert in enumerate(allowed):
        solved = float(solve_weights[var_idx]) if (solve_weights.size and variable_mask[idx]) else 0.0
        if variable_mask[idx]:
            var_idx += 1
        total = solved + fixed_grams.get(fert.name, 0.0)
        if total > 0:
            fertilizers_out.append({"name": fert.name, "grams": total})

    full_recipe = {
        "liters": liters,
        "fertilizers": fertilizers_out,
        "urea_as_nh4": bool(recipe.get("urea_as_nh4", False)),
        "phosphate_species": recipe.get("phosphate_species", "H2PO4"),
    }
    achieved = compute_solution(full_recipe, ferts, mm, water_mg_l, osmosis_percent=osmosis_percent)
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
