import logging
import json
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
            
        # Call the actual function, passing the fetched data
        return await func(player, armor_data, *args, **kwargs)
        
    return wrapper

@fetchplayer
def maxhp(player, armor_data):
    total_flat_hp_from_armor = 0
    total_multiplier_hp_from_armor = 0
    
    if armor_data and armor_data.get('instance_state'):
        state = armor_data['instance_state']
        if isinstance(state, str):
            state = json.loads(state)
            
        total_flat_hp_from_armor = state.get('flat_hp', 0)
        total_multiplier_hp_from_armor = state.get('multiplier_hp', 0)

    return (1+player['vitality']*0.02) * ((1+total_multiplier_hp_from_armor) * (100 + player['level']*50 + total_flat_hp_from_armor))