import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.sluijsmann import compute_sluijsmann


class SluijsmannTests(unittest.TestCase):
    def setUp(self) -> None:
        self.oxides = {
            "CaO": 227.8977,
            "MgO": 105.3953,
            "K2O": 137.1243,
            "Na2O": 7.1893,
            "P2O5": 63.0,
            "SO4": 257.0333,
            "Cl": 10.6667,
        }
        self.elements = {
            "N_total": 157.1558,
        }

    def test_arable_mode(self) -> None:
        result = compute_sluijsmann(
            liters=10.0,
            oxides_mg_l=self.oxides,
            elements_mg_l=self.elements,
            config={"mode": "arable"},
        )
        self.assertAlmostEqual(result["E_mg_CaOeq_per_l"], 123.34646893681031, places=6)
        self.assertAlmostEqual(result["E_g_CaOeq_for_batch"], 1.2334646893681032, places=6)
        self.assertAlmostEqual(result["n"], 1.0, places=6)

    def test_grassland_mode(self) -> None:
        result = compute_sluijsmann(
            liters=10.0,
            oxides_mg_l=self.oxides,
            elements_mg_l=self.elements,
            config={"mode": "grassland"},
        )
        self.assertAlmostEqual(result["E_mg_CaOeq_per_l"], 154.7776289368103, places=6)
        self.assertAlmostEqual(result["E_g_CaOeq_for_batch"], 1.5477762893681029, places=6)
        self.assertAlmostEqual(result["n"], 0.8, places=6)


if __name__ == "__main__":
    unittest.main()
