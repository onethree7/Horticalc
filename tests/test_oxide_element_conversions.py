import pytest

from horticalc.core import oxide_to_element_mg_l
from horticalc.data_io import load_molar_masses


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
    mg_l_oxide = 10.0

    result_element, result_mg_l = oxide_to_element_mg_l(mm, oxide_key, mg_l_oxide)

    expected = mg_l_oxide * (multiplier * mm[element_key]) / mm[oxide_key]

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
