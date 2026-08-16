import discord
from discord.ext import commands
import asyncpg

class RPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # start
    @commands.command()
    async def start(self, ctx):
        user_id = ctx.author.id

        async with self.bot.db_pool.acquire() as conn:
            try:
                response = await conn.fetchrow('''
                    INSERT INTO players (user_id) 
                    VALUES ($1) 
                    ON CONFLICT (user_id) DO NOTHING
                    RETURNING user_id;
                ''', user_id)
                
                # TODO: remove this in production
                self.bot.dblogger.info(f"Registering user {ctx.author.name} with id {user_id}.")
            except asyncpg.PostgresError as e:
                self.bot.dblogger.exception(f"DB error registering user {user_id}: {e}")
                await ctx.send("Something went wrong. Please try again later.")
                return

            if response:
                await ctx.send(f"Welcome, {ctx.author.mention}! Your adventure begins now.")
            else:
                await ctx.send(f"{ctx.author.mention}, you have already started your adventure!")

    # profile: main
    @commands.command(aliases=['p'])
    async def profile(self, ctx, user: discord.User | None = None):
        user_id = user.id if user else ctx.author.id

        async with self.bot.db_pool.acquire() as conn:
            try:
                player = await conn.fetchrow('SELECT * FROM players WHERE user_id = $1', user_id)

                # TODO: remove this in production
                self.bot.dblogger.info(f"Fetching profile for user {ctx.author.name} with id {user_id}.")
            except asyncpg.PostgresError as e:
                self.bot.dblogger.exception(f"DB error fetching profile for user {user_id}: {e}")
                await ctx.send("Something went wrong. Please try again later.")
                return

            if player:
                profilembed = discord.Embed(
                    title = f"{user.name if user else ctx.author.name} - {player['class'] if player['class'] else 'NPC'}",
                    color = discord.Color.blue(),
                    timestamp = ctx.message.created_at
                )

                profilembed.set_thumbnail(url = user.avatar.url if user else ctx.author.avatar.url)
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
                await ctx.send(f"{ctx.author.mention}, you haven't started your adventure yet! Use `!start` to begin.")

    # profile: combat
    @commands.command(aliases=['pc'])
    async def pcombat(self, ctx, user: discord.User | None = None):
        user_id = user.id if user else ctx.author.id

        async with self.bot.db_pool.acquire() as conn:
            try:
                player = await conn.fetchrow('SELECT * FROM skills WHERE user_id = $1', user_id)

                # TODO: remove this in production
                self.bot.dblogger.info(f"Fetching skills for user {ctx.author.name} with id {user_id}.")
            except asyncpg.PostgresError as e:
                self.bot.dblogger.exception(f"DB error fetching skills for user {user_id}: {e}")
                await ctx.send("Something went wrong. Please try again later.")
                return

            if player:
                combatembed = discord.Embed(
                    title = f"{user.name if user else ctx.author.name} - {player['class'] if player['class'] else 'NPC'}",
                    color = discord.Color.blue(),
                    timestamp = ctx.message.created_at
                )

                combatembed.set_thumbnail(url = user.avatar.url if user else ctx.author.avatar.url)
                combatembed.set_author(name = "Profile/Combat", icon_url = self.bot.user.avatar.url)

                combatembed.add_field(name = "ACTV", value = f"""
                    **HP**: {player['hp']}/{player['max_hp']}
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
                await ctx.send(f"{ctx.author.mention}, you haven't started your adventure yet! Use `!start` to begin.")   

async def setup(bot):
    await bot.add_cog(RPG(bot))