from pathlib import Path

import yaml

from horticalc.data_io import load_fertilizers


ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "recipes"
EXPECTED = {
    "athena_blended_clone_feed_10l.yml": [("Athena Bloom B", 26), ("Athena Bloom A", 26), ("Athena Cleanse", 3)],
    "athena_blended_veg_w1_4_10l.yml": [("Athena Grow B", 29), ("Athena Grow A", 29), ("Athena CaMg", 8), ("Athena Cleanse", 5)],
    "athena_blended_bluete_w1_2_10l.yml": [("Athena Bloom B", 32), ("Athena Bloom A", 32), ("Athena CaMg", 8), ("Athena Cleanse", 5)],
    "athena_blended_bluete_w3_10l.yml": [("Athena Bloom B", 32), ("Athena Bloom A", 32), ("Athena PK", 11), ("Athena CaMg", 8), ("Athena Cleanse", 5)],
    "athena_blended_bluete_w4_10l.yml": [("Athena Bloom B", 32), ("Athena Bloom A", 32), ("Athena PK", 16), ("Athena CaMg", 8), ("Athena Cleanse", 5)],
    "athena_blended_bluete_w5_10l.yml": [("Athena Bloom B", 26), ("Athena Bloom A", 26), ("Athena PK", 24), ("Athena CaMg", 8), ("Athena Cleanse", 5)],
    "athena_blended_bluete_w6_10l.yml": [("Athena Bloom B", 24), ("Athena Bloom A", 24), ("Athena PK", 26), ("Athena CaMg", 8), ("Athena Cleanse", 5)],
    "athena_blended_bluete_w7_10l.yml": [("Athena Bloom B", 13), ("Athena Bloom A", 13), ("Athena PK", 32), ("Athena CaMg", 8), ("Athena Cleanse", 5)],
    "athena_blended_bluete_w8_9_ohne_fade_10l.yml": [("Athena Bloom B", 11), ("Athena Bloom A", 11), ("Athena PK", 26), ("Athena Cleanse", 5)],
    "athena_blended_bluete_w8_9_mit_fade_10l.yml": [("Athena PK", 32), ("Athena Fade", 32), ("Athena Cleanse", 5)],
    "athena_pro_clone_feed_weight_10l.yml": [("Athena Pro Bloom 0-12-24", 12.9), ("Athena Pro Core 14-0-0", 7.7), ("Athena Cleanse", 3)],
    "athena_pro_vegetation_w1_4_weight_10l.yml": [("Athena Pro Grow 2-8-20", 20.3), ("Athena Pro Core 14-0-0", 12.2), ("Athena Cleanse", 5)],
    "athena_pro_bluete_w1_7_core_weight_10l.yml": [("Athena Pro Bloom 0-12-24", 20.3), ("Athena Pro Core 14-0-0", 12.2), ("Athena Cleanse", 5)],
    "athena_pro_bluete_w7_fade_optional_weight_10l.yml": [("Athena Pro Bloom 0-12-24", 20.3), ("Athena Pro Fade (Finisher)", 51), ("Athena Cleanse", 5)],
    "athena_pro_bluete_w8_9_fade_weight_10l.yml": [("Athena Pro Bloom 0-12-24", 20.3), ("Athena Pro Fade (Finisher)", 51), ("Athena Cleanse", 5)],
}


def test_athena_recipe_set_matches_manufacturer_schedule() -> None:
    files = {path.name: path for path in RECIPES.glob("athena_*.yml")}
    catalog = load_fertilizers(ROOT / "data" / "fertilizers.csv")

    assert set(files) == set(EXPECTED)
    for filename, expected_fertilizers in EXPECTED.items():
        recipe = yaml.safe_load(files[filename].read_text(encoding="utf-8"))
        actual = [(item["name"], item["grams"]) for item in recipe["fertilizers"]]

        assert recipe["liters"] == 10.0
        assert recipe["water_profile"] == "default"
        assert recipe["phosphate_species"] == "H2PO4"
        assert recipe["urea_as_nh4"] is False
        assert actual == expected_fertilizers
        assert all(name in catalog for name, _ in actual)

    blended_text = "\n".join(path.read_text(encoding="utf-8") for path in files.values() if "blended" in path.name)
    assert not {"12.7", "18.4", "27.6", "29.9", "36.8"} & set(blended_text.split())
