import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from tcg_engine import Action, Card, GameState, Phase, PlayerState, Zone, apply_action, move_card, next_phase


def make_state() -> GameState:
    p1 = PlayerState(id="p1", library=["c1", "c2"])
    p2 = PlayerState(id="p2", library=["c3"])
    cards = {
        "c1": Card(id="c1", name="Test One", owner_id="p1"),
        "c2": Card(id="c2", name="Test Two", owner_id="p1"),
        "c3": Card(id="c3", name="Test Three", owner_id="p2"),
    }
    return GameState(
        players={"p1": p1, "p2": p2},
        cards=cards,
        active_player_id="p1",
        priority_player_id="p1",
    )


class TestGame(unittest.TestCase):
    def test_draw_action_moves_card_to_hand(self) -> None:
        state = make_state()
        apply_action(state, Action(kind="draw", actor_id="p1"))

        self.assertEqual(state.players["p1"].library, ["c2"])
        self.assertEqual(state.players["p1"].hand, ["c1"])

    def test_phase_advances(self) -> None:
        state = make_state()
        self.assertEqual(state.phase, Phase.BEGINNING)

        next_phase(state)
        self.assertEqual(state.phase, Phase.PRECOMBAT_MAIN)

    def test_move_card_zone_change(self) -> None:
        state = make_state()
        apply_action(state, Action(kind="draw", actor_id="p1"))

        move_card(state, "p1", "c1", Zone.HAND, Zone.GRAVEYARD)

        self.assertEqual(state.players["p1"].hand, [])
        self.assertEqual(state.players["p1"].graveyard, ["c1"])


if __name__ == "__main__":
    unittest.main()
