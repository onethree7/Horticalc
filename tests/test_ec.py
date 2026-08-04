import math

import pytest

from horticalc.core import compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses
from horticalc.ec import (
    FALLBACK_LAMBDA_25,
    MCCLESKEY_PARAMS,
    _ionic_strength,
    _mccleskey_k,
    compute_ec,
    parse_ion_key,
)


def test_parse_ion_key() -> None:
    assert parse_ion_key("Ca+2") == ("Ca2+", 2)
    assert parse_ion_key("SO4^2-") == ("SO4^2-", -2)
    assert parse_ion_key("NH4+") == ("NH4+", 1)
    assert parse_ion_key("NO3-") == ("NO3-", -1)
    assert parse_ion_key("CO3^2-") == ("CO3^2-", -2)
    assert parse_ion_key("H2PO4-") == ("H2PO4-", -1)


def test_invalid_ion_diagnostics_are_in_english() -> None:
    with pytest.raises(ValueError, match="Unknown ion format"):
        parse_ion_key("invalid")

    result = compute_ec({"invalid": 1.0}, temps_c=(25.0,), include_atc_to_25=False)
    assert result["warnings"] == [
        "Ion 'invalid' could not be parsed and was ignored.",
        "Total EC at 25.0°C is 0; transport numbers = 0.",
    ]


def test_mccleskey_k_matches_k0_at_zero_strength() -> None:
    temp_c = 25.0
    for _ion, params in MCCLESKEY_PARAMS.items():
        expected = params.k0[0] * temp_c * temp_c + params.k0[1] * temp_c + params.k0[2]
        assert _mccleskey_k(params, temp_c, 0.0) == pytest.approx(expected, rel=0, abs=1e-12)


def test_mccleskey_k_small_strength_example() -> None:
    temp_c = 25.0
    ionic_strength = 0.01
    params = MCCLESKEY_PARAMS["K+"]
    k0 = params.k0[0] * temp_c * temp_c + params.k0[1] * temp_c + params.k0[2]
    A = params.A[0] * temp_c * temp_c + params.A[1] * temp_c + params.A[2]
    expected = k0 - (A * math.sqrt(ionic_strength)) / (1 + params.B * math.sqrt(ionic_strength))
    assert _mccleskey_k(params, temp_c, ionic_strength) == pytest.approx(expected, rel=0, abs=1e-12)


def test_ionic_strength() -> None:
    molalities = {"Ca2+": 0.001, "Cl-": 0.001}
    charges = {"Ca2+": 2, "Cl-": -1}
    expected = 0.0025
    assert _ionic_strength(molalities, charges) == pytest.approx(expected, rel=0, abs=1e-12)


def test_fallback_h2po4() -> None:
    ions = {"H2PO4-": 1.0}
    result = compute_ec(
        ions,
        temps_c=(18.0, 25.0),
        density_kg_per_l=1.0,
        fallback_temp_beta_per_c=0.022,
        include_breakdown=True,
        include_transport_numbers=False,
        include_atc_to_25=False,
    )
    lambda_25 = FALLBACK_LAMBDA_25["H2PO4-"]
    contrib_25 = lambda_25 * 0.001
    assert result["contrib_mS_per_cm"]["25.0"]["H2PO4-"] == pytest.approx(contrib_25, rel=0, abs=1e-9)

    lambda_18 = lambda_25 * (1 + 0.022 * (18.0 - 25.0))
    contrib_18 = lambda_18 * 0.001
    assert result["contrib_mS_per_cm"]["18.0"]["H2PO4-"] == pytest.approx(contrib_18, rel=0, abs=1e-9)


def test_transport_numbers_sum_to_one() -> None:
    ions = {"K+": 10.0, "NO3-": 10.0}
    result = compute_ec(
        ions,
        temps_c=(25.0,),
        include_breakdown=True,
        include_transport_numbers=True,
        include_atc_to_25=False,
    )
    tnums = result["transport_numbers"]["25.0"]
    assert sum(tnums.values()) == pytest.approx(1.0, rel=0, abs=1e-12)


def test_aliases_accumulate_and_unsupported_ions_warn_once_across_temperatures() -> None:
    aliased = compute_ec({"Ca+2": 1.0, "Ca2+": 2.0}, temps_c=(25.0,), include_atc_to_25=False)
    canonical = compute_ec({"Ca2+": 3.0}, temps_c=(25.0,), include_atc_to_25=False)
    assert aliased["ec_mS_per_cm"] == pytest.approx(canonical["ec_mS_per_cm"])

    unsupported = compute_ec({"Li+": 1.0}, temps_c=(18.0, 25.0), include_atc_to_25=False)
    warnings = [warning for warning in unsupported["warnings"] if "no McCleskey" in warning]
    assert warnings == ["Ion 'Li+' has no McCleskey or fallback parameters and was ignored."]
    assert unsupported["coverage"]["ignored_ions"] == ["Li+"]


@pytest.mark.parametrize("density", [0, -1, float("nan"), float("inf")])
def test_ec_rejects_invalid_density(density: float) -> None:
    with pytest.raises(ValueError, match="density_kg_per_l"):
        compute_ec({"K+": 1.0}, density_kg_per_l=density)


def _recipe_for_grams(grams: float) -> dict:
    return {
        "liters": 10.0,
        "fertilizers": [{"name": "Yara Tera CALCINIT", "grams": grams}],
        "urea_as_nh4": False,
    }


def _fertilizer_ec_25c(result: dict) -> float:
    return result["ec_fertilizer"]["ec_mS_per_cm"]["25.0"]


def test_ec_fertilizer_increases_and_is_deterministic() -> None:
    ferts = load_fertilizers()
    molar_masses = load_molar_masses()

    low_result = compute_solution(_recipe_for_grams(1.0), ferts, molar_masses, {}).to_dict()
    high_result = compute_solution(_recipe_for_grams(4.0), ferts, molar_masses, {}).to_dict()

    assert _fertilizer_ec_25c(high_result) > _fertilizer_ec_25c(low_result)

    repeat_low = compute_solution(_recipe_for_grams(1.0), ferts, molar_masses, {}).to_dict()
    assert repeat_low["ec_fertilizer"] == low_result["ec_fertilizer"]
