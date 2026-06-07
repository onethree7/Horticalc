
import pytest

from horticalc.core import augment_water_profile_with_elements, normalize_water_profile, oxide_to_element_mg_l
from horticalc.data_io import load_molar_masses

def test_oxide_to_element_helper_matches_internal_rules() -> None:
    mm = load_molar_masses()

    p_element, p_mg_l = oxide_to_element_mg_l(mm, "P2O5", 10.0)
    k_element, k_mg_l = oxide_to_element_mg_l(mm, "K2O", 10.0)
    na_element, na_mg_l = oxide_to_element_mg_l(mm, "Na2O", 10.0)

    assert p_element == "P"
    assert k_element == "K"
    assert na_element == "Na"

    assert p_mg_l == pytest.approx(10.0 * (2 * mm["P"]) / mm["P2O5"], rel=0, abs=1e-12)
    assert k_mg_l == pytest.approx(10.0 * (2 * mm["K"]) / mm["K2O"], rel=0, abs=1e-12)
    assert na_mg_l == pytest.approx(10.0 * (2 * mm["Na"]) / mm["Na2O"], rel=0, abs=1e-12)

def test_augment_water_profile_adds_element_forms_from_normalized_profile() -> None:
    mm = load_molar_masses()
    normalized = normalize_water_profile(mm, {"P": 5.0, "K": 10.0, "SO4": 12.0})

    augmented = augment_water_profile_with_elements(mm, normalized)

    p2o5_mg_l = normalized["P2O5"]
    k2o_mg_l = normalized["K2O"]
    so4_mg_l = normalized["SO4"]

    assert augmented["P"] == pytest.approx(p2o5_mg_l * (2 * mm["P"]) / mm["P2O5"], rel=0, abs=1e-12)
    assert augmented["PO4"] == pytest.approx(p2o5_mg_l * (2 * mm["PO4"]) / mm["P2O5"], rel=0, abs=1e-12)
    assert augmented["K"] == pytest.approx(k2o_mg_l * (2 * mm["K"]) / mm["K2O"], rel=0, abs=1e-12)
    assert augmented["S"] == pytest.approx(so4_mg_l * mm["S"] / mm["SO4"], rel=0, abs=1e-12)

def test_normalize_water_profile_converts_po4_to_p2o5() -> None:
    mm = load_molar_masses()
    normalized = normalize_water_profile(mm, {"PO4": 7.5})

    expected_p2o5 = 7.5 * mm["P2O5"] / (2 * mm["PO4"])

    assert normalized["P2O5"] == pytest.approx(expected_p2o5, rel=0, abs=1e-12)

def test_normalize_water_profile_converts_p_to_p2o5() -> None:
    mm = load_molar_masses()
    normalized = normalize_water_profile(mm, {"P": 5.0})

    expected_p2o5 = 5.0 * mm["P2O5"] / (2 * mm["P"])

    assert normalized["P2O5"] == pytest.approx(expected_p2o5, rel=0, abs=1e-12)

def test_normalize_water_profile_converts_s_to_so4() -> None:
    mm = load_molar_masses()
    normalized = normalize_water_profile(mm, {"S": 3.2})

    expected_so4 = 3.2 * mm["SO4"] / mm["S"]

    assert normalized["SO4"] == pytest.approx(expected_so4, rel=0, abs=1e-12)

def test_normalize_water_profile_converts_alkalinity_to_hco3() -> None:
    mm = load_molar_masses()
    normalized = normalize_water_profile(mm, {"KH": 4.0, "CaCO3": 120.0})

    expected_hco3_from_caco3 = 120.0 * mm["HCO3"] / (mm["CaCO3"] / 2.0)
    expected_hco3_from_kh = (4.0 * 17.848) * mm["HCO3"] / (mm["CaCO3"] / 2.0)

    assert normalized["HCO3"] == pytest.approx(expected_hco3_from_caco3 + expected_hco3_from_kh, rel=0, abs=1e-12)
