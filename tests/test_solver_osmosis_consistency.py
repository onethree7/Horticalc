import pytest

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data


def test_solver_subtracts_the_exact_osmosis_adjusted_water_calcium() -> None:
    molar_masses = load_molar_masses()
    fertilizer = Fertilizer(
        name="CaO only",
        liquid=False,
        weight_factor=1.0,
        comp={"CaO": 1.0},
    )
    result = solve_recipe_data(
        {
            "liters": 1.0,
            "osmosis_percent": 80.0,
            "targets_mg_per_l": {"Ca": 50.0},
            "fertilizers_allowed": [fertilizer.name],
            "solver_config": {"solver_model": "mass_nnls"},
        },
        ferts={fertilizer.name: fertilizer},
        mm=molar_masses,
        water_profile_data={"mg_per_l": {"Ca": 100.0}},
    )

    expected_water_ca_mg_l = 100.0 * (1.0 - 80.0 / 100.0)
    required_fertilizer_ca_mg_l = 50.0 - expected_water_ca_mg_l
    ca_mg_per_gram_cao = 1000.0 * molar_masses["Ca"] / molar_masses["CaO"]
    expected_grams = required_fertilizer_ca_mg_l / ca_mg_per_gram_cao

    assert result.fertilizers == [{"name": fertilizer.name, "grams": pytest.approx(expected_grams, abs=1e-12)}]
    assert result.achieved_elements_mg_l["Ca"] == pytest.approx(50.0, abs=1e-12)
    assert result.errors_mg_l["Ca"] == pytest.approx(0.0, abs=1e-12)
