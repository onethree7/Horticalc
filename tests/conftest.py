from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_solver_history(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    import api.app as api_app

    monkeypatch.setattr(api_app, "_solver_history_path", lambda: tmp_path / "solver_history.jsonl")
