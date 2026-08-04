from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def isolated_solver_history(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import api.app as api_app

    monkeypatch.setattr(api_app, "_solver_history_path", lambda: tmp_path / "solver_history.jsonl")


@pytest.fixture
def api_client(isolated_solver_history: None) -> Iterator[TestClient]:
    import api.app as api_app

    client = TestClient(api_app.app)
    yield client
    client.close()


@pytest.fixture
def api_client_no_raise(isolated_solver_history: None) -> Iterator[TestClient]:
    import api.app as api_app

    client = TestClient(api_app.app, raise_server_exceptions=False)
    yield client
    client.close()
