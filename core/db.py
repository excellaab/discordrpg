import logging
import asyncpg

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