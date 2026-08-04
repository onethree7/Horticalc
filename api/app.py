from __future__ import annotations

import logging
import math
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, FiniteFloat, ValidationError

from horticalc import __version__
from horticalc.chemistry import ALLOWED_TARGET_KEYS, ALLOWED_WATER_KEYS, COMP_COLS
from horticalc.core import (
    augment_water_profile_with_elements,
    compute_solution,
    normalize_water_profile,
)
from horticalc.data_io import (
    Fertilizer,
    fertilizer_name_key,
    load_fertilizers,
    load_molar_masses,
    load_nutrient_solution_data,
    load_recipe,
    load_user_preferences,
    load_water_profile_data,
    save_fertilizers,
    save_nutrient_solution,
    save_recipe,
    save_user_preferences,
    save_water_profile,
)
from horticalc.nutrient_profiles import normalize_nutrient_solution_data, nutrient_solution_has_setup
from horticalc.paths import (
    PortableLayout,
    app_root,
    default_recipe_path,
    ensure_portable_layout,
    resolve_layered_yaml_path,
    shipped_nutrient_solutions_dir,
    shipped_recipes_dir,
    shipped_water_profiles_dir,
    user_solver_history_path,
)
from horticalc.solver import solve_recipe_data
from horticalc.solver_config import SOLVER_CONFIG_DEFINITIONS, resolve_solver_config, validate_solver_config
from horticalc.solver_history import (
    DEFAULT_SOLVER_HISTORY_LIMIT,
    MAX_SOLVER_HISTORY_LIMIT,
    SOLVER_HISTORY_SCHEMA_VERSION,
    append_solver_history,
    clear_solver_history,
    solver_history_entry,
    solver_history_summaries,
    trim_solver_history,
)
from horticalc.units import (
    CANONICAL_LIQUID_DOSE_UNIT,
    CANONICAL_SOLID_DOSE_UNIT,
    CANONICAL_VOLUME_UNIT,
    LIQUID_VOLUME_UNIT_KEYS,
    MASS_UNIT_KEYS,
    VOLUME_UNIT_KEYS,
    liquid_volume_units_schema,
    mass_units_schema,
    volume_units_schema,
)
from horticalc.validation import non_negative_float, percentage_float, unique_strings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_app_data()
    yield


app = FastAPI(title="Horticalc API", version=__version__, lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def request_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    for error in errors:
        invalid_input = error.get("input")
        if isinstance(invalid_input, float) and not math.isfinite(invalid_input):
            error["input"] = str(invalid_input)
    return JSONResponse(status_code=422, content={"detail": errors})


FERTILIZERS: Dict[str, Fertilizer] = {}
MOLAR_MASSES: Dict[str, float] = {}
PORTABLE_LAYOUT: PortableLayout | None = None
FRONTEND_DIR = app_root() / "frontend"


class FertilizerEntry(BaseModel):
    name: str
    grams: FiniteFloat = Field(ge=0)


class FertilizerPayload(BaseModel):
    name: str
    liquid: bool
    weight_factor: float | None = None
    comp: Dict[str, float] | None = None
    solver_max_dose_per_l: FiniteFloat | None = Field(default=None, ge=0)


class PreferencesPayload(BaseModel):
    theme: Optional[str] = None
    locale: Optional[str] = None
    default_liters: Optional[FiniteFloat] = Field(default=None, gt=0)
    volume_unit: Optional[str] = None
    solid_dose_unit: Optional[str] = None
    liquid_dose_unit: Optional[str] = None
    solver_config: Optional[Dict[str, Any]] = None
    last_water_profile: Optional[str] = None
    solver_history_limit: Optional[int] = Field(default=None, ge=0, le=MAX_SOLVER_HISTORY_LIMIT)


class RecipeRequest(BaseModel):
    liters: FiniteFloat = Field(default=10.0, gt=0)
    fertilizers: List[FertilizerEntry] = Field(default_factory=list)
    urea_as_nh4: bool = False
    water_profile_name: Optional[str] = None
    water_mg_l: Optional[Dict[str, float]] = None
    osmosis_percent: FiniteFloat | None = Field(default=0, ge=0, le=100)


class CalculationResponse(BaseModel):
    liters: float
    elements_mg_per_l: Dict[str, float]
    oxides_mg_per_l: Dict[str, float]
    ions_mmol_per_l: Dict[str, float]
    ions_meq_per_l: Dict[str, float]
    ion_balance: Dict[str, float | str]
    fertilizer_elements_mg_per_l: Dict[str, float]
    fertilizer_oxides_mg_per_l: Dict[str, float]
    fertilizer_ions_mmol_per_l: Dict[str, float]
    fertilizer_ions_meq_per_l: Dict[str, float]
    fertilizer_ion_balance: Dict[str, float | str]
    ec_fertilizer: Dict[str, Any]
    water_elements_mg_per_l: Dict[str, float]
    water_oxides_mg_per_l: Dict[str, float]
    water_ions_mmol_per_l: Dict[str, float]
    water_ions_meq_per_l: Dict[str, float]
    water_ion_balance: Dict[str, float | str]
    ec: Dict[str, Any]
    ec_water: Dict[str, Any]
    npk_metrics: Dict[str, Any]
    sluijsmann: Dict[str, Any]
    osmosis_percent: float


class SolveRequest(BaseModel):
    targets: Dict[str, float] = Field(default_factory=dict)
    liters: FiniteFloat = Field(default=10.0, gt=0)
    water_profile: Optional[Dict[str, Any]] = None
    fertilizers_allowed: List[str] = Field(default_factory=list)
    fixed_grams: Dict[str, FiniteFloat] = Field(default_factory=dict)
    urea_as_nh4: bool = False
    solver_config: Dict[str, Any] = Field(default_factory=dict)


class SolveFertilizerEntry(BaseModel):
    name: str
    grams: float


class SolveResponse(BaseModel):
    liters: float
    solver_model: str
    fertilizers: List[SolveFertilizerEntry]
    objective_elements: List[str]
    ignored_elements: List[str]
    target_priorities: Dict[str, Dict[str, int]]
    priority_stages: List[Dict[str, int | float]]
    targets_mg_per_l: Dict[str, float]
    achieved_elements_mg_per_l: Dict[str, float]
    errors_mg_per_l: Dict[str, float]
    errors_percent: Dict[str, float]


class WaterProfilePayload(BaseModel):
    name: str
    source: Optional[str] = ""
    mg_per_l: Dict[str, float] = Field(default_factory=dict)
    osmosis_percent: FiniteFloat | None = Field(default=0, ge=0, le=100)


class NutrientSolutionPayload(BaseModel):
    name: str
    source: Optional[str] = ""
    targets_mg_per_l: Dict[str, float] = Field(default_factory=dict)
    liters: Optional[FiniteFloat] = Field(default=None, gt=0)
    water_profile: Optional[str] = None
    osmosis_percent: Optional[FiniteFloat] = Field(default=None, ge=0, le=100)
    fertilizers_allowed: Optional[List[str]] = None
    fixed_grams: Optional[Dict[str, FiniteFloat]] = None
    urea_as_nh4: Optional[bool] = None
    solver_config: Optional[Dict[str, Any]] = None
    overwrite: bool = False


class RecipePayload(BaseModel):
    name: str
    liters: FiniteFloat = Field(default=10.0, gt=0)
    fertilizers: List[FertilizerEntry] = Field(default_factory=list)
    fertilizers_allowed: List[str] = Field(default_factory=list)
    urea_as_nh4: bool = False
    water_profile: Optional[str] = None
    osmosis_percent: FiniteFloat | None = Field(default=0, ge=0, le=100)
    solver_config: Dict[str, Any] = Field(default_factory=dict)


async def _parse_request_payload(request: Request) -> dict:
    content_type = (request.headers.get("content-type") or "").lower()
    try:
        if "yaml" in content_type:
            raw_body = await request.body()
            payload = yaml.safe_load(raw_body.decode("utf-8"))
            if payload is None:
                payload = {}
        else:
            payload = await request.json()
    except (UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        raise HTTPException(status_code=400, detail="Invalid request payload") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request payload must be an object")
    return payload


def _validated_request_model(model_type: type[BaseModel], payload: dict) -> BaseModel:
    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        errors = exc.errors(include_url=False)
        for error in errors:
            invalid_input = error.get("input")
            if isinstance(invalid_input, float) and not math.isfinite(invalid_input):
                error["input"] = str(invalid_input)
        raise HTTPException(status_code=422, detail=errors) from exc


def _model_dump(model: BaseModel) -> dict:
    return model.model_dump()


def _safe_filename(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name).strip("_")


def _yaml_filename(name: str) -> str:
    stem = name[:-4] if name.endswith(".yml") else name
    return f"{_safe_filename(stem)}.yml"


def _required_name(value: str, detail: str) -> str:
    name = value.strip()
    if not name:
        raise HTTPException(status_code=400, detail=detail)
    return name


def _saved_yaml_path(directory: Path, name: str, empty_name_detail: str) -> Path:
    safe_name = _safe_filename(name)
    if not safe_name:
        raise HTTPException(status_code=400, detail=empty_name_detail)
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{safe_name}.yml"


def _named_yaml_entries(
    directories: Path | tuple[Path, ...],
    loader: Callable[[Path], dict],
    skip: Callable[[Path], bool] | None = None,
) -> List[dict]:
    resource_dirs = (directories,) if isinstance(directories, Path) else directories
    resources: dict[str, Path] = {}
    for directory in resource_dirs:
        if directory.exists():
            resources.update({path.name: path for path in directory.glob("*.yml")})
    entries = []
    for path in sorted(resources.values(), key=lambda resource: resource.name.casefold()):
        if skip and skip(path):
            continue
        try:
            data = loader(path)
        except (AttributeError, OSError, TypeError, ValueError, yaml.YAMLError) as exc:
            logger.warning("Skipping invalid YAML resource %s: %s", path, exc)
            continue
        entries.append(
            {
                "name": data.get("name") or path.stem,
                "filename": path.name,
            }
        )
    return entries


def _validated_float_mapping(
    values: Dict[str, Any],
    allowed_keys: set[str],
    invalid_key_prefix: str,
) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for key, value in values.items():
        if key not in allowed_keys:
            raise HTTPException(status_code=400, detail=f"{invalid_key_prefix}: {key}")
        try:
            numeric_value = non_negative_float(value, key)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid value for {key}") from exc
        result[key] = numeric_value
    return result


def _validated_water_mg_l(values: Dict[str, Any]) -> Dict[str, float]:
    return _validated_float_mapping(values, ALLOWED_WATER_KEYS, "Invalid water key")


def _validated_osmosis_percent(value: Any) -> float:
    try:
        return percentage_float(0 if value is None else value, "osmosis_percent")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid osmosis_percent value") from exc


def _validated_solver_config(
    values: Dict[str, Any],
    *,
    allow_advanced: bool = True,
) -> Dict[str, Any]:
    try:
        return validate_solver_config(values, allow_advanced=allow_advanced)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _validated_unique_names(values: List[str], *, field_name: str) -> List[str]:
    try:
        return unique_strings(values, field_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _portable_layout() -> PortableLayout:
    _ensure_initialized()
    if PORTABLE_LAYOUT is None:
        raise RuntimeError("Portable layout has not been initialized")
    return PORTABLE_LAYOUT


def _ensure_initialized() -> None:
    if not MOLAR_MASSES or PORTABLE_LAYOUT is None:
        load_app_data()


def load_app_data() -> None:
    layout = ensure_portable_layout()
    global FERTILIZERS, MOLAR_MASSES, PORTABLE_LAYOUT
    FERTILIZERS = load_fertilizers()
    MOLAR_MASSES = load_molar_masses()
    PORTABLE_LAYOUT = layout


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/schema/fertilizer-comp-keys")
def fertilizer_comp_keys() -> dict:
    return {"keys": COMP_COLS}


@app.get("/schema/solver-config")
def solver_config_schema() -> dict:
    return {"definitions": list(SOLVER_CONFIG_DEFINITIONS)}


@app.get("/schema/units")
def units_schema() -> dict:
    return {
        "canonical_volume_unit": CANONICAL_VOLUME_UNIT,
        "canonical_solid_dose_unit": CANONICAL_SOLID_DOSE_UNIT,
        "canonical_liquid_dose_unit": CANONICAL_LIQUID_DOSE_UNIT,
        "volume_units": volume_units_schema(),
        "mass_units": mass_units_schema(),
        "liquid_volume_units": liquid_volume_units_schema(),
    }


THEME_OPTIONS = {
    "horticalc-dark",
    "horticalc-light",
    "high-contrast",
    "soil",
    "gch-classic",
    "vt-green",
    "blue-matrix",
    "tokyo-night",
    "solarized-light",
    "dracula",
    "gruvbox-dark",
    "catppuccin-mocha",
    "monokai-classic",
    "windows-95",
    "commodore-64",
    "nord",
    "amber-crt",
}
LOCALE_OPTIONS = {"de", "en", "nl", "es", "zh"}


def _solver_history_path() -> Path:
    return user_solver_history_path(_portable_layout().root)


def _effective_solver_history_limit(preferences_data: dict[str, Any] | None = None) -> int:
    values = preferences_data if preferences_data is not None else load_user_preferences()
    value = values.get("solver_history_limit", DEFAULT_SOLVER_HISTORY_LIMIT)
    if isinstance(value, bool) or not isinstance(value, int):
        return DEFAULT_SOLVER_HISTORY_LIMIT
    if value < 0 or value > MAX_SOLVER_HISTORY_LIMIT:
        return DEFAULT_SOLVER_HISTORY_LIMIT
    return value


@app.get("/preferences")
def preferences() -> dict[str, Any]:
    return load_user_preferences()


@app.put("/preferences")
def put_preferences(payload: PreferencesPayload) -> dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True)
    if "theme" in updates and payload.theme not in THEME_OPTIONS:
        raise HTTPException(status_code=400, detail="Unknown theme")
    if "locale" in updates and payload.locale not in LOCALE_OPTIONS:
        raise HTTPException(status_code=400, detail="Unknown locale")
    if "volume_unit" in updates and payload.volume_unit not in VOLUME_UNIT_KEYS:
        raise HTTPException(status_code=400, detail="Unknown volume unit")
    if "solid_dose_unit" in updates and payload.solid_dose_unit not in MASS_UNIT_KEYS:
        raise HTTPException(status_code=400, detail="Unknown solid dose unit")
    if "liquid_dose_unit" in updates and payload.liquid_dose_unit not in LIQUID_VOLUME_UNIT_KEYS:
        raise HTTPException(status_code=400, detail="Unknown liquid dose unit")
    if payload.default_liters is not None and not math.isfinite(payload.default_liters):
        raise HTTPException(status_code=400, detail="Invalid default liters")
    if payload.last_water_profile is not None:
        profile_name = payload.last_water_profile.strip()
        if not profile_name or Path(profile_name).name != profile_name:
            raise HTTPException(status_code=400, detail="Invalid water profile")
        updates["last_water_profile"] = profile_name
    if payload.solver_config is not None:
        updates["solver_config"] = _validated_solver_config(
            payload.solver_config,
            allow_advanced=False,
        )
    if "solver_history_limit" in updates:
        updates["solver_history_limit"] = (
            DEFAULT_SOLVER_HISTORY_LIMIT if payload.solver_history_limit is None else int(payload.solver_history_limit)
        )
    preferences = load_user_preferences()
    preferences.update(updates)
    save_user_preferences(preferences)
    if "solver_history_limit" in updates:
        trim_solver_history(_solver_history_path(), _effective_solver_history_limit(preferences))
    return preferences


@app.get("/solver-history")
def solver_history() -> dict[str, Any]:
    return {
        "entries": solver_history_summaries(_solver_history_path()),
        "limit": _effective_solver_history_limit(),
    }


@app.get("/solver-history/{entry_id}")
def solver_history_detail(entry_id: str) -> dict[str, Any]:
    entry = solver_history_entry(_solver_history_path(), entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Solver history entry not found")
    return entry


@app.delete("/solver-history")
def delete_solver_history() -> dict[str, str]:
    clear_solver_history(_solver_history_path())
    return {"status": "ok"}


@app.get("/fertilizers")
def fertilizers() -> List[dict]:
    _ensure_initialized()
    return [
        {
            "name": fert.name,
            "liquid": fert.liquid,
            "weight_factor": fert.weight_factor,
            "comp": fert.comp,
            "solver_max_dose_per_l": fert.solver_max_dose_per_l,
        }
        for fert in FERTILIZERS.values()
    ]


@app.put("/fertilizers")
def put_fertilizers(payload: List[FertilizerPayload]) -> dict:
    _ensure_initialized()
    new_ferts: Dict[str, Fertilizer] = {}
    seen_names: set[str] = set()
    for entry in payload:
        name = entry.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Fertilizer name must not be empty")
        name_key = fertilizer_name_key(name)
        if name_key in seen_names:
            raise HTTPException(status_code=400, detail="Fertilizer names must be unique")
        seen_names.add(name_key)

        weight = entry.weight_factor if entry.weight_factor is not None else 1.0
        if not math.isfinite(weight) or weight <= 0:
            raise HTTPException(status_code=400, detail="Invalid weight value")

        comp: Dict[str, float] = {}
        if entry.comp:
            for key, value in entry.comp.items():
                if not math.isfinite(value):
                    raise HTTPException(status_code=400, detail="Invalid nutrient value")
                if value == 0:
                    continue
                comp[key] = value

        new_ferts[name] = Fertilizer(
            name=name,
            liquid=entry.liquid,
            weight_factor=weight,
            comp=comp,
            solver_max_dose_per_l=entry.solver_max_dose_per_l,
        )

    global FERTILIZERS
    save_fertilizers(new_ferts)
    FERTILIZERS = new_ferts
    return {"count": len(new_ferts)}


@app.get("/water-profiles")
def water_profiles() -> List[dict]:
    layout = _portable_layout()
    return _named_yaml_entries(
        (shipped_water_profiles_dir(layout.root), layout.water_profiles),
        load_water_profile_data,
    )


@app.get("/water-profiles/{profile_name}")
def water_profile(profile_name: str) -> dict:
    layout = _portable_layout()
    profile_path = resolve_layered_yaml_path(
        _yaml_filename(profile_name),
        layout.water_profiles,
        shipped_water_profiles_dir(layout.root),
    )
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="Water profile not found")
    data = load_water_profile_data(profile_path)
    mg_per_l = _validated_water_mg_l(data["mg_per_l"])
    data["mg_per_l"] = mg_per_l
    normalized = normalize_water_profile(MOLAR_MASSES, mg_per_l)
    data["normalized_mg_per_l"] = augment_water_profile_with_elements(MOLAR_MASSES, normalized)
    return data


@app.get("/nutrient-solutions")
def nutrient_solutions() -> List[dict]:
    layout = _portable_layout()
    return _named_yaml_entries(
        (shipped_nutrient_solutions_dir(layout.root), layout.nutrient_solutions),
        load_nutrient_solution_data,
    )


@app.get("/nutrient-solutions/{solution_name}")
def nutrient_solution(solution_name: str) -> dict:
    layout = _portable_layout()
    solution_path = resolve_layered_yaml_path(
        _yaml_filename(solution_name),
        layout.nutrient_solutions,
        shipped_nutrient_solutions_dir(layout.root),
    )
    if not solution_path.exists():
        raise HTTPException(status_code=404, detail="Nutrient Solution not found")
    return load_nutrient_solution_data(solution_path)


@app.post("/water-profiles")
@app.put("/water-profiles")
async def save_profile(request: Request) -> dict:
    payload = await _parse_request_payload(request)

    profile = _validated_request_model(WaterProfilePayload, payload)
    name = _required_name(profile.name, "Profile name is required")

    mg_per_l = _validated_water_mg_l(profile.mg_per_l)

    osmosis_percent = _validated_osmosis_percent(profile.osmosis_percent)
    water_profiles_dir = _portable_layout().water_profiles
    profile_path = _saved_yaml_path(water_profiles_dir, name, "Profile name results in empty filename")
    save_water_profile(
        profile_path,
        name=name,
        source=profile.source or "",
        mg_per_l=mg_per_l,
        osmosis_percent=osmosis_percent,
    )
    return {"status": "ok", "filename": profile_path.name}


@app.post("/nutrient-solutions")
@app.put("/nutrient-solutions")
async def save_nutrient_solution_profile(request: Request) -> dict:
    payload = await _parse_request_payload(request)

    solution = _validated_request_model(NutrientSolutionPayload, payload)
    name = _required_name(solution.name, "Nutrient Solution name is required")

    solution_data = solution.model_dump(exclude_unset=True)
    solution_data.pop("overwrite", None)
    solution_data["name"] = name
    try:
        normalized = normalize_nutrient_solution_data(solution_data)
    except ValueError as exc:
        detail = str(exc)
        target_value_prefix = "targets_mg_per_l."
        if detail.startswith(target_value_prefix):
            target_key = detail.removeprefix(target_value_prefix).split(" ", 1)[0]
            detail = f"Invalid value for {target_key}"
        raise HTTPException(status_code=400, detail=detail) from exc

    layout = _portable_layout()
    nutrient_solutions_dir = layout.nutrient_solutions
    solution_path = _saved_yaml_path(
        nutrient_solutions_dir,
        name,
        "Nutrient Solution name results in empty filename",
    )
    existing_path = resolve_layered_yaml_path(
        solution_path.name,
        layout.nutrient_solutions,
        shipped_nutrient_solutions_dir(layout.root),
    )
    if existing_path.exists() and not solution.overwrite:
        existing_name = existing_path.stem
        existing_has_setup = False
        try:
            existing = load_nutrient_solution_data(existing_path)
            existing_name = existing["name"]
            existing_has_setup = nutrient_solution_has_setup(existing)
        except (AttributeError, OSError, TypeError, ValueError, yaml.YAMLError) as exc:
            logger.warning("Unable to inspect existing nutrient solution %s: %s", existing_path, exc)
        raise HTTPException(
            status_code=409,
            detail={
                "code": "nutrient_solution_exists",
                "name": existing_name,
                "filename": solution_path.name,
                "has_solver_setup": existing_has_setup,
            },
        )

    save_nutrient_solution(solution_path, **normalized)
    return {"status": "ok", "filename": solution_path.name}


@app.get("/molar-masses")
def molar_masses() -> Dict[str, float]:
    _ensure_initialized()
    return MOLAR_MASSES


@app.get("/recipes/default")
def default_recipe() -> dict:
    recipe_path = default_recipe_path(_portable_layout().root)
    if not recipe_path.exists():
        raise HTTPException(status_code=404, detail="Default recipe not found")
    return load_recipe(recipe_path)


@app.get("/recipes")
def recipes() -> List[dict]:
    layout = _portable_layout()
    return _named_yaml_entries(
        (shipped_recipes_dir(layout.root), layout.recipes),
        load_recipe,
        skip=lambda path: path.stem.startswith("solve_") or path.name == "default.yml",
    )


@app.get("/recipes/{recipe_name}")
def recipe(recipe_name: str) -> dict:
    layout = _portable_layout()
    recipe_path = resolve_layered_yaml_path(
        _yaml_filename(recipe_name),
        layout.recipes,
        shipped_recipes_dir(layout.root),
    )
    if not recipe_path.exists():
        raise HTTPException(status_code=404, detail="Recipe not found")
    return load_recipe(recipe_path)


@app.post("/recipes")
@app.put("/recipes")
async def save_recipe_profile(request: Request) -> dict:
    payload = await _parse_request_payload(request)

    recipe = _validated_request_model(RecipePayload, payload)
    name = _required_name(recipe.name, "Recipe name is required")
    solver_config = _validated_solver_config(recipe.solver_config)
    fertilizers_allowed = _validated_unique_names(
        [str(entry) for entry in recipe.fertilizers_allowed if str(entry).strip()],
        field_name="fertilizers_allowed",
    )

    payload_out = {
        "name": name,
        "liters": recipe.liters,
        "fertilizers": [_model_dump(entry) for entry in recipe.fertilizers],
        "fertilizers_allowed": fertilizers_allowed,
        "urea_as_nh4": recipe.urea_as_nh4,
    }
    if solver_config:
        payload_out["solver_config"] = solver_config
    if recipe.water_profile:
        payload_out["water_profile"] = recipe.water_profile
    if recipe.osmosis_percent is not None:
        payload_out["osmosis_percent"] = recipe.osmosis_percent

    recipes_dir = _portable_layout().recipes
    recipe_path = _saved_yaml_path(recipes_dir, name, "Recipe name results in empty filename")
    save_recipe(recipe_path, payload_out)
    return {"status": "ok", "filename": recipe_path.name}


@app.post("/calculate", response_model=CalculationResponse)
def calculate(payload: RecipeRequest) -> CalculationResponse:
    _ensure_initialized()
    water_mg_l: Dict[str, float] = {}
    osmosis_percent = 0.0
    if payload.water_profile_name:
        layout = _portable_layout()
        profile_path = resolve_layered_yaml_path(
            _yaml_filename(payload.water_profile_name),
            layout.water_profiles,
            shipped_water_profiles_dir(layout.root),
        )
        if not profile_path.exists():
            raise HTTPException(status_code=404, detail="Water profile not found")
        profile = load_water_profile_data(profile_path)
        mg_per_l = profile["mg_per_l"]
        water_mg_l = _validated_water_mg_l(mg_per_l)
        osmosis_percent = _validated_osmosis_percent(profile.get("osmosis_percent"))
    elif payload.water_mg_l:
        water_mg_l = _validated_water_mg_l(payload.water_mg_l)
        if payload.osmosis_percent is not None:
            osmosis_percent = _validated_osmosis_percent(payload.osmosis_percent)

    recipe = {
        "liters": payload.liters,
        "fertilizers": [_model_dump(entry) for entry in payload.fertilizers],
        "urea_as_nh4": payload.urea_as_nh4,
    }

    try:
        result = compute_solution(
            recipe,
            FERTILIZERS,
            MOLAR_MASSES,
            water_mg_l=water_mg_l,
            osmosis_percent=osmosis_percent,
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CalculationResponse(**result.to_dict())


@app.post("/solve", response_model=SolveResponse)
def solve(payload: SolveRequest) -> SolveResponse:
    _ensure_initialized()
    water_profile_data: Dict[str, Any] | None = None
    if payload.water_profile:
        water_profile_data = dict(payload.water_profile)
        raw_mg_per_l = water_profile_data.get("mg_per_l")
        if raw_mg_per_l is None:
            mg_per_l = {}
        elif isinstance(raw_mg_per_l, dict):
            mg_per_l = raw_mg_per_l
        else:
            raise HTTPException(
                status_code=400,
                detail="water_profile.mg_per_l must be an object",
            )
        water_profile_data["mg_per_l"] = _validated_water_mg_l(mg_per_l)
        water_profile_data["osmosis_percent"] = _validated_osmosis_percent(water_profile_data.get("osmosis_percent"))

    fertilizers_allowed = _validated_unique_names(
        payload.fertilizers_allowed,
        field_name="fertilizers_allowed",
    )
    recipe = {
        "liters": payload.liters,
        "targets": _validated_float_mapping(payload.targets, ALLOWED_TARGET_KEYS, "Invalid target key"),
        "fertilizers_allowed": fertilizers_allowed,
        "fixed_grams": payload.fixed_grams,
        "urea_as_nh4": payload.urea_as_nh4,
        "solver_config": _validated_solver_config(payload.solver_config),
    }

    try:
        result = solve_recipe_data(
            recipe,
            ferts=FERTILIZERS,
            mm=MOLAR_MASSES,
            water_profile_data=water_profile_data,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result_data = result.to_dict()
    try:
        _record_solver_history(recipe, result_data, water_profile_data)
    except Exception:
        logger.exception("Unable to record successful solver run")

    return SolveResponse(**result_data)


def _resolved_history_water_profile(water_profile_data: dict[str, Any] | None) -> dict[str, Any]:
    if water_profile_data is not None:
        return {
            "mg_per_l": dict(water_profile_data.get("mg_per_l") or {}),
            "osmosis_percent": float(water_profile_data.get("osmosis_percent", 0)),
        }
    layout = _portable_layout()
    default_path = resolve_layered_yaml_path(
        "default.yml",
        layout.water_profiles,
        shipped_water_profiles_dir(layout.root),
    )
    profile = load_water_profile_data(default_path)
    return {
        "mg_per_l": dict(profile.get("mg_per_l") or {}),
        "osmosis_percent": float(profile.get("osmosis_percent", 0)),
    }


def _history_calculation_snapshot(
    result_data: dict[str, Any],
    water_profile: dict[str, Any],
    *,
    urea_as_nh4: bool,
) -> dict[str, Any]:
    calculation = compute_solution(
        {
            "liters": result_data["liters"],
            "fertilizers": result_data.get("fertilizers") or [],
            "urea_as_nh4": urea_as_nh4,
        },
        FERTILIZERS,
        MOLAR_MASSES,
        water_mg_l=dict(water_profile.get("mg_per_l") or {}),
        osmosis_percent=float(water_profile.get("osmosis_percent", 0)),
    ).to_dict()
    return {
        "npk_metrics": calculation.get("npk_metrics") or {},
        "ec": calculation.get("ec") or {},
        "elements_mg_per_l": calculation.get("elements_mg_per_l") or {},
    }


def _record_solver_history(
    recipe: dict[str, Any],
    result_data: dict[str, Any],
    water_profile_data: dict[str, Any] | None,
) -> None:
    if os.environ.get("HORTICALC_TEST_DISABLE_SOLVER_HISTORY") == "1":
        return
    limit = _effective_solver_history_limit()
    if limit == 0:
        return
    water_profile = _resolved_history_water_profile(water_profile_data)
    try:
        calculation = _history_calculation_snapshot(
            result_data,
            water_profile,
            urea_as_nh4=bool(recipe.get("urea_as_nh4")),
        )
    except Exception:
        logger.exception("Unable to build printable calculation snapshot for solver history")
        calculation = {}

    fertilizer_kinds = {}
    for fertilizer in result_data.get("fertilizers") or []:
        name = str(fertilizer.get("name") or "")
        definition = FERTILIZERS.get(name)
        fertilizer_kinds[name] = "liquid" if definition is not None and definition.liquid else "solid"

    entry = {
        "schema_version": SOLVER_HISTORY_SCHEMA_VERSION,
        "id": str(uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "setup": {
            "liters": float(recipe.get("liters", result_data.get("liters", 10))),
            "targets": dict(recipe.get("targets") or {}),
            "water_profile": water_profile,
            "fertilizers_allowed": list(recipe.get("fertilizers_allowed") or []),
            "fixed_grams": dict(recipe.get("fixed_grams") or {}),
            "urea_as_nh4": bool(recipe.get("urea_as_nh4")),
            "solver_config": resolve_solver_config(recipe.get("solver_config")),
        },
        "result": result_data,
        "fertilizer_kinds": fertilizer_kinds,
        "calculation": calculation,
    }
    append_solver_history(_solver_history_path(), entry, limit)


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
