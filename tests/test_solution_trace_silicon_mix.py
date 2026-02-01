import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.core import compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses, load_recipe, load_water_profile_data
from horticalc.ec import compute_ec


class TestSolutionTraceSiliconMix(unittest.TestCase):
    def test_trace_silicon_mix_snapshot(self) -> None:
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
        actual_elements = {
            key: round(result.elements_mg_l.get(key, 0.0), 6) for key in expected_elements
        }
        self.assertEqual(expected_elements, actual_elements)

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
        self.assertEqual(expected_ions, actual_ions)

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
        self.assertEqual(expected_ec, actual_ec)


if __name__ == "__main__":
    unittest.main()
