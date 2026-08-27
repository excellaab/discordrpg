from dataclasses import dataclass
from collections import defaultdict
from enum import StrEnum
from typing import Callable
from core.lib.db import GearTier
from core.data.classes import CharacterClass


class CardType(StrEnum):
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"
    SKILL = "skill"
    HEAL = "heal"
    BUFF = "buff"
    DEBUFF = "debuff"


@dataclass
class Card:
    description: str
    rarity: GearTier
    action: Callable[..., None] | None
    card_type: CardType
    class_owned: CharacterClass | None = None


CARDS: dict[str, Card] = {
    "Punch": Card(
        description="Add 10 damage.",
        rarity=GearTier.common,
        action=None,
        card_type=CardType.OFFENSIVE,
        class_owned=None,
    ),
    "Block": Card(
        description="Reduces damage by 30%.",
        rarity=GearTier.common,
        action=None,
        card_type=CardType.DEFENSIVE,
        class_owned=None,
    ),
    "Rest": Card(
        description="Recover 20% max HP.",
        rarity=GearTier.common,
        action=None,
        card_type=CardType.HEAL,
        class_owned=None,
    ),
}

CARDS_BY_RARITY: dict[GearTier, list[str]] = defaultdict(list)
for card, data in CARDS.items():
    CARDS_BY_RARITY[data.rarity].append(card)