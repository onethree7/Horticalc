import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.core import compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses


def _ion_charge(label: str) -> int:
    if "^" in label:
        _, charge = label.split("^", 1)
        sign = charge[-1]
        magnitude = int(charge[:-1]) if charge[:-1] else 1
        return magnitude if sign == "+" else -magnitude
    if label.endswith("+2"):
        return 2
    if label.endswith("-2"):
        return -2
    if label.endswith("+"):
        return 1
    if label.endswith("-"):
        return -1
    else:
        raise ValueError(f"Unrecognized ion charge format: {label}")


class TestFertilizerIonBalance(unittest.TestCase):
    def test_fertilizer_ion_balance_matches_charges(self) -> None:
        ferts = load_fertilizers()
        molar_masses = load_molar_masses()

        recipe = {
            "liters": 10.0,
            "fertilizers": [
                {"name": "Yara Tera CALCINIT", "grams": 5.0},
                {"name": "K+S soluSOP 52 Kaliumsulfat 52 (+54)", "grams": 5.0},
            ],
            "urea_as_nh4": False,
            "phosphate_species": "H2PO4",
        }

        result = compute_solution(recipe, ferts, molar_masses, water_mg_l={})

        expected_meq = {
            ion: mmol * _ion_charge(ion)
            for ion, mmol in result.fertilizer_ions_mmol_l.items()
        }

        for ion, expected_value in expected_meq.items():
            actual_value = result.fertilizer_ions_meq_l.get(ion)
            self.assertIsNotNone(actual_value, f"Missing meq/L for {ion}")
            self.assertAlmostEqual(actual_value, expected_value, places=9)

        cations_sum = sum(value for value in expected_meq.values() if value > 0)
        anions_sum = -sum(value for value in expected_meq.values() if value < 0)
        denom = cations_sum + anions_sum
        err_signed = 0.0 if denom == 0 else (cations_sum - anions_sum) / denom * 100.0
        err_abs = abs(err_signed)

        self.assertAlmostEqual(
            result.fertilizer_ion_balance["cations_meq_per_l"],
            cations_sum,
            places=9,
        )
        self.assertAlmostEqual(
            result.fertilizer_ion_balance["anions_meq_per_l"],
            anions_sum,
            places=9,
        )
        self.assertAlmostEqual(
            result.fertilizer_ion_balance["error_percent_signed"],
            err_signed,
            places=9,
        )
        self.assertAlmostEqual(
            result.fertilizer_ion_balance["error_percent_abs"],
            err_abs,
            places=9,
        )


if __name__ == "__main__":
    unittest.main()
