from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import api.app as api_app
from horticalc.core import COMP_COLS
from horticalc.data_io import Fertilizer


def test_fertilizer_save_failure_preserves_runtime_catalog(monkeypatch) -> None:
    original = {
        "Existing": Fertilizer(
            name="Existing",
            liquid=False,
            weight_factor=1.0,
            comp={"NO3": 0.1},
        ),
    }
    monkeypatch.setattr(api_app, "FERTILIZERS", original)
    monkeypatch.setattr(api_app, "_ensure_initialized", lambda: None)

    def fail_save(_fertilizers: dict[str, Fertilizer]) -> None:
        raise OSError("disk unavailable")

    monkeypatch.setattr(api_app, "save_fertilizers", fail_save)
    payload = [
        api_app.FertilizerPayload(
            name="Replacement",
            liquid=False,
            weight_factor=1.0,
            comp={"K2O": 0.2},
        ),
    ]

    with pytest.raises(OSError, match="disk unavailable"):
        api_app.put_fertilizers(payload)

    assert api_app.FERTILIZERS is original


def test_fertilizer_solver_max_round_trips_through_api(monkeypatch) -> None:
    saved: dict[str, Fertilizer] = {}
    monkeypatch.setattr(api_app, "_ensure_initialized", lambda: None)
    monkeypatch.setattr(api_app, "FERTILIZERS", {})
    monkeypatch.setattr(api_app, "save_fertilizers", lambda fertilizers: saved.update(fertilizers))

    result = api_app.put_fertilizers(
        [
            api_app.FertilizerPayload(
                name="Limited",
                liquid=True,
                weight_factor=1.0,
                comp={"NO3": 0.1},
                solver_max_dose_per_l=0.125,
            )
        ]
    )

    assert result == {"count": 1}
    assert saved["Limited"].solver_max_dose_per_l == 0.125
    assert api_app.fertilizers()[0]["solver_max_dose_per_l"] == 0.125


@pytest.mark.parametrize("weight", [0, -1])
def test_fertilizer_save_rejects_non_positive_weight(monkeypatch, weight: float) -> None:
    monkeypatch.setattr(api_app, "_ensure_initialized", lambda: None)
    payload = [
        api_app.FertilizerPayload(
            name="Invalid",
            liquid=False,
            weight_factor=weight,
            comp={"NO3": 0.1},
        )
    ]

    with pytest.raises(api_app.HTTPException) as error:
        api_app.put_fertilizers(payload)

    assert error.value.status_code == 400
    assert error.value.detail == "Invalid weight value"


def test_fertilizer_schema_keeps_nitrogen_form_order(api_client: TestClient) -> None:
    response = api_client.get("/schema/fertilizer-comp-keys")

    assert response.status_code == 200
    keys = response.json()["keys"]
    assert keys == COMP_COLS
    assert keys.index("NO3") < keys.index("NH4") < keys.index("UREA")


def test_fertilizer_api_uses_liquid_boolean_schema(api_client: TestClient) -> None:
    response = api_client.get("/fertilizers")

    assert response.status_code == 200
    assert response.json()
    assert all(isinstance(entry["liquid"], bool) for entry in response.json())
    assert all("form" not in entry for entry in response.json())
    assert set(api_app.FertilizerPayload.model_fields) == {
        "name",
        "liquid",
        "weight_factor",
        "comp",
        "solver_max_dose_per_l",
    }
