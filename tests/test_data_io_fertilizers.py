import csv
from pathlib import Path

from horticalc.data_io import Fertilizer, load_fertilizers, save_fertilizers

def test_load_fertilizers_ignores_number_field(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Nr.", "Düngername", "Form", "Gewicht", "NH4", "NO3"])
        writer.writerow(["12", "Test Dünger", "fest", "1.5", "0.12", "0"])

    fertilizers = load_fertilizers(csv_path)
    fert = fertilizers["Test Dünger"]

    assert fert.comp == {"NH4": 0.12}

def test_load_fertilizers_accepts_ascii_name_header(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["NR", "Duengername", "Form", "Gewicht", "NO3"])
        writer.writerow(["1", "Ascii Header", "fest", "1", "0.11"])

    fertilizers = load_fertilizers(csv_path)

    assert fertilizers["Ascii Header"].comp == {"NO3": 0.11}

def test_save_fertilizers_removes_legacy_number_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Nr.", "Düngername", "Form", "Gewicht", "NH4"])

    fertilizers = {
        "Test Dünger": Fertilizer(
            name="Test Dünger",
            form="fest",
            weight_factor=1.5,
            comp={"NH4": 0.12},
        )
    }
    save_fertilizers(fertilizers, csv_path)

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert reader.fieldnames == ["Düngername", "Form", "Gewicht", "NH4"]
    assert rows[0]["NH4"] == "0.12"


def test_load_fertilizers_sorts_factory_and_user_names_together(tmp_path: Path) -> None:
    csv_path = tmp_path / "fertilizers.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Düngername", "Form", "Gewicht", "NO3"])
        writer.writerow(["zeta", "fest", "1", "0.1"])
        writer.writerow(["Ähre", "fest", "1", "0.2"])
        writer.writerow(["Alpha", "fest", "1", "0.3"])

    assert list(load_fertilizers(csv_path)) == ["Alpha", "zeta", "Ähre"]
