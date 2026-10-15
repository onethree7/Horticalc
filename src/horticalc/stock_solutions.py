"""Recipe scaling and composition-based stock preparation suggestions."""

from __future__ import annotations

import hashlib
import json
from itertools import combinations
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator

from .chemistry import ALLOWED_WATER_KEYS
from .core import apply_osmosis_mix, compute_solution, normalize_water_profile
from .data_io import Fertilizer
from .validation import non_negative_float, positive_float

TankId = Literal["A", "B", "C"]
Assignment = Literal["A", "B", "C", "separate"] | None
MaterialName = Annotated[str, Field(min_length=1, max_length=200)]


class StockWater(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mg_per_l: dict[str, FiniteFloat] = Field(default_factory=dict, max_length=256)
    osmosis_percent: FiniteFloat = Field(default=0, ge=0, le=100)

    @field_validator("mg_per_l")
    @classmethod
    def validate_water(cls, values: dict[str, float]) -> dict[str, float]:
        for key, value in values.items():
            if key not in ALLOWED_WATER_KEYS:
                raise ValueError(f"Invalid water key: {key}")
            non_negative_float(value, f"water.{key}")
        return values


class StockTank(BaseModel):
    model_config = ConfigDict(extra="forbid")
    liters: FiniteFloat = Field(default=1, gt=0)
    factor: FiniteFloat = Field(default=100, gt=1)


class StockSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[2] = 2
    tanks: dict[TankId, StockTank] = Field(
        default_factory=lambda: {"A": StockTank(), "B": StockTank()}, min_length=1, max_length=3
    )
    assignments: dict[MaterialName, Assignment] = Field(default_factory=dict, max_length=1000)
    source_water: StockWater | None = None
    material_fingerprints: dict[MaterialName, str] = Field(default_factory=dict, max_length=1000)

    @field_validator("material_fingerprints")
    @classmethod
    def validate_fingerprints(cls, values: dict[str, str]) -> dict[str, str]:
        for value in values.values():
            if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                raise ValueError("Invalid material fingerprint")
        return values


def migrate_stock_settings(value: dict) -> StockSettings:
    """Convert a persisted version-one attachment before normal validation."""
    if not isinstance(value, dict):
        raise ValueError("Stock settings must be an object")
    if value.get("schema_version", 1) != 1:
        return StockSettings.model_validate(value)
    water = StockWater.model_validate(value.get("preparation_water", {}))
    if any(apply_osmosis_mix(water.mg_per_l, water.osmosis_percent).values()):
        raise ValueError(
            "This saved stock plan uses mineralized preparation water. "
            "Keep the original recipe and create a new stock plan using RO/distilled water."
        )
    migrated = dict(value)
    for key in ("preparation_water", "temperature_c", "evidence_revision"):
        migrated.pop(key, None)
    migrated["schema_version"] = 2
    return StockSettings.model_validate(migrated)


def _pair_risks(left: Fertilizer, right: Fertilizer) -> list[str]:
    risks = set()
    for first, second in ((left.comp, right.comp), (right.comp, left.comp)):
        if first.get("CaO", 0) > 0:
            if second.get("P2O5", 0) > 0:
                risks.add("calcium_phosphorus")
            if second.get("SO4", 0) > 0:
                risks.add("calcium_sulfate")
        if first.get("MgO", 0) > 0 and second.get("P2O5", 0) > 0:
            risks.add("magnesium_phosphorus")
        if (first.get("CaO", 0) > 0 or first.get("MgO", 0) > 0) and (
            second.get("CO3", 0) > 0 or second.get("HCO3", 0) > 0
        ):
            risks.add("carbonate")
        if first.get("SiO2", 0) > 0:
            risks.add("silicon")
    return sorted(risks)


def _suggest_assignments(
    assignments: dict[str, Assignment],
    pairs: dict[tuple[str, str], list[str]],
    fertilizers: dict[str, Fertilizer],
    tanks: dict,
) -> None:
    neighbors: dict[str, set[str]] = {name: set() for name in assignments}
    conditional: dict[str, set[str]] = {name: set() for name in assignments}
    for (left, right), risks in pairs.items():
        if any(risk != "magnesium_phosphorus" for risk in risks):
            neighbors[left].add(right)
            neighbors[right].add(left)
        else:
            conditional[left].add(right)
            conditional[right].add(left)
    order = sorted(assignments, key=lambda name: (-len(neighbors[name]), -fertilizers[name].comp.get("CaO", 0), name))
    for name in order:
        if assignments[name] is not None or fertilizers[name].liquid or not fertilizers[name].comp:
            continue
        occupied = {assignments[other] for other in neighbors[name]}
        available = [tank for tank in tanks if tank not in occupied]
        assignments[name] = min(
            available,
            key=lambda tank: (sum(assignments[other] == tank for other in conditional[name]), tank),
            default=None,
        )


def material_fingerprint(material: Fertilizer) -> str:
    definition = {
        "name": material.name,
        "liquid": material.liquid,
        "weight_factor": float(material.weight_factor),
        "comp": {key: float(value) for key, value in material.comp.items() if value},
    }
    return hashlib.sha256(json.dumps(definition, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def plan_stock_solutions(
    recipe: dict,
    source_water: StockWater,
    settings: StockSettings,
    fertilizers: dict[str, Fertilizer],
    molar_masses: dict[str, float],
    *,
    suggest_assignments: bool = False,
) -> dict:
    liters = positive_float(recipe["liters"], "liters")
    doses: dict[str, float] = {}
    for entry in recipe["fertilizers"]:
        dose = non_negative_float(entry["grams"], "dose")
        if dose:
            name = entry["name"]
            if name not in fertilizers:
                raise ValueError(f"Unknown fertilizer: {name}")
            doses[name] = positive_float(doses.get(name, 0) + dose, "combined dose")
    if not doses:
        raise ValueError("Stock preparation requires at least one positive fertilizer dose")

    findings: list[dict] = []

    def finding(code: str, names: list[str], tank: str | None = None, risks: list[str] | None = None) -> dict:
        item = {"code": code, "materials": names, "severity": "review", "tank": tank}
        if risks:
            item["risks"] = risks
        findings.append(item)
        return item

    tanks = {
        key: {"id": key, **tank.model_dump(), "ingredients": [], "dose_ml_per_l": 1000 / tank.factor}
        for key, tank in settings.tanks.items()
    }
    ingredients = []
    fingerprints = {}
    assignments = {name: settings.assignments.get(name) for name in doses}
    pairs = {
        (left, right): risks
        for left, right in combinations(sorted(doses), 2)
        if (risks := _pair_risks(fertilizers[left], fertilizers[right]))
    }
    if suggest_assignments:
        _suggest_assignments(assignments, pairs, fertilizers, tanks)
    for name, dose in doses.items():
        material = fertilizers[name]
        fingerprint = material_fingerprint(material)
        fingerprints[name] = settings.material_fingerprints.get(name, fingerprint)
        if fingerprints[name] != fingerprint:
            finding("material_changed", [name])["fingerprint"] = fingerprint
        assignment = assignments[name]
        if assignment is not None and assignment != "separate" and assignment not in tanks:
            raise ValueError(f"Assignment refers to an unavailable stock: {assignment}")
        item = {
            "name": name,
            "assignment": assignment,
            "recipe_amount": dose,
            "unit": "mL" if material.liquid else "g",
            "stock_amount": None,
            "stock_amount_per_l": None,
        }
        if assignment in tanks:
            tank = tanks[assignment]
            per_liter = positive_float(dose / liters * tank["factor"], "stock concentration")
            item["stock_amount"] = positive_float(per_liter * tank["liters"], "stock amount")
            item["stock_amount_per_l"] = per_liter
            tank["ingredients"].append(item)
        elif assignment is None:
            finding("unassigned", [name])
        ingredients.append(item)

    active_tanks = [tanks[key] for key in sorted(tanks) if tanks[key]["ingredients"]]
    for tank in active_tanks:
        for (left, right), risks in pairs.items():
            if assignments[left] == assignments[right] == tank["id"]:
                finding("pair_risk", [left, right], tank["id"], risks)
        liquid_ml = sum(item["stock_amount"] for item in tank["ingredients"] if item["unit"] == "mL")
        if liquid_ml > tank["liters"] * 1000:
            raise ValueError(f"Liquid ingredients exceed the finished volume of stock {tank['id']}")
        tank["dose_ml"] = positive_float(liters / tank["factor"] * 1000, "stock dose")
        tank["capacity_liters"] = positive_float(tank["liters"] * tank["factor"], "stock capacity")
        if tank["dose_ml"] > tank["liters"] * 1000:
            finding("insufficient_stock", [], tank=tank["id"])

    stock_fraction = sum(1 / tank["factor"] for tank in active_tanks)
    direct_liquid_liters = sum(
        item["recipe_amount"] / 1000
        for item in ingredients
        if item["assignment"] == "separate" and item["unit"] == "mL"
    )
    water_fraction = 1 - stock_fraction - direct_liquid_liters / liters
    if water_fraction <= 0:
        raise ValueError("Stocks and direct liquid additions leave no room for batch water")
    working_water = normalize_water_profile(
        molar_masses, apply_osmosis_mix(source_water.mg_per_l, source_water.osmosis_percent)
    )
    mixed_water = {key: value * water_fraction for key, value in working_water.items()}
    complete = all(item["assignment"] is not None for item in ingredients)
    final = compute_solution(recipe, fertilizers, molar_masses, mixed_water).to_dict() if complete else None
    attachment = settings.model_copy(
        update={
            "source_water": source_water,
            "assignments": assignments,
            "material_fingerprints": fingerprints,
        }
    ).model_dump()
    result = {
        "liters": liters,
        "ingredients": ingredients,
        "tanks": active_tanks,
        "complete": complete,
        "exportable": complete
        and not any(item["code"] in {"material_changed", "insufficient_stock"} for item in findings),
        "makeup_water_liters": liters * water_fraction,
        "findings": findings,
        "settings": attachment,
        "final_solution": final,
    }
    json.dumps(result, allow_nan=False)
    return result
