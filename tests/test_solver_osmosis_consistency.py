import json
import unittest

from horticalc.core import compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses
from horticalc.solver import solve_recipe_data

class TestSolverOsmosisConsistency(unittest.TestCase):
    def test_solver_osmosis_consistency(self) -> None:
        ferts = load_fertilizers()
        molar_masses = load_molar_masses()

        water_profile = {
            "mg_per_l": {
                "Ca": 120.0,
                "Mg": 35.0,
                "K": 10.0,
                "P": 4.0,
                "NO3": 20.0,
            }
        }
        recipe = {
            "liters": 10.0,
            "osmosis_percent": 80.0,
            "water_profile": water_profile,
            "targets_mg_per_l": {
                "N_total": 140.0,
                "P": 50.0,
                "K": 200.0,
                "Ca": 160.0,
                "Mg": 50.0,
            },
            "fertilizers_allowed": [
                "Biolchim Green-Go 12-12-36",
                "Yara Tera CALCINIT",
                "K+S EPSO Top Bittersalz 16-39",
            ],
            "urea_as_nh4": False,
        }

        result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)

        recomputed = compute_solution(
            {
                "liters": recipe["liters"],
                "fertilizers": result.fertilizers,
                "urea_as_nh4": recipe["urea_as_nh4"],
            },
            ferts,
            molar_masses,
            water_profile["mg_per_l"],
            osmosis_percent=recipe["osmosis_percent"],
        )

        for key in ("N_total", "P", "K", "Ca", "Mg"):
            expected = result.achieved_elements_mg_l.get(key, 0.0)
            actual = recomputed.elements_mg_l.get(key, 0.0)
            self.assertLessEqual(abs(actual - expected), 1e-6, f"{key} mismatch: {actual} vs {expected}")

    def test_solution_serialization_deterministic(self) -> None:
        ferts = load_fertilizers()
        molar_masses = load_molar_masses()

        recipe = {
            "liters": 5.0,
            "fertilizers": [
                {"name": "Yara Tera CALCINIT", "grams": 5.0},
                {"name": "Biolchim Green-Go 12-12-36", "grams": 3.5},
            ],
            "urea_as_nh4": False,
        }
        water_profile = {
            "Ca": 80.0,
            "Mg": 20.0,
            "NO3": 10.0,
        }

        first = compute_solution(recipe, ferts, molar_masses, water_profile)
        second = compute_solution(recipe, ferts, molar_masses, water_profile)

        for label, payload in (
            ("elements", (first.elements_mg_l, second.elements_mg_l)),
            ("oxides", (first.oxides_mg_l, second.oxides_mg_l)),
            ("ions", (first.ions_mmol_l, second.ions_mmol_l)),
        ):
            first_json = json.dumps(payload[0], sort_keys=True)
            second_json = json.dumps(payload[1], sort_keys=True)
            self.assertEqual(first_json, second_json, f"{label} serialization mismatch")

if __name__ == "__main__":
    unittest.main()
