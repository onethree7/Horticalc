from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

import api.app as api_app
from horticalc import paths
from horticalc.solver_history import (
    SOLVER_HISTORY_SCHEMA_VERSION,
    append_solver_history,
    clear_solver_history,
    load_solver_history,
    solver_history_entry,
    solver_history_summaries,
    trim_solver_history,
)


def _entry(entry_id: str, created_at: str) -> dict:
    return {
        "schema_version": SOLVER_HISTORY_SCHEMA_VERSION,
        "id": entry_id,
        "created_at": created_at,
        "setup": {"liters": 10},
        "result": {
            "liters": 10,
            "solver_model": "mass_nnls",
            "targets_mg_per_l": {"N_total": 100, "P": 20, "K": 150},
            "fertilizers": [{"name": "A", "grams": 1}],
        },
    }


def test_history_retention_order_detail_and_clear(tmp_path: Path) -> None:
    history_path = tmp_path / "solver_history.jsonl"
    append_solver_history(history_path, _entry("first", "2026-01-01T00:00:00+00:00"), 2)
    append_solver_history(history_path, _entry("second", "2026-01-02T00:00:00+00:00"), 2)
    append_solver_history(history_path, _entry("third", "2026-01-03T00:00:00+00:00"), 2)

    assert [entry["id"] for entry in load_solver_history(history_path)] == ["second", "third"]
    assert [entry["id"] for entry in solver_history_summaries(history_path)] == ["third", "second"]
    assert solver_history_entry(history_path, "second")["created_at"] == "2026-01-02T00:00:00+00:00"
    assert solver_history_entry(history_path, "missing") is None

    clear_solver_history(history_path)
    assert load_solver_history(history_path) == []
    assert not history_path.exists()


def test_history_skips_corrupt_lines_and_trims_to_zero(tmp_path: Path, caplog) -> None:
    history_path = tmp_path / "solver_history.jsonl"
    history_path.write_text(
        json.dumps(_entry("valid", "2026-01-01T00:00:00+00:00")) + "\n{broken\n{}\n",
        encoding="utf-8",
    )

    assert [entry["id"] for entry in load_solver_history(history_path)] == ["valid"]
    assert "Skipping invalid solver history" in caplog.text
    assert trim_solver_history(history_path, 0) == 0
    assert not history_path.exists()


def test_solver_history_api_records_success_and_exposes_routes(monkeypatch, tmp_path: Path) -> None:
    api_app._ensure_initialized()
    layout = api_app._portable_layout()
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", replace(layout, root=tmp_path, user=tmp_path / "user"))
    client = TestClient(api_app.app)
    assert client.put("/preferences", json={"solver_history_limit": 1000}).status_code == 200

    failed = client.post("/solve", json={"targets": {"INVALID": 1}})
    successful = client.post(
        "/solve",
        json={
            "liters": 10,
            "targets": {"N_total": 20},
            "water_profile": {"mg_per_l": {"Ca": 5}, "osmosis_percent": 10},
            "fertilizers_allowed": ["Compo Basfoliar Top-N SL"],
            "solver_config": {"solver_model": "mass_nnls"},
        },
    )

    assert failed.status_code == 400
    assert successful.status_code == 200
    listing = client.get("/solver-history")
    assert listing.status_code == 200
    assert listing.json()["limit"] == 1000
    assert len(listing.json()["entries"]) == 1

    entry_id = listing.json()["entries"][0]["id"]
    detail = client.get(f"/solver-history/{entry_id}")
    assert detail.status_code == 200
    assert detail.json()["setup"]["water_profile"]["mg_per_l"] == {"Ca": 5.0}
    assert detail.json()["result"] == successful.json()
    assert detail.json()["calculation"]["ec"]

    assert client.delete("/solver-history").status_code == 200
    assert client.get("/solver-history").json()["entries"] == []


def test_history_limit_preference_trims_immediately(monkeypatch, tmp_path: Path) -> None:
    api_app._ensure_initialized()
    layout = api_app._portable_layout()
    monkeypatch.setattr(paths, "app_root", lambda: tmp_path)
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", replace(layout, root=tmp_path, user=tmp_path / "user"))
    history_path = api_app._solver_history_path()
    append_solver_history(history_path, _entry("first", "2026-01-01T00:00:00+00:00"), 1000)
    append_solver_history(history_path, _entry("second", "2026-01-02T00:00:00+00:00"), 1000)

    client = TestClient(api_app.app)
    assert client.put("/preferences", json={"solver_history_limit": 1}).status_code == 200
    assert [entry["id"] for entry in load_solver_history(history_path)] == ["second"]
    assert client.put("/preferences", json={"solver_history_limit": 0}).status_code == 200
    assert not history_path.exists()
    assert client.put("/preferences", json={"solver_history_limit": 10001}).status_code == 422


def test_history_write_failure_does_not_fail_successful_solve(monkeypatch) -> None:
    api_app._ensure_initialized()

    def fail_write(*_args, **_kwargs):
        raise OSError("disk unavailable")

    monkeypatch.setattr(api_app, "_effective_solver_history_limit", lambda *_args, **_kwargs: 1000)
    monkeypatch.setattr(api_app, "append_solver_history", fail_write)
    response = TestClient(api_app.app).post(
        "/solve",
        json={
            "targets": {"N_total": 20},
            "water_profile": {"mg_per_l": {}, "osmosis_percent": 0},
            "fertilizers_allowed": ["Compo Basfoliar Top-N SL"],
            "solver_config": {"solver_model": "mass_nnls"},
        },
    )

    assert response.status_code == 200
    assert response.json()["solver_model"] == "mass_nnls"
