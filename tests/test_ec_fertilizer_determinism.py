import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.core import compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses


def _recipe_for_grams(grams: float) -> dict:
    return {
        "liters": 10.0,
        "fertilizers": [{"name": "Yara Tera CALCINIT", "grams": grams}],
        "urea_as_nh4": False,
        "phosphate_species": "H2PO4",
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
