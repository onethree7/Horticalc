import unittest

from fastapi.testclient import TestClient

import api.app as api_app


class TestSolveTargetKeys(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(api_app.app)

    def test_invalid_target_key_returns_400(self) -> None:
        response = self.client.post(
            "/solve",
            json={
                "liters": 10,
                "targets": {"INVALID": 1},
                "fertilizers_allowed": [],
                "fixed_grams": {},
                "urea_as_nh4": False,
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid target key: INVALID")

    def test_solver_config_primitives_are_accepted(self) -> None:
        response = self.client.post(
            "/solve",
            json={
                "liters": 10,
                "targets": {"N_total": 20},
                "fertilizers_allowed": ["Compo Basfoliar Top-N SL"],
                "fixed_grams": {},
                "urea_as_nh4": False,
                "solver_config": {
                    "solver_model": "mass_nnls",
                    "ignored_elements": ["Cu", "B"],
                    "relative_weighting": True,
                    "overshoot_penalty": 1.5,
                    "n_total_governor_enabled": True,
                    "n_total_governor_weight": 0.05,
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["liters"], 10)
        self.assertEqual(response.json()["solver_model"], "mass_nnls")
        self.assertEqual(response.json()["ignored_elements"], ["Cu", "B"])

    def test_invalid_solver_config_returns_400(self) -> None:
        base_payload = {
            "liters": 10,
            "targets": {"N_total": 20},
            "fertilizers_allowed": ["Compo Basfoliar Top-N SL"],
        }
        cases = (
            ({"mystery": True}, "Unknown solver config key: mystery"),
            ({"relative_weighting": "false"}, "Invalid solver config value: relative_weighting"),
            ({"irls_max_outer_iter": 1.5}, "Invalid solver config value: irls_max_outer_iter"),
            ({"solver_model": "unknown"}, "Invalid solver config value: solver_model"),
            ({"ignored_elements": ["UNKNOWN"]}, "Invalid solver config value: ignored_elements"),
            (
                {"nitrogen_objective_mode": "chaos_mode"},
                "Invalid solver config value: nitrogen_objective_mode",
            ),
        )

        for solver_config, detail in cases:
            with self.subTest(solver_config=solver_config):
                response = self.client.post(
                    "/solve",
                    json={**base_payload, "solver_config": solver_config},
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()["detail"], detail)

    def test_hierarchical_solver_returns_resolved_priorities_and_stage_diagnostics(self) -> None:
        response = self.client.post(
            "/solve",
            json={
                "liters": 10,
                "targets": {"N_total": 20},
                "fertilizers_allowed": ["Compo Basfoliar Top-N SL"],
                "solver_config": {
                    "solver_model": "hierarchical",
                    "target_priorities": {"N_total": {"under": 1, "over": 2}},
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["solver_model"], "hierarchical")
        self.assertEqual(payload["target_priorities"], {"N_total": {"under": 1, "over": 2}})
        self.assertEqual([stage["priority"] for stage in payload["priority_stages"]], [1, 2])


if __name__ == "__main__":
    unittest.main()
