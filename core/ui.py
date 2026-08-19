import discord
from core import db, statcalc


CLASS_OPTIONS = [
    "Knight",
    "Assassin",
    "Mage",
    "Necromancer",
    "Bard",
]

async def build_profile_embed(bot, user, player, created_at):
    profile_embed = discord.Embed(
        title=f"{user.name} - {player['class'] if player['class'] else 'NPC'}",
        color=discord.Color.blue(),
        timestamp=created_at,
    )

    profile_embed.set_thumbnail(url=user.avatar.url)
    profile_embed.set_author(name="Profile/Main", icon_url=bot.user.avatar.url)

    profile_embed.add_field(
        name="CHAR",
        value=f"""
        **Level**: {player['level']}
        **XP**: {player['xp']}
        """,
        inline=False,
    )
    profile_embed.add_field(
        name="STAT",
        value=f"""
        **STR**: {player['strength']} (+{await statcalc.strength(user):.1f})
        **DEX**: {player['dexterity']} (+{await statcalc.dexterity(user):.1f})
        **INT**: {player['intelligence']} (+{await statcalc.intelligence(user):.1f})
        """,
        inline=False,
    )
    profile_embed.add_field(
        name="GOLD",
        value=f"""
        **Gold**: {player['gold']}G
        **Crystal**: {player['crystal']}C
        """,
        inline=False,
    )

    return profile_embed

async def build_combat_embed(bot, user, player, created_at):
    combat_embed = discord.Embed(
        title=f"{user.name} - {player['class'] if player['class'] else 'NPC'}",
        color=discord.Color.red(),
        timestamp=created_at,
    )

    combat_embed.set_thumbnail(url=user.avatar.url)
    combat_embed.set_author(name="Profile/Combat", icon_url=bot.user.avatar.url)

    combat_embed.add_field(
        name="ACTV",
        value=f"""
        **HP**: {player['health']:.1f}/{await statcalc.maxhp(user):.1f}
        **DEF**: {await statcalc.defense(user):.1f}
        **MANA**: {player['mana']:.1f}/{await statcalc.maxmana(user):.1f}
        **STAM**: {player['stamina']:.1f}
        """,
        inline=False,
    )
    combat_embed.add_field(
        name="PASV",
        value=f"""
        **CRIT**: {await statcalc.crit_chance(user) * 100:.2f}%
        **CDMG**: {await statcalc.crit_damage(user) * 100:.2f}%
        **EVA**: {await statcalc.evasion(user) * 100:.2f}%
        **ACC**: {await statcalc.accuracy(user) * 100:.2f}%
        **PEN**: {await statcalc.penetration(user) * 100:.2f}%
        """,
        inline=False,
    )

    return combat_embed


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
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if hasattr(self, "message") and self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Main", style=discord.ButtonStyle.primary)
    async def main_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player, db_error = await db.fetch_player(self.user)
        if db_error or not player:
            await interaction.response.send_message("Something went wrong.", ephemeral=True)
            return

        self.player = player
        embed = await build_profile_embed(self.bot, self.user, self.player, discord.utils.utcnow())

        self.main_button.disabled = True
        self.combat_button.disabled = False

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Combat", style=discord.ButtonStyle.primary)
    async def combat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        player, db_error = await db.fetch_player(self.user)
        if db_error or not player:
            await interaction.response.send_message("Something went wrong.", ephemeral=True)
            return

        self.player = player
        embed = await build_combat_embed(self.bot, self.user, self.player, discord.utils.utcnow())

        self.main_button.disabled = False
        self.combat_button.disabled = True

        await interaction.response.edit_message(embed=embed, view=self)


class ClassChoiceSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=class_name, value=class_name) for class_name in CLASS_OPTIONS]
        super().__init__(placeholder="Choose class", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_class = self.values[0]
        dberror = await db.set_class(interaction.user, selected_class)

        if dberror:
            self.view.error = True
            await interaction.response.send_message("Something went wrong.", ephemeral=True)

            self.view.stop()
            return
        
        # TODO: improve ui, change into embed with icons
        await interaction.response.send_message(f"Welcome, **{interaction.user.name}**! You are playing as a **{selected_class}**.", ephemeral=False)
        self.view.stop()


class ClassChoiceView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=180)
        self.user = user
        self.error = False
        self.add_item(ClassChoiceSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if hasattr(self, "message") and self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass
