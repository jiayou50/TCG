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


class CardType(str, Enum):
    CREATURE = "creature"
    LAND = "land"
    SORCERY = "sorcery"


class ManaColor(str, Enum):
    WHITE = "W"
    BLUE = "U"
    BLACK = "B"
    RED = "R"
    GREEN = "G"
    COLORLESS = "C"


@dataclass(slots=True, frozen=True)
class Card:
    id: str
    name: str
    owner_id: str
    mana_cost: str
    card_type: CardType
    power: int | None = None
    toughness: int | None = None
    produces_mana: tuple[ManaColor, ...] = ()
    effect_kind: str | None = None
    effect_value: int | None = None
    oracle_text: str | None = None

    def __post_init__(self) -> None:
        if self.card_type == CardType.CREATURE:
            if self.power is None or self.toughness is None:
                raise ValueError("Creature cards must have power and toughness")
        if self.card_type == CardType.LAND:
            if self.mana_cost:
                raise ValueError("Land cards must not have a mana cost")
            if not self.produces_mana:
                raise ValueError("Land cards must produce at least one mana color")
            if self.effect_kind is not None or self.effect_value is not None:
                raise ValueError("Land cards cannot have spell effects")
        if self.card_type == CardType.CREATURE and (
            self.effect_kind is not None or self.effect_value is not None
        ):
            raise ValueError("Creature cards cannot have spell effects")
        if self.card_type == CardType.SORCERY:
            if self.power is not None or self.toughness is not None:
                raise ValueError("Sorcery cards cannot have power or toughness")
            if self.produces_mana:
                raise ValueError("Sorcery cards cannot produce mana")
            if self.effect_kind is None:
                raise ValueError("Sorcery cards must define an effect kind")
            if not self.oracle_text:
                raise ValueError("Sorcery cards must define oracle text")


@dataclass(slots=True)
class PlayerState:
    id: str
    life_total: int = 20
    library: list[str] = field(default_factory=list)
    hand: list[str] = field(default_factory=list)
    battlefield: list[str] = field(default_factory=list)
    graveyard: list[str] = field(default_factory=list)
    tapped_permanents: set[str] = field(default_factory=set)
    summoning_sick_creatures: set[str] = field(default_factory=set)
    lands_played_this_turn: int = 0
    mana_pool: dict[ManaColor, int] = field(
        default_factory=lambda: {color: 0 for color in ManaColor}
    )


@dataclass(slots=True)
class GameState:
    players: dict[str, PlayerState]
    cards: dict[str, Card]
    active_player_id: str
    priority_player_id: str
    phase: Phase = Phase.BEGINNING
    turn_number: int = 1
    stack: list[str] = field(default_factory=list)
    declared_attackers: dict[str, str] = field(default_factory=dict)
    declared_blocks: dict[str, str] = field(default_factory=dict)
    event_log: list[str] = field(default_factory=list)
    has_drawn_this_turn: bool = False
    creature_damage: dict[str, int] = field(default_factory=dict)
