# use uv instead of pip/python
import logging
import os
import subprocess
import discord
import asyncpg
from discord.ext import commands
from dotenv import load_dotenv
from core import db

discord.utils.setup_logging(level=logging.INFO, root=True)
subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True, check=False)

class NoTracebackFilter(logging.Filter):
    def filter(self, record):
        if "Attempting a reconnect" in record.getMessage():
            record.exc_info = None 
            record.exc_text = None
        return True
    
botlogger = logging.getLogger("discordrpg")
botlogger.addFilter(NoTracebackFilter())

dblogger = logging.getLogger("database")
dblogger.setLevel(logging.INFO)

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
database_url = os.getenv("DATABASE_URL")

if not token:
    raise RuntimeError("Token is not set.")

if not database_url:
    raise RuntimeError("Database URL is not set.")


class Main(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        try:
            db.dbpool = await asyncpg.create_pool(database_url)
            dblogger.info("Database pool created successfully.")
        except Exception as e:
            dblogger.exception(f"Failed to create database pool: {e}")
            raise

        try:
            for filename in os.listdir("./cogs"):
                if filename.endswith(".py"):
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    botlogger.info(f"Loaded cog: {filename[:-3]}")
        except Exception as e:
            botlogger.error(f"Error occurred while loading cogs: {e}")
            raise

    async def close(self):
        if db.dbpool:
            await db.dbpool.close()
        await super().close()

bot = Main()

@bot.event
async def on_ready():
    botlogger.info("────────────────────────────────")
    botlogger.info(f"> Logged in as {bot.user} (ID: {bot.user.id})")
    botlogger.info("────────────────────────────────")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    
    raise error

@bot.command(aliases=['r'])
@commands.is_owner()
async def reload(ctx):
    try:
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                extension = filename[:-3]
                await bot.reload_extension(f"cogs.{extension}")
                await ctx.send(f"Successfully reloaded `cogs.{extension}`.")
                botlogger.info(f"Successfully reloaded `cogs.{extension}`.")
    except Exception as e:
        await ctx.send(f"Error reloading extension `cogs.{extension}`. Check terminal for details.")
        botlogger.error(f"Error occurred while reloading extension: {e}")

bot.run(token)