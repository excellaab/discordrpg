import discord
from core.lib import db

class RunConfirmationView(discord.ui.View):
    def __init__(self, original_user):
        super().__init__(timeout=60)
        self.original_user = original_user
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.original_user:
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await self.message.edit(view=self)

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm_run(self, interaction: discord.Interaction, button: discord.ui.Button):
        run, db_error = await db.startrun(interaction.user, 0)
        started_new_run = run is not None

        if run is None and not db_error:
            run, db_error = await db.fetchrun(interaction.user)

        if db_error:
            await interaction.response.send_message("Error fetching run.", ephemeral=True)
            return

        if run is None:
            await interaction.response.edit_message(
                content="You don't have a character yet. Use `!start` first.",
                view=None,
            )
            self.stop()
            return

        if started_new_run:
            await interaction.response.edit_message(content="Run started!", view=None)
        else:
            await interaction.response.edit_message(content="You already have an active run.", view=None, ephemeral=True)
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel_run(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Run cancelled.", view=None, ephemeral=True)
        self.stop()
