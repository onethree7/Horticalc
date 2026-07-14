from __future__ import annotations

import json
import shutil
import subprocess

from horticalc.units import LIQUID_VOLUME_UNITS, MASS_UNITS, VOLUME_UNITS
from tests.frontend_assets import read_frontend_file


def test_volume_unit_control_uses_api_definitions_and_canonical_liters() -> None:
    html = read_frontend_file("index.html")
    api = read_frontend_file("app/api.js")
    settings = read_frontend_file("app/settings.js")
    calculator = read_frontend_file("app/calculator.js")
    assert 'id="configVolumeUnit"' in html
    assert 'value="us_gallon"' in html
    assert 'value="imperial_gallon"' in html
    assert 'getJson("/schema/units"' in api
    assert "units.displayVolumeToLiters(event.target.value)" in settings
    assert "persistPreferences({ volume_unit: units.volumeUnit });" in settings
    assert "liters: units.liters" in calculator


def test_frontend_fallback_unit_definitions_match_core_schema() -> None:
    node = shutil.which("node")
    assert node is not None
    result = subprocess.run(
        [
            node,
            "--input-type=module",
            "-e",
            """
import {
  FALLBACK_VOLUME_UNITS, FALLBACK_MASS_UNITS, FALLBACK_LIQUID_VOLUME_UNITS
} from './frontend/app/constants.js';
console.log(JSON.stringify([FALLBACK_VOLUME_UNITS, FALLBACK_MASS_UNITS, FALLBACK_LIQUID_VOLUME_UNITS]));
""",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    volume, mass, liquid = json.loads(result.stdout)
    assert [(item["key"], item["liters_per_unit"]) for item in volume] == [
        (definition.key, definition.liters_per_unit) for definition in VOLUME_UNITS
    ]
    assert [(item["key"], item["grams_per_unit"]) for item in mass] == [
        (definition.key, definition.grams_per_unit) for definition in MASS_UNITS
    ]
    assert [(item["key"], item["milliliters_per_unit"]) for item in liquid] == [
        (definition.key, definition.milliliters_per_unit) for definition in LIQUID_VOLUME_UNITS
    ]


def test_changing_display_unit_does_not_scale_or_recalculate_batch() -> None:
    settings = read_frontend_file("app/settings.js")
    listener = settings.split('volumeUnitSelect?.addEventListener("change"', 1)[1].split("});", 1)[0]
    assert "units.setVolumeUnit(event.target.value);" in listener
    assert "setLiters" not in listener
    assert "scaleBatch" not in listener
    assert "scheduleRecalculate" not in listener


def test_dose_unit_controls_convert_only_at_frontend_boundary() -> None:
    html = read_frontend_file("index.html")
    units = read_frontend_file("app/units.js")
    settings = read_frontend_file("app/settings.js")
    calculator = read_frontend_file("app/calculator.js")
    assert 'id="configSolidDoseUnit"' in html
    assert 'id="configLiquidDoseUnit"' in html
    assert "canonicalDoseToDisplay" in units
    assert "displayDoseToCanonical" in units
    assert "persistPreferences({ solid_dose_unit: units.solidDoseUnit });" in settings
    assert "persistPreferences({ liquid_dose_unit: units.liquidDoseUnit });" in settings
    assert "grams: Number(row.grams) || 0" in calculator
    assert "dose:" not in calculator


def test_display_preferences_are_collapsed_but_batch_amount_stays_visible() -> None:
    html = read_frontend_file("index.html")
    settings = read_frontend_file("app/settings.js")
    details_start = html.index('<details class="rail-settings">')
    details_end = html.index("</details>", details_start)
    markup = html[details_start:details_end]
    assert html.index('id="configLiters"') < details_start
    for element_id in (
        "configUnitSummary", "themeSelect", "languageSelect", "configVolumeUnit",
        "configSolidDoseUnit", "configLiquidDoseUnit",
    ):
        assert f'id="{element_id}"' in markup
    assert "unitSummary.textContent = [" in settings
    assert '].join(" · ");' in settings
