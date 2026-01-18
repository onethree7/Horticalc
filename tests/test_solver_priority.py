import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from horticalc.solver import _score_by_priority_groups, _solve_weights


def test_macro_priority_prefers_macros_over_trace() -> None:
    A = np.array([[10.0, 0.0], [0.1, 1.0]])
    b = np.array([100.0, 0.1])
    variable_mask = np.array([True, True])
    objective_keys = ["K", "Fe"]
    targets_raw = {"K": 100.0, "Fe": 0.1}
    priority_groups = [["N_NO3", "N_NH4", "N_UREA", "N_total"], ["K"], ["P"], ["Ca"], ["Mg"]]
    priority_group_weights = [3.0, 2.5, 2.0, 1.5, 1.5]

    x_no_priority = _solve_weights(
        A,
        b,
        np.array([]),
        variable_mask,
        relative_weighting=True,
        objective_keys=objective_keys,
        targets_raw=targets_raw,
        macro_priority_enabled=False,
        priority_groups=priority_groups,
        priority_group_weights=priority_group_weights,
    )
    x_with_priority = _solve_weights(
        A,
        b,
        np.array([]),
        variable_mask,
        relative_weighting=True,
        objective_keys=objective_keys,
        targets_raw=targets_raw,
        macro_priority_enabled=True,
        priority_groups=priority_groups,
        priority_group_weights=priority_group_weights,
    )

    achieved_no = {"K": float((A @ x_no_priority)[0]), "Fe": float((A @ x_no_priority)[1])}
    achieved_yes = {"K": float((A @ x_with_priority)[0]), "Fe": float((A @ x_with_priority)[1])}

    score_no = _score_by_priority_groups(
        objective_keys,
        targets_raw,
        achieved_no,
        priority_groups=priority_groups,
    )
    score_yes = _score_by_priority_groups(
        objective_keys,
        targets_raw,
        achieved_yes,
        priority_groups=priority_groups,
    )

    assert score_yes[1] < score_no[1]


def test_macro_priority_can_be_disabled() -> None:
    A = np.array([[10.0, 0.0], [0.1, 1.0]])
    b = np.array([100.0, 0.1])
    variable_mask = np.array([True, True])
    objective_keys = ["K", "Fe"]
    targets_raw = {"K": 100.0, "Fe": 0.1}

    x_disabled = _solve_weights(
        A,
        b,
        np.array([]),
        variable_mask,
        relative_weighting=True,
        objective_keys=objective_keys,
        targets_raw=targets_raw,
        macro_priority_enabled=False,
        priority_groups=[["K"]],
        priority_group_weights=[2.5],
    )
    x_baseline = _solve_weights(
        A,
        b,
        np.array([]),
        variable_mask,
        relative_weighting=True,
        objective_keys=objective_keys,
        targets_raw=targets_raw,
        macro_priority_enabled=True,
        priority_groups=[],
        priority_group_weights=[],
    )

    assert np.allclose(x_disabled, x_baseline)
