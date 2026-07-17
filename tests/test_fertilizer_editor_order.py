from __future__ import annotations

from fastapi.testclient import TestClient

import api.app as api_app
from horticalc.core import COMP_COLS


def test_fertilizer_schema_keeps_nitrogen_form_order() -> None:
    response = TestClient(api_app.app).get("/schema/fertilizer-comp-keys")

    assert response.status_code == 200
    keys = response.json()["keys"]
    assert keys == COMP_COLS
    assert keys.index("NO3") < keys.index("NH4") < keys.index("UREA")


def test_fertilizer_api_uses_liquid_boolean_schema() -> None:
    response = TestClient(api_app.app).get("/fertilizers")

    assert response.status_code == 200
    assert response.json()
    assert all(isinstance(entry["liquid"], bool) for entry in response.json())
    assert all("form" not in entry for entry in response.json())
    assert set(api_app.FertilizerPayload.model_fields) == {
        "name",
        "liquid",
        "weight_factor",
        "comp",
        "solver_role",
        "solver_max_dose_per_l",
    }
