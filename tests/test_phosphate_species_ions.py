

from horticalc.core import compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses

def test_phosphate_species_keeps_p_totals_but_changes_ion_label() -> None:
    ferts = load_fertilizers()
    molar_masses = load_molar_masses()

    base_recipe = {
        "liters": 10.0,
        "fertilizers": [
            {"name": "Biolchim Green-Go 6-48-18", "grams": 10.0},
            {"name": "K+S soluSOP 52 Kaliumsulfat 52 (+54)", "grams": 5.0},
        ],
        "urea_as_nh4": False,
    }

    h2po4_result = compute_solution(
        {**base_recipe, "phosphate_species": "H2PO4"},
        ferts,
        molar_masses,
        water_mg_l={},
    )
    hpo4_result = compute_solution(
        {**base_recipe, "phosphate_species": "HPO4"},
        ferts,
        molar_masses,
        water_mg_l={},
    )

    assert abs(h2po4_result.elements_mg_l["P"] - hpo4_result.elements_mg_l["P"]) <= 1e-9

    h2po4_ions = h2po4_result.fertilizer_ions_mmol_l
    hpo4_ions = hpo4_result.fertilizer_ions_mmol_l

    assert h2po4_ions.get("H2PO4-", 0.0) > 0.0
    assert hpo4_ions.get("HPO4^2-", 0.0) > 0.0
    assert h2po4_ions.get("HPO4^2-", 0.0) == 0.0
    assert hpo4_ions.get("H2PO4-", 0.0) == 0.0
