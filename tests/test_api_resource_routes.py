from fastapi.testclient import TestClient

import api.app as api_app
from horticalc import paths


def test_portable_layout_resource_routes() -> None:
    client = TestClient(api_app.app)

    responses = {
        "water profiles": client.get("/water-profiles"),
        "default water profile": client.get("/water-profiles/default"),
        "nutrient solutions": client.get("/nutrient-solutions"),
        "nutrient solution": client.get("/nutrient-solutions/Cooper_NFT_1979"),
        "default recipe": client.get("/recipes/default"),
        "recipe": client.get("/recipes/golden"),
    }

    assert {name: response.status_code for name, response in responses.items()} == {
        name: 200 for name in responses
    }


def test_resource_routes_layer_user_yaml_over_shipped_defaults(monkeypatch, tmp_path) -> None:
    shipped_water = tmp_path / "data" / "water_profiles"
    shipped_targets = tmp_path / "data" / "nutrient_solutions"
    shipped_recipes = tmp_path / "recipes"
    for directory in (shipped_water, shipped_targets, shipped_recipes):
        directory.mkdir(parents=True)

    (shipped_water / "tap.yml").write_text(
        "name: Shipped tap\nmg_per_l: {}\n",
        encoding="utf-8",
    )
    (shipped_targets / "target.yml").write_text(
        "name: Shipped target\ntargets_mg_per_l: {}\n",
        encoding="utf-8",
    )
    (shipped_recipes / "default.yml").write_text(
        "name: Shipped default\nliters: 10\nfertilizers: []\n",
        encoding="utf-8",
    )
    (shipped_recipes / "golden.yml").write_text(
        "name: Shipped golden\nliters: 10\nfertilizers: []\n",
        encoding="utf-8",
    )

    user_water = paths.user_water_profiles_dir(tmp_path)
    user_targets = paths.user_nutrient_solutions_dir(tmp_path)
    user_recipes = paths.user_recipes_dir(tmp_path)
    for directory in (user_water, user_targets, user_recipes):
        directory.mkdir(parents=True)
    (user_water / "tap.yml").write_text(
        "name: User tap\nmg_per_l: {Ca: 42}\n",
        encoding="utf-8",
    )
    (user_targets / "custom.yml").write_text(
        "name: User target\ntargets_mg_per_l: {N_total: 100}\n",
        encoding="utf-8",
    )
    (user_recipes / "golden.yml").write_text(
        "name: User golden\nliters: 20\nfertilizers: []\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", paths.ensure_portable_layout(tmp_path))
    client = TestClient(api_app.app)

    assert client.get("/water-profiles").json() == [
        {"name": "User tap", "filename": "tap.yml"}
    ]
    assert {entry["filename"] for entry in client.get("/nutrient-solutions").json()} == {
        "custom.yml",
        "target.yml",
    }
    assert client.get("/water-profiles/tap").json()["mg_per_l"] == {"Ca": 42.0}
    assert client.get("/recipes/golden").json()["name"] == "User golden"
    assert client.get("/recipes/default").json()["name"] == "Shipped default"
