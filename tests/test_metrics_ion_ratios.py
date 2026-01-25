import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.metrics import format_npks


def test_npk_ratios_use_ions():
    metrics = format_npks(
        {
            "elements_mg_per_l": {
                "N_NH4": 10.0,
                "N_NO3": 30.0,
                "N_UREA": 0.0,
                "K": 20.0,
            },
            "oxides_mg_per_l": {
                "P2O5": 5.0,
                "K2O": 10.0,
                "CaO": 12.0,
                "MgO": 6.0,
            },
            "ions_mmol_per_l": {
                "NH4+": 1.0,
                "NO3-": 3.0,
                "K+": 2.0,
                "Ca+2": 4.0,
                "Mg+2": 1.0,
                "Na+": 0.5,
                "SO4^2-": 2.0,
                "H2PO4-": 1.0,
                "Cl-": 1.0,
                "HCO3-": 2.0,
            },
        }
    )

    assert metrics["npk_ratios"]["N:K"] == "N:K=1:0.5"
    assert metrics["npk_ratios"]["Ca2+:K+"] == "Ca2+:K+=1:0.5"
    assert metrics["npk_ratios"]["Mg2+:Ca2+"] == "Mg2+:Ca2+=1:4"
    assert metrics["npk_ratios"]["Na+:Mg2+"] == "Na+:Mg2+=1:2"
    assert metrics["npk_ratios"]["SO4^2-:PO4"] == "SO4^2-:PO4=1:0.5"
    assert metrics["npk_ratios"]["PO4:K+"] == "PO4:K+=1:2"
    assert metrics["npk_ratios"]["Cl-:HCO3-"] == "Cl-:HCO3-=1:2"
    assert metrics["npk_ratios"]["NH4+:NO3-"] == "NH4+:NO3-=1:3"
