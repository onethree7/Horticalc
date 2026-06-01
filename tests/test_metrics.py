import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.metrics import format_npks


def test_npk_metrics_include_element_mg_l_ion_ratios() -> None:
    metrics = format_npks(
        {
            "elements_mg_per_l": {
                "N_NH4": 20.0,
                "K": 10.0,
                "Ca": 100.0,
                "Mg": 30.0,
                "Na": 0.0,
                "S": 40.0,
                "P": 40.0,
                "Fe": 1.0,
                "Si": 5.0,
            },
            "oxides_mg_per_l": {
                "P2O5": 90.0,
                "K2O": 12.0,
                "CaO": 56.0774,
                "MgO": 40.3044,
                "Na2O": 0.0,
                "SO4": 120.0,
                "CO3": 10.0,
                "SiO2": 0.0,
            },
        }
    )

    assert metrics["npk_ratios_ion"]["Ca:Mg"] == "Ca:Mg=1:0.3"
    assert metrics["npk_ratios_ion"]["N:K"] == "N:K=1:0.5"
    assert metrics["npk_ratios_ion"]["SO4:P"] == "SO4:P=1:0.3"
    assert metrics["npk_ratios_ion"]["CO3:Si"] == "CO3:Si=1:0.5"
    assert metrics["npk_ratios"]["MgO:CaO"] == "MgO:CaO=1:1.4"
