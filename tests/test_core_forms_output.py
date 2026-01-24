import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.core import compute_solution
from horticalc.data_io import load_fertilizers, load_molar_masses


def _compute_payload(include_forms: bool) -> dict:
    fertilizers = load_fertilizers()
    molar_masses = load_molar_masses()
    recipe = {
        "liters": 10.0,
        "fertilizers": [
            {"name": "Biolchim Green-Go 12-12-36", "grams": 10.0},
        ],
    }
    water_mg_l = {"NO3": 10.0, "HCO3": 20.0}

    result = compute_solution(recipe, fertilizers, molar_masses, water_mg_l=water_mg_l)
    return result.to_dict(include_forms=include_forms)


def test_forms_mg_per_l_included_by_default() -> None:
    payload = _compute_payload(include_forms=True)

    forms = payload["forms_mg_per_l"]
    water_forms = payload["water_forms_mg_per_l"]
    fertilizer_forms = payload["fertilizer_forms_mg_per_l"]

    assert fertilizer_forms["NH4"] == pytest.approx(21.1, rel=0, abs=1e-6)
    assert fertilizer_forms["NO3"] == pytest.approx(100.0, rel=0, abs=1e-6)
    assert water_forms["NO3"] == pytest.approx(10.0, rel=0, abs=1e-6)
    assert water_forms["HCO3"] == pytest.approx(20.0, rel=0, abs=1e-6)
    assert forms["NO3"] == pytest.approx(110.0, rel=0, abs=1e-6)
    assert forms["HCO3"] == pytest.approx(20.0, rel=0, abs=1e-6)


def test_forms_mg_per_l_can_be_excluded() -> None:
    payload = _compute_payload(include_forms=False)

    assert "forms_mg_per_l" not in payload
    assert "water_forms_mg_per_l" not in payload
    assert "fertilizer_forms_mg_per_l" not in payload

    assert "elements_mg_per_l" in payload
    assert "oxides_mg_per_l" in payload
    assert "ions_mmol_per_l" in payload
