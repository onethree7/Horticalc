from __future__ import annotations

from fastapi.testclient import TestClient

import api.app as api_app
from horticalc.core import COMP_COLS
from tests.frontend_assets import read_frontend_file

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


def test_fertilizer_editor_headers_are_sortable() -> None:
    app = read_frontend_file("app.js")
    styles = read_frontend_file("styles.css")

    assert "fertilizerEditorSort" in app
    assert "setFertilizerEditorSort" in app
    assert "compareFertilizerEditorRows" in app
    assert 'sortDirection: active ? `${fertilizerEditorSort.direction}ending` : "none"' in app
    assert ".table-sort-button" in styles
    assert 'th[aria-sort="ascending"]' in styles
    assert 'th[aria-sort="descending"]' in styles
