from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))

from fastapi.testclient import TestClient

from horticalc.core import COMP_COLS

spec = importlib.util.spec_from_file_location("api_app", ROOT / "api" / "app.py")
api_app = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(api_app)


def test_fertilizer_editor_n_form_order() -> None:
    client = TestClient(api_app.app)
    response = client.get("/schema/fertilizer-comp-keys")
    assert response.status_code == 200
    data = response.json()
    keys = data["keys"] if isinstance(data, dict) else data
    assert keys == COMP_COLS
    no3_index = keys.index("NO3")
    nh4_index = keys.index("NH4")
    urea_index = keys.index("UREA")
    assert no3_index < nh4_index < urea_index
