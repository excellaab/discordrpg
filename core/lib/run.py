from .db import *
from .log import botlogger, dblogger

@with_player_context
async def on_gain_xp(user, player):
    xp_threshold = 100 * 1.25**()

@with_player_context
async def on_death(user, player, equipment, victory):
    if not player:
        # this should not happen
        # if it triggers, there may be an issue with fetch_player or with_player_context
        dblogger.error(f"Unable to kill player: Player not found. Userid {user.id}")
        return False

    dberror = await endrun(user)

    if dberror:
        dblogger.error(f"Unable to kill player: Failed to update user database on death. Userid {user.id}.")
        return False

    for gear in equipment:
        # relic gained = gear tier * 50 base val
        # temporary; may change over time
        player['relic'] = player['relic'] + (gear['tier'] * 50) * (1.2 if victory else 0.7)

    return True
    