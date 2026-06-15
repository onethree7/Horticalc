from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
import yaml

from horticalc.data_io import (
    load_molar_masses,
    load_nutrient_solution_data,
    nutrient_solution_targets_from_basis,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "data" / "nutrient_solutions"
BERNSTEIN_SHA256 = "a0bbb4c22fdb8abc26fe6b99a36f5e9bedf29c79a4528fc38f396342694ba988"
UNCITED_LEGACY_PROFILES = {
    "Bugbee_Utah_Hydroponic_Cannabis_2022.yml",
    "Saloner_Bernstein_Cannabis_NPK_Target_Optimization.yml",
}


def _profile_paths() -> list[Path]:
    return sorted(PROFILE_DIR.glob("*.yml"))


def test_shipped_catalogue_contains_all_evidence_backed_profiles() -> None:
    filenames = {path.name for path in _profile_paths()}

    assert len(filenames) == 31
    assert {
        "Sachs_1860_Original.yml",
        "Knop_1861_Standard.yml",
        "Pfeffer_1900_Original.yml",
        "Crone_1902_Original.yml",
        "Hoagland_Arnon_1950_Solution1_Nitrate.yml",
        "Hoagland_Arnon_1950_Solution2_AmmoniumPhosphate.yml",
        "Murashige_Skoog_MS_1962_FullStrength.yml",
        "Somerville_Ogren_1982_Arabidopsis.yml",
        "Tocquin_2003_Arabidopsis.yml",
        "Hermans_2010_Arabidopsis.yml",
        "Conn_2013_Arabidopsis.yml",
        "Hoagland_Arnon_1950_Solution2_50pct_Arabidopsis_2020.yml",
        "Long_Ashton_Nutrient_Solution_LANS_NitrateType.yml",
        "Abram_Steiner_Hydrokultur_Naehrloesung.yml",
        "Yoshida_Rice_Solution_1976_CommonVariant.yml",
        "Cooper_NFT_1979.yml",
        "Sonneveld_Voogt_2009_Tomato_Closed_Supply.yml",
        "Sonneveld_Voogt_2009_Tomato_Free_Drainage_Supply.yml",
        "Sonneveld_Voogt_2009_Cucumber_Closed_Supply.yml",
        "Houston_2023_Arugula_Replenishment.yml",
        "Houston_2023_Basil_Replenishment.yml",
        "Yeo_2023_Paprika_NIHHS_Coir_Groups1_2.yml",
        "Yeo_2023_Paprika_NIHHS_Coir_Groups3_6.yml",
        "Sapkota_2019_Lettuce_N3.yml",
        "DeLaRosa_2025_Lettuce_T2_HighNitrate.yml",
        "DeLaRosa_2025_Lettuce_T3_HighSulfate.yml",
        "DeLaRosa_2025_Lettuce_T4_HighPotassium.yml",
        "DeLaRosa_2025_Lettuce_T5_HighCalcium.yml",
        "Gong_2024_Lettuce_Validation_T1.yml",
    } <= filenames


@pytest.mark.parametrize(
    "path",
    [path for path in _profile_paths() if path.name not in UNCITED_LEGACY_PROFILES],
    ids=lambda path: path.stem,
)
def test_profile_targets_recalculate_from_documented_basis(path: Path) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    calculated = nutrient_solution_targets_from_basis(
        data["original_basis"], load_molar_masses()
    )

    assert data["reference"]["source_url"]
    assert data["verification"]["independent_recalculation"] is True
    assert "SO4" not in data["targets_mg_per_l"]
    assert calculated.keys() == data["targets_mg_per_l"].keys()
    for key, expected in data["targets_mg_per_l"].items():
        assert calculated[key] == pytest.approx(expected, abs=1e-5)


def test_loader_preserves_provenance_metadata() -> None:
    data = load_nutrient_solution_data(PROFILE_DIR / "Tocquin_2003_Arabidopsis.yml")

    assert data["crop"] == "Arabidopsis thaliana"
    assert data["reference"]["doi_or_isbn"] == "10.1186/s13007-020-00606-4"
    assert data["original_basis"]["element_mmol_per_l"]["S"] == 0.52


def test_steiner_matches_reported_element_table_including_micronutrients() -> None:
    data = load_nutrient_solution_data(
        PROFILE_DIR / "Abram_Steiner_Hydrokultur_Naehrloesung.yml"
    )

    assert data["reference"]["doi_or_isbn"] == "10.2478/fhort-2024-0017"
    assert data["original_basis"]["units"] == "mg/L at 100% strength"
    assert data["targets_mg_per_l"] == {
        "N_total": 168.0,
        "N_NO3": 168.0,
        "N_NH4": 0.0,
        "N_UREA": 0.0,
        "P": 31.0,
        "K": 273.0,
        "Ca": 180.0,
        "Mg": 48.0,
        "S": 112.0,
        "Fe": 5.0,
        "Cu": 0.02,
        "Zn": 0.11,
        "Mn": 0.62,
        "B": 0.44,
        "Mo": 0.10,
    }


def test_bernstein_profile_is_unchanged() -> None:
    path = PROFILE_DIR / "Saloner_Bernstein_Cannabis_NPK_Target_Optimization.yml"
    assert sha256(path.read_bytes()).hexdigest() == BERNSTEIN_SHA256
