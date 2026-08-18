import logging
import asyncpg

dblogger = logging.getLogger("database")

dbpool: asyncpg.Pool = None

async def _new_player(user):
    userid = user.id
    try:
        async with dbpool.acquire() as conn:
            response = await conn.fetchrow('''
                INSERT INTO players (user_id) 
                VALUES ($1) 
                ON CONFLICT (user_id) DO NOTHING
                RETURNING user_id;
            ''', userid)
            
            return response, False
    except asyncpg.UndefinedTableError as e:
        dblogger.exception(f"Missing DB table while registering user {userid}: {e}")
        return None, True
    except asyncpg.UndefinedColumnError as e:
        dblogger.exception(f"Missing DB column while registering user {userid}: {e}")
        return None, True
    except Exception as e:
        dblogger.exception(f"DB error registering user {userid}: {e}")
        return None, True

async def _fetch_player(user):
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

async def _fetch_equipped_armor(user):
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