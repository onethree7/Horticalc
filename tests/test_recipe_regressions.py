from pathlib import Path

import pytest

from horticalc.core import COMP_COLS, compute_solution, run_recipe
from horticalc.data_io import load_fertilizers, load_molar_masses, load_recipe, load_water_profile_data
from horticalc.ec import compute_ec


def _expected_fertilizer_forms(recipe: dict, ferts: dict) -> dict:
    liters = float(recipe.get("liters") or 10.0)
    forms = dict.fromkeys(COMP_COLS, 0.0)
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


def test_recipe_silicate_k_boost_si_k_totals() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "recipes" / "silicate_k_boost.yml"
    result = run_recipe(recipe_path)

    oxides = result["oxides_mg_per_l"]
    elements = result["elements_mg_per_l"]

    liters = 10.0
    k2o_mg_l = ((1.0 * 1.24 * 0.07) + (1.0 * 1.26 * 0.08) + (1.0 * 1.0 * 0.56)) * 1000.0 / liters
    # Vitanica Si declares 10% SiO3; the catalog stores its SiO2 equivalent.
    sio2_mg_l = ((1.0 * 1.24 * 0.078971317) + (1.0 * 1.26 * 0.21)) * 1000.0 / liters

    mm = load_molar_masses()
    expected_k_mg_l = k2o_mg_l * (2 * mm["K"] / mm["K2O"])
    expected_si_mg_l = sio2_mg_l * (mm["Si"] / mm["SiO2"])

    assert oxides["K2O"] == pytest.approx(k2o_mg_l, rel=0, abs=1e-6)
    assert oxides["SiO2"] == pytest.approx(sio2_mg_l, rel=0, abs=1e-6)
    assert elements["K"] == pytest.approx(expected_k_mg_l, rel=0, abs=1e-6)
    assert elements["Si"] == pytest.approx(expected_si_mg_l, rel=0, abs=1e-6)


def test_trace_silicon_mix_snapshot() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    recipe = load_recipe(repo_root / "recipes" / "trace_silicon_mix.yml")
    water_profile = load_water_profile_data(repo_root / "data" / "water_profiles" / "default.yml")
    ferts = load_fertilizers()
    molar_masses = load_molar_masses()

    result = compute_solution(
        recipe,
        ferts,
        molar_masses,
        water_profile["mg_per_l"],
        osmosis_percent=water_profile.get("osmosis_percent", 0.0),
    )

    expected_elements = {
        "B": 1.85,
        "Cu": 3.0,
        "Fe": 7.0,
        "Mn": 8.15,
        "Si": 30.850823,
        "Zn": 5.25,
    }
    actual_elements = {key: round(result.elements_mg_l.get(key, 0.0), 6) for key in expected_elements}
    assert actual_elements == expected_elements

    expected_ions = {
        "NH4+": 0.0,
        "K+": 0.0,
        "Ca+2": 0.0,
        "Mg+2": 0.223301,
        "Na+": 0.0,
        "NO3-": 0.0,
        "SO4^2-": 0.28065,
        "Cl-": 0.0,
        "HCO3-": 0.0,
    }
    actual_ions = {key: round(result.ions_mmol_l.get(key, 0.0), 6) for key in expected_ions}
    assert actual_ions == expected_ions

    ec = compute_ec(result.ions_mmol_l)
    expected_ec = {
        "ionic_strength_mol_per_kg": 0.001008,
        "ec_mS_per_cm": {"18.0": 0.055376, "25.0": 0.064635},
        "ec_uS_per_cm": {"18.0": 55.375684, "25.0": 64.6346},
    }
    actual_ec = {
        "ionic_strength_mol_per_kg": round(ec["ionic_strength_mol_per_kg"], 6),
        "ec_mS_per_cm": {key: round(value, 6) for key, value in ec["ec_mS_per_cm"].items()},
        "ec_uS_per_cm": {key: round(value, 6) for key, value in ec["ec_uS_per_cm"].items()},
    }
    assert actual_ec == expected_ec
