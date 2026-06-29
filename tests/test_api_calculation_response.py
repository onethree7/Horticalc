from fastapi.testclient import TestClient

import api.app as api_app


def test_calculate_exposes_canonical_result_schema() -> None:
    api_app._ensure_initialized()
    fertilizer_name = next(iter(api_app.FERTILIZERS))
    client = TestClient(api_app.app)
    payload = {
        "liters": 10,
        "fertilizers": [{"name": fertilizer_name, "grams": 1.5}],
        "urea_as_nh4": False,
        "water_mg_l": {"Ca": 5},
        "osmosis_percent": 10,
    }

    response = client.post("/calculate", json=payload)

    expected = api_app.compute_solution(
        {
            "liters": payload["liters"],
            "fertilizers": payload["fertilizers"],
            "urea_as_nh4": payload["urea_as_nh4"],
        },
        api_app.FERTILIZERS,
        api_app.MOLAR_MASSES,
        water_mg_l=dict(payload["water_mg_l"]),
        osmosis_percent=payload["osmosis_percent"],
    ).to_dict()

    assert response.status_code == 200
    assert response.json() == expected
