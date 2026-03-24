"""Sample cards for early engine development."""

from __future__ import annotations

from .models import Card, CardType, ManaColor


SAMPLE_CARDS: dict[str, Card] = {
    "c_goblin_raider": Card(
        id="c_goblin_raider",
        name="Goblin Raider",
        owner_id="p1",
        mana_cost="1R",
        card_type=CardType.CREATURE,
        power=2,
        toughness=2,
    ),
    "c_elvish_mystic": Card(
        id="c_elvish_mystic",
        name="Elvish Mystic",
        owner_id="p1",
        mana_cost="G",
        card_type=CardType.CREATURE,
        power=1,
        toughness=1,
    ),
    "c_hill_giant": Card(
        id="c_hill_giant",
        name="Hill Giant",
        owner_id="p2",
        mana_cost="3R",
        card_type=CardType.CREATURE,
        power=3,
        toughness=3,
    ),
    "c_lightning_burst": Card(
        id="c_lightning_burst",
        name="Lightning Burst",
        owner_id="p1",
        mana_cost="1R",
        card_type=CardType.SORCERY,
        effect_kind="damage_target_creature",
        effect_value=2,
        oracle_text="Deal 2 damage to target creature.",
    ),
    "c_doom_blade": Card(
        id="c_doom_blade",
        name="Doom Blade",
        owner_id="p2",
        mana_cost="1B",
        card_type=CardType.SORCERY,
        effect_kind="destroy_target_creature",
        oracle_text="Destroy target creature.",
    ),
    "c_plains": Card(
        id="c_plains",
        name="Plains",
        owner_id="p1",
        mana_cost="",
        card_type=CardType.LAND,
        produces_mana=(ManaColor.WHITE,),
    ),
    "c_island": Card(
        id="c_island",
        name="Island",
        owner_id="p1",
        mana_cost="",
        card_type=CardType.LAND,
        produces_mana=(ManaColor.BLUE,),
    ),
    "c_swamp": Card(
        id="c_swamp",
        name="Swamp",
        owner_id="p1",
        mana_cost="",
        card_type=CardType.LAND,
        produces_mana=(ManaColor.BLACK,),
    ),
    "c_mountain": Card(
        id="c_mountain",
        name="Mountain",
        owner_id="p1",
        mana_cost="",
        card_type=CardType.LAND,
        produces_mana=(ManaColor.RED,),
    ),
    "c_forest": Card(
        id="c_forest",
        name="Forest",
        owner_id="p1",
        mana_cost="",
        card_type=CardType.LAND,
        produces_mana=(ManaColor.GREEN,),
    ),
}
