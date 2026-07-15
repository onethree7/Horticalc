from __future__ import annotations

import math
from dataclasses import asdict, dataclass

CANONICAL_VOLUME_UNIT = "liter"
CANONICAL_SOLID_DOSE_UNIT = "gram"
CANONICAL_LIQUID_DOSE_UNIT = "milliliter"


@dataclass(frozen=True)
class VolumeUnit:
    key: str
    label: str
    symbol: str
    liters_per_unit: float


@dataclass(frozen=True)
class MassUnit:
    key: str
    label: str
    symbol: str
    grams_per_unit: float


@dataclass(frozen=True)
class LiquidVolumeUnit:
    key: str
    label: str
    symbol: str
    milliliters_per_unit: float


VOLUME_UNITS = (
    VolumeUnit("liter", "Liter", "L", 1.0),
    VolumeUnit("us_gallon", "US gallon", "US gal", 3.785411784),
    VolumeUnit("imperial_gallon", "Imperial gallon", "Imp gal", 4.54609),
    VolumeUnit("cubic_meter", "Cubic meter", "m³", 1000.0),
)
VOLUME_UNITS_BY_KEY = {unit.key: unit for unit in VOLUME_UNITS}
VOLUME_UNIT_KEYS = frozenset(VOLUME_UNITS_BY_KEY)

MASS_UNITS = (
    MassUnit("gram", "Gram", "g", 1.0),
    MassUnit("kilogram", "Kilogram", "kg", 1000.0),
    MassUnit("ounce", "Ounce", "oz", 28.349523125),
    MassUnit("pound", "Pound", "lb", 453.59237),
)
MASS_UNITS_BY_KEY = {unit.key: unit for unit in MASS_UNITS}
MASS_UNIT_KEYS = frozenset(MASS_UNITS_BY_KEY)

LIQUID_VOLUME_UNITS = (
    LiquidVolumeUnit("milliliter", "Milliliter", "mL", 1.0),
    LiquidVolumeUnit("liter", "Liter", "L", 1000.0),
    LiquidVolumeUnit("us_fluid_ounce", "US fluid ounce", "US fl oz", 29.5735295625),
    LiquidVolumeUnit("imperial_fluid_ounce", "Imperial fluid ounce", "Imp fl oz", 28.4130625),
)
LIQUID_VOLUME_UNITS_BY_KEY = {unit.key: unit for unit in LIQUID_VOLUME_UNITS}
LIQUID_VOLUME_UNIT_KEYS = frozenset(LIQUID_VOLUME_UNITS_BY_KEY)


def _finite_quantity(value: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Quantity must be a finite number") from exc
    if not math.isfinite(numeric):
        raise ValueError("Quantity must be a finite number")
    return numeric


def volume_unit(unit_key: str) -> VolumeUnit:
    try:
        return VOLUME_UNITS_BY_KEY[unit_key]
    except KeyError as exc:
        raise ValueError(f"Unknown volume unit: {unit_key}") from exc


def mass_unit(unit_key: str) -> MassUnit:
    try:
        return MASS_UNITS_BY_KEY[unit_key]
    except KeyError as exc:
        raise ValueError(f"Unknown mass unit: {unit_key}") from exc


def liquid_volume_unit(unit_key: str) -> LiquidVolumeUnit:
    try:
        return LIQUID_VOLUME_UNITS_BY_KEY[unit_key]
    except KeyError as exc:
        raise ValueError(f"Unknown liquid volume unit: {unit_key}") from exc


def volume_to_liters(value: float, unit_key: str) -> float:
    return _finite_quantity(value) * volume_unit(unit_key).liters_per_unit


def liters_to_volume(liters: float, unit_key: str) -> float:
    return _finite_quantity(liters) / volume_unit(unit_key).liters_per_unit


def convert_volume(value: float, from_unit: str, to_unit: str) -> float:
    return liters_to_volume(volume_to_liters(value, from_unit), to_unit)


def mass_to_grams(value: float, unit_key: str) -> float:
    return _finite_quantity(value) * mass_unit(unit_key).grams_per_unit


def grams_to_mass(grams: float, unit_key: str) -> float:
    return _finite_quantity(grams) / mass_unit(unit_key).grams_per_unit


def liquid_volume_to_milliliters(value: float, unit_key: str) -> float:
    return _finite_quantity(value) * liquid_volume_unit(unit_key).milliliters_per_unit


def milliliters_to_liquid_volume(milliliters: float, unit_key: str) -> float:
    return _finite_quantity(milliliters) / liquid_volume_unit(unit_key).milliliters_per_unit


def volume_units_schema() -> list[dict[str, str | float]]:
    return [asdict(unit) for unit in VOLUME_UNITS]


def mass_units_schema() -> list[dict[str, str | float]]:
    return [asdict(unit) for unit in MASS_UNITS]


def liquid_volume_units_schema() -> list[dict[str, str | float]]:
    return [asdict(unit) for unit in LIQUID_VOLUME_UNITS]
