from __future__ import annotations

import logging
import math
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, FiniteFloat, ValidationError

import yaml

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
from horticalc.paths import (
    PortableLayout,
    app_root,
    default_recipe_path,
    ensure_portable_layout,
)
from horticalc.solver import solve_recipe_data
from horticalc.solver_config import SOLVER_CONFIG_DEFINITIONS, validate_solver_config


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    load_app_data()
    yield


app = FastAPI(title="Horticalc API", version="0.1.0", lifespan=lifespan)


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


class PreferencesPayload(BaseModel):
    theme: Optional[str] = None
    default_liters: Optional[FiniteFloat] = Field(default=None, gt=0)
    solver_config: Optional[Dict[str, Any]] = None
    last_water_profile: Optional[str] = None


class RecipeRequest(BaseModel):
    liters: FiniteFloat = Field(default=10.0, gt=0)
    fertilizers: List[FertilizerEntry] = Field(default_factory=list)
    urea_as_nh4: bool = False
    phosphate_species: str = Field(default="H2PO4")
    water_profile_name: Optional[str] = None
    water_mg_l: Optional[Dict[str, float]] = None
    osmosis_percent: FiniteFloat | None = 0


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
    phosphate_species: str = Field(default="H2PO4")
    solver_config: Dict[str, Any] = Field(default_factory=dict)


class SolveFertilizerEntry(BaseModel):
    name: str
    grams: float


class SolveResponse(BaseModel):
    liters: float
    fertilizers: List[SolveFertilizerEntry]
    objective_elements: List[str]
    targets_mg_per_l: Dict[str, float]
    achieved_elements_mg_per_l: Dict[str, float]
    errors_mg_per_l: Dict[str, float]
    errors_percent: Dict[str, float]


class WaterProfilePayload(BaseModel):
    name: str
    source: Optional[str] = ""
    mg_per_l: Dict[str, float] = Field(default_factory=dict)
    osmosis_percent: FiniteFloat | None = 0


class NutrientSolutionPayload(BaseModel):
    name: str
    source: Optional[str] = ""
    targets_mg_per_l: Dict[str, float] = Field(default_factory=dict)


class RecipePayload(BaseModel):
    name: str
    liters: FiniteFloat = Field(default=10.0, gt=0)
    fertilizers: List[FertilizerEntry] = Field(default_factory=list)
    fertilizers_allowed: List[str] = Field(default_factory=list)
    urea_as_nh4: bool = False
    phosphate_species: str = Field(default="H2PO4")
    water_profile: Optional[str] = None
    osmosis_percent: FiniteFloat | None = 0
    solver_config: Dict[str, Any] = Field(default_factory=dict)


async def _parse_request_payload(request: Request) -> dict:
    content_type = (request.headers.get("content-type") or "").lower()
    try:
        if "yaml" in content_type:
            raw_body = await request.body()
            payload = yaml.safe_load(raw_body.decode("utf-8")) or {}
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
        raise HTTPException(status_code=422, detail=exc.errors(include_url=False)) from exc


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
    directory: Path,
    loader: Callable[[Path], dict],
    skip: Callable[[Path], bool] | None = None,
) -> List[dict]:
    if not directory.exists():
        return []
    entries = []
    for path in sorted(directory.glob("*.yml")):
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
            numeric_value = float(value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"Invalid value for {key}") from exc
        if not math.isfinite(numeric_value):
            raise HTTPException(status_code=400, detail=f"Invalid value for {key}")
        result[key] = numeric_value
    return result


def _validated_water_mg_l(values: Dict[str, Any]) -> Dict[str, float]:
    return _validated_float_mapping(values, ALLOWED_WATER_KEYS, "Invalid water key")


def _validated_osmosis_percent(value: Any) -> float:
    try:
        numeric_value = float(value or 0)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid osmosis_percent value") from exc
    if not math.isfinite(numeric_value):
        raise HTTPException(status_code=400, detail="Invalid osmosis_percent value")
    return numeric_value


def _validated_solver_config(
    values: Dict[str, Any],
    *,
    allow_advanced: bool = True,
) -> Dict[str, Any]:
    try:
        return validate_solver_config(values, allow_advanced=allow_advanced)
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


THEME_OPTIONS = {
    "horticalc-dark",
    "horticalc-light",
    "high-contrast",
    "soil",
    "gch-classic",
    "vt-green",
    "blue-matrix",
}


@app.get("/preferences")
def preferences() -> dict[str, Any]:
    return load_user_preferences()


@app.put("/preferences")
def put_preferences(payload: PreferencesPayload) -> dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True)
    if "theme" in updates and payload.theme not in THEME_OPTIONS:
        raise HTTPException(status_code=400, detail="Unknown theme")
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
    preferences = load_user_preferences()
    preferences.update(updates)
    save_user_preferences(preferences)
    return preferences


@app.get("/fertilizers")
def fertilizers() -> List[dict]:
    _ensure_initialized()
    return [
        {
            "name": fert.name,
            "liquid": fert.liquid,
            "weight_factor": fert.weight_factor,
            "comp": fert.comp,
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
            raise HTTPException(status_code=400, detail="Düngername darf nicht leer sein")
        name_key = fertilizer_name_key(name)
        if name_key in seen_names:
            raise HTTPException(status_code=400, detail="Düngernamen müssen eindeutig sein")
        seen_names.add(name_key)

        weight = entry.weight_factor if entry.weight_factor is not None else 1.0
        if not math.isfinite(weight):
            raise HTTPException(status_code=400, detail="Ungültiger Gewichtswert")

        comp: Dict[str, float] = {}
        if entry.comp:
            for key, value in entry.comp.items():
                if not math.isfinite(value):
                    raise HTTPException(status_code=400, detail="Ungültiger Nährstoffwert")
                if value == 0:
                    continue
                comp[key] = value

        new_ferts[name] = Fertilizer(name=name, liquid=entry.liquid, weight_factor=weight, comp=comp)

    global FERTILIZERS
    save_fertilizers(new_ferts)
    FERTILIZERS = new_ferts
    return {"count": len(new_ferts)}


@app.get("/water-profiles")
def water_profiles() -> List[dict]:
    water_profiles_dir = _portable_layout().water_profiles
    return _named_yaml_entries(water_profiles_dir, load_water_profile_data)


@app.get("/water-profiles/{profile_name}")
def water_profile(profile_name: str) -> dict:
    water_profiles_dir = _portable_layout().water_profiles
    profile_path = water_profiles_dir / _yaml_filename(profile_name)
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="Water profile not found")
    data = load_water_profile_data(profile_path)
    mg_per_l = _validated_water_mg_l(data.get("mg_per_l") or {})
    data["mg_per_l"] = mg_per_l
    normalized = normalize_water_profile(MOLAR_MASSES, mg_per_l)
    data["normalized_mg_per_l"] = augment_water_profile_with_elements(MOLAR_MASSES, normalized)
    return data


@app.get("/nutrient-solutions")
def nutrient_solutions() -> List[dict]:
    nutrient_solutions_dir = _portable_layout().nutrient_solutions
    return _named_yaml_entries(nutrient_solutions_dir, load_nutrient_solution_data)


@app.get("/nutrient-solutions/{solution_name}")
def nutrient_solution(solution_name: str) -> dict:
    nutrient_solutions_dir = _portable_layout().nutrient_solutions
    solution_path = nutrient_solutions_dir / _yaml_filename(solution_name)
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
    if not 0 <= osmosis_percent <= 100:
        raise HTTPException(status_code=400, detail="osmosis_percent must be between 0 and 100")

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

    targets_mg_per_l = _validated_float_mapping(
        solution.targets_mg_per_l,
        ALLOWED_TARGET_KEYS,
        "Invalid target key",
    )

    nutrient_solutions_dir = _portable_layout().nutrient_solutions
    solution_path = _saved_yaml_path(
        nutrient_solutions_dir,
        name,
        "Nutrient Solution name results in empty filename",
    )
    save_nutrient_solution(
        solution_path,
        name=name,
        source=solution.source or "",
        targets_mg_per_l=targets_mg_per_l,
    )
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
    recipes_dir = _portable_layout().recipes
    return _named_yaml_entries(
        recipes_dir,
        load_recipe,
        skip=lambda path: path.stem.startswith("solve_") or path.name == "default.yml",
    )


@app.get("/recipes/{recipe_name}")
def recipe(recipe_name: str) -> dict:
    recipes_dir = _portable_layout().recipes
    recipe_path = recipes_dir / _yaml_filename(recipe_name)
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

    payload_out = {
        "name": name,
        "liters": recipe.liters,
        "fertilizers": [_model_dump(entry) for entry in recipe.fertilizers],
        "fertilizers_allowed": [str(name) for name in recipe.fertilizers_allowed if str(name).strip()],
        "urea_as_nh4": recipe.urea_as_nh4,
        "phosphate_species": recipe.phosphate_species,
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
        water_profiles_dir = _portable_layout().water_profiles
        profile_path = water_profiles_dir / _yaml_filename(payload.water_profile_name)
        if not profile_path.exists():
            raise HTTPException(status_code=404, detail="Water profile not found")
        profile = load_water_profile_data(profile_path)
        mg_per_l = profile.get("mg_per_l") or {}
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
        "phosphate_species": payload.phosphate_species,
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
        mg_per_l = water_profile_data.get("mg_per_l") or {}
        water_profile_data["mg_per_l"] = _validated_water_mg_l(mg_per_l)
        water_profile_data["osmosis_percent"] = _validated_osmosis_percent(
            water_profile_data.get("osmosis_percent")
        )

    recipe = {
        "liters": payload.liters,
        "targets": _validated_float_mapping(payload.targets, ALLOWED_TARGET_KEYS, "Invalid target key"),
        "fertilizers_allowed": payload.fertilizers_allowed,
        "fixed_grams": payload.fixed_grams,
        "urea_as_nh4": payload.urea_as_nh4,
        "phosphate_species": payload.phosphate_species,
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

    return SolveResponse(**result.to_dict())


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
