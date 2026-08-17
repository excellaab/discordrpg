import logging
import asyncpg

logger = logging.getLogger("database")

dbpool: asyncpg.Pool = None

async def _new_player(ctx, userid):
    try:
        async with dbpool.acquire() as conn:
            response = await conn.fetchrow('''
                INSERT INTO players (user_id) 
                VALUES ($1) 
                ON CONFLICT (user_id) DO NOTHING
                RETURNING user_id;
            ''', userid)

            # TODO: remove this in production
            logger.info(f"Registering user {ctx.author.name} with id {userid}.")

            return response
    except asyncpg.UndefinedTableError as e:
        logger.exception(f"Missing DB table while registering user {userid}: {e}")
        await ctx.send("Something went wrong. Please try again later.")
        return
    except asyncpg.UndefinedColumnError as e:
        logger.exception(f"Missing DB column while registering user {userid}: {e}")
        await ctx.send("Something went wrong. Please try again later.")
        return
    except Exception as e:
        logger.exception(f"DB error registering user {userid}: {e}")
        await ctx.send("Something went wrong. Please try again later.")
        return

async def _fetch_player(ctx, user):
    try:
        async with dbpool.acquire() as conn:
            player = await conn.fetchrow('SELECT * FROM players WHERE user_id = $1', user.id)

            # TODO: remove this in production
            logger.info(f"Fetching profile for user {user.name} with id {user.id}.")
            return player, False
    except asyncpg.UndefinedTableError as e:
        logger.exception(f"Missing DB table while fetching profile for user {user.id}: {e}")
        await ctx.send("Something went wrong. Please try again later.")
        return None, True
    except asyncpg.UndefinedColumnError as e:
        logger.exception(f"Missing DB column while fetching profile for user {user.id}: {e}")
        await ctx.send("Something went wrong. Please try again later.")
        return None, True
    except Exception as e:
        logger.exception(f"DB error fetching profile for user {user.id}: {e}")
        await ctx.send("Something went wrong. Please try again later.")
        return None, True