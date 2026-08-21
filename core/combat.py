from core import db

async def on_levelup(ctx, user):
    dberror, level = db.levelup(user)

    if dberror:
        ctx.send("An error has occured.")
        return

    await ctx.send(f"{ctx.author.mention} leveled up to Level {level}!")
