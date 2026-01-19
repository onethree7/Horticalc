import csv
from io import StringIO

from horticalc.data_io import Fertilizer, save_fertilizers


def read_csv_rows(path):
    with path.open("r", encoding="utf-8", newline="") as file_handle:
        content = file_handle.read()
    reader = csv.DictReader(StringIO(content))
    return reader.fieldnames, list(reader)


def test_save_fertilizers_preserves_header(tmp_path):
    csv_path = tmp_path / "fertilizers.csv"
    csv_path.write_text("NR,Düngername,Form,Gewicht,NO3,NH4\n", encoding="utf-8")
    fertilizers = {
        "Alpha": Fertilizer(name="Alpha", form="fest", weight_factor=1.0, comp={"NO3": 0.1}),
        "beta": Fertilizer(name="beta", form="flüssig", weight_factor=2.0, comp={"NH4": 0.2, "P": 0.3}),
    }

    save_fertilizers(fertilizers, csv_path)

    header, rows = read_csv_rows(csv_path)
    assert header == ["NR", "Düngername", "Form", "Gewicht", "NO3", "NH4"]
    assert [row["Düngername"] for row in rows] == ["Alpha", "beta"]
    assert [row["NR"] for row in rows] == ["1", "2"]
    assert rows[0]["NO3"] == "0.1"
    assert rows[1]["NH4"] == "0.2"


def test_save_fertilizers_fallback_header(tmp_path):
    csv_path = tmp_path / "fertilizers.csv"
    fertilizers = {
        "Zeta": Fertilizer(name="Zeta", form="fest", weight_factor=1.0, comp={"K": 0.2}),
        "Alpha": Fertilizer(name="Alpha", form="fest", weight_factor=1.0, comp={"NO3": 0.1, "Ur-N": 0.05}),
    }

    save_fertilizers(fertilizers, csv_path)

    header, rows = read_csv_rows(csv_path)
    assert header == ["NR", "Düngername", "Form", "Gewicht", "K", "NO3", "Ur-N"]
    assert [row["Düngername"] for row in rows] == ["Alpha", "Zeta"]
