import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from tcg_engine.api import app


class TestApi(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.client.post("/reset")

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_game_state(self) -> None:
        response = self.client.get("/game-state")
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["activePlayerId"], "p1")
        self.assertEqual(payload["turnNumber"], 1)
        self.assertIn("players", payload)
        self.assertIn("cards", payload)
        self.assertIn("p1", payload["players"])

    def test_legal_actions_for_player(self) -> None:
        response = self.client.get("/players/p1/legal-actions")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["playerId"], "p1")
        self.assertTrue(any(action["kind"] == "pass_priority" for action in payload["actions"]))

    def test_apply_action_advances_state(self) -> None:
        action_payload = {"kind": "pass_priority", "actorId": "p1"}
        response = self.client.post("/actions", json=action_payload)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["appliedAction"]["kind"], "pass_priority")
        self.assertEqual(payload["gameState"]["phase"], "precombat_main")


if __name__ == "__main__":
    unittest.main()
