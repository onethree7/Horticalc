from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import yaml

from horticalc.core import compute_solution
from horticalc.data_io import (
    load_fertilizers,
    load_molar_masses,
    load_nutrient_solution_data,
    load_recipe,
    load_water_profile_data,
    repo_root,
    save_nutrient_solution,
    save_recipe,
    save_water_profile,
)
from horticalc.solver import solve_recipe_data


app = FastAPI(title="Horticalc API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


FERTILIZERS = load_fertilizers()
MOLAR_MASSES = load_molar_masses()
WATER_PROFILES_DIR = repo_root() / "data" / "water_profiles"
NUTRIENT_SOLUTIONS_DIR = repo_root() / "data" / "nutrient_solutions"
DEFAULT_RECIPE_PATH = repo_root() / "recipes" / "default.yml"
RECIPES_DIR = repo_root() / "recipes"


class FertilizerEntry(BaseModel):
    name: str
    grams: float = Field(ge=0)


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
    "NH3",
    "NO3",
    "NO2",
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


def hco3_from_caco3(value: float) -> float:
    if value == 0.0:
        return 0.0
    equiv_weight_caco3 = MOLAR_MASSES["CaCO3"] / 2.0
    return value * MOLAR_MASSES["HCO3"] / equiv_weight_caco3


def hco3_from_kh(value: float) -> float:
    if value == 0.0:
        return 0.0
    mg_l_caco3 = value * 17.848
    return hco3_from_caco3(mg_l_caco3)


def sanitize_water_profile(mg_per_l: Dict[str, float]) -> Dict[str, float]:
    sanitized = dict(mg_per_l)
    hco3 = sanitized.get("HCO3", 0.0)
    if hco3 == 0.0:
        hco3 = hco3_from_caco3(sanitized.get("CaCO3", 0.0)) + hco3_from_kh(sanitized.get("KH", 0.0))
        if hco3:
            sanitized["HCO3"] = hco3
    for key in ("KH", "CaCO3", "CO3"):
        sanitized.pop(key, None)
    return sanitized


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/fertilizers")
def fertilizers() -> List[dict]:
    return [
        {
            "name": fert.name,
            "form": fert.form,
            "weight_factor": fert.weight_factor,
            "comp": fert.comp,
        }
        for fert in FERTILIZERS.values()
    ]


@app.get("/water-profiles")
def water_profiles() -> List[dict]:
    if not WATER_PROFILES_DIR.exists():
        return []
    profiles = []
    for path in sorted(WATER_PROFILES_DIR.glob("*.yml")):
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
    filename = profile_name if profile_name.endswith(".yml") else f"{profile_name}.yml"
    profile_path = WATER_PROFILES_DIR / filename
    if not profile_path.exists():
        raise HTTPException(status_code=404, detail="Water profile not found")
    return load_water_profile_data(profile_path)


@app.get("/nutrient-solutions")
def nutrient_solutions() -> List[dict]:
    if not NUTRIENT_SOLUTIONS_DIR.exists():
        return []
    solutions = []
    for path in sorted(NUTRIENT_SOLUTIONS_DIR.glob("*.yml")):
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
    filename = solution_name if solution_name.endswith(".yml") else f"{solution_name}.yml"
    solution_path = NUTRIENT_SOLUTIONS_DIR / filename
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

    profile_path = WATER_PROFILES_DIR / f"{safe_name}.yml"
    WATER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
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

    solution_path = NUTRIENT_SOLUTIONS_DIR / f"{safe_name}.yml"
    NUTRIENT_SOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
    save_nutrient_solution(
        solution_path,
        name=name,
        source=solution.source or "",
        targets_mg_per_l=targets_mg_per_l,
    )
    return {"status": "ok", "filename": solution_path.name}


@app.get("/molar-masses")
def molar_masses() -> Dict[str, float]:
    return MOLAR_MASSES


@app.get("/recipes/default")
def default_recipe() -> dict:
    if not DEFAULT_RECIPE_PATH.exists():
        raise HTTPException(status_code=404, detail="Default recipe not found")
    return load_recipe(DEFAULT_RECIPE_PATH)


@app.get("/recipes")
def recipes() -> List[dict]:
    if not RECIPES_DIR.exists():
        return []
    recipes_out = []
    for path in sorted(RECIPES_DIR.glob("*.yml")):
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
    filename = recipe_name if recipe_name.endswith(".yml") else f"{recipe_name}.yml"
    recipe_path = RECIPES_DIR / filename
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

    recipe_path = RECIPES_DIR / f"{safe_name}.yml"
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    save_recipe(recipe_path, payload_out)
    return {"status": "ok", "filename": recipe_path.name}


@app.post("/calculate", response_model=CalculationResponse)
def calculate(payload: RecipeRequest) -> CalculationResponse:
    water_mg_l: Dict[str, float] = {}
    osmosis_percent = 0.0
    if payload.water_profile_name:
        profile_path = WATER_PROFILES_DIR / payload.water_profile_name
        if not profile_path.exists():
            raise HTTPException(status_code=404, detail="Water profile not found")
        profile = load_water_profile_data(profile_path)
        water_mg_l = sanitize_water_profile(profile.get("mg_per_l") or {})
        osmosis_percent = float(profile.get("osmosis_percent") or 0)
    elif payload.water_mg_l:
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
    water_profile_data: Dict[str, Any] | None = None
    if payload.water_profile:
        water_profile_data = dict(payload.water_profile)
        mg_per_l = water_profile_data.get("mg_per_l") or {}
        water_profile_data["mg_per_l"] = sanitize_water_profile(mg_per_l)
        if "osmosis_percent" not in water_profile_data:
            water_profile_data["osmosis_percent"] = 0.0

    recipe = {
        "liters": payload.liters,
        "targets": payload.targets,
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
