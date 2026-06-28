from tests.frontend_assets import read_frontend_file


def test_solver_copy_button_present() -> None:
    content = read_frontend_file("index.html")

    assert 'id="copySolverResults"' in content
    assert 'data-i18n="solver.copyClipboard"' in content
    assert 'id="copySolverResultsStatus"' in content

def test_solver_copy_logic_present() -> None:
    content = read_frontend_file("app.js")

    assert "buildSolverClipboardText" in content
    assert "buildClipboardRows" in content
    assert "copySolverResultsToClipboard" in content
    assert "copyTextWithFallback" in content
    assert 't("solver.clipboardBatchLiters")' in content
    assert 't("solver.clipboardTargets")' in content
    assert "EC (mS/cm)" in content
    assert "\\t" not in content
    assert '.join("  ")' in content


def test_solver_recipe_button_uses_short_responsive_label() -> None:
    html = read_frontend_file("index.html")
    german = read_frontend_file("i18n/de.js")
    styles = read_frontend_file("styles.css")

    assert '>Use recipe</button>' in html
    assert '"solver.allowedFromRecipe": "Rezept übernehmen"' in german
    assert ".solver-picker-actions .btn" in styles
    assert "overflow-wrap: anywhere" in styles
