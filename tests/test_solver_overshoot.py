

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data

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
    assert result.errors_mg_l["Ca"] > 0.0
    assert result.errors_percent["Ca"] > 0.0
