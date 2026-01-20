import csv
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.data_io import Fertilizer, load_fertilizers, save_fertilizers


def test_load_fertilizers_ignores_nr_and_hco3_v(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    csv_path.write_text(
        "Nr.,Düngername,Form,Gewicht,NH4,HCO3,HCO3-V,Information\n"
        "1,Test,fest,1.0,0.1,0.2,0.3,notes\n",
        encoding="utf-8",
    )

    ferts = load_fertilizers(csv_path)
    fert = ferts["Test"]

    assert "NH4" in fert.comp
    assert "HCO3" in fert.comp
    assert "Nr." not in fert.comp
    assert "HCO3-V" not in fert.comp
    assert "Information" not in fert.comp


def test_save_fertilizers_preserves_nr_header_and_blanks_hco3_v(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    csv_path.write_text(
        "Nr.,Düngername,Form,Gewicht,NH4,HCO3,HCO3-V\n", encoding="utf-8"
    )

    ferts = {
        "Alpha": Fertilizer(
            name="Alpha",
            form="fest",
            weight_factor=1.0,
            comp={"NH4": 0.1, "HCO3": 0.2, "HCO3-V": 0.3},
        )
    }
    save_fertilizers(ferts, csv_path)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None
        assert reader.fieldnames[0] == "Nr."
        rows = list(reader)

    assert rows[0]["Nr."] == "1"
    assert rows[0]["HCO3-V"] == ""
    assert float(rows[0]["HCO3"]) == pytest.approx(0.2, rel=0, abs=1e-12)
