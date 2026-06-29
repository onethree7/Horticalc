import unittest

from horticalc.core import _compute_ion_balance, compute_solution
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
    def test_ion_balance_reports_raw_cbe_and_din_formula(self) -> None:
        balance = _compute_ion_balance(cations_sum=10.0, anions_sum=11.0)

        self.assertAlmostEqual(balance["raw_cbe_percent_signed"], -4.7619047619, places=9)
        self.assertAlmostEqual(balance["raw_cbe_percent_abs"], 4.7619047619, places=9)
        self.assertAlmostEqual(balance["din_38402_62_percent_signed"], -9.5238095238, places=9)
        self.assertAlmostEqual(balance["din_38402_62_percent_abs"], 9.5238095238, places=9)
        self.assertEqual(balance["error_percent_signed"], balance["raw_cbe_percent_signed"])
        self.assertEqual(balance["error_percent_abs"], balance["raw_cbe_percent_abs"])
        self.assertEqual(balance["balance_method"], "non_speciated_major_ion_balance")

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
        self.assertAlmostEqual(
            result.fertilizer_ion_balance["raw_cbe_percent_signed"],
            err_signed,
            places=9,
        )
        self.assertAlmostEqual(
            result.fertilizer_ion_balance["raw_cbe_percent_abs"],
            err_abs,
            places=9,
        )
        self.assertAlmostEqual(
            result.fertilizer_ion_balance["din_38402_62_percent_signed"],
            err_signed * 2.0,
            places=9,
        )
        self.assertAlmostEqual(
            result.fertilizer_ion_balance["din_38402_62_percent_abs"],
            err_abs * 2.0,
            places=9,
        )
        self.assertEqual(
            result.fertilizer_ion_balance["balance_method"],
            "non_speciated_major_ion_balance",
        )

    def test_nh4_is_cation_and_trace_elements_stay_out_of_ions(self) -> None:
        ferts = load_fertilizers()
        molar_masses = load_molar_masses()

        recipe = {
            "liters": 10.0,
            "fertilizers": [
                {"name": "Agrolution pHLow 222 20-20-20+TE", "grams": 5.0},
            ],
            "urea_as_nh4": False,
        }

        result = compute_solution(recipe, ferts, molar_masses, water_mg_l={})

        self.assertIn("NH4+", result.fertilizer_ions_meq_l)
        self.assertGreaterEqual(result.fertilizer_ions_meq_l["NH4+"], 0.0)
        for trace_label in ("Fe", "Mn", "Cu", "Zn", "B", "Mo"):
            self.assertNotIn(trace_label, result.fertilizer_ions_meq_l)

if __name__ == "__main__":
    unittest.main()
