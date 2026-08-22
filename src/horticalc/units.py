from __future__ import annotations

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


def volume_units_schema() -> list[dict[str, str | float]]:
    return [asdict(unit) for unit in VOLUME_UNITS]


def mass_units_schema() -> list[dict[str, str | float]]:
    return [asdict(unit) for unit in MASS_UNITS]


def liquid_volume_units_schema() -> list[dict[str, str | float]]:
    return [asdict(unit) for unit in LIQUID_VOLUME_UNITS]
