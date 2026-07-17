from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List

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
from .validation import non_negative_float, percentage_float, positive_float, unique_strings

ALWAYS_IGNORED_TARGETS = {"NA", "CL"}
S_TARGETS = {"S"}
DEFAULT_SOLVER_CONFIG = dict(SOLVER_CONFIG_DEFAULTS)


@dataclass
class SolveResult:
    liters: float
    solver_model: str
    fertilizers: List[Dict[str, float | str]]
    objective_elements: List[str]
    targets_mg_l: Dict[str, float]
    achieved_elements_mg_l: Dict[str, float]
    errors_mg_l: Dict[str, float]
    errors_percent: Dict[str, float]

    def to_dict(self) -> dict:
        return {
            "liters": self.liters,
            "solver_model": self.solver_model,
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
        target_value = non_negative_float(value, f"target {key_text}")
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
                overshoot_only_weights[idx] = (base_priority[idx] / scale) * max(0.0, float(n_total_governor_weight))
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


def _signed_percent_error(target: float, achieved: float) -> float:
    return 0.0 if target == 0.0 else (achieved - target) / target * 100.0


def _objective_percent_errors(
    objective_keys: List[str],
    targets_raw: Dict[str, float],
    achieved_elements: Dict[str, float],
) -> tuple[float, ...]:
    errors: list[float] = []
    for key in objective_keys:
        target = float(targets_raw.get(key, 0.0))
        achieved_val = float(achieved_elements.get(key, 0.0))
        errors.append(abs(_signed_percent_error(target, achieved_val)))
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
    return all(_solver_config_value_matches_default(str(key), value) for key, value in solver_config.items())


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
        errors.append(_signed_percent_error(target_value, achieved_value))
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
        regression_ok = all(
            new_val <= old_val + max_regress_pp for new_val, old_val in zip(new_score, old_score, strict=True)
        )
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


@dataclass
class _PreparedProblem:
    recipe: dict
    fertilizers: Dict[str, Fertilizer]
    molar_masses: Dict[str, float]
    liters: float
    water_mg_l: Dict[str, float]
    osmosis_percent: float
    targets: Dict[str, float]
    objective_keys: List[str]
    allowed: List[Fertilizer]
    fixed_weights: np.ndarray
    variable_mask: np.ndarray
    upper_bounds: np.ndarray
    matrix: np.ndarray
    remaining_targets: np.ndarray
    solver_config: dict[str, Any]


_Variant = tuple[bool, bool, bool]
_VariantResult = tuple[list[dict[str, float | str]], dict[str, float]]


class _VariantRunner:
    def __init__(self, problem: _PreparedProblem) -> None:
        self.problem = problem
        self._solved_variants: dict[_Variant, _VariantResult] = {}

    def _build_solution_for_weights(self, weights: np.ndarray) -> _VariantResult:
        problem = self.problem
        fertilizers_out, recipe_payload = _build_solution_payload(
            weights=weights,
            allowed=problem.allowed,
            liters=problem.liters,
            recipe=problem.recipe,
        )
        achieved_solution = compute_solution(
            recipe_payload,
            problem.fertilizers,
            problem.molar_masses,
            problem.water_mg_l,
            osmosis_percent=problem.osmosis_percent,
        )
        return fertilizers_out, achieved_solution.elements_mg_l

    def _achieved_for_weights(self, weights: np.ndarray) -> Dict[str, float]:
        return self._build_solution_for_weights(weights)[1]

    def _apply_singleton_pass(
        self,
        weights: np.ndarray,
        achieved_elements: Dict[str, float],
        *,
        mode: str,
        share_threshold: float,
        use_potential_share: bool,
    ) -> tuple[np.ndarray, Dict[str, float], bool]:
        problem = self.problem
        skip_keys = {"N_total"} if problem.solver_config["n_total_governor_enabled"] else None
        updated_weights, updated_elements = _singleton_supplier_pass(
            A=problem.matrix,
            x_full=weights,
            variable_mask_full=problem.variable_mask,
            objective_keys=problem.objective_keys,
            targets_raw=problem.targets,
            achieved_elements=achieved_elements,
            share_threshold=share_threshold,
            max_regress_pp=problem.solver_config["singleton_max_regress_pp"],
            skip_keys=skip_keys,
            recompute_achieved_fn=self._achieved_for_weights,
            mode=mode,
            use_potential_share=use_potential_share,
            upper_bounds_full=problem.upper_bounds,
        )
        changed = bool(np.any(np.abs(updated_weights - weights) > 1e-12))
        return updated_weights, updated_elements, changed

    def _solve_once(self, variant: _Variant) -> _VariantResult:
        cached = self._solved_variants.get(variant)
        if cached is not None:
            return cached

        use_relative_weighting, supplier_enabled, underfill_enabled = variant
        problem = self.problem
        config = problem.solver_config
        solved_weights = _solve_weights(
            problem.matrix,
            problem.remaining_targets,
            problem.fixed_weights,
            problem.variable_mask,
            relative_weighting=use_relative_weighting,
            objective_keys=problem.objective_keys,
            targets_raw=problem.targets,
            n_form_priority_weights=config["n_form_priority_weights"],
            n_total_governor_enabled=config["n_total_governor_enabled"],
            n_total_governor_weight=config["n_total_governor_weight"],
            overshoot_penalty=config["overshoot_penalty"],
            irls_max_outer_iter=config["irls_max_outer_iter"],
            scale_eps_mg_per_l=config["scale_eps_mg_per_l"],
            upper_bounds=problem.upper_bounds,
        )
        weights = problem.fixed_weights.copy()
        weights[problem.variable_mask] += solved_weights
        achieved_elements = self._achieved_for_weights(weights)

        if supplier_enabled:
            weights, achieved_elements, _ = self._apply_singleton_pass(
                weights,
                achieved_elements,
                mode="overshoot",
                share_threshold=config["singleton_share_threshold"],
                use_potential_share=False,
            )

        if underfill_enabled:
            for _ in range(config["singleton_underfill_max_iter"]):
                weights, achieved_elements, changed = self._apply_singleton_pass(
                    weights,
                    achieved_elements,
                    mode="underfill",
                    share_threshold=config["singleton_underfill_share_threshold"],
                    use_potential_share=True,
                )
                if not changed:
                    break

        fertilizers_out, _ = _build_solution_payload(
            weights=weights,
            allowed=problem.allowed,
            liters=problem.liters,
            recipe=problem.recipe,
        )
        result = fertilizers_out, achieved_elements
        self._solved_variants[variant] = result
        return result

    def solve(self, variant: _Variant) -> _VariantResult:
        result = self._solve_once(variant)
        use_relative_weighting, supplier_enabled, underfill_enabled = variant
        config = self.problem.solver_config
        if use_relative_weighting and not (config["n_total_governor_enabled"] or config["n_form_priority_weights"]):
            unweighted = self._solve_once((False, supplier_enabled, underfill_enabled))
            weighted_score = _score_percent_errors(
                self.problem.objective_keys,
                self.problem.targets,
                result[1],
            )
            unweighted_score = _score_percent_errors(
                self.problem.objective_keys,
                self.problem.targets,
                unweighted[1],
            )
            if unweighted_score < weighted_score:
                return unweighted
        return result


def _prepare_solve_problem(
    recipe: dict,
    *,
    ferts: Dict[str, Fertilizer] | None,
    mm: Dict[str, float] | None,
    water_profile_data: dict | None,
    water_profile_path: Path | None,
) -> _PreparedProblem:
    fertilizers = load_fertilizers() if ferts is None else ferts
    molar_masses = load_molar_masses() if mm is None else mm

    liters_value = recipe.get("liters", 10.0)
    liters = positive_float(10.0 if liters_value is None else liters_value, "liters")
    water_profile = _resolve_water_profile(recipe, water_profile_data, water_profile_path)
    osmosis_value = recipe.get("osmosis_percent")
    if osmosis_value is None:
        osmosis_value = water_profile.get("osmosis_percent", 0.0)
    osmosis_percent = percentage_float(osmosis_value, "osmosis_percent")
    water_mg_l = water_profile.get("mg_per_l") or {}

    targets = _normalize_targets(recipe.get("targets") or recipe.get("targets_mg_per_l") or {})
    solver_config = resolve_solver_config(recipe.get("solver_config"))
    mass_model_enabled = solver_config["solver_model"] == "mass_nnls"
    mass_nitrogen_mode = "n_total_only" if targets.get("N_total", 0.0) > 0.0 else "as_targets"
    objective_keys = _objective_keys(
        targets,
        nitrogen_objective_mode=mass_nitrogen_mode if mass_model_enabled else solver_config["nitrogen_objective_mode"],
        s_objective_enabled=True if mass_model_enabled else solver_config["s_objective_enabled"],
    )
    if not objective_keys:
        raise ValueError("No solvable targets defined (Na/Cl are report-only; legacy S requires s_objective_enabled).")

    allowed_names = unique_strings(
        recipe.get("fertilizers_allowed", []),
        "fertilizers_allowed",
    )
    if not allowed_names:
        raise ValueError("fertilizers_allowed must list at least one fertilizer")
    allowed: list[Fertilizer] = []
    for name in allowed_names:
        if name not in fertilizers:
            raise KeyError(f"Unknown fertilizer in fertilizers_allowed: '{name}'")
        allowed.append(fertilizers[name])

    fixed_grams: dict[str, float] = {}
    for raw_name, value in (recipe.get("fixed_grams") or {}).items():
        name = str(raw_name)
        try:
            fixed_grams[name] = non_negative_float(value, "fixed_grams")
        except ValueError as exc:
            raise ValueError(f"{exc}: {name}") from exc
    unknown_fixed = sorted(set(fixed_grams) - {fert.name for fert in allowed})
    if unknown_fixed:
        raise ValueError(f"fixed_grams not in fertilizers_allowed: {unknown_fixed}")

    fixed_weights = np.array(
        [fixed_grams.get(fert.name, 0.0) for fert in allowed],
        dtype=float,
    )
    variable_mask = np.array(
        [fert.name not in fixed_grams and fert.solver_role == "variable" for fert in allowed],
        dtype=bool,
    )
    upper_bounds = np.array(
        [
            np.inf
            if fert.name in fixed_grams or fert.solver_max_dose_per_l is None
            else non_negative_float(
                fert.solver_max_dose_per_l,
                f"solver_max_dose_per_l for {fert.name}",
            )
            * liters
            for fert in allowed
        ],
        dtype=float,
    )

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
    remaining_targets = np.array(
        [targets.get(key, 0.0) - water_only.elements_mg_l.get(key, 0.0) for key in objective_keys],
        dtype=float,
    )
    matrix = _build_matrix(allowed, molar_masses, objective_keys, liters)

    return _PreparedProblem(
        recipe=recipe,
        fertilizers=fertilizers,
        molar_masses=molar_masses,
        liters=liters,
        water_mg_l=water_mg_l,
        osmosis_percent=osmosis_percent,
        targets=targets,
        objective_keys=objective_keys,
        allowed=allowed,
        fixed_weights=fixed_weights,
        variable_mask=variable_mask,
        upper_bounds=upper_bounds,
        matrix=matrix,
        remaining_targets=remaining_targets,
        solver_config=solver_config,
    )


def _select_solver_variant(problem: _PreparedProblem, runner: _VariantRunner) -> _VariantResult:
    config = problem.solver_config
    current_variant = (
        config["relative_weighting"],
        config["singleton_supplier_enabled"],
        config["singleton_underfill_enabled"],
    )
    best_result = runner.solve(current_variant)
    if config["nitrogen_objective_mode"] != "n_total_only" or not _uses_default_solver_portfolio(config):
        return best_result

    variants = (
        current_variant,
        (True, False, current_variant[2]),
        (False, current_variant[1], current_variant[2]),
        (False, False, current_variant[2]),
    )
    best_score = _default_portfolio_score(
        problem.objective_keys,
        problem.targets,
        best_result[1],
    )
    for candidate in dict.fromkeys(variants):
        if candidate == current_variant:
            continue
        candidate_result = runner.solve(candidate)
        candidate_score = _default_portfolio_score(
            problem.objective_keys,
            problem.targets,
            candidate_result[1],
        )
        if candidate_score < best_score:
            best_result = candidate_result
            best_score = candidate_score
    return best_result


def _build_solve_result(
    problem: _PreparedProblem,
    variant_result: _VariantResult,
) -> SolveResult:
    fertilizers_out, achieved_elements = variant_result
    errors_mg_l: dict[str, float] = {}
    errors_percent: dict[str, float] = {}
    for key in problem.objective_keys:
        target = problem.targets.get(key, 0.0)
        achieved = achieved_elements.get(key, 0.0)
        errors_mg_l[key] = achieved - target
        errors_percent[key] = _signed_percent_error(target, achieved)

    return SolveResult(
        liters=problem.liters,
        solver_model=str(problem.solver_config["solver_model"]),
        fertilizers=fertilizers_out,
        objective_elements=problem.objective_keys,
        targets_mg_l=problem.targets,
        achieved_elements_mg_l=achieved_elements,
        errors_mg_l=errors_mg_l,
        errors_percent=errors_percent,
    )


def _solve_mass_nnls(problem: _PreparedProblem) -> SolveResult:
    """Minimize the unweighted squared elemental error in canonical mg/L."""
    result = _build_solve_result(problem, _VariantRunner(problem).solve((False, False, False)))
    values = (
        *(float(item["grams"]) for item in result.fertilizers),
        *result.achieved_elements_mg_l.values(),
        *result.errors_mg_l.values(),
    )
    if not all(np.isfinite(value) for value in values):
        raise ValueError("Mass NNLS produced a non-finite result")
    if any(float(item["grams"]) < 0.0 for item in result.fertilizers):
        raise ValueError("Mass NNLS produced a negative fertilizer dose")
    return result


def solve_recipe_data(
    recipe: dict,
    *,
    ferts: Dict[str, Fertilizer] | None = None,
    mm: Dict[str, float] | None = None,
    water_profile_data: dict | None = None,
    water_profile_path: Path | None = None,
) -> SolveResult:
    problem = _prepare_solve_problem(
        recipe,
        ferts=ferts,
        mm=mm,
        water_profile_data=water_profile_data,
        water_profile_path=water_profile_path,
    )
    if problem.solver_config["solver_model"] == "mass_nnls":
        return _solve_mass_nnls(problem)
    return _build_solve_result(problem, _select_solver_variant(problem, _VariantRunner(problem)))


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
