import logging
import asyncpg
import json
import inspect
from functools import wraps

dblogger = logging.getLogger("database")
dbpool: asyncpg.Pool = None

async def new_player(user):
    try:
        async with dbpool.acquire() as conn:
            response = await conn.fetchrow('''
                INSERT INTO players (user_id) 
                VALUES ($1) 
                ON CONFLICT (user_id) DO NOTHING
                RETURNING user_id;
            ''', user.id)
            
            return response, False
    except asyncpg.UndefinedTableError as e:
        dblogger.exception(f"Missing DB table while registering user {user.id}: {e}")
        return None, True
    except asyncpg.UndefinedColumnError as e:
        dblogger.exception(f"Missing DB column while registering user {user.id}: {e}")
        return None, True
    except Exception as e:
        dblogger.exception(f"DB error registering user {user.id}: {e}")
        return None, True

async def set_class(user, class_name):
    try:
        async with dbpool.acquire() as conn:
            await conn.execute('''
                UPDATE players 
                SET class = $1 
                WHERE user_id = $2
            ''', class_name, user.id)
    except asyncpg.UndefinedTableError as e:
            dblogger.exception(f"Missing DB table while setting class for user {user.id}: {e}")
            return True
    except asyncpg.UndefinedColumnError as e:
        dblogger.exception(f"Missing DB column while setting class for user {user.id}: {e}")
        return True
    except Exception as e:
        dblogger.exception(f"DB error setting class for user {user.id}: {e}")
        return True
    return False

async def fetch_player(user):
    try:
        async with dbpool.acquire() as conn:
            player = await conn.fetchrow('SELECT * FROM players WHERE user_id = $1', user.id)
            return player, False
    except asyncpg.UndefinedTableError as e:
        dblogger.exception(f"Missing DB table while fetching profile for user {user.id}: {e}")
        return None, True
    except asyncpg.UndefinedColumnError as e:
        dblogger.exception(f"Missing DB column while fetching profile for user {user.id}: {e}")
        return None, True
    except Exception as e:
        dblogger.exception(f"DB error fetching profile for user {user.id}: {e}")
        return None, True

async def fetch_equipped_armor(user):
    try:
        async with dbpool.acquire() as conn:
            armor = await conn.fetchrow('''
                SELECT i.instance_state 
                FROM player_equipment e
                JOIN player_inventory i ON e.armor_instance_id = i.instance_id
                WHERE e.user_id = $1
            ''', user.id)

            return armor, False
    except asyncpg.UndefinedTableError as e:
        dblogger.exception(f"Missing DB table while fetching armor for user {user.id}: {e}")
        return None, True
    except asyncpg.UndefinedColumnError as e:
        dblogger.exception(f"Missing DB column while fetching armor for user {user.id}: {e}")
        return None, True
    except Exception as e:
        dblogger.exception(f"DB error fetching armor for user {user.id}: {e}")
        return None, True

def get_armor_modifiers(armor_data, stat_prefix):
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

def with_player_context(func):
    @wraps(func)
    async def wrapper(user, *args, **kwargs):
        sig = inspect.signature(func)
        needs_player = 'player' in sig.parameters
        needs_armor = 'armor_data' in sig.parameters
        needs_class = 'class_name' in sig.parameters
        
        player = None
        if needs_player or needs_class:
            player, db_error = await fetch_player(user)
            if db_error:
                dblogger.exception(f"Error fetching player for user {user.id} during stat calculation.")
                return None
                
        armor_data = None
        if needs_armor:
            armor_data, armor_error = await fetch_equipped_armor(user)
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