from discord.ext import commands


class Run(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def startrun(self, ctx):
        pass

async def setup(bot):
    await bot.add_cog(Run(bot))