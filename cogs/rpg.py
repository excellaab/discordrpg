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
            except asyncpg.PostgresError as e:
                self.bot.botlogger.exception(f"DB error registering user {user_id}: {e}")
                await ctx.send("Something went wrong. Please try again later.")
                return

            if response:
                await ctx.send(f"Welcome, {ctx.author.mention}! Your adventure begins now.")
            else:
                await ctx.send(f"{ctx.author.mention}, you have already started your adventure!")

    # profile
    @commands.command()
    async def profile(self, ctx, user: discord.User | None = None):
        user_id = user.id if user else ctx.author.id

        async with self.bot.db_pool.acquire() as conn:
            try:
                player = await conn.fetchrow('SELECT * FROM players WHERE user_id = $1', user_id)
            except asyncpg.PostgresError as e:
                self.bot.botlogger.exception(f"DB error fetching profile for user {user_id}: {e}")
                await ctx.send("Something went wrong. Please try again later.")
                return

            if player:
                embed = discord.Embed(
                    title = user.name if user else ctx.author.name,
                    color = discord.Color.blue(),
                    timestamp = ctx.message.created_at
                )

                embed.set_thumbnail(url = user.avatar.url if user else ctx.author.avatar.url)
                embed.set_author(name = "Profile")

                embed.add_field(name = "Health", value = f"{player['hp']}/{player['maxhp']}", inline = False)
                embed.add_field(name = "Level", value = player['level'], inline = False)
                embed.add_field(name = "Experience", value = player['xp'], inline = False)
                embed.add_field(name = "Gold", value = f"{player['gold']}G", inline = False)

                await ctx.send(embed = embed)
            else:
                await ctx.send(f"{ctx.author.mention}, you haven't started your adventure yet! Use `!start` to begin.")

async def setup(bot):
    await bot.add_cog(RPG(bot))