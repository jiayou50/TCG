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
        self.assertEqual(len(payload["players"]["p1"]["library"]), 10)
        self.assertEqual(len(payload["players"]["p2"]["library"]), 10)
        self.assertEqual(len(payload["players"]["p1"]["hand"]), 3)
        self.assertEqual(len(payload["players"]["p2"]["hand"]), 3)

        def _count_types(card_ids: list[str]) -> tuple[int, int]:
            lands = 0
            creatures = 0
            for card_id in card_ids:
                card_type = payload["cards"][card_id]["cardType"]
                if card_type == "land":
                    lands += 1
                if card_type == "creature":
                    creatures += 1
            return lands, creatures

        p1_cards = payload["players"]["p1"]["library"] + payload["players"]["p1"]["hand"]
        p2_cards = payload["players"]["p2"]["library"] + payload["players"]["p2"]["hand"]
        self.assertEqual(len(p1_cards), 13)
        self.assertEqual(len(p2_cards), 13)

        p1_lands, p1_creatures = _count_types(p1_cards)
        p2_lands, p2_creatures = _count_types(p2_cards)
        self.assertEqual((p1_lands, p1_creatures), (5, 8))
        self.assertEqual((p2_lands, p2_creatures), (5, 8))

        p1_names = {payload["cards"][card_id]["name"] for card_id in p1_cards}
        p2_names = {payload["cards"][card_id]["name"] for card_id in p2_cards}
        self.assertIn("Ancient Grove Behemoth", p1_names)
        self.assertIn("Abyssal Colossus", p2_names)

        p1_land_colors = {
            payload["cards"][card_id]["producesMana"][0]
            for card_id in p1_cards
            if payload["cards"][card_id]["cardType"] == "land"
        }
        p2_land_colors = {
            payload["cards"][card_id]["producesMana"][0]
            for card_id in p2_cards
            if payload["cards"][card_id]["cardType"] == "land"
        }
        self.assertEqual(p1_land_colors, {"G", "W"})
        self.assertEqual(p2_land_colors, {"U", "B"})

        def _creature_cost_colors(card_ids: list[str]) -> set[str]:
            colors = set()
            for card_id in card_ids:
                card = payload["cards"][card_id]
                if card["cardType"] != "creature":
                    continue
                for symbol in ("W", "U", "B", "R", "G"):
                    if symbol in card["manaCost"]:
                        colors.add(symbol)
            return colors

        self.assertEqual(_creature_cost_colors(p1_cards), {"G", "W"})
        self.assertEqual(_creature_cost_colors(p2_cards), {"U", "B"})

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
