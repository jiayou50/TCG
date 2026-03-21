"""Rule validation helpers.

This module is intentionally small for now and is the home for incremental
Magic-style timing and legality rules.
"""

from __future__ import annotations

from .game import Action, get_legal_actions
from .models import GameState


def is_legal_action(state: GameState, action: Action) -> bool:
    legal = get_legal_actions(state, action.actor_id)
    return action in legal
