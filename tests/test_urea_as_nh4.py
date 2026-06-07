import unittest

from horticalc.core import compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses, load_recipe, load_water_profile_data
from horticalc.paths import repo_root

class TestUreaAsNh4(unittest.TestCase):
    def test_urea_as_nh4_rebalances_nitrogen_forms(self) -> None:
        ferts = load_fertilizers()
        molar_masses = load_molar_masses()
        recipe_path = repo_root() / "recipes" / "urea_n_mix.yml"
        recipe = load_recipe(recipe_path)

        water_profile_name = recipe.get("water_profile", "default")
        water_profile_path = repo_root() / "data" / "water_profiles" / f"{water_profile_name}.yml"
        water_profile = load_water_profile_data(water_profile_path)
        water_mg_l = water_profile.get("mg_per_l", {})

        results = {}
        for flag in (False, True):
            recipe_run = dict(recipe)
            recipe_run["urea_as_nh4"] = flag
            results[flag] = compute_solution(recipe_run, ferts, molar_masses, water_mg_l)

        elements_false = results[False].elements_mg_l
        elements_true = results[True].elements_mg_l

        self.assertAlmostEqual(elements_false["N_total"], elements_true["N_total"], places=6)
        self.assertAlmostEqual(elements_false["N_NO3"], elements_true["N_NO3"], places=6)
        self.assertGreater(elements_true["N_NH4"], elements_false["N_NH4"])
        self.assertGreater(elements_false["N_UREA"], elements_true["N_UREA"])
        self.assertLessEqual(elements_true["N_UREA"], 1e-6)

if __name__ == "__main__":
    unittest.main()
