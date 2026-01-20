from horticalc.data_io import load_fertilizers


def test_fertilizer_data_excludes_nr_and_hco3():
    fertilizers = load_fertilizers()
    assert fertilizers, "Expected fertilizers to load"
    for fert in fertilizers.values():
        assert "Nr." not in fert.comp
        assert "Nr" not in fert.comp
        assert "NR" not in fert.comp
        assert "HCO3" not in fert.comp
