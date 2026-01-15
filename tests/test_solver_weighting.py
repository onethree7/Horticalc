import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer
from horticalc.solver import (
    _fertilizer_element_contrib_per_g,
    _singleton_supplier_pass,
    _solve_weights,
)


def test_fertilizer_contrib_respects_weight_factor() -> None:
    fert = Fertilizer(name="K2O Test", form="solid", weight_factor=2.0, comp={"K2O": 0.5})
    mm = {"K": 39.0983, "K2O": 94.196}

    contrib = _fertilizer_element_contrib_per_g(fert, mm)
    expected = 0.5 * 1000.0 * 2.0 * (2 * mm["K"] / mm["K2O"])

    assert np.isclose(contrib["K"], expected)


def test_relative_weighting_reduces_small_target_error() -> None:
    A = np.array([[1.0, 1.0], [10.0, 0.0]])
    b = np.array([1.0, 100.0])
    variable_mask = np.array([True, True])

    x_unweighted = _solve_weights(A, b, np.array([]), variable_mask, relative_weighting=False)
    x_weighted = _solve_weights(
        A,
        b,
        np.array([]),
        variable_mask,
        relative_weighting=True,
        objective_keys=["A", "B"],
        targets_raw={"A": 1.0, "B": 100.0},
    )

    r_unweighted = A @ x_unweighted - b
    r_weighted = A @ x_weighted - b

    assert abs(r_weighted[0]) < abs(r_unweighted[0])


def test_singleton_supplier_pass_reduces_overshoot() -> None:
    A = np.array([[10.0, 1.0]])
    x_full = np.array([15.0, 0.0])
    targets_raw = {"K": 100.0}
    achieved_elements = {"K": 150.0}

    def recompute_achieved_fn(new_x_full: np.ndarray) -> dict:
        return {"K": float((A @ new_x_full)[0])}

    updated = _singleton_supplier_pass(
        A=A,
        x_full=x_full,
        variable_mask_full=np.array([True, True]),
        objective_keys=["K"],
        targets_raw=targets_raw,
        achieved_elements=achieved_elements,
        liters=10.0,
        share_threshold=0.85,
        max_regress_pp=0.25,
        recompute_achieved_fn=recompute_achieved_fn,
    )

    assert updated[0] == 10.0


def test_singleton_supplier_pass_rolls_back_on_regression() -> None:
    A = np.array([[10.0, 0.0], [0.0, 1.0]])
    x_full = np.array([15.0, 1.0])
    targets_raw = {"K": 100.0, "Ca": 1.0}
    achieved_elements = {"K": 150.0, "Ca": 1.0}

    def recompute_achieved_fn(new_x_full: np.ndarray) -> dict:
        _ = new_x_full
        return {"K": 100.0, "Ca": 10.0}

    updated = _singleton_supplier_pass(
        A=A,
        x_full=x_full,
        variable_mask_full=np.array([True, True]),
        objective_keys=["K", "Ca"],
        targets_raw=targets_raw,
        achieved_elements=achieved_elements,
        liters=10.0,
        share_threshold=0.85,
        max_regress_pp=0.0,
        recompute_achieved_fn=recompute_achieved_fn,
    )

    assert np.allclose(updated, x_full)
