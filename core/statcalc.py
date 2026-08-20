import logging
import json
import math
import inspect
from functools import wraps
from . import db

logger = logging.getLogger("discordrpg")
dblogger = logging.getLogger("database")

CLASS_OPTIONS = [
    "Knight",
    "Assassin",
    "Mage",
    "Succubus",
    "Bard",
]

class_stat_bonuses = {
    "strength": {"Knight"},
    "dexterity": {"Assassin", "Mage"},
    "intelligence": {"Mage", "Succubus"},
    "vitality": {"Knight"},
    "charisma": {"Bard", "Succubus"},
    "luck": {"Assassin", "Bard"}
}

# placeholder passives until changed later
# TODO: change passives, remove these comments when done
class_passive = {
    "Knight": [
        "Takes 15% less damage when below 50% HP.",
        "Converts 10% of total DEF into bonus attack damage."
    ],
    "Assassin": [
        "100% Critical Strike Chance on the 1st turn of combat.",
        "Deals +25% damage against enemies below 30% HP (Execute)."
    ],
    "Mage": [
        "Critical spell hits refund 20% of the spell's Mana cost.",
        "Ignores 20% of enemy Magic Resistance/Defense."
    ],
    "Succubus": [
        "15% Lifesteal: Heals for 15% of all damage dealt.",
        "When an enemy dies, gains a temporary Bone Shield equal to 10% of Max HP."
    ],
    "Bard": [
        "Gains +20% Gold and +15% XP from all battles and quests.",
        "Every basic attack has a 25% chance to grant a random party buff (e.g. +ATK, +DEF, or +EVA for 2 turns)."
    ]
}

def fetchplayer(func):
    @wraps(func)
    async def wrapper(user, *args, **kwargs):
        sig = inspect.signature(func)
        needs_player = 'player' in sig.parameters
        needs_armor = 'armor_data' in sig.parameters
        needs_class = 'class_name' in sig.parameters
        
        player = None
        if needs_player or needs_class:
            player, db_error = await db.fetch_player(user)
            if db_error:
                dblogger.exception(f"Error fetching player for user {user.id} during stat calculation.")
                return None
                
        armor_data = None
        if needs_armor:
            armor_data, armor_error = await db.fetch_equipped_armor(user)
            if armor_error:
                dblogger.exception(f"Error fetching armor for user {user.id} during stat calculation.")
                return None
                
        inject = {}
        if needs_player: 
            inject['player'] = player
        if needs_armor: 
            inject['armor_data'] = armor_data
        if needs_class:
            inject['class_name'] = player['class'] if player else None
            
        final_kwargs = {**inject, **kwargs}
        
        if inspect.iscoroutinefunction(func):
            return await func(*args, **final_kwargs)
        return func(*args, **final_kwargs)
        
    return wrapper

def _get_armor_modifiers(armor_data, stat_prefix):
    flat = 0
    multiplier = 0
    if armor_data and armor_data.get('instance_state'):
        state = armor_data['instance_state']
        if isinstance(state, str):
            try:
                state = json.loads(state)
            except json.JSONDecodeError:
                return 0, 0
                
        flat = state.get(f'flat_{stat_prefix}', 0)
        multiplier = state.get(f'multiplier_{stat_prefix}', 0)
    return flat, multiplier

# stat

@fetchplayer
def fetchStat(stat, armor_data, class_name):
    baseClassBonus = 5 if class_name in class_stat_bonuses.get(stat, set()) else 0
    baseArmorBonus = _get_armor_modifiers(armor_data, stat)[0] if armor_data else 0

    return round(baseClassBonus + baseArmorBonus)

# class passives

@fetchplayer
def classPassive(class_name):
    try:
        firstPassive = class_passive[class_name][0]
    except KeyError:
        firstPassive = "None"
    except IndexError:
        firstPassive = "_Error parsing passive._"
        logger.exception(f"Failed to parse class first passive. Class name {class_name}.")

    try:
        secondPassive = class_passive[class_name][1]
    except KeyError:
        secondPassive = "None"
    except IndexError:
        secondPassive = "_Error parsing passive._"
        logger.exception(f"Failed to parse class second passive. Class name {class_name}.")

    return firstPassive, secondPassive

# active skills

@fetchplayer
def maxhp(player, armor_data):
    flat_hp, multi_hp = _get_armor_modifiers(armor_data, 'hp')
    return round((1 + player.get('vitality', 0) * 0.02) * ((1 + multi_hp) * (100 + (player.get('level', 1)-1) * 50 + flat_hp)), 1)

@fetchplayer
def defense(player, armor_data):
    flat_def, multi_def = _get_armor_modifiers(armor_data, 'defense')
    
    # Defense scales with level, and is boosted heavily by vitality and slightly by strength.
    vitality_bonus = player.get('vitality', 0) * 0.015
    strength_bonus = player.get('strength', 0) * 0.005
    base_def = (player.get('level', 1) - 1) * 15 + flat_def
    
    return round((1 + vitality_bonus + strength_bonus) * ((1 + multi_def) * base_def), 1)

@fetchplayer
def maxmana(player, armor_data):
    flat_mana, multi_mana = _get_armor_modifiers(armor_data, 'mana')
    
    # Mana scales with level, boosted by intelligence.
    intelligence_bonus = player.get('intelligence', 0) * 0.02
    base_mana = 100 + (player.get('level', 1) - 1) * 30 + flat_mana
    
    return round((1 + intelligence_bonus) * ((1 + multi_mana) * base_mana), 1)

# passive skills

@fetchplayer
def crit_chance(player, armor_data):
    flat_crit, multi_crit = _get_armor_modifiers(armor_data, 'crit')
    
    # Crit chance receives a small base scaling from dexterity
    dex_bonus = player.get('dexterity', 0) * 0.001
    raw_crit = player.get('crit_chance', 0) + dex_bonus + flat_crit
    
    return round(raw_crit * (1 + multi_crit), 4)

@fetchplayer
def crit_damage(player, armor_data):
    flat_critdmg, multi_critdmg = _get_armor_modifiers(armor_data, 'critdmg')
    
    # Crit damage scales with strength
    str_bonus = player.get('strength', 0) * 0.002
    raw_critdmg = player.get('crit_damage', 0) + str_bonus + flat_critdmg
    
    return round(raw_critdmg * (1 + multi_critdmg), 4)

@fetchplayer
def evasion(player, armor_data):
    flat_evasion, multi_evasion = _get_armor_modifiers(armor_data, 'evasion')
    
    # Evasion scales with dexterity
    dex_bonus = player.get('dexterity', 0) * 0.001
    raw_evasion = player.get('evasion', 0) + dex_bonus + flat_evasion
    evasion_value = raw_evasion * (1 + multi_evasion)
    
    # Evasion NEVER exceeds 90%
    return round(min(0.90, evasion_value), 4)

@fetchplayer
def accuracy(player, armor_data):
    flat_acc, multi_acc = _get_armor_modifiers(armor_data, 'accuracy')
    
    # Accuracy scales heavily with dexterity
    dex_bonus = player.get('dexterity', 0) * 0.002
    raw_acc = player.get('accuracy', 0) + dex_bonus + flat_acc
    
    return round(raw_acc * (1 + multi_acc), 4)

@fetchplayer
def penetration(player, armor_data):
    flat_pen, multi_pen = _get_armor_modifiers(armor_data, 'pen')
    
    # Penetration scales with strength
    str_bonus = player.get('strength', 0) * 0.001
    raw_pen = player.get('penetration', 0) + str_bonus + flat_pen
    total_pen = raw_pen * (1 + multi_pen)
    
    # Exponentially harder to reach 100%. 
    # e^(-total_pen) approaches 0 as total_pen grows.
    # So 1 - e^(-total_pen) approaches 1.0 (100%) but will never reach it.
    if total_pen <= 0:
        return 0.0
    return round(1.0 - math.exp(-total_pen), 4)
