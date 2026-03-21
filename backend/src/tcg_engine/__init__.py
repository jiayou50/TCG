"""Public interface for the TCG engine package."""

from .game import Action, apply_action, draw_card, get_legal_actions, move_card, next_phase
from .models import Card, GameState, Phase, PlayerState, Zone
from .rules import is_legal_action

__all__ = [
    "Action",
    "Card",
    "GameState",
    "Phase",
    "PlayerState",
    "Zone",
    "apply_action",
    "draw_card",
    "get_legal_actions",
    "is_legal_action",
    "move_card",
    "next_phase",
]
