import pytest

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import SolveResult, _validate_solve_result, solve_recipe_data


def _solve_result(*, grams: float = 1.0, achieved: float = 100.0) -> SolveResult:
    return SolveResult(
        liters=10.0,
        solver_model="nnls_tuning",
        fertilizers=[{"name": "K test", "grams": grams}],
        objective_elements=["K"],
        ignored_elements=[],
        target_priorities={},
        priority_stages=[],
        targets_mg_l={"K": 100.0},
        achieved_elements_mg_l={"K": achieved},
        errors_mg_l={"K": achieved - 100.0},
        errors_percent={"K": achieved - 100.0},
    )


def test_shared_solver_result_validation_rejects_non_finite_values() -> None:
    with pytest.raises(ValueError, match=r"NNLS \+ tuning solver produced a non-finite result"):
        _validate_solve_result(_solve_result(achieved=float("nan")))


def test_shared_solver_result_validation_rejects_negative_doses() -> None:
    with pytest.raises(ValueError, match=r"NNLS \+ tuning solver produced a negative fertilizer dose"):
        _validate_solve_result(_solve_result(grams=-0.1))


def test_solve_recipe_data_rejects_invalid_target_key() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K2O test": Fertilizer("K2O test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K2O test"],
        "targets": {"K2O": 100.0},
    }

    with pytest.raises(ValueError, match="Invalid target key: K2O"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_non_positive_liters() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 0,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "targets": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="liters must be > 0"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_invalid_solver_config() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "targets": {"K": 10.0},
        "fertilizers_allowed": ["K test"],
        "solver_config": {"relative_weighting": "false"},
    }

    with pytest.raises(ValueError, match="Invalid solver config value: relative_weighting"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_negative_fixed_grams() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "fixed_grams": {"K test": -1.0},
        "targets": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="fixed_grams must be >= 0: K test"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_fixed_grams_outside_allowed_list() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
        "Other": Fertilizer("Other", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "fixed_grams": {"Other": 1.0},
        "targets": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="fixed_grams not in fertilizers_allowed"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_duplicate_fertilizers_allowed() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test", "K test"],
        "targets": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="fertilizers_allowed must not contain duplicates"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_does_not_use_water_elements_as_targets() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "water_elements_mg_per_l": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="No solvable targets defined"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_can_solve_hco3_from_direct_hco3_composition() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "HCO3 test": Fertilizer("HCO3 test", False, 1.0, {"HCO3": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["HCO3 test"],
        "targets": {"HCO3": 100.0},
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)

    assert result.objective_elements == ["HCO3"]
    assert result.fertilizers == [{"name": "HCO3 test", "grams": pytest.approx(0.1, abs=1e-12)}]
    assert result.achieved_elements_mg_l["HCO3"] == pytest.approx(100.0, abs=1e-10)


def test_water_profile_overshoot_remains_visible_in_errors() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K-only": Fertilizer(name="K-only", liquid=False, weight_factor=1.0, comp={"K2O": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"Ca": 100.0},
        "fertilizers_allowed": ["K-only"],
    }
    water_profile_data = {"mg_per_l": {"Ca": 200.0}}

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses, water_profile_data=water_profile_data)

    assert result.fertilizers == []
    assert result.errors_mg_l["Ca"] == pytest.approx(100.0, abs=1e-12)
    assert result.errors_percent["Ca"] == pytest.approx(100.0, abs=1e-12)
