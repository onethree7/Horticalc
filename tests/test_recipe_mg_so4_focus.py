import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.core import COMP_COLS, compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses, load_recipe, load_water_profile_data


def _expected_fertilizer_forms(recipe: dict, ferts: dict) -> dict:
    liters = float(recipe.get("liters") or 10.0)
    forms = {key: 0.0 for key in COMP_COLS}
    for entry in recipe.get("fertilizers", []):
        name = str(entry.get("name") or "").strip()
        grams = float(entry.get("grams") or 0.0)
        if not grams:
            continue
        fert = ferts[name]
        eff_g = grams * float(fert.weight_factor or 1.0)
        for key, frac in fert.comp.items():
            if key not in forms:
                continue
            forms[key] += eff_g * float(frac) * 1000.0 / liters
    return forms


def test_mg_so4_focus_recipe_elements_and_balance() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    recipe = load_recipe(repo_root / "recipes" / "mg_so4_focus.yml")
    ferts = load_fertilizers()
    mm = load_molar_masses()
    water_profile = load_water_profile_data(repo_root / "data" / "water_profiles" / "default.yml")

    result = compute_solution(
        recipe,
        ferts,
        mm,
        water_profile["mg_per_l"],
        osmosis_percent=float(recipe.get("osmosis_percent", 0.0)),
    )

    expected_forms = _expected_fertilizer_forms(recipe, ferts)
    expected_s = expected_forms["SO4"] * mm["S"] / mm["SO4"]
    expected_mg = expected_forms["MgO"] * mm["Mg"] / mm["MgO"]

    assert result.elements_mg_l["S"] == pytest.approx(expected_s, rel=0, abs=1e-9)
    assert result.elements_mg_l["Mg"] == pytest.approx(expected_mg, rel=0, abs=1e-9)

    mg_mmol = expected_mg / mm["Mg"]
    so4_mmol = expected_forms["SO4"] / mm["SO4"]
    cations_meq = mg_mmol * 2.0
    anions_meq = so4_mmol * 2.0
    denom = cations_meq + anions_meq
    error_signed = 0.0 if denom == 0 else (cations_meq - anions_meq) / denom * 100.0
    din_signed = 0.0 if denom == 0 else (cations_meq - anions_meq) / (0.5 * denom) * 100.0

    assert result.fertilizer_ion_balance["cations_meq_per_l"] == pytest.approx(cations_meq, rel=0, abs=1e-9)
    assert result.fertilizer_ion_balance["anions_meq_per_l"] == pytest.approx(anions_meq, rel=0, abs=1e-9)
    assert result.fertilizer_ion_balance["error_percent_signed"] == pytest.approx(error_signed, rel=0, abs=1e-9)
    assert result.fertilizer_ion_balance["error_percent_abs"] == pytest.approx(abs(error_signed), rel=0, abs=1e-9)
    assert result.fertilizer_ion_balance["raw_cbe_percent_signed"] == pytest.approx(error_signed, rel=0, abs=1e-9)
    assert result.fertilizer_ion_balance["raw_cbe_percent_abs"] == pytest.approx(abs(error_signed), rel=0, abs=1e-9)
    assert result.fertilizer_ion_balance["din_38402_62_percent_signed"] == pytest.approx(din_signed, rel=0, abs=1e-9)
    assert result.fertilizer_ion_balance["din_38402_62_percent_abs"] == pytest.approx(abs(din_signed), rel=0, abs=1e-9)
