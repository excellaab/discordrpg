import discord
from discord.ext import commands
from core.ui.run_ui import RunConfirmationView, MainRunView
from core.lib.db import *


class Run(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @with_player_context
    async def run(self, ctx, player, run):
        if not player:
            await ctx.send("You don't have a character yet. Use `!start` first.", ephemeral=True)
            return

        if run:
            main_run_embed = discord.Embed(
                title="Run",
                description="[Placeholder main run embed]"
            )
            view = MainRunView(ctx.author)
            view.message = await ctx.send(embed=main_run_embed, view=view, ephemeral=True)
        else:
            view = RunConfirmationView(ctx.author)
            view.message = await ctx.send("Start a run?", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Run(bot))