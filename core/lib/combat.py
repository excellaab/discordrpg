from .db import *
from .log import botlogger, dblogger

async def on_death(ctx, user: discord.User):
    player, dberror = await fetch_player(user)

    if dberror:
        dblogger.error("CRITICAL ERROR! Failed to update user database on death. Userid {user.id}.")
        return False

    dberror = await endrun(user)

    if dberror:
        dblogger.error("CRITICAL ERROR! Failed to update user database on death. Userid {user.id}.")
        return False

    