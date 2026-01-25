from __future__ import annotations

WATER_PROFILE_FIELDS: tuple[dict[str, object], ...] = (
    {"key": "NH4", "label": "Ammonium in NH4", "normalize": True},
    {"key": "NO3", "label": "Nitrat in NO3", "normalize": True},
    {"key": "PO4", "label": "Phosphat in PO4"},
    {"key": "P", "label": "Phosphor in P"},
    {"key": "K", "label": "Kalium in K"},
    {"key": "Ca", "label": "Calcium in Ca"},
    {"key": "Mg", "label": "Magnesium in Mg"},
    {"key": "Na", "label": "Natrium in Na"},
    {"key": "SO4", "label": "Sulfat in SO4", "normalize": True},
    {"key": "S", "label": "Schwefel in S"},
    {"key": "Fe", "label": "Eisen in Fe", "normalize": True},
    {"key": "Mn", "label": "Mangan in Mn", "normalize": True},
    {"key": "Cu", "label": "Kupfer in Cu", "normalize": True},
    {"key": "Zn", "label": "Zink in Zn", "normalize": True},
    {"key": "B", "label": "Bor in B", "normalize": True},
    {"key": "Mo", "label": "Molybdän in Mo", "normalize": True},
    {"key": "Cl", "label": "Chlor in Cl", "normalize": True},
    {"key": "HCO3", "label": "Carbonate in HCO3", "normalize": True},
    {"key": "CO3", "label": "Carbonat in CO3"},
    {"key": "CaCO3", "label": "Gesamtcarbonathärte in CaCO3"},
    {"key": "KH", "label": "Carbonathärte in °KH"},
    {"key": "SiO2", "label": "Silicium in SiO2", "normalize": True},
    {"key": "P2O5", "label": "Phosphor in P2O5", "normalize": True},
    {"key": "K2O", "label": "Kalium in K2O", "normalize": True},
    {"key": "CaO", "label": "Calcium in CaO", "normalize": True},
    {"key": "MgO", "label": "Magnesium in MgO", "normalize": True},
    {"key": "Na2O", "label": "Natrium in Na2O", "normalize": True},
)

WATER_PROFILE_KEYS: list[str] = [
    field["key"] for field in WATER_PROFILE_FIELDS if field.get("normalize")
]
WATER_PROFILE_INPUT_KEYS: list[str] = [field["key"] for field in WATER_PROFILE_FIELDS]


def water_profile_schema() -> list[dict[str, str]]:
    return [
        {"key": field["key"], "label": str(field.get("label") or field["key"])}
        for field in WATER_PROFILE_FIELDS
    ]
