import unittest

from horticalc.data_io import load_molar_masses
from horticalc.sluijsmann import compute_sluijsmann


class SluijsmannTests(unittest.TestCase):
    def setUp(self) -> None:
        self.molar_masses = load_molar_masses()
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
            molar_masses=self.molar_masses,
            config={"mode": "arable"},
        )
        self.assertAlmostEqual(result["E_mg_CaOeq_per_l"], 123.35015336867821, places=6)
        self.assertAlmostEqual(result["E_g_CaOeq_for_batch"], 1.233501533686782, places=6)
        self.assertAlmostEqual(result["n"], 1.0, places=6)

    def test_grassland_mode(self) -> None:
        result = compute_sluijsmann(
            liters=10.0,
            oxides_mg_l=self.oxides,
            elements_mg_l=self.elements,
            molar_masses=self.molar_masses,
            config={"mode": "grassland"},
        )
        self.assertAlmostEqual(result["E_mg_CaOeq_per_l"], 154.7813133686782, places=6)
        self.assertAlmostEqual(result["E_g_CaOeq_for_batch"], 1.547813133686782, places=6)
        self.assertAlmostEqual(result["n"], 0.8, places=6)

    def test_so3_conversion_uses_supplied_molar_masses(self) -> None:
        cases = (
            ({"SO4": 8.0}, {}, 4.0),
            ({}, {"S": 3.0}, 6.0),
        )

        for oxides, elements, expected_so3 in cases:
            with self.subTest(oxides=oxides, elements=elements):
                result = compute_sluijsmann(
                    liters=1.0,
                    oxides_mg_l=oxides,
                    elements_mg_l=elements,
                    molar_masses={"SO3": 2.0, "SO4": 4.0, "S": 1.0},
                )

                self.assertEqual(result["inputs_mg_per_l"]["SO3"], expected_so3)


if __name__ == "__main__":
    unittest.main()
