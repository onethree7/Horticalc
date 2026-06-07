from pathlib import Path

import pytest

from horticalc.core import run_recipe
from horticalc.data_io import load_molar_masses

def test_recipe_silicate_k_boost_si_k_totals() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "recipes" / "silicate_k_boost.yml"
    result = run_recipe(recipe_path)

    oxides = result["oxides_mg_per_l"]
    elements = result["elements_mg_per_l"]

    liters = 10.0
    k2o_mg_l = ((1.0 * 1.24 * 0.07) + (1.0 * 1.26 * 0.08) + (1.0 * 1.0 * 0.56)) * 1000.0 / liters
    sio2_mg_l = ((1.0 * 1.24 * 0.10) + (1.0 * 1.26 * 0.21)) * 1000.0 / liters

    mm = load_molar_masses()
    expected_k_mg_l = k2o_mg_l * (2 * mm["K"] / mm["K2O"])
    expected_si_mg_l = sio2_mg_l * (mm["Si"] / mm["SiO2"])

    assert oxides["K2O"] == pytest.approx(k2o_mg_l, rel=0, abs=1e-6)
    assert oxides["SiO2"] == pytest.approx(sio2_mg_l, rel=0, abs=1e-6)
    assert elements["K"] == pytest.approx(expected_k_mg_l, rel=0, abs=1e-6)
    assert elements["Si"] == pytest.approx(expected_si_mg_l, rel=0, abs=1e-6)
