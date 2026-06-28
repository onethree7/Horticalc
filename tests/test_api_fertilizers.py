from __future__ import annotations

import pytest

import api.app as api_app
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
