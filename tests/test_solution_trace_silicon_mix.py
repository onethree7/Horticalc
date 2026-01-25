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
            "B": 1.85544,
            "Cu": 3.00068,
            "Fe": 7.00204,
            "Mn": 8.15068,
            "Si": 33.870464,
            "Zn": 5.25,
        }
        actual_elements = {
            key: round(result.elements_mg_l.get(key, 0.0), 6) for key in expected_elements
        }
        self.assertEqual(expected_elements, actual_elements)

        expected_ions = {
            "NH4+": 0.000377,
            "K+": 0.02261,
            "Ca+2": 0.90773,
            "Mg+2": 0.461112,
            "Na+": 0.236627,
            "NO3-": 0.010967,
            "SO4^2-": 0.528405,
            "Cl-": 0.306911,
            "HCO3-": 1.722935,
        }
        actual_ions = {key: round(result.ions_mmol_l.get(key, 0.0), 6) for key in expected_ions}
        self.assertEqual(expected_ions, actual_ions)

        ec = compute_ec(result.ions_mmol_l)
        expected_ec = {
            "ionic_strength_mol_per_kg": 0.004945,
            "ec_mS_per_cm": {"18.0": 0.275871, "25.0": 0.322263},
            "ec_uS_per_cm": {"18.0": 275.871073, "25.0": 322.263372},
        }
        actual_ec = {
            "ionic_strength_mol_per_kg": round(ec["ionic_strength_mol_per_kg"], 6),
            "ec_mS_per_cm": {key: round(value, 6) for key, value in ec["ec_mS_per_cm"].items()},
            "ec_uS_per_cm": {key: round(value, 6) for key, value in ec["ec_uS_per_cm"].items()},
        }
        self.assertEqual(expected_ec, actual_ec)


if __name__ == "__main__":
    unittest.main()
