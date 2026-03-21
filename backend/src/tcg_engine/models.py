"""Domain models for the core TCG engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Zone(str, Enum):
    LIBRARY = "library"
    HAND = "hand"
    BATTLEFIELD = "battlefield"
    GRAVEYARD = "graveyard"
    EXILE = "exile"
    STACK = "stack"


class Phase(str, Enum):
    BEGINNING = "beginning"
    PRECOMBAT_MAIN = "precombat_main"
    COMBAT = "combat"
    POSTCOMBAT_MAIN = "postcombat_main"
    ENDING = "ending"


@dataclass(slots=True, frozen=True)
class Card:
    id: str
    name: str
    owner_id: str


@dataclass(slots=True)
class PlayerState:
    id: str
    life_total: int = 20
    library: list[str] = field(default_factory=list)
    hand: list[str] = field(default_factory=list)
    battlefield: list[str] = field(default_factory=list)
    graveyard: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GameState:
    players: dict[str, PlayerState]
    cards: dict[str, Card]
    active_player_id: str
    priority_player_id: str
    phase: Phase = Phase.BEGINNING
    turn_number: int = 1
    stack: list[str] = field(default_factory=list)
    event_log: list[str] = field(default_factory=list)
