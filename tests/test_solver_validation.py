import pytest

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import (
    SOLVER_OUTPUT_DOSE_EPSILON,
    SolveResult,
    _build_solution_payload,
    _validate_solve_result,
    solve_recipe_data,
)


def _solve_result(*, grams: float = 1.0, achieved: float = 100.0) -> SolveResult:
    return SolveResult(
        liters=10.0,
        solver_model="nnls_tuning",
        fertilizers=[{"name": "K test", "grams": grams}],
        objective_elements=["K"],
        ignored_elements=[],
        target_priorities={},
        priority_stages=[],
        targets_mg_l={"K": 100.0},
        achieved_elements_mg_l={"K": achieved},
        errors_mg_l={"K": achieved - 100.0},
        errors_percent={"K": achieved - 100.0},
    )


def test_shared_solver_result_validation_rejects_non_finite_values() -> None:
    with pytest.raises(ValueError, match=r"NNLS \+ tuning solver produced a non-finite result"):
        _validate_solve_result(_solve_result(achieved=float("nan")))


def test_shared_solver_result_validation_rejects_negative_doses() -> None:
    with pytest.raises(ValueError, match=r"NNLS \+ tuning solver produced a negative fertilizer dose"):
        _validate_solve_result(_solve_result(grams=-0.1))


def test_solver_output_omits_numerical_dose_residue() -> None:
    fertilizers = [
        Fertilizer("Below epsilon", False, 1.0, {}),
        Fertilizer("At epsilon", False, 1.0, {}),
        Fertilizer("Above epsilon", False, 1.0, {}),
    ]

    output, recipe = _build_solution_payload(
        weights=[
            SOLVER_OUTPUT_DOSE_EPSILON / 10.0,
            SOLVER_OUTPUT_DOSE_EPSILON,
            SOLVER_OUTPUT_DOSE_EPSILON * 10.0,
        ],
        allowed=fertilizers,
        liters=10.0,
        recipe={},
    )

    expected = [{"name": "Above epsilon", "grams": SOLVER_OUTPUT_DOSE_EPSILON * 10.0}]
    assert output == expected
    assert recipe["fertilizers"] == expected


def test_solve_recipe_data_rejects_invalid_target_key() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K2O test": Fertilizer("K2O test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K2O test"],
        "targets": {"K2O": 100.0},
    }

    with pytest.raises(ValueError, match="Invalid target key: K2O"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_non_positive_liters() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 0,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "targets": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="liters must be > 0"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_invalid_solver_config() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "targets": {"K": 10.0},
        "fertilizers_allowed": ["K test"],
        "solver_config": {"relative_weighting": "false"},
    }

    with pytest.raises(ValueError, match="Invalid solver config value: relative_weighting"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_negative_fixed_grams() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "fixed_grams": {"K test": -1.0},
        "targets": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="fixed_grams must be >= 0: K test"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_fixed_grams_outside_allowed_list() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
        "Other": Fertilizer("Other", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "fixed_grams": {"Other": 1.0},
        "targets": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="fixed_grams not in fertilizers_allowed"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_rejects_duplicate_fertilizers_allowed() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test", "K test"],
        "targets": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="fertilizers_allowed must not contain duplicates"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_does_not_use_water_elements_as_targets() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K test": Fertilizer("K test", False, 1.0, {"K2O": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["K test"],
        "water_elements_mg_per_l": {"K": 100.0},
    }

    with pytest.raises(ValueError, match="No solvable targets defined"):
        solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)


def test_solve_recipe_data_can_solve_hco3_from_direct_hco3_composition() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "HCO3 test": Fertilizer("HCO3 test", False, 1.0, {"HCO3": 1.0}),
    }
    recipe = {
        "liters": 1,
        "water_profile": {"mg_per_l": {}},
        "fertilizers_allowed": ["HCO3 test"],
        "targets": {"HCO3": 100.0},
    }

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses)

    assert result.objective_elements == ["HCO3"]
    assert result.fertilizers == [{"name": "HCO3 test", "grams": pytest.approx(0.1, abs=1e-12)}]
    assert result.achieved_elements_mg_l["HCO3"] == pytest.approx(100.0, abs=1e-10)


def test_water_profile_overshoot_remains_visible_in_errors() -> None:
    molar_masses = load_molar_masses()
    ferts = {
        "K-only": Fertilizer(name="K-only", liquid=False, weight_factor=1.0, comp={"K2O": 1.0}),
    }
    recipe = {
        "liters": 1.0,
        "targets": {"Ca": 100.0},
        "fertilizers_allowed": ["K-only"],
    }
    water_profile_data = {"mg_per_l": {"Ca": 200.0}}

    result = solve_recipe_data(recipe, ferts=ferts, mm=molar_masses, water_profile_data=water_profile_data)

    assert result.fertilizers == []
    assert result.errors_mg_l["Ca"] == pytest.approx(100.0, abs=1e-12)
    assert result.errors_percent["Ca"] == pytest.approx(100.0, abs=1e-12)


@pytest.mark.parametrize("model", ["mass_nnls", "hierarchical", "nnls_tuning"])
@pytest.mark.parametrize("urea_as_nh4", [False, True])
@pytest.mark.parametrize("fixed_dose", [0.0, 0.02])
def test_solver_urea_mode_matches_delivered_nitrogen_with_water_and_fixed_doses(
    model: str, urea_as_nh4: bool, fixed_dose: float
) -> None:
    mm = load_molar_masses()
    fertilizers = {name: Fertilizer(name, False, 1.0, {"UREA": 0.46}) for name in ("Variable", "Fixed")}
    # One mmol/L of water ammonium supplies one mmol/L of elemental nitrogen.
    water_nitrogen = mm["N"]
    fertilizer_nitrogen = 46.0 + fixed_dose * 460.0
    # Hierarchical stages retain optima within 1e-7 mg/L; allow twice that for the final LP.
    concentration_tolerance = 2e-7
    target_key = "N_NH4" if urea_as_nh4 else "N_UREA"
    result = solve_recipe_data(
        {
            "liters": 1,
            "fertilizers_allowed": list(fertilizers),
            "fixed_grams": {"Fixed": fixed_dose},
            "targets": {target_key: fertilizer_nitrogen + (water_nitrogen if urea_as_nh4 else 0)},
            "urea_as_nh4": urea_as_nh4,
            "solver_config": {"solver_model": model, "nitrogen_objective_mode": "n_forms_only"},
        },
        ferts=fertilizers,
        mm=mm,
        water_profile_data={"mg_per_l": {"NH4": mm["NH4"]}},
    )

    doses = {entry["name"]: entry["grams"] for entry in result.fertilizers}
    assert doses["Variable"] == pytest.approx(0.1, rel=0, abs=concentration_tolerance / 460)
    assert doses.get("Fixed", 0) == pytest.approx(fixed_dose, rel=0, abs=1e-12)
    assert result.achieved_elements_mg_l["N_total"] == pytest.approx(
        fertilizer_nitrogen + water_nitrogen, rel=0, abs=concentration_tolerance
    )
    assert result.errors_mg_l[target_key] == pytest.approx(0, rel=0, abs=concentration_tolerance)
    assert result.achieved_elements_mg_l["N_UREA"] == pytest.approx(
        0 if urea_as_nh4 else fertilizer_nitrogen, rel=0, abs=concentration_tolerance
    )


@pytest.mark.parametrize("model", ["mass_nnls", "hierarchical", "nnls_tuning"])
def test_ammonium_mode_does_not_claim_to_supply_urea(model: str) -> None:
    result = solve_recipe_data(
        {
            "liters": 1,
            "fertilizers_allowed": ["Urea"],
            "targets": {"N_UREA": 46},
            "urea_as_nh4": True,
            "solver_config": {"solver_model": model, "nitrogen_objective_mode": "n_forms_only"},
        },
        ferts={"Urea": Fertilizer("Urea", False, 1.0, {"UREA": 0.46})},
        mm=load_molar_masses(),
        water_profile_data={"mg_per_l": {}},
    )

    assert result.fertilizers == []
    assert result.errors_mg_l["N_UREA"] == -46
    if model == "hierarchical":
        assert result.priority_stages[0]["max_error_mg_per_l"] == pytest.approx(46)


@pytest.mark.parametrize("include_zero, expected_dose", [(True, 0.5), (False, 1.0)])
def test_zero_nitrogen_form_target_remains_an_objective(include_zero: bool, expected_dose: float) -> None:
    targets = {"N_NO3": 100, "K": 0}
    if include_zero:
        targets["N_NH4"] = 0
    result = solve_recipe_data(
        {
            "liters": 1,
            "fertilizers_allowed": ["Mixed"],
            "targets": targets,
            "solver_config": {"nitrogen_objective_mode": "n_forms_only", "singleton_underfill_enabled": False},
        },
        ferts={"Mixed": Fertilizer("Mixed", False, 1.0, {"NO3": 0.1, "NH4": 0.1})},
        mm=load_molar_masses(),
        water_profile_data={"mg_per_l": {}},
    )

    assert result.fertilizers[0]["grams"] == pytest.approx(expected_dose)
    assert ("N_NH4" in result.objective_elements) is include_zero
    assert "K" not in result.objective_elements


@pytest.mark.parametrize("form, target_key", [("NH4", "N_NH4"), ("UREA", "N_UREA")])
@pytest.mark.parametrize(
    "relative_weighting, scale, expected_dose",
    [(False, 1.0, 0.5), (True, 1.0, 1 / 10001), (True, 2.0, 4 / 10004)],
)
def test_tuning_scores_zero_nitrogen_objectives(
    form: str, target_key: str, relative_weighting: bool, scale: float, expected_dose: float
) -> None:
    result = solve_recipe_data(
        {
            "liters": 1,
            "fertilizers_allowed": ["Mixed"],
            "targets": {"N_NO3": 100, target_key: 0, "K": 0},
            "solver_config": {
                "nitrogen_objective_mode": "n_forms_only",
                "relative_weighting": relative_weighting,
                "overshoot_penalty": 0,
                "scale_eps_mg_per_l": scale,
            },
        },
        ferts={"Mixed": Fertilizer("Mixed", False, 1.0, {"NO3": 0.1, form: 0.1})},
        mm=load_molar_masses(),
        water_profile_data={"mg_per_l": {}},
    )

    # Minimize (100*x - 100)^2 + (100*x)^2, with row scaling when enabled.
    assert result.fertilizers[0]["grams"] == pytest.approx(expected_dose, rel=0, abs=1e-10)
    assert result.achieved_elements_mg_l[target_key] == pytest.approx(100 * expected_dose, rel=0, abs=1e-8)
    assert target_key in result.objective_elements
    assert "K" not in result.objective_elements


def test_zero_objective_tuning_accounts_for_fixed_doses_and_water() -> None:
    mm = load_molar_masses()
    result = solve_recipe_data(
        {
            "liters": 1,
            "fertilizers_allowed": ["Mixed", "Fixed ammonium"],
            "fixed_grams": {"Fixed ammonium": 0.1},
            "targets": {"N_NO3": 100, "N_NH4": 0},
            "solver_config": {"nitrogen_objective_mode": "n_forms_only"},
        },
        ferts={
            "Mixed": Fertilizer("Mixed", False, 1.0, {"NO3": 0.1, "NH4": 0.1}),
            "Fixed ammonium": Fertilizer("Fixed ammonium", False, 1.0, {"NH4": 0.1}),
        },
        mm=mm,
        water_profile_data={"mg_per_l": {"NH4": 10 * mm["NH4"] / mm["N"]}},
    )

    # Fixed dose and water each supply 10 mg/L N; the variable optimum is 0.4 g.
    doses = {entry["name"]: entry["grams"] for entry in result.fertilizers}
    assert doses == pytest.approx({"Mixed": 0.4, "Fixed ammonium": 0.1}, rel=0, abs=1e-10)
    assert result.achieved_elements_mg_l["N_NH4"] == pytest.approx(60, rel=0, abs=1e-8)
