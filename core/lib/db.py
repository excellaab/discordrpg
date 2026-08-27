import asyncpg
import json
import inspect
from functools import wraps
from core.lib.log import dblogger
import discord
import enum

class GearTier(enum.IntEnum):
    common = 1
    rare = 2
    legendary = 3
    prismatic_i = 4
    prismatic_ii = 5
    prismatic_iii = 6

async def init_db(conn: asyncpg.Connection):
    await conn.set_type_codec(
        'gear_tier',
        encoder=lambda t: t.name,
        decoder=lambda t: GearTier[t],
        schema='public'
    )

dbpool: asyncpg.Pool = None
def dbExceptionHandler(func):
    @wraps(func)
    async def wrapper(user: discord.User, *args, **kwargs):
        try:
            async with dbpool.acquire() as conn:
                response = await func(user, conn, *args, **kwargs)
                return response, False
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
    return response

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
    return player

@dbExceptionHandler
async def fetch_equipment(user: discord.User, conn: asyncpg.Connection):
    records = await conn.fetch('''
        SELECT i.* 
        FROM run_equipment e
        JOIN run_inventory i ON i.instance_id IN (
            e.armor_instance_id, 
            e.weapon_instance_id, 
            e.secondary_instance_id
        )
        WHERE e.user_id = $1
    ''', user.id)

    # gear_slot = ['armor', 'weapon', 'secondary']
    equipment = {record['slot']: record for record in records}
    return equipment

def with_player_context(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # check if the user object exists
        user = kwargs.get('user')
        ctx_or_interaction = None
        if not user:
            for arg in args:
                if isinstance(arg, (discord.User, discord.Member)):
                    user = arg
                    break
                elif hasattr(arg, 'author') and isinstance(getattr(arg, 'author'), (discord.User, discord.Member)):
                    user = arg.author
                    ctx_or_interaction = arg
                    break
                elif hasattr(arg, 'user') and isinstance(getattr(arg, 'user'), (discord.User, discord.Member)):
                    user = arg.user
                    ctx_or_interaction = arg
                    break
                    
        if not user:
            # fallback if user object doesnt exist
            return await func(*args, **kwargs) if inspect.iscoroutinefunction(func) else func(*args, **kwargs)

        sig = inspect.signature(func)
        needs_user = 'user' in sig.parameters
        needs_player = 'player' in sig.parameters
        needs_gear = 'equipment' in sig.parameters
        needs_class = 'class_name' in sig.parameters
        needs_run = 'run' in sig.parameters
        
        async def send_error(msg):
            if ctx_or_interaction:
                if hasattr(ctx_or_interaction, 'send'):
                    await ctx_or_interaction.send(msg)
                elif hasattr(ctx_or_interaction, 'response') and hasattr(ctx_or_interaction.response, 'send_message'):
                    if not ctx_or_interaction.response.is_done():
                        await ctx_or_interaction.response.send_message(msg, ephemeral=True) 

        player = None
        if needs_player or needs_class:
            player, db_error = await fetch_player(user)
            if db_error:
                dblogger.exception(f"Error fetching player for user {user.id}")
                await send_error("An error occurred while accessing the database. Please try again later.")
                return None
                
        equipment = None
        if needs_gear:
            equipment, armor_error = await fetch_equipment(user)
            if armor_error:
                dblogger.exception(f"Error fetching armor for user {user.id}")
                await send_error("An error occurred while accessing the database. Please try again later.")
                return None
                
        run = None
        if needs_run:
            run, run_error = await fetchrun(user)
            if run_error:
                dblogger.exception(f"Error fetching run for user {user.id}")
                await send_error("An error occurred while accessing the database. Please try again later.")
                return None
                
        inject = {}
        if needs_user:
            inject['user'] = user
        if needs_player: 
            inject['player'] = player
        if needs_gear: 
            inject['equipment'] = equipment
        if needs_class:
            inject['class_name'] = player['class'] if player else None
        if needs_run:
            inject['run'] = run
            
        final_kwargs = {**inject, **kwargs}
        
        if inspect.iscoroutinefunction(func):
            return await func(*args, **final_kwargs)
        return func(*args, **final_kwargs)
        
    return wrapper

@dbExceptionHandler
async def update_xp(user: discord.User, conn: asyncpg.Connection, xp: int, levelup: int = 0):
    await conn.execute('''
        UPDATE runs
        SET xp = $2
        WHERE user_id = $1;
    ''', user.id, xp)

    if levelup > 0:
        await conn.execute('''
            UPDATE runs
            SET run_level = run_level + $2
            WHERE user_id = $1;
        ''', user.id, levelup)

    return None

@dbExceptionHandler
async def update_relic(user: discord.User, conn: asyncpg.Connection, relic: int):
    await conn.execute('''
        UPDATE players
        SET relic = relic + $1
        WHERE user_id = $2;
    ''', user.id, relic)

    return None

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
    return response

@dbExceptionHandler
async def fetchrun(user: discord.User, conn: asyncpg.Connection):
    run = await conn.fetchrow('SELECT * FROM runs WHERE user_id = $1', user.id)

    return run

@dbExceptionHandler
async def endrun(user: discord.User, conn: asyncpg.Connection):
    await conn.fetchrow('DELETE FROM runs WHERE user_id = $1', user.id)

    return None
