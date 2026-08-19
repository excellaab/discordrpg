import logging
from discord.ext import commands
from core import db
from core.ui import ClassChoiceView, ProfileView, build_combat_embed, build_profile_embed

logger = logging.getLogger("discordrpg")
dblogger = logging.getLogger("database")


class fetchUser(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            user = await commands.MemberConverter().convert(ctx, argument)
        except commands.UserNotFound:
            await ctx.send(f"User `{argument}` not found.")
            raise commands.BadArgument(f"User `{argument}` not found.")

        return user


class RPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # start
    @commands.command()
    async def start(self, ctx):
        user = ctx.author

        response, db_error = await db.new_player(user)

        if db_error:
            await ctx.send("Something went wrong. Please try again later.")
            dblogger.exception(f"Error fetching player for user {user.id} during stat calculation.")
            return

        if not response:
            await ctx.send(f"{ctx.author.mention}, you have already started your adventure!")
            return

        class_choice_view = ClassChoiceView(ctx.author)
        class_choice_view.message = await ctx.send("Hero, welcome! Choose your class.", view=class_choice_view)

        await class_choice_view.wait()
        if class_choice_view.error:
            return

    # profile: main
    @commands.command(aliases=['p'])
    async def profile(self, ctx, query: fetchUser | None = None):
        user = query if query else ctx.author
        player, db_error = await db.fetch_player(user)

        if db_error:
            await ctx.send("Something went wrong. Please try again later.")
            return

        if player:
            embed = await build_profile_embed(self.bot, user, player, ctx.message.created_at)
            view = ProfileView(self.bot, user, player, active_page="main")
            view.message = await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(f"{user.mention}, hasn't started an adventure yet! Use `!start` to begin.")

    # profile: combat
    @commands.command(aliases=['pc'])
    async def pcombat(self, ctx, query: fetchUser | None = None):
        user = query if query else ctx.author
        player, db_error = await db.fetch_player(user)

        if db_error:
            await ctx.send("Something went wrong. Please try again later.")
            return

        if player:
            embed = await build_combat_embed(self.bot, user, player, ctx.message.created_at)
            view = ProfileView(self.bot, user, player, active_page="combat")
            view.message = await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(f"{user.mention}, hasn't started an adventure yet! Use `!start` to begin.")

async def setup(bot):
    await bot.add_cog(RPG(bot))