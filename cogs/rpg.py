import discord
from discord.ext import commands
import asyncpg
from core import db

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
        userid = ctx.author.id

        response = await db._new_player(ctx, userid)

        if response:
            await ctx.send(f"Welcome, {ctx.author.mention}! Your adventure begins now.")
        else:
            await ctx.send(f"{ctx.author.mention}, you have already started your adventure!")

    # profile: main
    @commands.command(aliases=['p'])
    async def profile(self, ctx, query: fetchUser | None = None):
        user = query if query else ctx.author
        player, db_error = await db._fetch_player(ctx, user)

        if db_error:
            return

        if player:
            profilembed = discord.Embed(
                title = f"{user.name} - {player['class'] if player['class'] else 'NPC'}",
                color = discord.Color.blue(),
                timestamp = ctx.message.created_at
            )

            profilembed.set_thumbnail(url = user.avatar.url)
            profilembed.set_author(name = "Profile/Main", icon_url = self.bot.user.avatar.url)

            profilembed.add_field(name = "CHAR", value = f"""
                **Level**: {player['level']}
                **XP**: {player['xp']}
            """, inline = False)
            profilembed.add_field(name = "STAT", value = f"""
                **STR**: {player['strength']}
                **DEX**: {player['dexterity']}
                **AGI**: {player['agility']}
                **INT**: {player['intelligence']}
                **DEF**: {player['defense']}
                **WIL**: {player['willpower']}
            """, inline = False)
            profilembed.add_field(name = "GOLD", value = f"""
                **Gold**: {player['gold']}G
                **Crystal**: {player['crystal']}C
            """, inline = False)

            await ctx.send(embed = profilembed)
        else:
            await ctx.send(f"{user.mention}, hasn't started an adventure yet! Use `!start` to begin.")

    # profile: combat
    # temporarily disabled until inventory system is implemented
    '''
    @commands.command(aliases=['pc'])
    async def pcombat(self, ctx, query: fetchUser | None = None):
        user = query if query else ctx.author
        player, db_error = await db._fetch_player(ctx, user)

        if db_error:
            return

        if player:
            combatembed = discord.Embed(
                title = f"{user.name} - {player['class'] if player['class'] else 'NPC'}",
                color = discord.Color.red(),
                timestamp = ctx.message.created_at
            )

            combatembed.set_thumbnail(url = user.avatar.url)
            combatembed.set_author(name = "Profile/Combat", icon_url = self.bot.user.avatar.url)

            combatembed.add_field(name = "ACTV", value = f"""
                **HP**: {player['health']}/{100}
                **MANA**: {player['mana']}
                **STAM**: {player['stamina']}
                **SPD**: {player['speed']}
            """, inline = False)
            combatembed.add_field(name = "PASV", value = f"""
                **CRIT**: {player['crit_chance']}%
                **CDMG**: {player['crit_damage']}%
                **EVA**: {player['evasion']}%
                **ACC**: {player['accuracy']}%
                **PEN**: {player['penetration']}%
            """, inline = False)

            await ctx.send(embed = combatembed)
        else:
            await ctx.send(f"{user.mention}, hasn't started an adventure yet! Use `!start` to begin.")   
    '''

async def setup(bot):
    await bot.add_cog(RPG(bot))