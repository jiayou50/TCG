"""Core game operations for the TCG engine."""

from __future__ import annotations

from dataclasses import dataclass

from .models import CardType, GameState, ManaColor, Phase, PlayerState, Zone


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
    if to_zone != Zone.BATTLEFIELD:
        player.tapped_permanents.discard(card_id)
    state.event_log.append(f"{card_id}: {from_zone.value} -> {to_zone.value}")


def play_land(state: GameState, player_id: str, card_id: str) -> None:
    player = state.players[player_id]
    if player_id != state.active_player_id:
        raise ValueError("Only the active player can play a land")
    if state.phase not in (Phase.PRECOMBAT_MAIN, Phase.POSTCOMBAT_MAIN):
        raise ValueError("Lands can only be played during main phases")
    if player.lands_played_this_turn >= 1:
        raise ValueError("A player can only play one land each turn")

    card = state.cards[card_id]
    if card.card_type != CardType.LAND:
        raise ValueError("Only lands can be played with play_land")

    move_card(state, player_id, card_id, Zone.HAND, Zone.BATTLEFIELD)
    player.lands_played_this_turn += 1
    state.event_log.append(f"{player_id} played land {card_id}")


def tap_land_for_mana(state: GameState, player_id: str, card_id: str) -> None:
    player = state.players[player_id]
    if card_id not in player.battlefield:
        raise ValueError("Land must be on the battlefield to tap for mana")
    if card_id in player.tapped_permanents:
        raise ValueError("Card is already tapped")

    card = state.cards[card_id]
    if card.card_type != CardType.LAND:
        raise ValueError("Only lands can be tapped for mana")

    player.tapped_permanents.add(card_id)
    for color in card.produces_mana:
        add_mana(player, color, 1)
    produced = "".join(color.value for color in card.produces_mana)
    state.event_log.append(f"{player_id} tapped {card_id} for {produced}")


def add_mana(player: PlayerState, color: ManaColor, amount: int = 1) -> None:
    if amount <= 0:
        raise ValueError("amount must be positive")
    player.mana_pool[color] += amount


def clear_mana_pool(player: PlayerState) -> None:
    for color in ManaColor:
        player.mana_pool[color] = 0


def can_pay_mana_cost(player: PlayerState, mana_cost: str) -> bool:
    required, generic = _parse_mana_cost(mana_cost)

    for color, amount in required.items():
        if player.mana_pool[color] < amount:
            return False

    remaining = sum(player.mana_pool.values()) - sum(required.values())
    return remaining >= generic


def spend_mana_cost(player: PlayerState, mana_cost: str) -> None:
    if not can_pay_mana_cost(player, mana_cost):
        raise ValueError("Insufficient mana")

    required, generic = _parse_mana_cost(mana_cost)

    for color, amount in required.items():
        player.mana_pool[color] -= amount

    generic_to_pay = generic
    for color in ManaColor:
        if generic_to_pay == 0:
            break
        available = player.mana_pool[color]
        spend = min(available, generic_to_pay)
        player.mana_pool[color] -= spend
        generic_to_pay -= spend


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
    if action.kind == "play_land" and action.card_id:
        play_land(state, action.actor_id, action.card_id)
        return
    if action.kind == "tap_land_for_mana" and action.card_id:
        tap_land_for_mana(state, action.actor_id, action.card_id)
        return
    raise ValueError(f"Unsupported action kind: {action.kind}")


def get_legal_actions(state: GameState, player_id: str) -> list[Action]:
    actions: list[Action] = []
    if player_id == state.priority_player_id:
        actions.append(Action(kind="next_phase", actor_id=player_id))

    if player_id == state.active_player_id and state.players[player_id].library:
        actions.append(Action(kind="draw", actor_id=player_id))

    player = state.players[player_id]
    if player_id == state.active_player_id and state.phase in (Phase.PRECOMBAT_MAIN, Phase.POSTCOMBAT_MAIN):
        if player.lands_played_this_turn < 1:
            for card_id in player.hand:
                if state.cards[card_id].card_type == CardType.LAND:
                    actions.append(Action(kind="play_land", actor_id=player_id, card_id=card_id))

    for card_id in player.battlefield:
        card = state.cards[card_id]
        if card.card_type == CardType.LAND and card_id not in player.tapped_permanents:
            actions.append(Action(kind="tap_land_for_mana", actor_id=player_id, card_id=card_id))
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

    for player in state.players.values():
        clear_mana_pool(player)

    active_player = state.players[next_player]
    active_player.tapped_permanents.clear()
    active_player.lands_played_this_turn = 0

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


def _parse_mana_cost(mana_cost: str) -> tuple[dict[ManaColor, int], int]:
    required = {color: 0 for color in ManaColor}
    generic = 0
    generic_buffer = ""

    for symbol in mana_cost:
        if symbol.isdigit():
            generic_buffer += symbol
            continue

        if generic_buffer:
            generic += int(generic_buffer)
            generic_buffer = ""

        color = ManaColor(symbol)
        required[color] += 1

    if generic_buffer:
        generic += int(generic_buffer)

    return required, generic
