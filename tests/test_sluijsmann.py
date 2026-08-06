import pytest

from horticalc.data_io import load_molar_masses
from horticalc.sluijsmann import compute_sluijsmann


@pytest.mark.parametrize(("mode", "n"), [("arable", 1.0), ("grassland", 0.8)])
def test_sluijsmann_matches_the_declared_formula(mode: str, n: float) -> None:
    molar_masses = load_molar_masses()
    liters = 10.0
    oxides = {
        "CaO": 100.0,
        "MgO": 10.0,
        "K2O": 20.0,
        "Na2O": 5.0,
        "P2O5": 10.0,
        "SO4": 40.0,
        "Cl": 2.0,
    }
    elements = {"N_total": 30.0}

    result = compute_sluijsmann(
        liters=liters,
        oxides_mg_l=oxides,
        elements_mg_l=elements,
        molar_masses=molar_masses,
        config={"mode": mode},
    )

    so3_mg_l = oxides["SO4"] * molar_masses["SO3"] / molar_masses["SO4"]
    expected_terms = {
        "+CaO": oxides["CaO"],
        "+1.4*MgO": 1.4 * oxides["MgO"],
        "+0.6*K2O": 0.6 * oxides["K2O"],
        "+0.9*Na2O": 0.9 * oxides["Na2O"],
        "-0.4*P2O5": -0.4 * oxides["P2O5"],
        "-0.7*SO3": -0.7 * so3_mg_l,
        "-0.8*Cl": -0.8 * oxides["Cl"],
        "-n*N": -n * elements["N_total"],
    }
    expected_e_mg_l = sum(expected_terms.values())

    assert result["mode"] == mode
    assert result["n"] == n
    assert result["inputs_mg_per_l"]["SO3"] == pytest.approx(so3_mg_l, rel=0, abs=1e-12)
    assert result["terms_mg_per_l"] == pytest.approx(expected_terms, rel=0, abs=1e-12)
    assert result["E_mg_CaOeq_per_l"] == pytest.approx(expected_e_mg_l, rel=0, abs=1e-12)
    assert result["E_kg_CaOeq_per_m3"] == pytest.approx(expected_e_mg_l / 1000.0, rel=0, abs=1e-12)
    assert result["E_g_CaOeq_for_batch"] == pytest.approx(expected_e_mg_l * liters / 1000.0, rel=0, abs=1e-12)


@pytest.mark.parametrize(
    ("oxides", "elements", "molar_masses", "expected_so3"),
    [
        ({"SO4": 8.0}, {}, {"SO3": 2.0, "SO4": 4.0, "S": 1.0}, 4.0),
        ({}, {"S": 3.0}, {"SO3": 2.0, "SO4": 4.0, "S": 1.0}, 6.0),
    ],
)
def test_so3_conversion_uses_supplied_molar_masses(
    oxides: dict[str, float],
    elements: dict[str, float],
    molar_masses: dict[str, float],
    expected_so3: float,
) -> None:
    result = compute_sluijsmann(
        liters=1.0,
        oxides_mg_l=oxides,
        elements_mg_l=elements,
        molar_masses=molar_masses,
    )

    assert result["inputs_mg_per_l"]["SO3"] == expected_so3
