from tests.frontend_assets import read_frontend_file
from horticalc.units import LIQUID_VOLUME_UNITS, MASS_UNITS, VOLUME_UNITS


def test_volume_unit_control_uses_api_definitions_and_canonical_liters() -> None:
    html = read_frontend_file("index.html")
    app = read_frontend_file("app.js")

    assert 'id="configVolumeUnit"' in html
    assert 'value="us_gallon"' in html
    assert 'value="imperial_gallon"' in html
    assert "fetchVolumeUnitDefinitions()" in app
    assert '`${apiBase()}/schema/units`' in app
    assert "displayVolumeToLiters(event.target.value)" in app
    assert "persistPreferences({ volume_unit: volumeUnit });" in app
    assert "liters: currentLiters" in app


def test_frontend_fallback_volume_definitions_match_core_schema() -> None:
    app = read_frontend_file("app.js")

    for definition in VOLUME_UNITS:
        assert f'key: "{definition.key}"' in app
        assert f'liters_per_unit: {definition.liters_per_unit!r}' in app
    for definition in MASS_UNITS:
        assert f'key: "{definition.key}"' in app
        assert f'grams_per_unit: {definition.grams_per_unit!r}' in app
    for definition in LIQUID_VOLUME_UNITS:
        assert f'key: "{definition.key}"' in app
        assert f'milliliters_per_unit: {definition.milliliters_per_unit!r}' in app


def test_changing_display_unit_does_not_scale_or_recalculate_batch() -> None:
    app = read_frontend_file("app.js")
    listener = app.split('configVolumeUnitSelect.addEventListener("change"', 1)[1].split("});", 1)[0]

    assert "setVolumeUnit(event.target.value);" in listener
    assert "setCurrentLiters" not in listener
    assert "scaleCurrentBatch" not in listener
    assert "scheduleRecalculate" not in listener


def test_dose_unit_controls_convert_only_at_frontend_boundary() -> None:
    html = read_frontend_file("index.html")
    app = read_frontend_file("app.js")

    assert 'id="configSolidDoseUnit"' in html
    assert 'id="configLiquidDoseUnit"' in html
    assert "canonicalDoseToDisplay" in app
    assert "displayDoseToCanonical" in app
    assert "persistPreferences({ solid_dose_unit: solidDoseUnit });" in app
    assert "persistPreferences({ liquid_dose_unit: liquidDoseUnit });" in app
    assert "grams: Number(row.grams) || 0" in app
    assert "dose:" not in app
