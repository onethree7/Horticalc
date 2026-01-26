from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi import Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import yaml

from horticalc.core import (
    COMP_COLS,
    augment_water_profile_with_elements,
    compute_solution,
    normalize_water_profile,
)
from horticalc.data_io import (
    Fertilizer,
    load_fertilizers,
    load_molar_masses,
    load_nutrient_solution_data,
    load_recipe,
    load_water_profile_data,
    save_fertilizers,
    save_nutrient_solution,
    save_recipe,
    save_water_profile,
)
from horticalc.paths import (
    app_root,
    default_recipe_path,
    ensure_portable_layout,
)
from horticalc.solver import solve_recipe_data


app = FastAPI(title="Horticalc API", version="0.1.0")


FERTILIZERS: Dict[str, Fertilizer] = {}
MOLAR_MASSES: Dict[str, float] = {}
FRONTEND_DIR = app_root() / "frontend"
WATER_PROFILES_DIR: Path | None = None
NUTRIENT_SOLUTIONS_DIR: Path | None = None
DEFAULT_RECIPE_PATH: Path | None = None
RECIPES_DIR: Path | None = None


class FertilizerEntry(BaseModel):
    name: str
    grams: float = Field(ge=0)


class FertilizerPayload(BaseModel):
    name: str
    form: str | None = None
    weight_factor: float | None = None
    comp: Dict[str, float] | None = None


class RecipeRequest(BaseModel):
    liters: float = Field(default=10.0, gt=0)
    fertilizers: List[FertilizerEntry] = Field(default_factory=list)
    urea_as_nh4: bool = False
    phosphate_species: str = Field(default="H2PO4")
    water_profile_name: Optional[str] = None
    water_mg_l: Optional[Dict[str, float]] = None
    osmosis_percent: float | None = 0


class CalculationResponse(BaseModel):
    liters: float
    elements_mg_per_l: Dict[str, float]
    oxides_mg_per_l: Dict[str, float]
    ions_mmol_per_l: Dict[str, float]
    ions_meq_per_l: Dict[str, float]
    ion_balance: Dict[str, float]
    water_elements_mg_per_l: Dict[str, float]
    water_oxides_mg_per_l: Dict[str, float]
    water_ions_mmol_per_l: Dict[str, float]
    water_ions_meq_per_l: Dict[str, float]
    water_ion_balance: Dict[str, float]
    ec: Dict[str, Any]
    ec_water: Dict[str, Any]
    npk_metrics: Dict[str, Any]
    osmosis_percent: float


class SolveRequest(BaseModel):
    targets: Dict[str, float] = Field(default_factory=dict)
    liters: float = Field(default=10.0, gt=0)
    water_profile: Optional[Dict[str, Any]] = None
    fertilizers_allowed: List[str] = Field(default_factory=list)
    fixed_grams: Dict[str, float] = Field(default_factory=dict)
    urea_as_nh4: bool = False
    phosphate_species: str = Field(default="H2PO4")


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
    osmosis_percent: float | None = 0


class NutrientSolutionPayload(BaseModel):
    name: str
    source: Optional[str] = ""
    targets_mg_per_l: Dict[str, float] = Field(default_factory=dict)


class RecipePayload(BaseModel):
    name: str
    liters: float = Field(default=10.0, gt=0)
    fertilizers: List[FertilizerEntry] = Field(default_factory=list)
    urea_as_nh4: bool = False
    phosphate_species: str = Field(default="H2PO4")
    water_profile: Optional[str] = None
    osmosis_percent: float | None = 0


ALLOWED_WATER_KEYS = {
    "NH4",
    "NO3",
    "PO4",
    "P",
    "SO4",
    "S",
    "K",
    "Ca",
    "Mg",
    "Na",
    "Cl",
    "HCO3",
    "CO3",
    "CaCO3",
    "KH",
    "Fe",
    "Mn",
    "Cu",
    "Zn",
    "B",
    "Mo",
    "SiO2",
    "P2O5",
    "K2O",
    "CaO",
    "MgO",
    "Na2O",
}

ALLOWED_TARGET_KEYS = {
    "N_total",
    "N_NH4",
    "N_NO3",
    "N_UREA",
    "P",
    "K",
    "Ca",
    "Mg",
    "S",
    "SO4",
    "Fe",
    "Mn",
    "Cu",
    "Zn",
    "B",
    "Mo",
    "Si",
    "Cl",
    "Na",
    "HCO3",
}


def sanitize_water_profile(mg_per_l: Dict[str, float]) -> Dict[str, float]:
    sanitized: Dict[str, float] = {}
    for key, value in mg_per_l.items():
        try:
            sanitized[key] = float(value)
        except (TypeError, ValueError):
            sanitized[key] = 0.0
    return sanitized


def normalized_water_profile(mm: Dict[str, float], water_mg_l: Dict[str, float]) -> Dict[str, float]:
    normalized = normalize_water_profile(mm, water_mg_l)
    return augment_water_profile_with_elements(mm, normalized)


def _require_path(getter: Callable[[], Path | None], name: str) -> Path:
    _ensure_initialized()
    path = getter()
    if path is None:
        raise RuntimeError(f"{name} directory has not been initialized")
    return path


def _ensure_initialized() -> None:
    if not MOLAR_MASSES or WATER_PROFILES_DIR is None or NUTRIENT_SOLUTIONS_DIR is None or RECIPES_DIR is None:
        load_app_data()


@app.on_event("startup")
def load_app_data() -> None:
    layout = ensure_portable_layout()
    global FERTILIZERS, MOLAR_MASSES, WATER_PROFILES_DIR, NUTRIENT_SOLUTIONS_DIR, DEFAULT_RECIPE_PATH, RECIPES_DIR
    FERTILIZERS = load_fertilizers()
    MOLAR_MASSES = load_molar_masses()
    WATER_PROFILES_DIR = layout.water_profiles
    NUTRIENT_SOLUTIONS_DIR = layout.nutrient_solutions
    RECIPES_DIR = layout.recipes
    DEFAULT_RECIPE_PATH = default_recipe_path(layout.root)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/schema/fertilizer-comp-keys")
def fertilizer_comp_keys() -> dict:
    return {"keys": COMP_COLS}


@app.get("/fertilizers")
def fertilizers() -> List[dict]:
    _ensure_initialized()
    return [
        {
            "name": fert.name,
            "form": fert.form,
            "weight_factor": fert.weight_factor,
            "comp": fert.comp,
        }
        for fert in FERTILIZERS.values()
    ]


@app.put("/fertilizers")
def put_fertilizers(payload: List[FertilizerPayload]) -> dict:
    _ensure_initialized()
    new_ferts: Dict[str, Fertilizer] = {}
    for entry in payload:
        name = entry.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Düngername darf nicht leer sein")
        if name in new_ferts:
            raise HTTPException(status_code=400, detail="Düngernamen müssen eindeutig sein")

        form = entry.form.strip() if entry.form and entry.form.strip() else "fest"
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

        new_ferts[name] = Fertilizer(name=name, form=form, weight_factor=weight, comp=comp)

    global FERTILIZERS
    FERTILIZERS = new_ferts
    save_fertilizers(FERTILIZERS)
    return {"count": len(FERTILIZERS)}


@app.get("/water-profiles")
def water_profiles() -> List[dict]:
    water_profiles_dir = _require_path(lambda: WATER_PROFILES_DIR, "Water profiles")
    if not water_profiles_dir.exists():
        return []
    profiles = []
    for path in sorted(water_profiles_dir.glob("*.yml")):
        data = load_water_profile_data(path)
        profiles.append(
            {
                "name": data.get("name") or path.stem,
                "filename": path.name,
            }
        )
    return profiles


@app.get("/water-profiles/{profile_name}")
def water_profile(profile_name: str) -> dict:
    water_profiles_dir = _require_path(lambda: WATER_PROFILES_DIR, "Water profiles")
    filename = profile_name if profile_name.endswith(".yml") else f"{profile_name}.yml"
    profile_path = water_profiles_dir / filename
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="Water profile not found")
    data = load_water_profile_data(profile_path)
    mg_per_l = sanitize_water_profile(data.get("mg_per_l") or {})
    data["mg_per_l"] = mg_per_l
    data["normalized_mg_per_l"] = normalized_water_profile(MOLAR_MASSES, mg_per_l)
    return data


@app.get("/nutrient-solutions")
def nutrient_solutions() -> List[dict]:
    nutrient_solutions_dir = _require_path(lambda: NUTRIENT_SOLUTIONS_DIR, "Nutrient solutions")
    if not nutrient_solutions_dir.exists():
        return []
    solutions = []
    for path in sorted(nutrient_solutions_dir.glob("*.yml")):
        data = load_nutrient_solution_data(path)
        solutions.append(
            {
                "name": data.get("name") or path.stem,
                "filename": path.name,
            }
        )
    return solutions


@app.get("/nutrient-solutions/{solution_name}")
def nutrient_solution(solution_name: str) -> dict:
    nutrient_solutions_dir = _require_path(lambda: NUTRIENT_SOLUTIONS_DIR, "Nutrient solutions")
    filename = solution_name if solution_name.endswith(".yml") else f"{solution_name}.yml"
    solution_path = nutrient_solutions_dir / filename
    if not solution_path.exists():
        raise HTTPException(status_code=404, detail="Nutrient Solution not found")
    return load_nutrient_solution_data(solution_path)


@app.post("/water-profiles")
@app.put("/water-profiles")
async def save_profile(request: Request) -> dict:
    content_type = (request.headers.get("content-type") or "").lower()
    raw_body = await request.body()
    if "yaml" in content_type:
        payload = yaml.safe_load(raw_body.decode("utf-8")) or {}
    else:
        payload = await request.json()

    profile = WaterProfilePayload(**payload)
    name = profile.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Profile name is required")

    mg_per_l: Dict[str, float] = {}
    for key, value in profile.mg_per_l.items():
        if key not in ALLOWED_WATER_KEYS:
            raise HTTPException(status_code=400, detail=f"Invalid water key: {key}")
        try:
            mg_per_l[key] = float(value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"Invalid value for {key}") from exc

    mg_per_l = sanitize_water_profile(mg_per_l)

    osmosis_percent = profile.osmosis_percent if profile.osmosis_percent is not None else 0
    try:
        osmosis_percent = float(osmosis_percent)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid osmosis_percent value") from exc
    if not 0 <= osmosis_percent <= 100:
        raise HTTPException(status_code=400, detail="osmosis_percent must be between 0 and 100")

    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name).strip("_")
    if not safe_name:
        raise HTTPException(status_code=400, detail="Profile name results in empty filename")

    water_profiles_dir = _require_path(lambda: WATER_PROFILES_DIR, "Water profiles")
    profile_path = water_profiles_dir / f"{safe_name}.yml"
    water_profiles_dir.mkdir(parents=True, exist_ok=True)
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
    content_type = (request.headers.get("content-type") or "").lower()
    raw_body = await request.body()
    if "yaml" in content_type:
        payload = yaml.safe_load(raw_body.decode("utf-8")) or {}
    else:
        payload = await request.json()

    solution = NutrientSolutionPayload(**payload)
    name = solution.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nutrient Solution name is required")

    targets_mg_per_l: Dict[str, float] = {}
    for key, value in solution.targets_mg_per_l.items():
        if key not in ALLOWED_TARGET_KEYS:
            raise HTTPException(status_code=400, detail=f"Invalid target key: {key}")
        try:
            targets_mg_per_l[key] = float(value)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"Invalid value for {key}") from exc

    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name).strip("_")
    if not safe_name:
        raise HTTPException(status_code=400, detail="Nutrient Solution name results in empty filename")

    nutrient_solutions_dir = _require_path(lambda: NUTRIENT_SOLUTIONS_DIR, "Nutrient solutions")
    solution_path = nutrient_solutions_dir / f"{safe_name}.yml"
    nutrient_solutions_dir.mkdir(parents=True, exist_ok=True)
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
    default_recipe_path = _require_path(lambda: DEFAULT_RECIPE_PATH, "Recipes")
    if not default_recipe_path.exists():
        raise HTTPException(status_code=404, detail="Default recipe not found")
    return load_recipe(default_recipe_path)


@app.get("/recipes")
def recipes() -> List[dict]:
    recipes_dir = _require_path(lambda: RECIPES_DIR, "Recipes")
    if not recipes_dir.exists():
        return []
    recipes_out = []
    for path in sorted(recipes_dir.glob("*.yml")):
        if path.stem.startswith("solve_"):
            continue
        if path.name == "default.yml":
            continue
        data = load_recipe(path)
        recipes_out.append(
            {
                "name": data.get("name") or path.stem,
                "filename": path.name,
            }
        )
    return recipes_out


@app.get("/recipes/{recipe_name}")
def recipe(recipe_name: str) -> dict:
    recipes_dir = _require_path(lambda: RECIPES_DIR, "Recipes")
    filename = recipe_name if recipe_name.endswith(".yml") else f"{recipe_name}.yml"
    recipe_path = recipes_dir / filename
    if not recipe_path.exists():
        raise HTTPException(status_code=404, detail="Recipe not found")
    return load_recipe(recipe_path)


@app.post("/recipes")
@app.put("/recipes")
async def save_recipe_profile(request: Request) -> dict:
    content_type = (request.headers.get("content-type") or "").lower()
    raw_body = await request.body()
    if "yaml" in content_type:
        payload = yaml.safe_load(raw_body.decode("utf-8")) or {}
    else:
        payload = await request.json()

    recipe = RecipePayload(**payload)
    name = recipe.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Recipe name is required")

    safe_name = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name).strip("_")
    if not safe_name:
        raise HTTPException(status_code=400, detail="Recipe name results in empty filename")

    payload_out = {
        "name": name,
        "liters": recipe.liters,
        "fertilizers": [entry.dict() for entry in recipe.fertilizers],
        "urea_as_nh4": recipe.urea_as_nh4,
        "phosphate_species": recipe.phosphate_species,
    }
    if recipe.water_profile:
        payload_out["water_profile"] = recipe.water_profile
    if recipe.osmosis_percent is not None:
        payload_out["osmosis_percent"] = recipe.osmosis_percent

    recipes_dir = _require_path(lambda: RECIPES_DIR, "Recipes")
    recipe_path = recipes_dir / f"{safe_name}.yml"
    recipes_dir.mkdir(parents=True, exist_ok=True)
    save_recipe(recipe_path, payload_out)
    return {"status": "ok", "filename": recipe_path.name}


@app.post("/calculate", response_model=CalculationResponse)
def calculate(payload: RecipeRequest) -> CalculationResponse:
    _ensure_initialized()
    water_mg_l: Dict[str, float] = {}
    osmosis_percent = 0.0
    if payload.water_profile_name:
        water_profiles_dir = _require_path(lambda: WATER_PROFILES_DIR, "Water profiles")
        filename = (
            payload.water_profile_name
            if payload.water_profile_name.endswith(".yml")
            else f"{payload.water_profile_name}.yml"
        )
        profile_path = water_profiles_dir / filename
        if not profile_path.exists():
            raise HTTPException(status_code=404, detail="Water profile not found")
        profile = load_water_profile_data(profile_path)
        mg_per_l = profile.get("mg_per_l") or {}
        for key in mg_per_l:
            if key not in ALLOWED_WATER_KEYS:
                raise HTTPException(status_code=400, detail=f"Invalid water key: {key}")
        water_mg_l = sanitize_water_profile(mg_per_l)
        osmosis_percent = float(profile.get("osmosis_percent") or 0)
    elif payload.water_mg_l:
        for key, _ in payload.water_mg_l.items():
            if key not in ALLOWED_WATER_KEYS:
                raise HTTPException(status_code=400, detail=f"Invalid water key: {key}")
        water_mg_l = sanitize_water_profile(payload.water_mg_l)
        if payload.osmosis_percent is not None:
            osmosis_percent = float(payload.osmosis_percent)

    recipe = {
        "liters": payload.liters,
        "fertilizers": [entry.dict() for entry in payload.fertilizers],
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
        water_profile_data["mg_per_l"] = sanitize_water_profile(mg_per_l)
        if "osmosis_percent" not in water_profile_data:
            water_profile_data["osmosis_percent"] = 0.0

    targets: Dict[str, float] = {}
    for key, value in payload.targets.items():
        if key not in ALLOWED_TARGET_KEYS:
            raise HTTPException(status_code=400, detail=f"Invalid target key: {key}")
        targets[key] = value

    recipe = {
        "liters": payload.liters,
        "targets": targets,
        "fertilizers_allowed": payload.fertilizers_allowed,
        "fixed_grams": payload.fixed_grams,
        "urea_as_nh4": payload.urea_as_nh4,
        "phosphate_species": payload.phosphate_species,
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
