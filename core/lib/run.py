import random
from .db import *
from .log import botlogger, dblogger
from core.data.cards import CARDS, CARDS_BY_RARITY

CARD_DROPRATE: dict[int, list[int]] = {
    0: [80, 19, 1, 0],
    1: [55, 38, 7, 0],
    2: [35, 50, 14, 1],
    3: [20, 50, 25, 5],
}

CARD_GUARANTEED: dict[int, GearTier] = {
    0: GearTier.rare,
    1: GearTier.rare,
    2: GearTier.legendary,
    3: GearTier.legendary,
}

RARITIES = [GearTier.common, GearTier.rare, GearTier.legendary, GearTier.prismatic_i]

@with_player_context
async def generate_card(user, run):
    pulls = 2

    # Level 1–4: 80% Common, 19% Rare, 1% Legendary
    # Level 5–9: 55% Common, 38% Rare, 7% Legendary
    # Level 10–14: 35% Common, 50% Rare, 14% Legendary, 1% Prismatic I
    # Level 15+: 20% Common, 50% Rare, 25% Legendary, 5% Prismatic I
    # Level 0 and 5 guarantees a rare card, level 10 and 15 guarantees a legendary
    level = run['level']
    cards = []
    
    for x in range(pulls):
        bracket = min(level // 5, 3)
        if level % 5 == 0:
            rolled_rarity = CARD_GUARANTEED[bracket]
        else:
            rolled_rarity = random.choices(RARITIES, weights=CARD_DROPRATE[bracket])[0]
            
        available_cards = [c for c in CARDS_BY_RARITY[rolled_rarity] if c not in cards]
        if not available_cards:
            available_cards = CARDS_BY_RARITY[rolled_rarity]
            
        cards.append(random.choice(available_cards))

    return cards

@with_player_context
async def on_gain_xp(user, run, xp):
    temp_xp = run['xp'] + xp
    level = run['run_level']
    xp_threshold = 100 * 1.25**(level-1)

    if temp_xp >= xp_threshold:
        level_increment = 0

        while temp_xp >= xp_threshold:
            level_increment += 1
            temp_xp -= xp_threshold
            xp_threshold = 100 * 1.25**((level+level_increment)-1)
            
        await update_xp(user, xp=temp_xp, levelup=level_increment)
    else:
        await update_xp(user, xp=temp_xp)

@with_player_context
async def on_death(user, player, equipment, victory):
    if not player:
        # this should not happen
        # if it triggers, there may be an issue with fetch_player or with_player_context
        dblogger.error(f"Unable to kill player: Player not found. Userid {user.id}")
        return False

    dberror = await endrun(user)

    if dberror:
        dblogger.error(f"Unable to kill player: Failed to update user database on death. Userid {user.id}.")
        return False

    for gear in equipment:
        # relic gained = gear tier * 50 base val
        # temporary; may change over time
        update_relic(user, relic=player['relic'] + (gear['tier'] * 50) * (1.2 if victory else 0.7))

    return True
    