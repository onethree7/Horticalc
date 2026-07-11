from __future__ import annotations

import numpy as np

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import _bounded_nnls, _nnls, _singleton_supplier_pass, solve_recipe_data


def test_bounded_nnls_enforces_multiple_upper_bounds() -> None:
    A = np.eye(2)
    b = np.array([2.0, 3.0])

    result = _bounded_nnls(A, b, np.array([1.0, 1.5]))

    assert np.allclose(result, [1.0, 1.5], atol=1e-8)


def test_bounded_nnls_redistributes_to_an_unlimited_product() -> None:
    A = np.array([[1.0, 1.0], [1.0, 0.0]])
    b = np.array([2.0, 2.0])

    result = _bounded_nnls(A, b, np.array([0.5, np.inf]))

    assert np.allclose(result, [0.5, 1.5], atol=1e-7)


def test_bounded_nnls_keeps_original_path_without_limits() -> None:
    A = np.array([[1.0, 0.5], [0.25, 2.0]])
    b = np.array([3.0, 4.0])

    assert np.array_equal(_bounded_nnls(A, b, np.array([np.inf, np.inf])), _nnls(A, b))


def _solve(maximum: float | None, *, liters: float = 10.0, fixed: float | None = None):
    fertilizer = Fertilizer(
        "N source", False, 1.0, {"NO3": 0.1},
        solver_max_dose_per_l=maximum,
    )
    recipe = {
        "liters": liters,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["N source"],
        "targets_mg_per_l": {"N_total": 100.0},
    }
    if fixed is not None:
        recipe["fixed_grams"] = {"N source": fixed}
    return solve_recipe_data(
        recipe,
        ferts={"N source": fertilizer},
        mm=load_molar_masses(),
    )


def test_solver_max_scales_with_solution_liters() -> None:
    result = _solve(0.2, liters=10.0)

    assert np.isclose(result.fertilizers[0]["grams"], 2.0, atol=1e-7)


def test_zero_solver_max_excludes_variable_product() -> None:
    result = _solve(0.0)

    assert result.fertilizers == []


def test_fixed_grams_explicitly_override_solver_max() -> None:
    result = _solve(0.2, fixed=5.0)

    assert result.fertilizers == [{"name": "N source", "grams": 5.0}]


def test_singleton_underfill_cannot_exceed_solver_max() -> None:
    A = np.array([[10.0]])

    updated, _ = _singleton_supplier_pass(
        A=A,
        x_full=np.array([1.0]),
        variable_mask_full=np.array([True]),
        objective_keys=["K"],
        targets_raw={"K": 100.0},
        achieved_elements={"K": 10.0},
        share_threshold=0.0,
        max_regress_pp=100.0,
        skip_keys=None,
        recompute_achieved_fn=lambda weights: {"K": float((A @ weights)[0])},
        mode="underfill",
        use_potential_share=True,
        upper_bounds_full=np.array([2.0]),
    )

    assert updated[0] <= 2.0
