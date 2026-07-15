from horticalc.core import compute_solution
from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_co3_water_profile_converts_to_hco3_for_solution() -> None:
    molar_masses = load_molar_masses()
    recipe = {"liters": 1.0, "fertilizers": []}
    water_mg_l = {"CO3": 120.0}

    result = compute_solution(recipe, {}, molar_masses, water_mg_l)

    assert result.water_elements_mg_l.get("HCO3", 0.0) > 0.0
    assert result.water_ions_mmol_l.get("HCO3-", 0.0) > 0.0


def test_solve_recipe_data_includes_co3_derived_hco3() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K-only": Fertilizer(name="K-only", liquid=False, weight_factor=1.0, comp={"K2O": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"K": 50.0},
        "fertilizers_allowed": ["K-only"],
    }
    water_profile_data = {"mg_per_l": {"CO3": 120.0}}

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses, water_profile_data=water_profile_data)

    assert result.achieved_elements_mg_l.get("HCO3", 0.0) > 0.0
