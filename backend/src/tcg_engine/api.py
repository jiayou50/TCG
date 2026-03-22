"""FastAPI app for exposing the TCG engine."""

from __future__ import annotations

from fastapi import FastAPI

from .bootstrap import create_starting_game_state

app = FastAPI(title="TCG Backend API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/game-state")
def game_state() -> dict[str, object]:
    state = create_starting_game_state()

    return {
        "turnNumber": state.turn_number,
        "phase": state.phase.value,
        "activePlayerId": state.active_player_id,
        "priorityPlayerId": state.priority_player_id,
        "eventLog": state.event_log,
        "players": {
            player_id: {
                "lifeTotal": player.life_total,
                "library": player.library,
                "hand": player.hand,
                "battlefield": player.battlefield,
                "graveyard": player.graveyard,
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
