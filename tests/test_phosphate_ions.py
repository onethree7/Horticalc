import pytest

from horticalc.core import compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses


def test_phosphorus_is_represented_as_h2po4() -> None:
    ferts = load_fertilizers()
    molar_masses = load_molar_masses()
    recipe = {
        "liters": 10.0,
        "fertilizers": [
            {"name": "Biolchim Green-Go 6-48-18", "grams": 10.0},
            {"name": "K+S soluSOP 52 Kaliumsulfat 52 (+54)", "grams": 5.0},
        ],
        "urea_as_nh4": False,
    }

    result = compute_solution(recipe, ferts, molar_masses, water_mg_l={})
    phosphate_labels = [label for label in result.fertilizer_ions_mmol_l if "PO4" in label]
    phosphate_mmol_l = result.fertilizer_elements_mg_l["P"] / molar_masses["P"]

    assert phosphate_labels == ["H2PO4-"]
    assert result.fertilizer_ions_mmol_l["H2PO4-"] == pytest.approx(phosphate_mmol_l)
    assert result.fertilizer_ions_meq_l["H2PO4-"] == pytest.approx(-phosphate_mmol_l)
