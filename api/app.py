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
    load_recipe,
    load_water_profile,
    load_water_profile_data,
    repo_root,
    save_water_profile,
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
    water_mg_l: Optional[Dict[str, float]] = None


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


class WaterProfilePayload(BaseModel):
    name: str
    source: Optional[str] = ""
    mg_per_l: Dict[str, float] = Field(default_factory=dict)
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


@app.get("/molar-masses")
def molar_masses() -> Dict[str, float]:
    return MOLAR_MASSES


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
        profile = load_water_profile_data(profile_path)
        water_mg_l = sanitize_water_profile(profile.get("mg_per_l") or {})
        osmosis_percent = float(profile.get("osmosis_percent") or 0)
        if osmosis_percent:
            factor = 1 - max(min(osmosis_percent, 100.0), 0.0) / 100.0
            water_mg_l = {key: value * factor for key, value in water_mg_l.items()}
    elif payload.water_mg_l:
        water_mg_l = sanitize_water_profile(payload.water_mg_l)

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
