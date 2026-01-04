from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from horticalc.core import compute_solution
from horticalc.data_io import (
    load_fertilizers,
    load_molar_masses,
    load_recipe,
    load_water_profile,
    repo_root,
)


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
DEFAULT_RECIPE_PATH = repo_root() / "recipes" / "default.yml"


class FertilizerEntry(BaseModel):
    name: str
    grams: float = Field(ge=0)


class RecipeRequest(BaseModel):
    liters: float = Field(default=10.0, gt=0)
    fertilizers: List[FertilizerEntry] = Field(default_factory=list)
    urea_as_nh4: bool = False
    phosphate_species: str = Field(default="H2PO4")
    water_profile_name: Optional[str] = None
    # NH4/NO3 are always molecule-based inputs; Ur-N stays element-N.
    water_mg_l: Optional[Dict[str, float]] = None


class CalculationResponse(BaseModel):
    liters: float
    elements_mg_per_l: Dict[str, float]
    oxides_mg_per_l: Dict[str, float]
    ions_mmol_per_l: Dict[str, float]
    ions_meq_per_l: Dict[str, float]
    ion_balance: Dict[str, float]


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
def water_profiles() -> List[str]:
    if not WATER_PROFILES_DIR.exists():
        return []
    return sorted([p.name for p in WATER_PROFILES_DIR.glob("*.yml")])


@app.get("/recipes/default")
def default_recipe() -> dict:
    if not DEFAULT_RECIPE_PATH.exists():
        raise HTTPException(status_code=404, detail="Default recipe not found")
    return load_recipe(DEFAULT_RECIPE_PATH)


@app.post("/calculate", response_model=CalculationResponse)
def calculate(payload: RecipeRequest) -> CalculationResponse:
    water_mg_l: Dict[str, float] = {}
    if payload.water_profile_name:
        profile_path = WATER_PROFILES_DIR / payload.water_profile_name
        if not profile_path.exists():
            raise HTTPException(status_code=404, detail="Water profile not found")
        water_mg_l = load_water_profile(profile_path)
    elif payload.water_mg_l:
        water_mg_l = payload.water_mg_l

    recipe = {
        "liters": payload.liters,
        "fertilizers": [entry.dict() for entry in payload.fertilizers],
        "urea_as_nh4": payload.urea_as_nh4,
        "phosphate_species": payload.phosphate_species,
    }

    try:
        result = compute_solution(recipe, FERTILIZERS, MOLAR_MASSES, water_mg_l=water_mg_l)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CalculationResponse(**result.to_dict())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
