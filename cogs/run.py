from discord.ext import commands
from core.ui.run_ui import RunConfirmationView


class Run(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def run(self, ctx):
        view = RunConfirmationView(ctx.author)
        view.message = await ctx.send("Start a run?", view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Run(bot))