from __future__ import annotations

import math

import pytest

from horticalc.units import (
    LIQUID_VOLUME_UNIT_KEYS,
    MASS_UNIT_KEYS,
    CANONICAL_VOLUME_UNIT,
    VOLUME_UNIT_KEYS,
    convert_volume,
    grams_to_mass,
    liquid_volume_to_milliliters,
    liters_to_volume,
    mass_to_grams,
    milliliters_to_liquid_volume,
    volume_to_liters,
    volume_units_schema,
)


@pytest.mark.parametrize(
    ("value", "unit", "expected_liters"),
    [
        (10, "liter", 10.0),
        (10, "us_gallon", 37.85411784),
        (10, "imperial_gallon", 45.4609),
        (2, "cubic_meter", 2000.0),
    ],
)
def test_volume_units_convert_to_canonical_liters(value, unit, expected_liters) -> None:
    assert volume_to_liters(value, unit) == pytest.approx(expected_liters)


@pytest.mark.parametrize("unit", sorted(VOLUME_UNIT_KEYS))
def test_volume_conversions_round_trip_through_liters(unit) -> None:
    displayed = liters_to_volume(123.456, unit)

    assert volume_to_liters(displayed, unit) == pytest.approx(123.456)


def test_volume_conversion_can_cross_units() -> None:
    assert convert_volume(1, "us_gallon", "liter") == pytest.approx(3.785411784)
    assert convert_volume(4.54609, "liter", "imperial_gallon") == pytest.approx(1)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan, "not-a-number"])
def test_volume_conversion_rejects_non_finite_values(value) -> None:
    with pytest.raises(ValueError, match="finite number"):
        volume_to_liters(value, CANONICAL_VOLUME_UNIT)


def test_volume_conversion_rejects_unknown_unit() -> None:
    with pytest.raises(ValueError, match="Unknown volume unit"):
        liters_to_volume(10, "gallon")


def test_volume_schema_is_explicit_about_ambiguous_gallons() -> None:
    definitions = {entry["key"]: entry for entry in volume_units_schema()}

    assert definitions["us_gallon"]["symbol"] == "US gal"
    assert definitions["imperial_gallon"]["symbol"] == "Imp gal"
    assert "gallon" not in definitions


@pytest.mark.parametrize("unit", sorted(MASS_UNIT_KEYS))
def test_solid_dose_units_round_trip_through_grams(unit) -> None:
    displayed = grams_to_mass(123.456, unit)

    assert mass_to_grams(displayed, unit) == pytest.approx(123.456)


@pytest.mark.parametrize("unit", sorted(LIQUID_VOLUME_UNIT_KEYS))
def test_liquid_dose_units_round_trip_through_milliliters(unit) -> None:
    displayed = milliliters_to_liquid_volume(123.456, unit)

    assert liquid_volume_to_milliliters(displayed, unit) == pytest.approx(123.456)


def test_dose_unit_factors_use_exact_canonical_boundaries() -> None:
    assert mass_to_grams(1, "ounce") == pytest.approx(28.349523125)
    assert mass_to_grams(1, "pound") == pytest.approx(453.59237)
    assert liquid_volume_to_milliliters(1, "us_fluid_ounce") == pytest.approx(29.5735295625)
    assert liquid_volume_to_milliliters(1, "imperial_fluid_ounce") == pytest.approx(28.4130625)
