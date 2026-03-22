"""Public interface for the TCG engine package."""

from .game import (
    Action,
    add_mana,
    apply_action,
    attack_with_creature,
    block_with_creature,
    can_pay_mana_cost,
    clear_mana_pool,
    draw_card,
    get_legal_actions,
    move_card,
    next_phase,
    play_card,
    play_land,
    spend_mana_cost,
    tap_all_lands_for_mana,
    tap_land_for_mana,
)
from .bootstrap import create_starting_game_state
from .models import Card, CardType, GameState, ManaColor, Phase, PlayerState, Zone
from .rules import is_legal_action
from .sample_cards import SAMPLE_CARDS

__all__ = [
    "Action",
    "Card",
    "CardType",
    "GameState",
    "ManaColor",
    "Phase",
    "PlayerState",
    "SAMPLE_CARDS",
    "Zone",
    "add_mana",
    "apply_action",
    "attack_with_creature",
    "block_with_creature",
    "can_pay_mana_cost",
    "clear_mana_pool",
    "create_starting_game_state",
    "draw_card",
    "get_legal_actions",
    "is_legal_action",
    "move_card",
    "next_phase",
    "play_card",
    "play_land",
    "spend_mana_cost",
    "tap_all_lands_for_mana",
    "tap_land_for_mana",
]
