import logging
import json
import math
from functools import wraps
from . import db

dblogger = logging.getLogger("database")

def fetchplayer(func):
    @wraps(func)
    async def wrapper(user, *args, **kwargs):
        player, db_error = await db._fetch_player(user)
        
        if db_error:
            # Handle the error centrally (e.g., log it, return a default)
            dblogger.exception(f"Error fetching player for user {user.id} during stat calculation.")
            return None
            
        armor_data, armor_error = await db._fetch_equipped_armor(user)
        
        if armor_error:
            dblogger.exception(f"Error fetching armor for user {user.id} during stat calculation.")
            return None
            
        import inspect
        # Call the actual function, passing the fetched data
        if inspect.iscoroutinefunction(func):
            return await func(player, armor_data, *args, **kwargs)
        return func(player, armor_data, *args, **kwargs)
        
    return wrapper

def _get_armor_modifiers(armor_data, stat_prefix):
    """Centralized helper to extract flat and multiplier stats from armor instance state."""
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

# active skills

@fetchplayer
async def maxhp(player, armor_data):
    flat_hp, multi_hp = _get_armor_modifiers(armor_data, 'hp')
    return (1 + player.get('vitality', 0) * 0.02) * ((1 + multi_hp) * (100 + player.get('level', 1) * 50 + flat_hp))

@fetchplayer
async def defense(player, armor_data):
    flat_def, multi_def = _get_armor_modifiers(armor_data, 'defense')
    
    # Defense scales with level, and is boosted heavily by vitality and slightly by strength.
    vitality_bonus = player.get('vitality', 0) * 0.015
    strength_bonus = player.get('strength', 0) * 0.005
    base_def = (player.get('level', 1) - 1) * 15 + flat_def
    
    return (1 + vitality_bonus + strength_bonus) * ((1 + multi_def) * base_def)

@fetchplayer
async def maxmana(player, armor_data):
    flat_mana, multi_mana = _get_armor_modifiers(armor_data, 'mana')
    
    # Mana scales with level, boosted by intelligence.
    intelligence_bonus = player.get('intelligence', 0) * 0.02
    base_mana = 100 + (player.get('level', 1) - 1) * 30 + flat_mana
    
    return (1 + intelligence_bonus) * ((1 + multi_mana) * base_mana)

# passive skills

@fetchplayer
async def crit_chance(player, armor_data):
    flat_crit, multi_crit = _get_armor_modifiers(armor_data, 'crit')
    
    # Crit chance receives a small base scaling from dexterity
    dex_bonus = player.get('dexterity', 0) * 0.001
    raw_crit = player.get('crit_chance', 0) + dex_bonus + flat_crit
    
    return raw_crit * (1 + multi_crit)

@fetchplayer
async def crit_damage(player, armor_data):
    flat_critdmg, multi_critdmg = _get_armor_modifiers(armor_data, 'critdmg')
    
    # Crit damage scales with strength
    str_bonus = player.get('strength', 0) * 0.002
    raw_critdmg = player.get('crit_damage', 0) + str_bonus + flat_critdmg
    
    return raw_critdmg * (1 + multi_critdmg)

@fetchplayer
async def evasion(player, armor_data):
    flat_evasion, multi_evasion = _get_armor_modifiers(armor_data, 'evasion')
    
    # Evasion scales with dexterity
    dex_bonus = player.get('dexterity', 0) * 0.001
    raw_evasion = player.get('evasion', 0) + dex_bonus + flat_evasion
    evasion_value = raw_evasion * (1 + multi_evasion)
    
    # Evasion NEVER exceeds 90%
    return min(0.90, evasion_value)

@fetchplayer
async def accuracy(player, armor_data):
    flat_acc, multi_acc = _get_armor_modifiers(armor_data, 'accuracy')
    
    # Accuracy scales heavily with dexterity
    dex_bonus = player.get('dexterity', 0) * 0.002
    raw_acc = player.get('accuracy', 0) + dex_bonus + flat_acc
    
    return raw_acc * (1 + multi_acc)

@fetchplayer
async def penetration(player, armor_data):
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
    return 1.0 - math.exp(-total_pen)
