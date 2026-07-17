from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from horticalc.data_io import (
    Fertilizer,
    load_fertilizers,
    load_molar_masses,
    load_nutrient_solution_data,
    load_water_profile_data,
)
from horticalc.paths import shipped_fertilizers_path
from horticalc.solver import solve_recipe_data

ROOT = Path(__file__).resolve().parents[1]
MOLAR_MASSES = load_molar_masses()


def _fertilizer(name: str, form: str, fraction: float, *, role: str = "variable") -> Fertilizer:
    return Fertilizer(
        name=name,
        liquid=False,
        weight_factor=1.0,
        comp={form: fraction},
        solver_role=role,
    )


def test_mass_nnls_uses_raw_mg_per_l_squared_error() -> None:
    result = solve_recipe_data(
        {
            "liters": 10.0,
            "targets_mg_per_l": {"N_total": 100.0, "K": 100.0},
            "fertilizers_allowed": ["N", "K"],
            "solver_config": {"solver_model": "mass_nnls"},
        },
        ferts={
            "N": _fertilizer("N", "NO3", 0.1),
            "K": _fertilizer("K", "K2O", 0.1),
        },
        mm=MOLAR_MASSES,
        water_profile_data={"mg_per_l": {}},
    )

    assert result.solver_model == "mass_nnls"
    assert result.errors_mg_l["N_total"] == pytest.approx(0.0, abs=1e-7)
    assert result.errors_mg_l["K"] == pytest.approx(0.0, abs=1e-7)


def test_mass_nnls_does_not_optimize_fixed_only_products_without_a_fixed_dose() -> None:
    recipe = {
        "liters": 10.0,
        "targets_mg_per_l": {"N_total": 100.0},
        "fertilizers_allowed": ["Variable", "Additive"],
        "solver_config": {"solver_model": "mass_nnls"},
    }
    fertilizers = {
        "Variable": _fertilizer("Variable", "NO3", 0.1),
        "Additive": _fertilizer("Additive", "NO3", 1.0, role="fixed_only"),
    }

    result = solve_recipe_data(
        recipe,
        ferts=fertilizers,
        mm=MOLAR_MASSES,
        water_profile_data={"mg_per_l": {}},
    )

    assert [row["name"] for row in result.fertilizers] == ["Variable"]
    assert result.fertilizers[0]["grams"] == pytest.approx(10.0)


def test_mass_nnls_accounts_for_a_fixed_only_product_at_the_user_dose() -> None:
    result = solve_recipe_data(
        {
            "liters": 10.0,
            "targets_mg_per_l": {"N_total": 100.0},
            "fertilizers_allowed": ["Variable", "Additive"],
            "fixed_grams": {"Additive": 0.5},
            "solver_config": {"solver_model": "mass_nnls"},
        },
        ferts={
            "Variable": _fertilizer("Variable", "NO3", 0.1),
            "Additive": _fertilizer("Additive", "NO3", 1.0, role="fixed_only"),
        },
        mm=MOLAR_MASSES,
        water_profile_data={"mg_per_l": {}},
    )

    doses = {row["name"]: row["grams"] for row in result.fertilizers}
    assert doses == pytest.approx({"Variable": 5.0, "Additive": 0.5})
    assert result.errors_mg_l["N_total"] == pytest.approx(0.0, abs=1e-7)


def test_mass_nnls_forces_total_nitrogen_and_sulfur_when_available() -> None:
    result = solve_recipe_data(
        {
            "liters": 10.0,
            "targets_mg_per_l": {"N_total": 100.0, "N_NO3": 80.0, "S": 20.0},
            "fertilizers_allowed": ["N", "S"],
            "solver_config": {
                "solver_model": "mass_nnls",
                "nitrogen_objective_mode": "n_forms_only",
                "s_objective_enabled": False,
            },
        },
        ferts={
            "N": _fertilizer("N", "NO3", 0.1),
            "S": _fertilizer("S", "SO4", 0.1),
        },
        mm=MOLAR_MASSES,
        water_profile_data={"mg_per_l": {}},
    )

    assert result.objective_elements == ["N_total", "S"]
    assert result.errors_mg_l["N_total"] == pytest.approx(0.0, abs=1e-7)
    assert result.errors_mg_l["S"] == pytest.approx(0.0, abs=1e-7)


def _solve_shipped_profile(targets: dict[str, float], allowed: list[str]):
    return solve_recipe_data(
        {
            "liters": 10.0,
            "osmosis_percent": 66.0,
            "targets_mg_per_l": targets,
            "fertilizers_allowed": allowed,
            "solver_config": {"solver_model": "mass_nnls"},
        },
        ferts=load_fertilizers(shipped_fertilizers_path(ROOT)),
        mm=MOLAR_MASSES,
        water_profile_data=load_water_profile_data(ROOT / "data" / "water_profiles" / "65936.yml"),
    )


def test_saloner_regression_stays_mass_accurate_with_unbounded_fetrilon() -> None:
    recipe = yaml.safe_load((ROOT / "recipes" / "solve_augmented_saloner_bernstein.yml").read_text(encoding="utf-8"))

    result = _solve_shipped_profile(recipe["targets_mg_per_l"], recipe["fertilizers_allowed"])

    doses = {row["name"]: float(row["grams"]) for row in result.fertilizers}
    assert result.achieved_elements_mg_l["Fe"] == pytest.approx(1.51242, abs=1e-4)
    assert doses["Compo Fetrilon Combi 1"] == pytest.approx(0.17243, abs=1e-4)
    for element in ("N_total", "P", "K", "Ca", "Mg", "S", "Si"):
        assert abs(result.errors_mg_l[element]) < 0.01


def test_allowing_fixed_only_humin_does_not_change_saloner_solution() -> None:
    recipe = yaml.safe_load((ROOT / "recipes" / "solve_augmented_saloner_bernstein.yml").read_text(encoding="utf-8"))
    base = _solve_shipped_profile(recipe["targets_mg_per_l"], recipe["fertilizers_allowed"])
    with_humin = _solve_shipped_profile(
        recipe["targets_mg_per_l"],
        [
            *recipe["fertilizers_allowed"],
            "HuminTech AMINO POWER Plus Liquid",
            "HuminTech Fulvital Plus Liquid",
        ],
    )

    assert with_humin.achieved_elements_mg_l == pytest.approx(base.achieved_elements_mg_l)
    assert not any(row["name"].startswith("HuminTech") for row in with_humin.fertilizers)


def test_bugbee_regression_does_not_trade_macros_for_fetrilon_micros() -> None:
    sal_oner = yaml.safe_load((ROOT / "recipes" / "solve_augmented_saloner_bernstein.yml").read_text(encoding="utf-8"))
    bugbee = load_nutrient_solution_data(
        ROOT / "data" / "nutrient_solutions" / "Bugbee_Utah_Hydroponic_Cannabis_2022.yml"
    )

    result = _solve_shipped_profile(bugbee["targets_mg_per_l"], sal_oner["fertilizers_allowed"])

    assert result.achieved_elements_mg_l["Fe"] == pytest.approx(1.3039, abs=1e-4)
    assert result.achieved_elements_mg_l["Mn"] == pytest.approx(1.1186, abs=1e-4)
    assert result.achieved_elements_mg_l["Cu"] == pytest.approx(0.1111, abs=1e-4)
    assert all(float(row["grams"]) >= 0.0 for row in result.fertilizers)
