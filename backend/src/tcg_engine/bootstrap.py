"""Helpers for creating ready-to-run game states."""

from __future__ import annotations

from .models import Card, CardType, GameState, ManaColor, PlayerState


def create_starting_game_state() -> GameState:
    """Create a static game state suitable for first end-to-end integration."""
    p1 = PlayerState(
        id="p1",
        library=["p1_c1", "p1_c2"],
        hand=["p1_l1", "p1_c3"],
        battlefield=["p1_l2"],
    )
    p2 = PlayerState(
        id="p2",
        library=["p2_c1", "p2_c2"],
        hand=["p2_l1"],
    )

    cards = {
        "p1_c1": Card(
            id="p1_c1",
            name="Frontier Wolf",
            owner_id="p1",
            mana_cost="1G",
            card_type=CardType.CREATURE,
            power=2,
            toughness=2,
        ),
        "p1_c2": Card(
            id="p1_c2",
            name="River Serpent",
            owner_id="p1",
            mana_cost="2U",
            card_type=CardType.CREATURE,
            power=2,
            toughness=3,
        ),
        "p1_c3": Card(
            id="p1_c3",
            name="Hill Scout",
            owner_id="p1",
            mana_cost="1R",
            card_type=CardType.CREATURE,
            power=2,
            toughness=1,
        ),
        "p1_l1": Card(
            id="p1_l1",
            name="Forest",
            owner_id="p1",
            mana_cost="",
            card_type=CardType.LAND,
            produces_mana=(ManaColor.GREEN,),
        ),
        "p1_l2": Card(
            id="p1_l2",
            name="Mountain",
            owner_id="p1",
            mana_cost="",
            card_type=CardType.LAND,
            produces_mana=(ManaColor.RED,),
        ),
        "p2_c1": Card(
            id="p2_c1",
            name="Night Drake",
            owner_id="p2",
            mana_cost="2B",
            card_type=CardType.CREATURE,
            power=2,
            toughness=3,
        ),
        "p2_c2": Card(
            id="p2_c2",
            name="Stoneguard",
            owner_id="p2",
            mana_cost="3W",
            card_type=CardType.CREATURE,
            power=2,
            toughness=4,
        ),
        "p2_l1": Card(
            id="p2_l1",
            name="Swamp",
            owner_id="p2",
            mana_cost="",
            card_type=CardType.LAND,
            produces_mana=(ManaColor.BLACK,),
        ),
    }

    state = GameState(
        players={"p1": p1, "p2": p2},
        cards=cards,
        active_player_id="p1",
        priority_player_id="p1",
    )
    state.event_log.append("Game initialized with static starting state")
    return state
