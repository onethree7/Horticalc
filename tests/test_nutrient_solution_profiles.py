from __future__ import annotations

from pathlib import Path

from horticalc.data_io import load_molar_masses, load_nutrient_solution_data

ROOT = Path(__file__).resolve().parents[1]
PROFILE_DIR = ROOT / "data" / "nutrient_solutions"
EXPECTED_PROFILE_FILENAMES = {
    "Abram_Steiner_Hydrokultur_Naehrloesung.yml",
    "Bugbee_Utah_Hydroponic_Cannabis_2022.yml",
    "Conn_2013_Arabidopsis.yml",
    "Cooper_NFT_1979.yml",
    "Crone_1902_Original.yml",
    "DeLaRosa_2025_Lettuce_T2_HighNitrate.yml",
    "DeLaRosa_2025_Lettuce_T3_HighSulfate.yml",
    "DeLaRosa_2025_Lettuce_T4_HighPotassium.yml",
    "DeLaRosa_2025_Lettuce_T5_HighCalcium.yml",
    "Gong_2024_Lettuce_Validation_T1.yml",
    "Hermans_2010_Arabidopsis.yml",
    "Hoagland_Arnon_1950_Solution1_Nitrate.yml",
    "Hoagland_Arnon_1950_Solution2_50pct_Arabidopsis_2020.yml",
    "Hoagland_Arnon_1950_Solution2_AmmoniumPhosphate.yml",
    "Houston_2023_Arugula_Replenishment.yml",
    "Houston_2023_Basil_Replenishment.yml",
    "Knop_1861_Standard.yml",
    "Long_Ashton_Nutrient_Solution_LANS_NitrateType.yml",
    "Murashige_Skoog_MS_1962_FullStrength.yml",
    "Pfeffer_1900_Original.yml",
    "Sachs_1860_Original.yml",
    "Saloner_Bernstein_Cannabis_NPK_Target_Optimization.yml",
    "Sapkota_2019_Lettuce_N3.yml",
    "Somerville_Ogren_1982_Arabidopsis.yml",
    "Sonneveld_Voogt_2009_Cucumber_Closed_Supply.yml",
    "Sonneveld_Voogt_2009_Tomato_Closed_Supply.yml",
    "Sonneveld_Voogt_2009_Tomato_Free_Drainage_Supply.yml",
    "Tocquin_2003_Arabidopsis.yml",
    "Yeo_2023_Paprika_NIHHS_Coir_Groups1_2.yml",
    "Yeo_2023_Paprika_NIHHS_Coir_Groups3_6.yml",
    "Yoshida_Rice_Solution_1976_CommonVariant.yml",
}


def _profile_paths() -> list[Path]:
    return sorted(PROFILE_DIR.glob("*.yml"))


def test_shipped_catalogue_contains_all_evidence_backed_profiles() -> None:
    filenames = {path.name for path in _profile_paths()}

    assert filenames == EXPECTED_PROFILE_FILENAMES


def test_loader_returns_only_runtime_profile_fields() -> None:
    data = load_nutrient_solution_data(PROFILE_DIR / "Tocquin_2003_Arabidopsis.yml")

    assert set(data) == {"name", "source", "targets_mg_per_l"}
    assert "10.1186/s13007-020-00606-4" in data["source"]


def test_explicitly_accepted_user_provided_profiles_keep_their_provenance() -> None:
    for filename in (
        "Bugbee_Utah_Hydroponic_Cannabis_2022.yml",
        "Saloner_Bernstein_Cannabis_NPK_Target_Optimization.yml",
    ):
        data = load_nutrient_solution_data(PROFILE_DIR / filename)
        assert data["source"] == "User provided dataset"


def test_steiner_matches_reported_element_table_including_micronutrients() -> None:
    data = load_nutrient_solution_data(PROFILE_DIR / "Abram_Steiner_Hydrokultur_Naehrloesung.yml")

    assert "10.2478/fhort-2024-0017" in data["source"]
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


def test_saloner_profile_matches_the_explicitly_accepted_user_dataset() -> None:
    data = load_nutrient_solution_data(PROFILE_DIR / "Saloner_Bernstein_Cannabis_NPK_Target_Optimization.yml")

    assert data["source"] == "User provided dataset"
    assert data["targets_mg_per_l"] == {
        "N_total": 160.0,
        "N_NH4": 32.0,
        "N_NO3": 128.0,
        "N_UREA": 0.0,
        "P": 30.0,
        "K": 100.0,
        "Ca": 119.8,
        "Mg": 35.2,
        "Na": 0.0,
        "S": 0.0,
        "Si": 0.0,
        "Cl": 0.0,
        "Fe": 1.67535,
        "Mn": 1.09876,
        "Zn": 0.39228,
        "Cu": 0.0508368,
        "Mo": 0.028785,
        "B": 0.09729,
        "HCO3": 0.0,
    }


def test_sonneveld_voogt_tomato_closed_profile_is_derived_from_source_mmol_per_l() -> None:
    data = load_nutrient_solution_data(PROFILE_DIR / "Sonneveld_Voogt_2009_Tomato_Closed_Supply.yml")
    mm = load_molar_masses()
    source_mmol_per_l = {
        "N_NO3": (10.75, "N"),
        "N_NH4": (1.0, "N"),
        "P": (1.25, "P"),
        "K": (6.5, "K"),
        "Ca": (2.75, "Ca"),
        "Mg": (1.0, "Mg"),
        "S": (1.5, "S"),
    }
    expected = {
        key: round(amount_mmol_l * mm[element], 6) for key, (amount_mmol_l, element) in source_mmol_per_l.items()
    }
    expected["N_total"] = expected["N_NO3"] + expected["N_NH4"]
    expected["N_UREA"] = 0.0

    assert "Sonneveld and Voogt (2009)" in data["source"]
    assert "10.1007/978-90-481-2532-6" in data["source"]
    assert data["targets_mg_per_l"] == expected
