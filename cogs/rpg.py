import logging
import discord
from discord.ui import View, Button
from discord.ext import commands
from core import db, statcalc

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

async def _build_profile_embed(bot, user, player, created_at):
    profilembed = discord.Embed(
        title = f"{user.name} - {player['class'] if player['class'] else 'NPC'}",
        color = discord.Color.blue(),
        timestamp = created_at
    )

    profilembed.set_thumbnail(url = user.avatar.url)
    profilembed.set_author(name = "Profile/Main", icon_url = bot.user.avatar.url)

    profilembed.add_field(name = "CHAR", value = f"""
        **Level**: {player['level']}
        **XP**: {player['xp']}
    """, inline = False)
    profilembed.add_field(name = "STAT", value = f"""
        **STR**: {player['strength']}
        **DEX**: {player['dexterity']}
        **INT**: {player['intelligence']}
    """, inline = False)
    profilembed.add_field(name = "GOLD", value = f"""
        **Gold**: {player['gold']}G
        **Crystal**: {player['crystal']}C
    """, inline = False)

    return profilembed

async def _build_combat_embed(bot, user, player, created_at):
    combatembed = discord.Embed(
        title = f"{user.name} - {player['class'] if player['class'] else 'NPC'}",
        color = discord.Color.red(),
        timestamp = created_at
    )

    combatembed.set_thumbnail(url = user.avatar.url)
    combatembed.set_author(name = "Profile/Combat", icon_url = bot.user.avatar.url)

    combatembed.add_field(name = "ACTV", value = f"""
        **HP**: {player['health']}/{await statcalc.maxhp(user)}
        **DEF**: {await statcalc.defense(user)}
        **MANA**: {player['mana']}/{await statcalc.maxmana(user)}
        **STAM**: {player['stamina']}
    """, inline = False)
    combatembed.add_field(name = "PASV", value = f"""
        **CRIT**: {await statcalc.crit_chance(user) * 100:.2f}%
        **CDMG**: {await statcalc.crit_damage(user) * 100:.2f}%
        **EVA**: {await statcalc.evasion(user) * 100:.2f}%
        **ACC**: {await statcalc.accuracy(user) * 100:.2f}%
        **PEN**: {await statcalc.penetration(user) * 100:.2f}%
    """, inline = False)

    return combatembed

class ProfileView(discord.ui.View):
    def __init__(self, bot, user, player, active_page="main"):
        super().__init__(timeout=180)
        self.bot = bot
        self.user = user
        self.player = player
        
        if active_page == "main":
            self.main_button.disabled = True
            self.combat_button.disabled = False
        else:
            self.main_button.disabled = False
            self.combat_button.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("You cannot interact with someone else's profile!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if hasattr(self, 'message') and self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Main", style=discord.ButtonStyle.primary)
    async def main_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player, db_error = await db._fetch_player(self.user)
        if db_error or not player:
            await interaction.response.send_message("Something went wrong.", ephemeral=True)
            return
            
        self.player = player
        embed = await _build_profile_embed(self.bot, self.user, self.player, discord.utils.utcnow())
        
        self.main_button.disabled = True
        self.combat_button.disabled = False
        
        await interaction.response.edit_message(embed=embed, view=self)
        
    @discord.ui.button(label="Combat", style=discord.ButtonStyle.primary)
    async def combat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player, db_error = await db._fetch_player(self.user)
        if db_error or not player:
            await interaction.response.send_message("Something went wrong.", ephemeral=True)
            return
            
        self.player = player
        embed = await _build_combat_embed(self.bot, self.user, self.player, discord.utils.utcnow())
        
        self.main_button.disabled = False
        self.combat_button.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

class RPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # start
    @commands.command()
    async def start(self, ctx):
        user = ctx.author

        response, db_error = await db._new_player(user)

        if db_error:
            await ctx.send("Something went wrong. Please try again later.")
            dblogger.exception(f"Error fetching player for user {user.id} during stat calculation.")
            return

        if response:
            await ctx.send(f"Welcome, {ctx.author.mention}! Your adventure begins now.")
        else:
            await ctx.send(f"{ctx.author.mention}, you have already started your adventure!")

    # profile: main
    @commands.command(aliases=['p'])
    async def profile(self, ctx, query: fetchUser | None = None):
        user = query if query else ctx.author
        player, db_error = await db._fetch_player(user)

        if db_error:
            await ctx.send("Something went wrong. Please try again later.")
            return

        if player:
            embed = await _build_profile_embed(self.bot, user, player, ctx.message.created_at)
            view = ProfileView(self.bot, user, player, active_page="main")
            view.message = await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(f"{user.mention}, hasn't started an adventure yet! Use `!start` to begin.")

    # profile: combat
    # NOTE: not working yet, resolved later; do NOT start the bot
    @commands.command(aliases=['pc'])
    async def pcombat(self, ctx, query: fetchUser | None = None):
        user = query if query else ctx.author
        player, db_error = await db._fetch_player(user)

        if db_error:
            await ctx.send("Something went wrong. Please try again later.")
            return

        if player:
            embed = await _build_combat_embed(self.bot, user, player, ctx.message.created_at)
            view = ProfileView(self.bot, user, player, active_page="combat")
            view.message = await ctx.send(embed=embed, view=view)
        else:
            await ctx.send(f"{user.mention}, hasn't started an adventure yet! Use `!start` to begin.")

async def setup(bot):
    await bot.add_cog(RPG(bot))