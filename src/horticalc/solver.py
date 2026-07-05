from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List

import numpy as np

from .chemistry import (
    ALLOWED_TARGET_KEYS,
    DEFAULT_PORTFOLIO_MACRO_KEYS,
    DEFAULT_PORTFOLIO_MICRO_KEYS,
    FERTILIZER_N_FORM_OUTPUT_KEYS,
    N_FORM_KEYS,
    OTHER_ELEMENT_FORMS,
    OXIDE_ELEMENT_FORMS,
)
from .core import (
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
from .paths import resolve_water_profile_name
from .solver_config import (
    NITROGEN_OBJECTIVE_MODES,
    SOLVER_CONFIG_DEFAULTS,
    resolve_solver_config,
)


ALWAYS_IGNORED_TARGETS = {"NA", "CL"}
S_TARGETS = {"S"}
DEFAULT_SOLVER_CONFIG = dict(SOLVER_CONFIG_DEFAULTS)


@dataclass
class SolveResult:
    liters: float
    fertilizers: List[Dict[str, float | str]]
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


def _bounded_nnls(
    A: np.ndarray,
    b: np.ndarray,
    upper_bounds: np.ndarray,
    *,
    tol: float = 1e-10,
    max_iter: int = 10000,
) -> np.ndarray:
    """Solve non-negative least squares with optional per-column upper bounds."""
    if A.size == 0:
        return np.zeros(A.shape[1])
    upper = np.asarray(upper_bounds, dtype=float)
    if upper.shape != (A.shape[1],):
        raise ValueError("upper_bounds must match the number of fertilizer columns")
    if np.any(np.isnan(upper)) or np.any(upper < 0.0):
        raise ValueError("upper_bounds must be non-negative")
    if np.all(np.isinf(upper)):
        return _nnls(A, b, tol=tol)

    unconstrained = _nnls(A, b, tol=tol)
    x = np.clip(unconstrained, 0.0, upper)
    spectral_norm = float(np.linalg.norm(A, ord=2))
    if spectral_norm <= tol:
        return np.zeros(A.shape[1])
    step = 1.0 / (spectral_norm * spectral_norm)
    y = x.copy()
    momentum = 1.0
    for _ in range(max_iter):
        gradient = A.T @ (A @ y - b)
        updated = np.clip(y - step * gradient, 0.0, upper)
        if np.max(np.abs(updated - x), initial=0.0) <= tol * max(
            1.0,
            np.max(np.abs(x), initial=0.0),
        ):
            x = updated
            break
        next_momentum = (1.0 + np.sqrt(1.0 + 4.0 * momentum * momentum)) / 2.0
        y = updated + ((momentum - 1.0) / next_momentum) * (updated - x)
        x = updated
        momentum = next_momentum
    return np.clip(x, 0.0, upper)


def _normalize_targets(targets: Dict[str, float]) -> Dict[str, float]:
    cleaned: Dict[str, float] = {}
    for key, value in (targets or {}).items():
        if key is None:
            continue
        key_text = str(key)
        if key_text not in ALLOWED_TARGET_KEYS:
            raise ValueError(f"Invalid target key: {key_text}")
        target_value = float(value)
        if not np.isfinite(target_value):
            raise ValueError(f"Invalid target value for {key_text}: {value!r}")
        cleaned[key_text] = target_value
    return cleaned


def _objective_keys(
    targets: Dict[str, float],
    *,
    nitrogen_objective_mode: str = "as_targets",
    s_objective_enabled: bool = False,
) -> List[str]:
    if nitrogen_objective_mode not in NITROGEN_OBJECTIVE_MODES:
        allowed = ", ".join(sorted(NITROGEN_OBJECTIVE_MODES))
        raise ValueError(f"Unknown nitrogen_objective_mode: {nitrogen_objective_mode!r}; expected one of {allowed}")
    keys = []
    for key, val in targets.items():
        include_zero_n_form = nitrogen_objective_mode == "n_forms_only" and key in N_FORM_KEYS
        if val == 0 and not include_zero_n_form:
            continue
        key_upper = key.upper()
        if key_upper in ALWAYS_IGNORED_TARGETS:
            continue
        if key_upper in S_TARGETS and not s_objective_enabled:
            continue
        keys.append(key)
    if nitrogen_objective_mode == "n_total_only":
        return [key for key in keys if key not in N_FORM_KEYS]
    if nitrogen_objective_mode == "n_forms_only":
        return [key for key in keys if key != "N_total"]
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
        n_form_key = FERTILIZER_N_FORM_OUTPUT_KEYS.get(form)
        if n_form_key is not None:
            add("N_total", mg_per_g)
            add(n_form_key, mg_per_g)
            continue
        if form in OXIDE_ELEMENT_FORMS:
            element, mg_el = _oxide_to_element(mg_per_g, mm, form)
            add(element, mg_el)
            continue
        if form in OTHER_ELEMENT_FORMS:
            element, mg_el = _form_to_element(mg_per_g, mm, form)
            add(element, mg_el)
            continue
        if form == "HCO3":
            add("HCO3", mg_per_g)
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
    upper_bounds: np.ndarray,
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
    x = _bounded_nnls(A_weighted, b_weighted, upper_bounds, tol=tol)
    for _ in range(max_outer_iter - 1):
        r = A @ x - b
        w = base_w * (1.0 + overshoot_penalty * (r > 0)) + overshoot_only * (r > 0)
        A_weighted = A * w[:, None]
        b_weighted = b * w
        x_new = _bounded_nnls(A_weighted, b_weighted, upper_bounds, tol=tol)
        if np.max(np.abs(x_new - x)) <= rtol * max(1.0, np.max(np.abs(x))):
            x = x_new
            break
        x = x_new
    return x


def _build_base_priority(
    objective_keys: List[str],
    *,
    n_form_priority_weights: Dict[str, float],
) -> np.ndarray:
    base_priority = np.ones(len(objective_keys), dtype=float)
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
    return base_priority


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
    n_form_priority_weights: Dict[str, float] | None = None,
    n_total_governor_enabled: bool = False,
    n_total_governor_weight: float = 1.0,
    overshoot_penalty: float = 1.0,
    irls_max_outer_iter: int = 4,
    scale_eps_mg_per_l: float = 1.0,
    upper_bounds: np.ndarray | None = None,
) -> np.ndarray:
    if A.size == 0:
        return np.array([])
    if fixed.size:
        b = b - A @ fixed
    A_var = A[:, variable_mask]
    if A_var.size == 0:
        return np.zeros(int(variable_mask.sum()))
    variable_upper_bounds = (
        np.full(A_var.shape[1], np.inf)
        if upper_bounds is None
        else np.asarray(upper_bounds, dtype=float)[variable_mask]
    )
    if not relative_weighting:
        return _bounded_nnls(A_var, b, variable_upper_bounds)
    if objective_keys is None or targets_raw is None:
        raise ValueError("objective_keys and targets_raw are required when relative_weighting is enabled")
    scales = _build_row_scales(objective_keys, targets_raw, b, eps_mg_per_l=scale_eps_mg_per_l)
    base_priority = _build_base_priority(
        objective_keys,
        n_form_priority_weights=n_form_priority_weights or {},
    )
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
        upper_bounds=variable_upper_bounds,
    )


def _score_percent_errors(
    objective_keys: List[str],
    targets_raw: Dict[str, float],
    achieved_elements: Dict[str, float],
) -> tuple[float, ...]:
    return (max(_objective_percent_errors(objective_keys, targets_raw, achieved_elements), default=0.0),)


def _objective_percent_errors(
    objective_keys: List[str],
    targets_raw: Dict[str, float],
    achieved_elements: Dict[str, float],
) -> tuple[float, ...]:
    errors: list[float] = []
    for key in objective_keys:
        target = float(targets_raw.get(key, 0.0))
        if target == 0:
            errors.append(0.0)
            continue
        achieved_val = float(achieved_elements.get(key, 0.0))
        errors.append(abs((achieved_val - target) / target * 100.0))
    return tuple(errors)


def _solver_config_value_matches_default(key: str, value: object) -> bool:
    if key not in DEFAULT_SOLVER_CONFIG:
        return False
    default_value = DEFAULT_SOLVER_CONFIG[key]
    if isinstance(default_value, bool):
        return bool(value) is default_value
    if isinstance(default_value, int) and not isinstance(default_value, bool):
        try:
            return int(value) == default_value
        except (TypeError, ValueError):
            return False
    if isinstance(default_value, float):
        try:
            return abs(float(value) - default_value) <= 1e-12
        except (TypeError, ValueError):
            return False
    return str(value) == str(default_value)


def _uses_default_solver_portfolio(solver_config: Dict[str, object]) -> bool:
    if not solver_config:
        return True
    for key, value in solver_config.items():
        if not _solver_config_value_matches_default(str(key), value):
            return False
    return True


def _percent_errors(
    keys: list[str],
    targets_raw: Dict[str, float],
    achieved_elements: Dict[str, float],
) -> list[float]:
    errors: list[float] = []
    for key in keys:
        target_value = float(targets_raw.get(key, 0.0))
        if target_value == 0.0:
            continue
        achieved_value = float(achieved_elements.get(key, 0.0))
        errors.append((achieved_value - target_value) / target_value * 100.0)
    return errors


def _rms_percent_error(
    keys: list[str],
    targets_raw: Dict[str, float],
    achieved_elements: Dict[str, float],
) -> float:
    errors = _percent_errors(keys, targets_raw, achieved_elements)
    if not errors:
        return 0.0
    squared_errors = [error**2 for error in errors]
    return float(np.sqrt(sum(squared_errors) / len(squared_errors)))


def _max_percent_error(
    keys: list[str],
    targets_raw: Dict[str, float],
    achieved_elements: Dict[str, float],
) -> float:
    return max((abs(error) for error in _percent_errors(keys, targets_raw, achieved_elements)), default=0.0)


def _default_portfolio_score(
    objective_keys: List[str],
    targets_raw: Dict[str, float],
    achieved_elements: Dict[str, float],
) -> tuple[float, ...]:
    objective_key_set = set(objective_keys)
    n_total_error = _max_percent_error(["N_total"], targets_raw, achieved_elements)
    macro_keys = [key for key in DEFAULT_PORTFOLIO_MACRO_KEYS if key in objective_key_set]
    micro_keys = [key for key in DEFAULT_PORTFOLIO_MICRO_KEYS if key in objective_key_set]
    other_keys = [
        key
        for key in objective_keys
        if key not in {"N_total", *DEFAULT_PORTFOLIO_MACRO_KEYS, *DEFAULT_PORTFOLIO_MICRO_KEYS, *N_FORM_KEYS}
    ]
    return (
        n_total_error,
        _max_percent_error(macro_keys, targets_raw, achieved_elements),
        _rms_percent_error(macro_keys, targets_raw, achieved_elements),
        _rms_percent_error(micro_keys, targets_raw, achieved_elements),
        _max_percent_error(micro_keys, targets_raw, achieved_elements),
        _rms_percent_error(other_keys, targets_raw, achieved_elements),
    )


def _singleton_supplier_pass(
    *,
    A: np.ndarray,
    x_full: np.ndarray,
    variable_mask_full: np.ndarray,
    objective_keys: List[str],
    targets_raw: Dict[str, float],
    achieved_elements: Dict[str, float],
    share_threshold: float,
    max_regress_pp: float,
    skip_keys: set[str] | None,
    recompute_achieved_fn: Callable[[np.ndarray], Dict[str, float]],
    mode: str = "overshoot",
    use_potential_share: bool = False,
    upper_bounds_full: np.ndarray | None = None,
) -> tuple[np.ndarray, Dict[str, float]]:
    adjusted = x_full.copy()
    skip = skip_keys or set()
    for row, key in enumerate(objective_keys):
        if key in skip:
            continue
        contrib_row = A[row, :] * adjusted
        sum_row = float(np.sum(contrib_row))
        potential_row = np.clip(A[row, :], 0.0, None)
        sum_potential = float(np.sum(potential_row))
        if sum_potential <= 0:
            continue
        if use_potential_share or sum_row <= 0:
            base_row = potential_row
            share_denominator = sum_potential
        else:
            base_row = contrib_row
            share_denominator = sum_row
        j_star = int(np.argmax(base_row))
        share = base_row[j_star] / share_denominator if share_denominator > 0 else 0.0
        if share < share_threshold:
            continue
        if not variable_mask_full[j_star]:
            continue
        if A[row, j_star] <= 0:
            continue
        target_value = float(targets_raw.get(key, 0.0))
        achieved_value = float(achieved_elements.get(key, 0.0))
        delta_mg_l = achieved_value - target_value
        if mode == "overshoot":
            if delta_mg_l <= 0:
                continue
            delta_g = delta_mg_l / A[row, j_star]
            if delta_g <= 0:
                continue
            proposed = adjusted.copy()
            proposed[j_star] = max(0.0, adjusted[j_star] - delta_g)
        elif mode == "underfill":
            if delta_mg_l >= 0:
                continue
            delta_g = (-delta_mg_l) / A[row, j_star]
            if delta_g <= 0:
                continue
            proposed = adjusted.copy()
            proposed[j_star] = adjusted[j_star] + delta_g
            if upper_bounds_full is not None:
                proposed[j_star] = min(proposed[j_star], upper_bounds_full[j_star])
        else:
            raise ValueError(f"Unknown singleton supplier mode: {mode}")
        achieved_new = recompute_achieved_fn(proposed)
        score_fn = _objective_percent_errors if mode == "overshoot" else _score_percent_errors
        old_score = score_fn(objective_keys, targets_raw, achieved_elements)
        new_score = score_fn(objective_keys, targets_raw, achieved_new)
        improves = (mode == "overshoot" and achieved_new.get(key, 0.0) <= achieved_elements.get(key, 0.0)) or (
            mode == "underfill" and achieved_new.get(key, 0.0) >= achieved_elements.get(key, 0.0)
        )
        regression_ok = all(new_val <= old_val + max_regress_pp for new_val, old_val in zip(new_score, old_score))
        if improves and regression_ok:
            adjusted = proposed
            achieved_elements = achieved_new
    return adjusted, achieved_elements


def _build_solution_payload(
    *,
    weights: np.ndarray,
    allowed: List[Fertilizer],
    liters: float,
    recipe: dict,
) -> tuple[list[dict[str, float | str]], dict]:
    ferts_out: list[dict[str, float | str]] = []
    for idx, fert in enumerate(allowed):
        grams = float(weights[idx])
        if grams > 0:
            ferts_out.append({"name": fert.name, "grams": grams})
    recipe_payload = {
        "liters": liters,
        "fertilizers": ferts_out,
        "urea_as_nh4": bool(recipe.get("urea_as_nh4", False)),
    }
    return ferts_out, recipe_payload


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
    return load_water_profile_data(resolve_water_profile_name(str(water_profile_value)))


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

    liters_value = recipe.get("liters", 10.0)
    if liters_value is None:
        liters_value = 10.0
    liters = float(liters_value)
    if not np.isfinite(liters) or liters <= 0.0:
        raise ValueError("liters must be > 0")
    water_profile = _resolve_water_profile(recipe, water_profile_data, water_profile_path)
    osmosis_percent = float(recipe.get("osmosis_percent", water_profile.get("osmosis_percent", 0.0)))
    # compute_solution() applies osmosis_mix; do not pre-mix here.
    water_mg_l = water_profile.get("mg_per_l") or {}
    target_raw = _normalize_targets(
        recipe.get("targets")
        or recipe.get("targets_mg_per_l")
        or {}
    )
    solver_config = resolve_solver_config(recipe.get("solver_config"))
    relative_weighting = solver_config["relative_weighting"]
    overshoot_penalty = solver_config["overshoot_penalty"]
    irls_max_outer_iter = solver_config["irls_max_outer_iter"]
    scale_eps_mg_per_l = solver_config["scale_eps_mg_per_l"]
    singleton_supplier_enabled = solver_config["singleton_supplier_enabled"]
    singleton_share_threshold = solver_config["singleton_share_threshold"]
    singleton_max_regress_pp = solver_config["singleton_max_regress_pp"]
    singleton_underfill_enabled = solver_config["singleton_underfill_enabled"]
    singleton_underfill_share_threshold = solver_config["singleton_underfill_share_threshold"]
    singleton_underfill_max_iter = solver_config["singleton_underfill_max_iter"]
    nitrogen_objective_mode = solver_config["nitrogen_objective_mode"]
    s_objective_enabled = solver_config["s_objective_enabled"]
    n_total_governor_enabled = solver_config["n_total_governor_enabled"]
    n_total_governor_weight = solver_config["n_total_governor_weight"]
    n_form_priority_weights = solver_config["n_form_priority_weights"]
    objective_keys = _objective_keys(
        target_raw,
        nitrogen_objective_mode=nitrogen_objective_mode,
        s_objective_enabled=s_objective_enabled,
    )
    if not objective_keys:
        raise ValueError("No solvable targets defined (Na/Cl are ignored; S requires s_objective_enabled).")

    allowed_names = [str(name) for name in recipe.get("fertilizers_allowed", [])]
    if not allowed_names:
        raise ValueError("fertilizers_allowed must list at least one fertilizer")

    allowed = []
    for name in allowed_names:
        if name not in fertilizers:
            raise KeyError(f"Unknown fertilizer in fertilizers_allowed: '{name}'")
        allowed.append(fertilizers[name])

    fixed_grams: dict[str, float] = {}
    for key, value in (recipe.get("fixed_grams") or {}).items():
        name = str(key)
        grams = float(value)
        if not np.isfinite(grams):
            raise ValueError(f"fixed_grams must be finite: {name}")
        if grams < 0:
            raise ValueError(f"fixed_grams must be >= 0: {name}")
        fixed_grams[name] = grams
    unknown_fixed = sorted(set(fixed_grams) - {fert.name for fert in allowed})
    if unknown_fixed:
        raise ValueError(f"fixed_grams not in fertilizers_allowed: {unknown_fixed}")
    fixed_weights = np.array([fixed_grams.get(fert.name, 0.0) for fert in allowed], dtype=float)
    variable_mask = np.array([fert.name not in fixed_grams for fert in allowed], dtype=bool)
    solver_upper_bounds = np.array([
        np.inf
        if fert.name in fixed_grams or fert.solver_max_dose_per_l is None
        else fert.solver_max_dose_per_l * liters
        for fert in allowed
    ], dtype=float)

    water_only_recipe = {
        "liters": liters,
        "fertilizers": [],
        "urea_as_nh4": bool(recipe.get("urea_as_nh4", False)),
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

    def build_solution_for_weights(
        weights: np.ndarray,
    ) -> tuple[list[dict[str, float | str]], dict[str, float]]:
        ferts_out, recipe_payload = _build_solution_payload(
            weights=weights,
            allowed=allowed,
            liters=liters,
            recipe=recipe,
        )
        achieved_solution = compute_solution(
            recipe_payload,
            fertilizers,
            molar_masses,
            water_mg_l,
            osmosis_percent=osmosis_percent,
        )
        return ferts_out, achieved_solution.elements_mg_l

    solved_variants: dict[
        tuple[bool, bool, bool],
        tuple[list[dict[str, float | str]], dict[str, float]],
    ] = {}

    def solve_once(
        *,
        use_relative_weighting: bool,
        singleton_supplier_enabled_local: bool,
        singleton_underfill_enabled_local: bool,
    ) -> tuple[list[dict[str, float | str]], dict[str, float]]:
        variant_key = (
            use_relative_weighting,
            singleton_supplier_enabled_local,
            singleton_underfill_enabled_local,
        )
        if variant_key in solved_variants:
            return solved_variants[variant_key]

        solved_weights = _solve_weights(
            A,
            b,
            fixed_weights,
            variable_mask,
            relative_weighting=use_relative_weighting,
            objective_keys=objective_keys,
            targets_raw=target_raw,
            n_form_priority_weights=n_form_priority_weights,
            n_total_governor_enabled=n_total_governor_enabled,
            n_total_governor_weight=n_total_governor_weight,
            overshoot_penalty=overshoot_penalty,
            irls_max_outer_iter=irls_max_outer_iter,
            scale_eps_mg_per_l=scale_eps_mg_per_l,
            upper_bounds=solver_upper_bounds,
        )
        x_full_local = fixed_weights.copy()
        x_full_local[variable_mask] += solved_weights
        latest_fertilizers, achieved_elements_local = build_solution_for_weights(x_full_local)

        singleton_skip_keys = {"N_total"} if n_total_governor_enabled else None

        def recompute_achieved_fn(new_x_full: np.ndarray) -> Dict[str, float]:
            return build_solution_for_weights(new_x_full)[1]

        def apply_singleton_pass(
            *,
            mode: str,
            share_threshold: float,
            use_potential_share: bool,
        ) -> bool:
            nonlocal x_full_local, latest_fertilizers, achieved_elements_local
            x_full_updated, achieved_elements_updated = _singleton_supplier_pass(
                A=A,
                x_full=x_full_local,
                variable_mask_full=variable_mask,
                objective_keys=objective_keys,
                targets_raw=target_raw,
                achieved_elements=achieved_elements_local,
                share_threshold=share_threshold,
                max_regress_pp=singleton_max_regress_pp,
                skip_keys=singleton_skip_keys,
                recompute_achieved_fn=recompute_achieved_fn,
                mode=mode,
                use_potential_share=use_potential_share,
                upper_bounds_full=solver_upper_bounds,
            )
            if not np.any(np.abs(x_full_updated - x_full_local) > 1e-12):
                return False
            x_full_local = x_full_updated
            latest_fertilizers, _ = _build_solution_payload(
                weights=x_full_local,
                allowed=allowed,
                liters=liters,
                recipe=recipe,
            )
            achieved_elements_local = achieved_elements_updated
            return True

        if singleton_supplier_enabled_local:
            apply_singleton_pass(
                mode="overshoot",
                share_threshold=singleton_share_threshold,
                use_potential_share=False,
            )

        if singleton_underfill_enabled_local:
            for _ in range(max(1, singleton_underfill_max_iter)):
                if not apply_singleton_pass(
                    mode="underfill",
                    share_threshold=singleton_underfill_share_threshold,
                    use_potential_share=True,
                ):
                    break

        result = latest_fertilizers, achieved_elements_local
        solved_variants[variant_key] = result
        return result

    def solve_variant(
        *,
        use_relative_weighting: bool,
        singleton_supplier_enabled_local: bool,
        singleton_underfill_enabled_local: bool,
    ) -> tuple[list[dict[str, float | str]], dict[str, float]]:
        fertilizers_local, achieved_local = solve_once(
            use_relative_weighting=use_relative_weighting,
            singleton_supplier_enabled_local=singleton_supplier_enabled_local,
            singleton_underfill_enabled_local=singleton_underfill_enabled_local,
        )
        if use_relative_weighting and not (n_total_governor_enabled or n_form_priority_weights):
            ferts_unweighted, achieved_unweighted = solve_once(
                use_relative_weighting=False,
                singleton_supplier_enabled_local=singleton_supplier_enabled_local,
                singleton_underfill_enabled_local=singleton_underfill_enabled_local,
            )
            weighted_score = _score_percent_errors(
                objective_keys,
                target_raw,
                achieved_local,
            )
            unweighted_score = _score_percent_errors(
                objective_keys,
                target_raw,
                achieved_unweighted,
            )
            if unweighted_score < weighted_score:
                return ferts_unweighted, achieved_unweighted
        return fertilizers_local, achieved_local

    current_variant = (
        relative_weighting,
        singleton_supplier_enabled,
        singleton_underfill_enabled,
    )
    fertilizers_out, achieved_elements = solve_variant(
        use_relative_weighting=relative_weighting,
        singleton_supplier_enabled_local=singleton_supplier_enabled,
        singleton_underfill_enabled_local=singleton_underfill_enabled,
    )
    if nitrogen_objective_mode == "n_total_only" and _uses_default_solver_portfolio(solver_config):
        default_variants = [
            (relative_weighting, singleton_supplier_enabled, singleton_underfill_enabled),
            (True, False, singleton_underfill_enabled),
            (False, singleton_supplier_enabled, singleton_underfill_enabled),
            (False, False, singleton_underfill_enabled),
        ]
        best_variant = (fertilizers_out, achieved_elements)
        best_score = _default_portfolio_score(objective_keys, target_raw, achieved_elements)
        seen_variants = {current_variant}
        for candidate in default_variants:
            if candidate in seen_variants:
                continue
            seen_variants.add(candidate)
            candidate_result = solve_variant(
                use_relative_weighting=candidate[0],
                singleton_supplier_enabled_local=candidate[1],
                singleton_underfill_enabled_local=candidate[2],
            )
            candidate_score = _default_portfolio_score(
                objective_keys,
                target_raw,
                candidate_result[1],
            )
            if candidate_score < best_score:
                best_variant = candidate_result
                best_score = candidate_score
        fertilizers_out, achieved_elements = best_variant

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


def solve_recipe(
    recipe_path: Path,
    water_profile_path: Path | None = None,
    solver_config_overrides: dict | None = None,
) -> SolveResult:
    recipe = load_recipe(recipe_path)
    if solver_config_overrides:
        recipe = dict(recipe)
        solver_config = dict(recipe.get("solver_config") or {})
        solver_config.update(solver_config_overrides)
        recipe["solver_config"] = solver_config
    return solve_recipe_data(recipe, water_profile_path=water_profile_path)
