import discord
from discord.ext import commands


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def print(self, ctx, *, message: str | None = None):
        if message is None:
            await ctx.send("Please provide a message to print.")
            return
        await ctx.send(message)

async def setup(bot):
    await bot.add_cog(Misc(bot))