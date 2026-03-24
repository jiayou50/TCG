import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from tcg_engine import (
    Action,
    Card,
    CardType,
    GameState,
    ManaColor,
    Phase,
    PlayerState,
    SAMPLE_CARDS,
    Zone,
    apply_action,
    can_pay_mana_cost,
    get_legal_actions,
    move_card,
    next_phase,
    play_card,
    play_land,
    spend_mana_cost,
    tap_all_lands_for_mana,
    tap_land_for_mana,
)


def make_state() -> GameState:
    p1 = PlayerState(id="p1", library=["c1", "c2"], hand=["l1", "l2"])
    p2 = PlayerState(id="p2", library=["c3"])
    cards = {
        "c1": Card(
            id="c1",
            name="Test One",
            owner_id="p1",
            mana_cost="1G",
            card_type=CardType.CREATURE,
            power=2,
            toughness=2,
        ),
        "c2": Card(
            id="c2",
            name="Test Two",
            owner_id="p1",
            mana_cost="2W",
            card_type=CardType.CREATURE,
            power=2,
            toughness=3,
        ),
        "c3": Card(
            id="c3",
            name="Test Three",
            owner_id="p2",
            mana_cost="R",
            card_type=CardType.CREATURE,
            power=1,
            toughness=1,
        ),
        "c4": Card(
            id="c4",
            name="Test Burn",
            owner_id="p1",
            mana_cost="1R",
            card_type=CardType.SORCERY,
            effect_kind="damage_target_creature",
            effect_value=1,
            oracle_text="Deal 1 damage to target creature.",
        ),
        "c5": Card(
            id="c5",
            name="Test Removal",
            owner_id="p1",
            mana_cost="1G",
            card_type=CardType.SORCERY,
            effect_kind="destroy_target_creature",
            oracle_text="Destroy target creature.",
        ),
        "c6": Card(
            id="c6",
            name="Test Four",
            owner_id="p2",
            mana_cost="2R",
            card_type=CardType.CREATURE,
            power=2,
            toughness=2,
        ),
        "l1": Card(
            id="l1",
            name="Forest",
            owner_id="p1",
            mana_cost="",
            card_type=CardType.LAND,
            produces_mana=(ManaColor.GREEN,),
        ),
        "l2": Card(
            id="l2",
            name="Mountain",
            owner_id="p1",
            mana_cost="",
            card_type=CardType.LAND,
            produces_mana=(ManaColor.RED,),
        ),
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
        self.assertEqual(state.players["p1"].hand, ["l1", "l2", "c1"])
        self.assertTrue(state.has_drawn_this_turn)

    def test_cannot_draw_more_than_once_in_beginning_phase(self) -> None:
        state = make_state()
        apply_action(state, Action(kind="draw", actor_id="p1"))

        with self.assertRaises(ValueError):
            apply_action(state, Action(kind="draw", actor_id="p1"))

    def test_phase_advances(self) -> None:
        state = make_state()
        self.assertEqual(state.phase, Phase.BEGINNING)

        next_phase(state)
        self.assertEqual(state.phase, Phase.PRECOMBAT_MAIN)

    def test_move_card_zone_change(self) -> None:
        state = make_state()
        apply_action(state, Action(kind="draw", actor_id="p1"))

        move_card(state, "p1", "c1", Zone.HAND, Zone.GRAVEYARD)

        self.assertEqual(state.players["p1"].hand, ["l1", "l2"])
        self.assertEqual(state.players["p1"].graveyard, ["c1"])

    def test_creature_requires_power_and_toughness(self) -> None:
        with self.assertRaises(ValueError):
            Card(
                id="bad",
                name="Bad Creature",
                owner_id="p1",
                mana_cost="1U",
                card_type=CardType.CREATURE,
            )

    def test_land_requires_no_cost_and_mana_output(self) -> None:
        with self.assertRaises(ValueError):
            Card(
                id="bad_land",
                name="Bad Land",
                owner_id="p1",
                mana_cost="1",
                card_type=CardType.LAND,
                produces_mana=(ManaColor.GREEN,),
            )

        with self.assertRaises(ValueError):
            Card(
                id="bad_land_2",
                name="Bad Land 2",
                owner_id="p1",
                mana_cost="",
                card_type=CardType.LAND,
            )

    def test_sorcery_requires_oracle_text(self) -> None:
        with self.assertRaises(ValueError):
            Card(
                id="bad_sorcery",
                name="Bad Sorcery",
                owner_id="p1",
                mana_cost="1R",
                card_type=CardType.SORCERY,
                effect_kind="damage_target_creature",
                effect_value=2,
            )

    def test_sample_cards_include_five_basic_lands(self) -> None:
        basics = {"c_plains", "c_island", "c_swamp", "c_mountain", "c_forest"}
        self.assertTrue(basics.issubset(set(SAMPLE_CARDS.keys())))

    def test_play_land_and_tap_for_mana(self) -> None:
        state = make_state()
        state.phase = Phase.PRECOMBAT_MAIN

        play_land(state, "p1", "l1")
        self.assertIn("l1", state.players["p1"].battlefield)
        self.assertEqual(state.players["p1"].lands_played_this_turn, 1)

        tap_land_for_mana(state, "p1", "l1")
        self.assertEqual(state.players["p1"].mana_pool[ManaColor.GREEN], 1)
        self.assertIn("l1", state.players["p1"].tapped_permanents)

    def test_tap_all_lands_for_mana_taps_only_untapped_lands(self) -> None:
        state = make_state()
        state.phase = Phase.PRECOMBAT_MAIN
        player = state.players["p1"]
        player.battlefield.extend(["l1", "l2"])
        player.tapped_permanents.add("l2")

        tap_all_lands_for_mana(state, "p1")

        self.assertEqual(player.mana_pool[ManaColor.GREEN], 1)
        self.assertEqual(player.mana_pool[ManaColor.RED], 0)
        self.assertIn("l1", player.tapped_permanents)
        self.assertIn("l2", player.tapped_permanents)

    def test_tap_all_lands_for_mana_requires_active_player(self) -> None:
        state = make_state()
        state.players["p2"].battlefield.append("l3")
        state.cards["l3"] = Card(
            id="l3",
            name="Forest",
            owner_id="p2",
            mana_cost="",
            card_type=CardType.LAND,
            produces_mana=(ManaColor.GREEN,),
        )

        with self.assertRaises(ValueError):
            tap_all_lands_for_mana(state, "p2")

    def test_spend_mana_cost(self) -> None:
        state = make_state()
        player = state.players["p1"]
        player.mana_pool[ManaColor.GREEN] = 1
        player.mana_pool[ManaColor.RED] = 1

        self.assertTrue(can_pay_mana_cost(player, "1G"))
        spend_mana_cost(player, "1G")
        self.assertEqual(player.mana_pool[ManaColor.GREEN], 0)
        self.assertEqual(sum(player.mana_pool.values()), 0)

    def test_can_only_play_one_land_per_turn(self) -> None:
        state = make_state()
        state.phase = Phase.PRECOMBAT_MAIN

        play_land(state, "p1", "l1")
        with self.assertRaises(ValueError):
            play_land(state, "p1", "l2")

    def test_play_card_spends_mana_and_moves_to_battlefield(self) -> None:
        state = make_state()
        state.phase = Phase.PRECOMBAT_MAIN
        player = state.players["p1"]
        player.hand.append("c1")
        player.mana_pool[ManaColor.GREEN] = 1
        player.mana_pool[ManaColor.RED] = 1

        play_card(state, "p1", "c1")

        self.assertIn("c1", player.battlefield)
        self.assertNotIn("c1", player.hand)
        self.assertEqual(sum(player.mana_pool.values()), 0)

    def test_sorcery_can_only_be_played_in_own_main_phase(self) -> None:
        state = make_state()
        p1 = state.players["p1"]
        p1.hand.append("c4")
        p1.mana_pool[ManaColor.GREEN] = 1
        p1.mana_pool[ManaColor.RED] = 1
        state.players["p2"].battlefield.append("c3")

        state.phase = Phase.COMBAT
        with self.assertRaises(ValueError):
            play_card(state, "p1", "c4", target_id="c3")

        state.phase = Phase.PRECOMBAT_MAIN
        state.active_player_id = "p2"
        with self.assertRaises(ValueError):
            play_card(state, "p1", "c4", target_id="c3")

    def test_burn_sorcery_tracks_damage_and_turn_end_clears_it(self) -> None:
        state = make_state()
        p1 = state.players["p1"]
        p2 = state.players["p2"]
        state.phase = Phase.PRECOMBAT_MAIN
        p1.hand.append("c4")
        p2.battlefield.append("c6")
        p1.mana_pool[ManaColor.GREEN] = 1
        p1.mana_pool[ManaColor.RED] = 1

        play_card(state, "p1", "c4", target_id="c6")

        self.assertEqual(state.creature_damage.get("c6"), 1)
        self.assertIn("c4", p1.graveyard)

        apply_action(state, Action(kind="pass_turn", actor_id="p1"))
        self.assertEqual(state.creature_damage, {})

    def test_removal_sorcery_moves_target_creature_to_graveyard(self) -> None:
        state = make_state()
        p1 = state.players["p1"]
        p2 = state.players["p2"]
        state.phase = Phase.PRECOMBAT_MAIN
        p1.hand.append("c5")
        p2.battlefield.append("c3")
        p1.mana_pool[ManaColor.GREEN] = 2

        play_card(state, "p1", "c5", target_id="c3")

        self.assertNotIn("c3", p2.battlefield)
        self.assertIn("c3", p2.graveyard)
        self.assertIn("c5", p1.graveyard)

    def test_combat_damage_accumulates_with_sorcery_damage(self) -> None:
        state = make_state()
        p1 = state.players["p1"]
        p2 = state.players["p2"]
        state.phase = Phase.PRECOMBAT_MAIN
        p1.hand.append("c4")
        p2.battlefield.append("c6")
        p1.mana_pool[ManaColor.GREEN] = 1
        p1.mana_pool[ManaColor.RED] = 1

        play_card(state, "p1", "c4", target_id="c6")
        self.assertEqual(state.creature_damage.get("c6"), 1)

        p1.battlefield.append("c1")
        state.phase = Phase.COMBAT
        state.active_player_id = "p2"
        state.priority_player_id = "p2"
        state.players["p2"].summoning_sick_creatures.clear()
        state.players["p1"].summoning_sick_creatures.clear()
        apply_action(state, Action(kind="attack_with_creature", actor_id="p2", card_id="c6"))
        apply_action(state, Action(kind="pass_priority", actor_id="p2"))
        apply_action(state, Action(kind="block_with_creature", actor_id="p1", card_id="c1", target_id="c6"))
        apply_action(state, Action(kind="pass_priority", actor_id="p1"))

        self.assertIn("c6", p2.graveyard)

    def test_combat_actions_attack_and_block(self) -> None:
        state = make_state()
        p1 = state.players["p1"]
        p2 = state.players["p2"]
        p1.battlefield.append("c1")
        p2.battlefield.append("c3")
        state.phase = Phase.COMBAT

        apply_action(state, Action(kind="attack_with_creature", actor_id="p1", card_id="c1"))
        self.assertIn("c1", p1.tapped_permanents)
        self.assertEqual(state.declared_attackers["c1"], "p2")
        self.assertEqual(state.active_player_id, "p1")

        apply_action(
            state,
            Action(kind="block_with_creature", actor_id="p2", card_id="c3", target_id="c1"),
        )
        self.assertEqual(state.declared_blocks["c3"], "c1")

    def test_creature_gains_and_loses_summoning_sickness(self) -> None:
        state = make_state()
        state.phase = Phase.PRECOMBAT_MAIN
        player = state.players["p1"]
        player.hand.append("c1")
        player.mana_pool[ManaColor.GREEN] = 1
        player.mana_pool[ManaColor.RED] = 1

        play_card(state, "p1", "c1")
        self.assertIn("c1", player.summoning_sick_creatures)

        move_card(state, "p1", "c1", Zone.BATTLEFIELD, Zone.GRAVEYARD)
        self.assertNotIn("c1", player.summoning_sick_creatures)

    def test_summoning_sickness_prevents_attack_until_next_turn(self) -> None:
        state = make_state()
        p1 = state.players["p1"]
        p1.battlefield.append("c1")
        p1.summoning_sick_creatures.add("c1")
        state.phase = Phase.COMBAT

        with self.assertRaises(ValueError):
            apply_action(state, Action(kind="attack_with_creature", actor_id="p1", card_id="c1"))

        state.phase = Phase.PRECOMBAT_MAIN
        apply_action(state, Action(kind="pass_turn", actor_id="p1"))
        apply_action(state, Action(kind="draw", actor_id="p2"))
        apply_action(state, Action(kind="pass_turn", actor_id="p2"))
        apply_action(state, Action(kind="draw", actor_id="p1"))
        apply_action(state, Action(kind="pass_priority", actor_id="p1"))
        self.assertEqual(state.phase, Phase.COMBAT)

        apply_action(state, Action(kind="attack_with_creature", actor_id="p1", card_id="c1"))
        self.assertEqual(state.declared_attackers["c1"], "p2")

    def test_combat_pass_priority_moves_from_attacker_to_defender(self) -> None:
        state = make_state()
        p1 = state.players["p1"]
        p1.battlefield.append("c1")
        state.phase = Phase.COMBAT

        apply_action(state, Action(kind="attack_with_creature", actor_id="p1", card_id="c1"))
        self.assertEqual(state.active_player_id, "p1")

        apply_action(state, Action(kind="pass_priority", actor_id="p1"))
        self.assertEqual(state.active_player_id, "p2")
        self.assertEqual(state.phase, Phase.COMBAT)

    def test_unblocked_attacker_deals_damage_on_combat_end(self) -> None:
        state = make_state()
        p1 = state.players["p1"]
        p2 = state.players["p2"]
        p1.battlefield.append("c1")
        state.phase = Phase.COMBAT

        apply_action(state, Action(kind="attack_with_creature", actor_id="p1", card_id="c1"))
        apply_action(state, Action(kind="pass_priority", actor_id="p1"))
        apply_action(state, Action(kind="pass_priority", actor_id="p2"))

        self.assertEqual(p2.life_total, 18)
        self.assertEqual(state.phase, Phase.POSTCOMBAT_MAIN)
        self.assertEqual(state.declared_attackers, {})

    def test_blocked_combat_sends_lethally_damaged_blocker_to_graveyard(self) -> None:
        state = make_state()
        p1 = state.players["p1"]
        p2 = state.players["p2"]
        p1.battlefield.append("c1")
        p2.battlefield.append("c3")
        state.phase = Phase.COMBAT

        apply_action(state, Action(kind="attack_with_creature", actor_id="p1", card_id="c1"))
        apply_action(state, Action(kind="pass_priority", actor_id="p1"))
        apply_action(
            state,
            Action(kind="block_with_creature", actor_id="p2", card_id="c3", target_id="c1"),
        )

        next_phase(state)

        self.assertNotIn("c3", p2.battlefield)
        self.assertIn("c1", p1.battlefield)
        self.assertIn("c3", p2.graveyard)
        self.assertEqual(p2.life_total, 20)

    def test_legal_actions_include_requested_player_actions(self) -> None:
        state = make_state()
        p1 = state.players["p1"]
        p2 = state.players["p2"]
        state.phase = Phase.PRECOMBAT_MAIN
        p1.hand.append("c1")
        p1.hand.append("c4")
        p1.battlefield.append("l1")
        p2.battlefield.append("c3")
        p1.mana_pool[ManaColor.GREEN] = 1
        p1.mana_pool[ManaColor.RED] = 1

        legal_main = {action.kind for action in get_legal_actions(state, "p1")}
        self.assertTrue({"play_land", "play_card", "tap_land_for_mana", "pass_priority"}.issubset(legal_main))
        self.assertTrue(
            any(
                action.kind == "play_card" and action.card_id == "c4" and action.target_id == "c3"
                for action in get_legal_actions(state, "p1")
            )
        )

        p1.battlefield.append("c1")
        p2.battlefield.append("c3")
        state.phase = Phase.COMBAT
        apply_action(state, Action(kind="attack_with_creature", actor_id="p1", card_id="c1"))
        apply_action(state, Action(kind="pass_priority", actor_id="p1"))

        legal_defender = get_legal_actions(state, "p2")
        self.assertTrue(any(action.kind == "block_with_creature" for action in legal_defender))

    def test_attacker_can_declare_multiple_attackers_before_passing_priority(self) -> None:
        state = make_state()
        p1 = state.players["p1"]
        p1.battlefield.extend(["c1", "c2"])
        p1.summoning_sick_creatures.clear()
        state.phase = Phase.COMBAT

        apply_action(state, Action(kind="attack_with_creature", actor_id="p1", card_id="c1"))

        legal_attacker_actions = get_legal_actions(state, "p1")
        self.assertTrue(
            any(
                action.kind == "attack_with_creature" and action.card_id == "c2"
                for action in legal_attacker_actions
            )
        )

        apply_action(state, Action(kind="attack_with_creature", actor_id="p1", card_id="c2"))

        self.assertEqual(state.active_player_id, "p1")
        self.assertEqual(state.priority_player_id, "p1")
        self.assertEqual(state.declared_attackers["c1"], "p2")
        self.assertEqual(state.declared_attackers["c2"], "p2")

    def test_draw_legal_action_only_once_during_beginning_phase(self) -> None:
        state = make_state()
        legal_before = {action.kind for action in get_legal_actions(state, "p1")}
        self.assertIn("draw", legal_before)
        self.assertIn("start_new_game", legal_before)
        self.assertNotIn("pass_priority", legal_before)

        apply_action(state, Action(kind="draw", actor_id="p1"))
        legal_after = {action.kind for action in get_legal_actions(state, "p1")}
        self.assertNotIn("draw", legal_after)
        self.assertIn("pass_priority", legal_after)

    def test_pass_turn_is_legal_during_main_phase(self) -> None:
        state = make_state()
        state.phase = Phase.PRECOMBAT_MAIN

        legal_actions = {action.kind for action in get_legal_actions(state, "p1")}
        self.assertIn("pass_turn", legal_actions)

    def test_pass_turn_moves_to_next_players_beginning(self) -> None:
        state = make_state()
        state.phase = Phase.PRECOMBAT_MAIN
        state.has_drawn_this_turn = True

        apply_action(state, Action(kind="pass_turn", actor_id="p1"))

        self.assertEqual(state.turn_number, 2)
        self.assertEqual(state.phase, Phase.BEGINNING)
        self.assertEqual(state.active_player_id, "p2")
        self.assertEqual(state.priority_player_id, "p2")
        self.assertFalse(state.has_drawn_this_turn)

    def test_mana_pool_clears_for_all_players_when_phase_advances(self) -> None:
        state = make_state()
        state.players["p1"].mana_pool[ManaColor.GREEN] = 2
        state.players["p2"].mana_pool[ManaColor.BLUE] = 1

        next_phase(state)

        self.assertEqual(sum(state.players["p1"].mana_pool.values()), 0)
        self.assertEqual(sum(state.players["p2"].mana_pool.values()), 0)

    def test_legal_actions_include_tap_all_lands_for_active_player(self) -> None:
        state = make_state()
        state.phase = Phase.PRECOMBAT_MAIN
        state.players["p1"].battlefield.extend(["l1", "l2"])

        legal_actions = get_legal_actions(state, "p1")
        self.assertTrue(any(action.kind == "tap_all_lands_for_mana" for action in legal_actions))

    def test_start_new_game_action_is_available_for_any_player_any_time(self) -> None:
        state = make_state()

        p1_beginning_actions = get_legal_actions(state, "p1")
        p2_beginning_actions = get_legal_actions(state, "p2")
        self.assertTrue(any(action.kind == "start_new_game" for action in p1_beginning_actions))
        self.assertTrue(any(action.kind == "start_new_game" for action in p2_beginning_actions))

        state.phase = Phase.COMBAT
        p2_combat_actions = get_legal_actions(state, "p2")
        self.assertTrue(any(action.kind == "start_new_game" for action in p2_combat_actions))


if __name__ == "__main__":
    unittest.main()
