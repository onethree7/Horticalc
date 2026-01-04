import math
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.ec import (
    MCCLESKEY_PARAMS,
    FALLBACK_LAMBDA_25,
    compute_ec,
    parse_ion_key,
    _ionic_strength,
    _mccleskey_k,
)


def test_parse_ion_key() -> None:
    assert parse_ion_key("Ca+2") == ("Ca2+", 2)
    assert parse_ion_key("SO4^2-") == ("SO4^2-", -2)
    assert parse_ion_key("NH4+") == ("NH4+", 1)
    assert parse_ion_key("NO3-") == ("NO3-", -1)
    assert parse_ion_key("CO3^2-") == ("CO3^2-", -2)
    assert parse_ion_key("H2PO4-") == ("H2PO4-", -1)


def test_mccleskey_k_matches_k0_at_zero_strength() -> None:
    temp_c = 25.0
    for ion, params in MCCLESKEY_PARAMS.items():
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
