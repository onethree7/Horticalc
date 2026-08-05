import pytest

from horticalc.core import _compute_ion_balance, compute_solution, oxide_to_element_mg_l
from horticalc.data_io import load_fertilizers, load_molar_masses, load_recipe, load_water_profile_data
from horticalc.metrics import format_npks
from horticalc.paths import repo_root


def _ion_charge(label: str) -> int:
    if "^" in label:
        _, charge = label.split("^", 1)
        sign = charge[-1]
        magnitude = int(charge[:-1]) if charge[:-1] else 1
        return magnitude if sign == "+" else -magnitude
    if label.endswith("+2"):
        return 2
    if label.endswith("-2"):
        return -2
    if label.endswith("+"):
        return 1
    if label.endswith("-"):
        return -1
    raise ValueError(f"Unrecognized ion charge format: {label}")


def test_ion_balance_reports_raw_cbe_and_din_formula() -> None:
    balance = _compute_ion_balance(cations_sum=10.0, anions_sum=11.0)

    assert balance["raw_cbe_percent_signed"] == pytest.approx(-4.7619047619, abs=1e-9)
    assert balance["raw_cbe_percent_abs"] == pytest.approx(4.7619047619, abs=1e-9)
    assert balance["din_38402_62_percent_signed"] == pytest.approx(-9.5238095238, abs=1e-9)
    assert balance["din_38402_62_percent_abs"] == pytest.approx(9.5238095238, abs=1e-9)
    assert balance["error_percent_signed"] == balance["raw_cbe_percent_signed"]
    assert balance["error_percent_abs"] == balance["raw_cbe_percent_abs"]
    assert balance["balance_method"] == "non_speciated_major_ion_balance"


def test_fertilizer_ion_balance_matches_charges() -> None:
    ferts = load_fertilizers()
    molar_masses = load_molar_masses()
    recipe = {
        "liters": 10.0,
        "fertilizers": [
            {"name": "Yara Tera CALCINIT", "grams": 5.0},
            {"name": "K+S soluSOP 52 Kaliumsulfat 52 (+54)", "grams": 5.0},
        ],
        "urea_as_nh4": False,
    }

    result = compute_solution(recipe, ferts, molar_masses, water_mg_l={})
    expected_meq = {ion: mmol * _ion_charge(ion) for ion, mmol in result.fertilizer_ions_mmol_l.items()}

    for ion, expected_value in expected_meq.items():
        actual_value = result.fertilizer_ions_meq_l.get(ion)
        assert actual_value is not None, f"Missing meq/L for {ion}"
        assert actual_value == pytest.approx(expected_value, abs=1e-9)

    cations_sum = sum(value for value in expected_meq.values() if value > 0)
    anions_sum = -sum(value for value in expected_meq.values() if value < 0)
    denom = cations_sum + anions_sum
    err_signed = 0.0 if denom == 0 else (cations_sum - anions_sum) / denom * 100.0
    err_abs = abs(err_signed)

    assert result.fertilizer_ion_balance["cations_meq_per_l"] == pytest.approx(cations_sum, abs=1e-9)
    assert result.fertilizer_ion_balance["anions_meq_per_l"] == pytest.approx(anions_sum, abs=1e-9)
    assert result.fertilizer_ion_balance["error_percent_signed"] == pytest.approx(err_signed, abs=1e-9)
    assert result.fertilizer_ion_balance["error_percent_abs"] == pytest.approx(err_abs, abs=1e-9)
    assert result.fertilizer_ion_balance["raw_cbe_percent_signed"] == pytest.approx(err_signed, abs=1e-9)
    assert result.fertilizer_ion_balance["raw_cbe_percent_abs"] == pytest.approx(err_abs, abs=1e-9)
    assert result.fertilizer_ion_balance["din_38402_62_percent_signed"] == pytest.approx(err_signed * 2.0, abs=1e-9)
    assert result.fertilizer_ion_balance["din_38402_62_percent_abs"] == pytest.approx(err_abs * 2.0, abs=1e-9)
    assert result.fertilizer_ion_balance["balance_method"] == "non_speciated_major_ion_balance"


def test_nh4_is_cation_and_trace_elements_stay_out_of_ions() -> None:
    ferts = load_fertilizers()
    molar_masses = load_molar_masses()
    recipe = {
        "liters": 10.0,
        "fertilizers": [{"name": "Agrolution pHLow 222 20-20-20+TE", "grams": 5.0}],
        "urea_as_nh4": False,
    }

    result = compute_solution(recipe, ferts, molar_masses, water_mg_l={})

    expected_n_nh4_mg_l = 5.0 / 10.0 * 1000.0 * 0.029
    expected_nh4_mmol_l = expected_n_nh4_mg_l / molar_masses["N"]
    assert result.fertilizer_elements_mg_l["N_NH4"] == pytest.approx(expected_n_nh4_mg_l, abs=1e-12)
    assert result.fertilizer_ions_mmol_l["NH4+"] == pytest.approx(expected_nh4_mmol_l, abs=1e-12)
    assert result.fertilizer_ions_meq_l["NH4+"] == pytest.approx(expected_nh4_mmol_l, abs=1e-12)
    for trace_label in ("Fe", "Mn", "Cu", "Zn", "B", "Mo"):
        assert trace_label not in result.fertilizer_ions_meq_l


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


def test_urea_as_nh4_rebalances_nitrogen_forms() -> None:
    ferts = load_fertilizers()
    molar_masses = load_molar_masses()
    recipe = load_recipe(repo_root() / "recipes" / "reference_agrolution_313_1g_per_l.yml")
    water_profile_name = recipe.get("water_profile", "default")
    water_profile = load_water_profile_data(repo_root() / "data" / "water_profiles" / f"{water_profile_name}.yml")
    water_mg_l = water_profile.get("mg_per_l", {})

    results = {}
    for flag in (False, True):
        recipe_run = dict(recipe)
        recipe_run["urea_as_nh4"] = flag
        results[flag] = compute_solution(recipe_run, ferts, molar_masses, water_mg_l)

    elements_false = results[False].elements_mg_l
    elements_true = results[True].elements_mg_l

    assert {key: elements_false[key] for key in ("N_total", "N_NO3", "N_NH4", "N_UREA")} == pytest.approx(
        {"N_total": 140.0, "N_NO3": 117.0, "N_NH4": 0.0, "N_UREA": 23.0},
        rel=0,
        abs=1e-12,
    )
    assert {key: elements_true[key] for key in ("N_total", "N_NO3", "N_NH4", "N_UREA")} == pytest.approx(
        {"N_total": 140.0, "N_NO3": 117.0, "N_NH4": 23.0, "N_UREA": 0.0},
        rel=0,
        abs=1e-12,
    )


def test_npk_metrics_include_element_mg_l_ion_ratios() -> None:
    metrics = format_npks(
        {
            "elements_mg_per_l": {
                "N_NH4": 20.0,
                "K": 10.0,
                "Ca": 100.0,
                "Mg": 30.0,
                "Na": 0.0,
                "S": 40.0,
                "P": 40.0,
                "Fe": 1.0,
                "Si": 5.0,
            },
            "oxides_mg_per_l": {
                "P2O5": 90.0,
                "K2O": 12.0,
                "CaO": 56.0774,
                "MgO": 40.3044,
                "Na2O": 0.0,
                "SO4": 120.0,
                "CO3": 10.0,
                "SiO2": 0.0,
            },
        }
    )

    assert metrics["npk_ratios_ion"]["Ca:Mg"] == "Ca:Mg=1:0.3"
    assert metrics["npk_ratios_ion"]["N:K"] == "N:K=1:0.5"
    assert metrics["npk_ratios_ion"]["SO4:P"] == "SO4:P=1:0.3"
    assert metrics["npk_ratios_ion"]["CO3:Si"] == "CO3:Si=1:0.5"
    assert metrics["npk_ratios"]["MgO:CaO"] == "MgO:CaO=1:1.4"


@pytest.mark.parametrize(
    "oxide_key, element_key, multiplier",
    [
        ("P2O5", "P", 2.0),
        ("K2O", "K", 2.0),
        ("CaO", "Ca", 1.0),
        ("MgO", "Mg", 1.0),
        ("Na2O", "Na", 2.0),
        ("SO4", "S", 1.0),
    ],
)
def test_oxide_to_element_matches_molar_masses(oxide_key: str, element_key: str, multiplier: float) -> None:
    mm = load_molar_masses()
    result_element, result_mg_l = oxide_to_element_mg_l(mm, oxide_key, 10.0)
    expected = 10.0 * (multiplier * mm[element_key]) / mm[oxide_key]

    assert result_element == element_key
    assert result_mg_l == pytest.approx(expected, rel=0, abs=1e-12)


@pytest.mark.parametrize(
    "oxide_key, element_key",
    [
        ("P2O5", "P"),
        ("K2O", "K"),
        ("CaO", "Ca"),
        ("MgO", "Mg"),
        ("Na2O", "Na"),
        ("SO4", "S"),
    ],
)
def test_oxide_to_element_zero_value_edge_cases(oxide_key: str, element_key: str) -> None:
    mm = load_molar_masses()
    result_element, result_mg_l = oxide_to_element_mg_l(mm, oxide_key, 0.0)

    assert result_element == element_key
    assert result_mg_l == 0.0
