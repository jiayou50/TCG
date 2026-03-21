"""Core game operations for the TCG engine."""

from __future__ import annotations

from dataclasses import dataclass

from .models import GameState, Phase, PlayerState, Zone


@dataclass(slots=True, frozen=True)
class Action:
    kind: str
    actor_id: str
    card_id: str | None = None


def draw_card(state: GameState, player_id: str) -> None:
    player = state.players[player_id]
    if not player.library:
        state.event_log.append(f"{player_id} tried to draw from empty library")
        return

    card_id = player.library.pop(0)
    player.hand.append(card_id)
    state.event_log.append(f"{player_id} drew {card_id}")


def move_card(state: GameState, player_id: str, card_id: str, from_zone: Zone, to_zone: Zone) -> None:
    player = state.players[player_id]
    from_list = _zone_list(player, from_zone)
    to_list = _zone_list(player, to_zone)

    if card_id not in from_list:
        raise ValueError(f"Card {card_id} not in {from_zone}")

    from_list.remove(card_id)
    to_list.append(card_id)
    state.event_log.append(f"{card_id}: {from_zone.value} -> {to_zone.value}")


def next_phase(state: GameState) -> None:
    order = [
        Phase.BEGINNING,
        Phase.PRECOMBAT_MAIN,
        Phase.COMBAT,
        Phase.POSTCOMBAT_MAIN,
        Phase.ENDING,
    ]
    idx = order.index(state.phase)
    if idx == len(order) - 1:
        _next_turn(state)
        return
    state.phase = order[idx + 1]
    state.event_log.append(f"phase -> {state.phase.value}")


def apply_action(state: GameState, action: Action) -> None:
    if action.kind == "draw":
        draw_card(state, action.actor_id)
        return
    if action.kind == "next_phase":
        next_phase(state)
        return
    raise ValueError(f"Unsupported action kind: {action.kind}")


def get_legal_actions(state: GameState, player_id: str) -> list[Action]:
    actions: list[Action] = []
    if player_id == state.priority_player_id:
        actions.append(Action(kind="next_phase", actor_id=player_id))
    if player_id == state.active_player_id and state.players[player_id].library:
        actions.append(Action(kind="draw", actor_id=player_id))
    return actions


def _next_turn(state: GameState) -> None:
    player_ids = list(state.players.keys())
    current_idx = player_ids.index(state.active_player_id)
    next_idx = (current_idx + 1) % len(player_ids)
    next_player = player_ids[next_idx]

    state.turn_number += 1
    state.active_player_id = next_player
    state.priority_player_id = next_player
    state.phase = Phase.BEGINNING
    state.event_log.append(f"turn -> {state.turn_number}, active -> {next_player}")


def _zone_list(player: PlayerState, zone: Zone) -> list[str]:
    if zone == Zone.LIBRARY:
        return player.library
    if zone == Zone.HAND:
        return player.hand
    if zone == Zone.BATTLEFIELD:
        return player.battlefield
    if zone == Zone.GRAVEYARD:
        return player.graveyard
    raise ValueError(f"Zone {zone} not supported for direct movement in player state")
