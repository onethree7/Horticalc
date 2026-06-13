from pathlib import Path

import numpy as np
import yaml

from horticalc.data_io import load_fertilizers, load_molar_masses, load_water_profile_data
from horticalc.data_io import Fertilizer
from horticalc.solver import (
    _fertilizer_element_contrib_per_g,
    _score_percent_errors,
    _singleton_supplier_pass,
    _solve_weights,
    solve_recipe_data,
)

def test_fertilizer_contrib_respects_weight_factor() -> None:
    fert = Fertilizer(name="K2O Test", liquid=False, weight_factor=2.0, comp={"K2O": 0.5})
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
        skip_keys=None,
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
        skip_keys=None,
        recompute_achieved_fn=recompute_achieved_fn,
    )

    assert np.allclose(updated, x_full)

def test_singleton_supplier_pass_checks_each_objective_regression() -> None:
    A = np.array([[10.0, 0.0], [10.0, 0.0]])
    x_full = np.array([15.0, 0.0])
    targets_raw = {"K": 100.0, "Ca": 150.0}
    achieved_elements = {"K": 150.0, "Ca": 150.0}

    def recompute_achieved_fn(new_x_full: np.ndarray) -> dict:
        values = A @ new_x_full
        return {"K": float(values[0]), "Ca": float(values[1])}

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
        skip_keys=None,
        recompute_achieved_fn=recompute_achieved_fn,
    )

    assert np.allclose(updated, x_full)

def test_score_percent_errors_returns_max_percent_error() -> None:
    objective_keys = ["K", "Fe"]
    targets_raw = {"K": 100.0, "Fe": 0.1}
    achieved = {"K": 90.0, "Fe": 0.2}

    score = _score_percent_errors(objective_keys, targets_raw, achieved)

    assert score == (100.0,)

def test_default_n_total_portfolio_avoids_saloner_macro_collapse() -> None:
    root = Path(__file__).resolve().parents[1]
    with (root / "user" / "nutrient_solutions" / "Saloner_Bernstein_Cannabis_NPK_Target_Optimization.yml").open(
        "r",
        encoding="utf-8",
    ) as handle:
        profile = yaml.safe_load(handle)

    recipe = {
        "liters": 10.0,
        "targets_mg_per_l": {
            **profile["targets_mg_per_l"],
            "Si": 7.0,
        },
        "fertilizers_allowed": [
            "Compo Fetrilon Combi 1",
            "Yara Magnitra-L Magnesiumnitrat",
            "HAIFA monokaliumphosphat MKP",
            "Yara Tera KRISTALON ROT CALCIUM",
            "Agrolution Special 313 14-7-14+14CaO+TE",
            "S3 Kaliwasser 28 Be",
            "Peters Professional Combi Sol 6-18-36+3MgO+TE",
        ],
        "water_profile": "65936",
        "osmosis_percent": 66.0,
        "solver_config": {
            "relative_weighting": False,
            "overshoot_penalty": 1.0,
            "irls_max_outer_iter": 4,
            "scale_eps_mg_per_l": 1.0,
            "singleton_supplier_enabled": False,
            "singleton_share_threshold": 0.85,
            "singleton_max_regress_pp": 0.25,
            "singleton_underfill_enabled": True,
            "singleton_underfill_share_threshold": 0.85,
            "singleton_underfill_max_iter": 2,
            "n_total_governor_enabled": False,
            "n_total_governor_weight": 1.0,
            "nitrogen_objective_mode": "n_total_only",
        },
    }

    result = solve_recipe_data(
        recipe,
        ferts=load_fertilizers(),
        mm=load_molar_masses(),
        water_profile_data=load_water_profile_data(root / "user" / "water_profiles" / "65936.yml"),
    )

    achieved = result.achieved_elements_mg_l
    assert achieved["N_total"] > 150.0
    assert achieved["P"] > 26.0
    assert achieved["K"] > 100.0
    assert achieved["Ca"] > 120.0
    assert np.isclose(achieved["Si"], 7.0)
