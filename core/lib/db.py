import logging
import asyncpg
import json
import inspect
from functools import wraps

dblogger = logging.getLogger("database")
dbpool: asyncpg.Pool = None

async def new_player(user, class_name):
    try:
        async with dbpool.acquire() as conn:
            response = await conn.fetchrow('''
                INSERT INTO players (user_id, class) 
                VALUES ($1, $2) 
                ON CONFLICT (user_id) DO NOTHING
                RETURNING user_id;
            ''', user.id, class_name)
            
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

async def levelup(user):
    try:
        async with dbpool.acquire() as conn:
            pass
    except asyncpg.UndefinedTableError as e:
                dblogger.exception(f"Missing DB table while executing level up event for user {user.id}: {e}")
                return True, None
    except asyncpg.UndefinedColumnError as e:
        dblogger.exception(f"Missing DB column while executing level up event for user {user.id}: {e}")
        return True, None
    except Exception as e:
        dblogger.exception(f"DB error while executing level up event for user {user.id}: {e}")
        return True, None
    return False, None

async def startrun(user, hp):
    try:
        async with dbpool.acquire() as conn:
            response = await conn.fetchrow('''
                INSERT INTO runs (user_id, hp, rank_snapshot)
                SELECT $1, $2, rank
                FROM players
                WHERE user_id = $1
                ON CONFLICT (user_id) DO NOTHING
                RETURNING *;
            ''', user.id, hp)
            
            return response, False
    except asyncpg.UndefinedTableError as e:
        dblogger.exception(f"Missing DB table while starting run for {user.id}: {e}")
        return None, True
    except asyncpg.UndefinedColumnError as e:
        dblogger.exception(f"Missing DB column while starting run for {user.id}: {e}")
        return None, True
    except Exception as e:
        dblogger.exception(f"DB error starting run for {user.id}: {e}")
        return None, True

async def fetchrun(user):
    try:
        async with dbpool.acquire() as conn:
            run = await conn.fetchrow('SELECT * FROM runs WHERE user_id = $1', user.id)
            
            return run, False
    except asyncpg.UndefinedTableError as e:
        dblogger.exception(f"Missing DB table while fetching run for {user.id}: {e}")
        return None, True
    except asyncpg.UndefinedColumnError as e:
        dblogger.exception(f"Missing DB column while fetching run for {user.id}: {e}")
        return None, True
    except Exception as e:
        dblogger.exception(f"DB error fetching run for {user.id}: {e}")
        return None, True