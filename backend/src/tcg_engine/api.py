"""FastAPI app for exposing the TCG engine."""

from __future__ import annotations

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

from .bootstrap import create_starting_game_state
from .game import Action, apply_action, get_legal_actions
from .models import GameState

app = FastAPI(title="TCG Backend API", version="0.1.0")
_STATE = create_starting_game_state()


class ActionRequest(BaseModel):
    kind: str
    actorId: str
    cardId: str | None = None
    targetId: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/game-state")
def game_state() -> dict[str, object]:
    return _serialize_state(_STATE)


@app.get("/players/{player_id}/legal-actions")
def legal_actions(player_id: str) -> dict[str, object]:
    if player_id not in _STATE.players:
        raise HTTPException(status_code=404, detail=f"Unknown player: {player_id}")

    actions = get_legal_actions(_STATE, player_id)
    return {
        "playerId": player_id,
        "actions": [_serialize_action(action) for action in actions],
    }


@app.post("/actions")
def perform_action(payload: ActionRequest) -> dict[str, object]:
    global _STATE

    if payload.actorId not in _STATE.players:
        raise HTTPException(status_code=404, detail=f"Unknown player: {payload.actorId}")

    action = Action(
        kind=payload.kind,
        actor_id=payload.actorId,
        card_id=payload.cardId,
        target_id=payload.targetId,
    )

    if action.kind == "start_new_game":
        _STATE = create_starting_game_state()
        return {
            "appliedAction": _serialize_action(action),
            "gameState": _serialize_state(_STATE),
        }

    try:
        apply_action(_STATE, action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "appliedAction": _serialize_action(action),
        "gameState": _serialize_state(_STATE),
    }


@app.post("/reset")
def reset_game() -> dict[str, object]:
    global _STATE
    _STATE = create_starting_game_state()
    return {"status": "reset", "gameState": _serialize_state(_STATE)}


def _serialize_state(state: GameState) -> dict[str, object]:
    return {
        "turnNumber": state.turn_number,
        "phase": state.phase.value,
        "activePlayerId": state.active_player_id,
        "priorityPlayerId": state.priority_player_id,
        "declaredAttackers": state.declared_attackers,
        "declaredBlocks": state.declared_blocks,
        "eventLog": state.event_log,
        "players": {
            player_id: {
                "lifeTotal": player.life_total,
                "library": player.library,
                "hand": player.hand,
                "battlefield": player.battlefield,
                "graveyard": player.graveyard,
                "tappedPermanents": sorted(player.tapped_permanents),
                "summoningSickCreatures": sorted(player.summoning_sick_creatures),
                "manaPool": {color.value: amount for color, amount in player.mana_pool.items()},
            }
            for player_id, player in state.players.items()
        },
        "cards": {
            card_id: {
                "name": card.name,
                "ownerId": card.owner_id,
                "manaCost": card.mana_cost,
                "cardType": card.card_type.value,
                "power": card.power,
                "toughness": card.toughness,
                "producesMana": [color.value for color in card.produces_mana],
            }
            for card_id, card in state.cards.items()
        },
    }


def _serialize_action(action: Action) -> dict[str, str | None]:
    return {
        "kind": action.kind,
        "actorId": action.actor_id,
        "cardId": action.card_id,
        "targetId": action.target_id,
    }
