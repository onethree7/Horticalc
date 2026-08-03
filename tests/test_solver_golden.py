from pathlib import Path

import pytest

from horticalc.solver import solve_recipe


def test_solver_golden_solution_close() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "recipes" / "solve_golden.yml"
    result = solve_recipe(recipe_path, solver_config_overrides={"solver_model": "mass_nnls"})

    assert result.solver_model == "mass_nnls"
    objective_upper = {key.upper() for key in result.objective_elements}
    assert "S" in objective_upper
    assert "SO4" not in objective_upper
    assert "NA" not in objective_upper
    assert "CL" not in objective_upper

    macro_keys = {"N_TOTAL", "P", "K", "CA", "MG", "S"}
    macro_errors_mg_l = [abs(error) for key, error in result.errors_mg_l.items() if key.upper() in macro_keys]
    trace_errors_mg_l = [abs(error) for key, error in result.errors_mg_l.items() if key.upper() not in macro_keys]

    assert max(macro_errors_mg_l) <= 4.0
    assert max(trace_errors_mg_l) <= 1.0


def test_solver_golden_uses_recipe_derived_s_target_when_enabled() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "recipes" / "solve_golden.yml"

    result = solve_recipe(
        recipe_path,
        solver_config_overrides={"solver_model": "legacy", "s_objective_enabled": True},
    )

    assert "S" in result.objective_elements
    assert result.targets_mg_l["S"] == pytest.approx(85.79586471044226)


def test_augmented_saloner_bernstein_solution_is_stable() -> None:
    recipe_path = Path(__file__).resolve().parents[1] / "recipes" / "solve_augmented_saloner_bernstein.yml"

    result = solve_recipe(recipe_path)

    assert result.objective_elements == [
        "B",
        "Ca",
        "Cu",
        "Fe",
        "K",
        "Mg",
        "Mn",
        "Mo",
        "N_total",
        "P",
        "S",
        "Si",
        "Zn",
    ]

    fertilizer_doses = {entry["name"]: entry["grams"] for entry in result.fertilizers}
    assert fertilizer_doses == pytest.approx(
        {
            "Yara Tera CALCINIT": 3.5400667611842356,
            "K+S EPSO Top Bittersalz 16-39": 0.3514281081202175,
            "S3 Kaliwasser 28 Be": 0.6451058228516668,
            "Compo Fetrilon Combi 1": 0.17243495009427762,
            "Haifa MAG Magnesiumnitrat 11-0-0+16MgO": 2.0246713748373297,
            "ICL Nova PeKacid 0-60-20": 0.4612283348195081,
            "Agrolution Special 313 14-7-14+14CaO+TE": 1.7629679291508717,
            "Compo Hakaphos Soft16-8-22(+3) Spezial": 3.5904274184269394,
        },
        rel=0.0,
        abs=1e-6,
    )

    achieved = {key: result.achieved_elements_mg_l[key] for key in result.targets_mg_l}
    assert achieved == pytest.approx(
        {
            "B": 0.2169999768914585,
            "Ca": 119.80105533292209,
            "Cl": 10.879999999999999,
            "Cu": 0.3487706528014719,
            "Fe": 1.5124187818053114,
            "HCO3": 105.12799999999999,
            "K": 100.00214001458366,
            "Mg": 35.20144237718789,
            "Mn": 1.1520160399626165,
            "Mo": 0.05282531139307164,
            "N_NH4": 27.088081646808497,
            "N_NO3": 128.85582694491396,
            "N_UREA": 4.054826237046979,
            "N_total": 159.99873482876941,
            "Na": 5.4399999999999995,
            "P": 29.998643107305597,
            "S": 24.998929571598765,
            "Si": 10.99855216185143,
            "Zn": 0.3480906528014719,
        },
        rel=0.0,
        abs=1e-6,
    )
