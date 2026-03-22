"""Core game operations for the TCG engine."""

from __future__ import annotations

from dataclasses import dataclass

from .models import CardType, GameState, ManaColor, Phase, PlayerState, Zone


@dataclass(slots=True, frozen=True)
class Action:
    kind: str
    actor_id: str
    card_id: str | None = None
    target_id: str | None = None


def draw_card(state: GameState, player_id: str) -> None:
    if player_id != state.active_player_id:
        raise ValueError("Only the active player can draw")
    if state.phase != Phase.BEGINNING:
        raise ValueError("Cards can only be drawn during the beginning phase")
    if state.has_drawn_this_turn:
        raise ValueError("A player can only draw one card during the beginning phase")

    player = state.players[player_id]
    if not player.library:
        state.event_log.append(f"{player_id} tried to draw from empty library")
        state.has_drawn_this_turn = True
        return

    card_id = player.library.pop(0)
    player.hand.append(card_id)
    state.has_drawn_this_turn = True
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
        player.summoning_sick_creatures.discard(card_id)
    elif state.cards[card_id].card_type == CardType.CREATURE:
        player.summoning_sick_creatures.add(card_id)
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


def tap_all_lands_for_mana(state: GameState, player_id: str) -> None:
    if player_id != state.active_player_id:
        raise ValueError("Only the active player can tap all lands")

    player = state.players[player_id]
    untapped_lands = [
        card_id
        for card_id in player.battlefield
        if state.cards[card_id].card_type == CardType.LAND and card_id not in player.tapped_permanents
    ]
    if not untapped_lands:
        raise ValueError("No untapped lands available to tap")

    for card_id in untapped_lands:
        tap_land_for_mana(state, player_id, card_id)

    state.event_log.append(f"{player_id} tapped all untapped lands for mana")


def play_card(state: GameState, player_id: str, card_id: str) -> None:
    player = state.players[player_id]
    if player_id != state.active_player_id:
        raise ValueError("Only the active player can play a card")
    if state.phase not in (Phase.PRECOMBAT_MAIN, Phase.POSTCOMBAT_MAIN):
        raise ValueError("Cards can only be played during main phases")
    if card_id not in player.hand:
        raise ValueError("Card must be in hand")

    card = state.cards[card_id]
    if card.card_type == CardType.LAND:
        raise ValueError("Use play_land for land cards")
    if not can_pay_mana_cost(player, card.mana_cost):
        raise ValueError("Insufficient mana to play card")

    spend_mana_cost(player, card.mana_cost)
    move_card(state, player_id, card_id, Zone.HAND, Zone.BATTLEFIELD)
    state.event_log.append(f"{player_id} played card {card_id}")


def attack_with_creature(state: GameState, player_id: str, card_id: str) -> None:
    player = state.players[player_id]
    if state.phase != Phase.COMBAT:
        raise ValueError("Attacks can only be declared during combat")
    if player_id != state.active_player_id:
        raise ValueError("Only the active player can declare attackers")
    if card_id not in player.battlefield:
        raise ValueError("Creature must be on the battlefield")
    if card_id in player.tapped_permanents:
        raise ValueError("Creature is tapped")
    if card_id in player.summoning_sick_creatures:
        raise ValueError("Creature has summoning sickness")

    card = state.cards[card_id]
    if card.card_type != CardType.CREATURE:
        raise ValueError("Only creatures can attack")

    player.tapped_permanents.add(card_id)
    defending_player_id = next(pid for pid in state.players if pid != player_id)
    state.declared_attackers[card_id] = defending_player_id
    state.event_log.append(f"{player_id} attacked with {card_id}")


def block_with_creature(state: GameState, player_id: str, card_id: str, attacker_id: str) -> None:
    player = state.players[player_id]
    if state.phase != Phase.COMBAT:
        raise ValueError("Blocks can only be declared during combat")
    attacking_player_id = _attacking_player_id(state)
    if attacking_player_id is None:
        raise ValueError("No attackers declared")
    if player_id == attacking_player_id:
        raise ValueError("Attacking player cannot block")
    if card_id not in player.battlefield:
        raise ValueError("Blocking creature must be on the battlefield")
    if card_id in player.tapped_permanents:
        raise ValueError("Blocking creature is tapped")
    if attacker_id not in state.declared_attackers:
        raise ValueError("Target attacker is not currently attacking")

    card = state.cards[card_id]
    if card.card_type != CardType.CREATURE:
        raise ValueError("Only creatures can block")

    if card_id in state.declared_blocks:
        raise ValueError("Blocker has already been assigned")

    state.declared_blocks[card_id] = attacker_id
    state.event_log.append(f"{player_id} blocked {attacker_id} with {card_id}")


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


def resolve_combat_damage(state: GameState) -> None:
    if state.phase != Phase.COMBAT:
        raise ValueError("Combat damage can only be resolved during combat")

    combat_damage: dict[str, int] = {}
    blockers_by_attacker: dict[str, list[str]] = {}
    for blocker_id, attacker_id in state.declared_blocks.items():
        blockers_by_attacker.setdefault(attacker_id, []).append(blocker_id)

    for attacker_id, defending_player_id in state.declared_attackers.items():
        attacker = state.cards[attacker_id]
        if attacker.card_type != CardType.CREATURE:
            continue

        blockers = blockers_by_attacker.get(attacker_id, [])
        if not blockers:
            state.players[defending_player_id].life_total -= attacker.power or 0
            state.event_log.append(
                f"{attacker_id} dealt {attacker.power} damage to {defending_player_id}"
            )
            continue

        primary_blocker_id = blockers[0]
        primary_blocker = state.cards[primary_blocker_id]
        combat_damage[primary_blocker_id] = combat_damage.get(primary_blocker_id, 0) + (attacker.power or 0)
        state.event_log.append(
            f"{attacker_id} dealt {attacker.power} damage to {primary_blocker_id}"
        )

        for blocker_id in blockers:
            blocker = state.cards[blocker_id]
            combat_damage[attacker_id] = combat_damage.get(attacker_id, 0) + (blocker.power or 0)
            state.event_log.append(
                f"{blocker_id} dealt {blocker.power} damage to {attacker_id}"
            )

    for creature_id, damage in combat_damage.items():
        creature = state.cards[creature_id]
        if creature.card_type != CardType.CREATURE:
            continue
        if damage < (creature.toughness or 0):
            continue

        owner_id = creature.owner_id
        if creature_id not in state.players[owner_id].battlefield:
            continue

        move_card(state, owner_id, creature_id, Zone.BATTLEFIELD, Zone.GRAVEYARD)
        state.event_log.append(f"{creature_id} was destroyed in combat")


def next_phase(state: GameState) -> None:
    order = [
        Phase.BEGINNING,
        Phase.PRECOMBAT_MAIN,
        Phase.COMBAT,
        Phase.POSTCOMBAT_MAIN,
        Phase.ENDING,
    ]
    idx = order.index(state.phase)
    _clear_all_mana_pools(state)
    if idx == len(order) - 1:
        _next_turn(state)
        return
    if state.phase == Phase.COMBAT:
        resolve_combat_damage(state)
        state.declared_attackers.clear()
        state.declared_blocks.clear()
    state.phase = order[idx + 1]
    state.event_log.append(f"phase -> {state.phase.value}")


def pass_turn(state: GameState, player_id: str) -> None:
    if player_id != state.active_player_id:
        raise ValueError("Only the active player can pass the turn")
    if state.phase not in (Phase.PRECOMBAT_MAIN, Phase.POSTCOMBAT_MAIN):
        raise ValueError("Turns can only be passed during main phases")

    _next_turn(state)
    state.event_log.append(f"{player_id} passed turn")


def apply_action(state: GameState, action: Action) -> None:
    if action.kind == "draw":
        draw_card(state, action.actor_id)
        next_phase(state)
        return
    if action.kind == "pass_priority":
        attacking_player_id = _attacking_player_id(state)
        if state.phase == Phase.COMBAT and attacking_player_id is not None:
            defending_player_id = next(pid for pid in state.players if pid != attacking_player_id)
            if action.actor_id == attacking_player_id and state.active_player_id == attacking_player_id:
                state.active_player_id = defending_player_id
                state.priority_player_id = defending_player_id
                state.event_log.append(f"priority passed to {defending_player_id} (declare blockers)")
                return
            if action.actor_id == defending_player_id and state.active_player_id == defending_player_id:
                state.active_player_id = attacking_player_id
                state.priority_player_id = attacking_player_id
                state.event_log.append(f"priority passed to {attacking_player_id}")
                return
        next_phase(state)
        return
    if action.kind == "next_phase":
        next_phase(state)
        return
    if action.kind == "pass_turn":
        pass_turn(state, action.actor_id)
        return
    if action.kind == "play_land" and action.card_id:
        play_land(state, action.actor_id, action.card_id)
        return
    if action.kind == "play_card" and action.card_id:
        play_card(state, action.actor_id, action.card_id)
        return
    if action.kind == "attack_with_creature" and action.card_id:
        attack_with_creature(state, action.actor_id, action.card_id)
        return
    if action.kind == "block_with_creature" and action.card_id and action.target_id:
        block_with_creature(state, action.actor_id, action.card_id, action.target_id)
        return
    if action.kind == "tap_land_for_mana" and action.card_id:
        tap_land_for_mana(state, action.actor_id, action.card_id)
        return
    if action.kind == "tap_all_lands_for_mana":
        tap_all_lands_for_mana(state, action.actor_id)
        return
    if action.kind == "resolve_combat_damage":
        resolve_combat_damage(state)
        state.declared_attackers.clear()
        state.declared_blocks.clear()
        return
    raise ValueError(f"Unsupported action kind: {action.kind}")


def get_legal_actions(state: GameState, player_id: str) -> list[Action]:
    actions: list[Action] = [Action(kind="start_new_game", actor_id=player_id)]
    if state.phase == Phase.BEGINNING:
        if player_id == state.active_player_id and not state.has_drawn_this_turn:
            actions.append(Action(kind="draw", actor_id=player_id))
        return actions

    if player_id == state.priority_player_id:
        actions.append(Action(kind="pass_priority", actor_id=player_id))

    player = state.players[player_id]
    if player_id == state.active_player_id and state.phase in (Phase.PRECOMBAT_MAIN, Phase.POSTCOMBAT_MAIN):
        actions.append(Action(kind="pass_turn", actor_id=player_id))
        if player.lands_played_this_turn < 1:
            for card_id in player.hand:
                if state.cards[card_id].card_type == CardType.LAND:
                    actions.append(Action(kind="play_land", actor_id=player_id, card_id=card_id))
        for card_id in player.hand:
            card = state.cards[card_id]
            if card.card_type == CardType.CREATURE and can_pay_mana_cost(player, card.mana_cost):
                actions.append(Action(kind="play_card", actor_id=player_id, card_id=card_id))

    if state.phase == Phase.COMBAT:
        attacking_player_id = _attacking_player_id(state) or state.active_player_id
        if player_id == attacking_player_id:
            for card_id in player.battlefield:
                card = state.cards[card_id]
                if (
                    card.card_type == CardType.CREATURE
                    and card_id not in state.declared_attackers
                    and card_id not in player.tapped_permanents
                    and card_id not in player.summoning_sick_creatures
                ):
                    actions.append(Action(kind="attack_with_creature", actor_id=player_id, card_id=card_id))
        elif state.declared_attackers:
            for card_id in player.battlefield:
                card = state.cards[card_id]
                if card.card_type != CardType.CREATURE or card_id in player.tapped_permanents:
                    continue
                for attacker_id in state.declared_attackers:
                    actions.append(
                        Action(
                            kind="block_with_creature",
                            actor_id=player_id,
                            card_id=card_id,
                            target_id=attacker_id,
                        )
                    )

    for card_id in player.battlefield:
        card = state.cards[card_id]
        if card.card_type == CardType.LAND and card_id not in player.tapped_permanents:
            actions.append(Action(kind="tap_land_for_mana", actor_id=player_id, card_id=card_id))
            if player_id == state.active_player_id and not any(
                action.kind == "tap_all_lands_for_mana" for action in actions
            ):
                actions.append(Action(kind="tap_all_lands_for_mana", actor_id=player_id))
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
    state.has_drawn_this_turn = False
    state.declared_attackers.clear()
    state.declared_blocks.clear()

    for player in state.players.values():
        clear_mana_pool(player)

    active_player = state.players[next_player]
    active_player.tapped_permanents.clear()
    active_player.summoning_sick_creatures.clear()
    active_player.lands_played_this_turn = 0

    state.event_log.append(f"turn -> {state.turn_number}, active -> {next_player}")


def _clear_all_mana_pools(state: GameState) -> None:
    for player in state.players.values():
        clear_mana_pool(player)


def _attacking_player_id(state: GameState) -> str | None:
    if not state.declared_attackers:
        return None
    first_attacker_id = next(iter(state.declared_attackers))
    return state.cards[first_attacker_id].owner_id


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
