from fastapi.testclient import TestClient

import api.app as api_app


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
