from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from shutil import copytree

import pytest
from fastapi.testclient import TestClient

import api.app as api_app
from horticalc import paths
from horticalc.activation import clear_activation_handler, configure_activation_token
from horticalc.data_io import load_fertilizers, load_molar_masses
from horticalc.paths import PortableLayout, shipped_fertilizers_path

TEST_SESSION_TOKEN = "t" * 43


@pytest.fixture(autouse=True)
def isolated_app_root(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    sandbox = tmp_path / "app"
    for name in ("data", "recipes"):
        copytree(root / name, sandbox / name)
    monkeypatch.setattr(paths, "app_root", lambda: sandbox)
    return sandbox


def _authenticate(client: TestClient) -> None:
    configure_activation_token(TEST_SESSION_TOKEN)
    response = client.get("/", params={"session": TEST_SESSION_TOKEN}, follow_redirects=False)
    assert response.status_code == 303


@pytest.fixture
def isolated_api_layout(monkeypatch: pytest.MonkeyPatch, isolated_app_root: Path) -> PortableLayout:
    layout = paths.ensure_portable_layout()
    monkeypatch.setattr(api_app, "FERTILIZERS", load_fertilizers(shipped_fertilizers_path(isolated_app_root)))
    monkeypatch.setattr(api_app, "MOLAR_MASSES", load_molar_masses())
    monkeypatch.setattr(api_app, "PORTABLE_LAYOUT", layout)
    return layout


@pytest.fixture
def isolated_solver_history(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import api.app as api_app

    monkeypatch.setattr(api_app, "_solver_history_path", lambda: tmp_path / "solver_history.jsonl")


@pytest.fixture
def api_client(isolated_solver_history: None, isolated_api_layout: PortableLayout) -> Iterator[TestClient]:
    client = TestClient(api_app.app, base_url="http://127.0.0.1")
    _authenticate(client)
    yield client
    client.close()
    clear_activation_handler()


@pytest.fixture
def api_client_no_raise(isolated_solver_history: None, isolated_api_layout: PortableLayout) -> Iterator[TestClient]:
    client = TestClient(api_app.app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    _authenticate(client)
    yield client
    client.close()
    clear_activation_handler()
