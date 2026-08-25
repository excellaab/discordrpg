import discord
from discord.ext import commands
from core.ui.run_ui import RunConfirmationView, MainRunView
from core.lib import db


class Run(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def run(self, ctx):
        player, db_error = await db.fetch_player(ctx.author)
        if db_error:
            await ctx.send("Error fetching player.", ephemeral=True)
            return
        if not player:
            await ctx.send("You don't have a character yet. Use `!start` first.", ephemeral=True)
            return
            
        run, db_error = await db.fetchrun(ctx.author)
        if db_error:
            await ctx.send("Error fetching run.", ephemeral=True)
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