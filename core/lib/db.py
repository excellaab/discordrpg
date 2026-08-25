import asyncpg
import json
import inspect
from functools import wraps
from core.lib.log import dblogger
import discord
dbpool: asyncpg.Pool = None

def dbExceptionHandler(func):
    @wraps(func)
    async def wrapper(user: discord.User, *args, **kwargs):
        try:
            async with dbpool.acquire() as conn:
                return await func(user, conn, *args, **kwargs)
        except asyncpg.UndefinedTableError as e:
            dblogger.exception(f"Missing DB table. UserID: {user.id}. Error: {e}")
            return None, True
        except asyncpg.UndefinedColumnError as e:
            dblogger.exception(f"Missing DB column. UserID: {user.id}. Error: {e}")
            return None, True
        except Exception as e:
            dblogger.exception(f"DB error occured. UserID: {user.id}. Error: {e}")
            return None, True
    return wrapper

@dbExceptionHandler
async def new_player(user: discord.User, conn: asyncpg.Connection, class_name: str):
    response = await conn.fetchrow('''
        INSERT INTO players (user_id, class) 
        VALUES ($1, $2) 
        ON CONFLICT (user_id) DO NOTHING
        RETURNING user_id;
    ''', user.id, class_name)
    
    return response, False

@dbExceptionHandler
async def set_class(user: discord.User, conn: asyncpg.Connection, class_name: str):
    await conn.execute('''
        UPDATE players 
        SET class = $1 
        WHERE user_id = $2
    ''', class_name, user.id)

@dbExceptionHandler
async def fetch_player(user: discord.User, conn: asyncpg.Connection):
    player = await conn.fetchrow('SELECT * FROM players WHERE user_id = $1', user.id)
    return player, False

@dbExceptionHandler
async def fetch_equipped_armor(user: discord.User, conn: asyncpg.Connection):
    armor = await conn.fetchrow('''
        SELECT i.instance_state 
        FROM player_equipment e
        JOIN player_inventory i ON e.armor_instance_id = i.instance_id
        WHERE e.user_id = $1
    ''', user.id)

    return armor, False

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

@dbExceptionHandler
async def levelup(user: discord.User, conn: asyncpg.Connection):
    pass

@dbExceptionHandler
async def startrun(user: discord.User, conn: asyncpg.Connection, hp: int):
    response = await conn.fetchrow('''
        INSERT INTO runs (user_id, hp, rank_snapshot)
        SELECT $1, $2, rank
        FROM players
        WHERE user_id = $1
        ON CONFLICT (user_id) DO NOTHING
        RETURNING *;
    ''', user.id, hp)
    
    return response, False

@dbExceptionHandler
async def fetchrun(user: discord.User, conn: asyncpg.Connection):
    run = await conn.fetchrow('SELECT * FROM runs WHERE user_id = $1', user.id)
    
    return run, False

@dbExceptionHandler
async def endrun(user: discord.User, conn: asyncpg.Connection):
    await conn.fetchrow('DELETE FROM runs WHERE user_id = $1', user.id)
    
    return False