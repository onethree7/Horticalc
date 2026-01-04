import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.core import _compute_sluijsmann


class TestSluijsmann(unittest.TestCase):
    def test_sluijsmann_arable(self) -> None:
        oxides = {
            "CaO": 227.8977,
            "MgO": 105.3953,
            "K2O": 137.1243,
            "Na2O": 7.1893,
            "P2O5": 63.0,
            "SO4": 257.0333,
            "Cl": 10.6667,
        }
        elements = {
            "N_total": 157.1558,
        }
        result = _compute_sluijsmann({"sluijsmann": {"mode": "arable"}}, oxides, elements, liters=10.0)
        self.assertAlmostEqual(result["inputs_mg_per_l"]["SO3"], 214.2292, places=4)
        self.assertAlmostEqual(result["E_mg_CaOeq_per_l"], 123.3466, places=3)
        self.assertAlmostEqual(result["E_g_CaOeq_for_batch"], 1.233466, places=5)

    def test_sluijsmann_grassland(self) -> None:
        oxides = {
            "CaO": 227.8977,
            "MgO": 105.3953,
            "K2O": 137.1243,
            "Na2O": 7.1893,
            "P2O5": 63.0,
            "SO4": 257.0333,
            "Cl": 10.6667,
        }
        elements = {
            "N_total": 157.1558,
        }
        result = _compute_sluijsmann({"sluijsmann": {"mode": "grassland"}}, oxides, elements, liters=10.0)
        self.assertAlmostEqual(result["E_mg_CaOeq_per_l"], 154.7777, places=3)
        self.assertAlmostEqual(result["E_g_CaOeq_for_batch"], 1.547777, places=5)


if __name__ == "__main__":
    unittest.main()
