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
                "phosphate_species": "H2PO4",
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
                "phosphate_species": "H2PO4",
                "solver_config": {
                    "relative_weighting": True,
                    "overshoot_penalty": 1.5,
                    "n_total_governor_enabled": True,
                    "n_total_governor_weight": 0.05,
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["liters"], 10)

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

if __name__ == "__main__":
    unittest.main()
