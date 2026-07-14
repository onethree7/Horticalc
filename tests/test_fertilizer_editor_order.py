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
    app = read_frontend_file("app/editor.js")
    styles = read_frontend_file("styles.css")

    assert "fertilizerEditorSort" in app
    assert "setFertilizerEditorSort" in app
    assert "compareFertilizerEditorRows" in app
    assert 'sortDirection: active ? `${fertilizerEditorSort.direction}ending` : "none"' in app
    assert ".table-sort-button" in styles
    assert 'th[aria-sort="ascending"]' in styles
    assert 'th[aria-sort="descending"]' in styles


def test_fertilizer_editor_refreshes_catalog_without_restarting_app() -> None:
    editor = read_frontend_file("app/editor.js")
    main = read_frontend_file("app/main.js")
    save_block = editor.split("async function saveFertilizerEditor()", 1)[1].split(
        "async function reloadFertilizerEditor()",
        1,
    )[0]

    assert "async function refreshFertilizerCatalog()" in editor
    assert "await refreshFertilizerCatalog();" in save_block
    assert "await init();" not in save_block
    assert "onCatalogChange(refreshedFertilizers);" in editor
    assert "calculator.setFertilizers(fertilizers);" in main
    assert "solver.setFertilizers(fertilizers);" in main
    assert "calculator.scheduleRecalculate();" in main


def test_fertilizer_api_uses_liquid_boolean_schema() -> None:
    client = TestClient(api_app.app)
    response = client.get("/fertilizers")

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


def test_fertilizer_editor_places_solver_max_after_nutrients() -> None:
    app = read_frontend_file("app/editor.js")

    columns = app.split("const headerCells = [", 1)[1].split("];", 1)[0]
    assert columns.index("...fertilizerEditorCompKeys") < columns.index("Solver max / L")
    assert "solver_max_dose_per_l" in app
