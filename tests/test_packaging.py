from horticalc import packaging


def test_packaging_spec_exists() -> None:
    spec_path = packaging.get_spec_path()
    assert spec_path.exists()
