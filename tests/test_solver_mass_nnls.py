from __future__ import annotations

import pytest

from horticalc.data_io import Fertilizer, load_molar_masses
from horticalc.solver import solve_recipe_data

MOLAR_MASSES = load_molar_masses()


def _fertilizer(name: str, form: str, fraction: float) -> Fertilizer:
    return Fertilizer(
        name=name,
        liquid=False,
        weight_factor=1.0,
        comp={form: fraction},
    )


def test_mass_nnls_uses_raw_mg_per_l_squared_error() -> None:
    result = solve_recipe_data(
        {
            "liters": 10.0,
            "targets_mg_per_l": {"N_total": 100.0, "K": 100.0},
            "fertilizers_allowed": ["N", "K"],
            "solver_config": {"solver_model": "mass_nnls"},
        },
        ferts={
            "N": _fertilizer("N", "NO3", 0.1),
            "K": _fertilizer("K", "K2O", 0.1),
        },
        mm=MOLAR_MASSES,
        water_profile_data={"mg_per_l": {}},
    )

    assert result.solver_model == "mass_nnls"
    assert result.errors_mg_l["N_total"] == pytest.approx(0.0, abs=1e-7)
    assert result.errors_mg_l["K"] == pytest.approx(0.0, abs=1e-7)


def test_mass_nnls_ignores_selected_elements_but_still_reports_their_result() -> None:
    result = solve_recipe_data(
        {
            "liters": 10.0,
            "targets_mg_per_l": {"N_total": 100.0, "Cu": 0.1},
            "fertilizers_allowed": ["Coupled"],
            "solver_config": {"solver_model": "mass_nnls", "ignored_elements": ["Cu"]},
        },
        ferts={
            "Coupled": Fertilizer(
                name="Coupled",
                liquid=False,
                weight_factor=1.0,
                comp={"NO3": 0.1, "Cu": 0.01},
            )
        },
        mm=MOLAR_MASSES,
        water_profile_data={"mg_per_l": {}},
    )

    assert result.objective_elements == ["N_total"]
    assert result.ignored_elements == ["Cu"]
    assert result.targets_mg_l["Cu"] == pytest.approx(0.1)
    assert result.achieved_elements_mg_l["Cu"] == pytest.approx(10.0)
    assert "Cu" not in result.errors_mg_l
    assert result.errors_mg_l["N_total"] == pytest.approx(0.0, abs=1e-7)


def test_mass_nnls_rejects_ignoring_every_active_objective() -> None:
    with pytest.raises(ValueError, match="all active targets are ignored"):
        solve_recipe_data(
            {
                "liters": 10.0,
                "targets_mg_per_l": {"N_total": 100.0},
                "fertilizers_allowed": ["N"],
                "solver_config": {"solver_model": "mass_nnls", "ignored_elements": ["N_total"]},
            },
            ferts={"N": _fertilizer("N", "NO3", 0.1)},
            mm=MOLAR_MASSES,
            water_profile_data={"mg_per_l": {}},
        )


def test_mass_nnls_forces_total_nitrogen_and_sulfur_when_available() -> None:
    result = solve_recipe_data(
        {
            "liters": 10.0,
            "targets_mg_per_l": {"N_total": 100.0, "N_NO3": 80.0, "S": 20.0},
            "fertilizers_allowed": ["N", "S"],
            "solver_config": {
                "solver_model": "mass_nnls",
                "nitrogen_objective_mode": "n_forms_only",
                "s_objective_enabled": False,
            },
        },
        ferts={
            "N": _fertilizer("N", "NO3", 0.1),
            "S": _fertilizer("S", "SO4", 0.1),
        },
        mm=MOLAR_MASSES,
        water_profile_data={"mg_per_l": {}},
    )

    assert result.objective_elements == ["N_total", "S"]
    assert result.errors_mg_l["N_total"] == pytest.approx(0.0, abs=1e-7)
    assert result.errors_mg_l["S"] == pytest.approx(0.0, abs=1e-7)
