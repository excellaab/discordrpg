import discord
from core.lib import db
from core.lib.log import dblogger


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

        if db_error:
            await interaction.response.send_message("Error starting run.", ephemeral=True)
            return

        if run is None:
            # Fallback if startrun failed (e.g. run already exists)
            run, db_error = await db.fetchrun(interaction.user)
            if db_error or run is None:
                dblogger.error(f"Unable to start run for {interaction.user.id}. run output:\n{run}")
                await interaction.response.edit_message(content="Error starting run. Do you have a character?", view=None)
                self.stop()
                return

        main_run_embed = discord.Embed(
            title="Run",
            description="[Placeholder main run embed]"
        )

        view = BasecampView(self.original_user)
        await interaction.response.edit_message(content=None, embed=main_run_embed, view=view)
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel_run(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="Run cancelled.", view=None, ephemeral=True)
        self.stop()


class BaseRoomView(discord.ui.View):
    def __init__(self, original_user):
        super().__init__(timeout=None)
        self.original_user = original_user
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.original_user:
            return False
        return True


class BasecampView(BaseRoomView):
    pass


class BattleView(BaseRoomView):
    pass


class EventView(BaseRoomView):
    pass


class FountainView(BaseRoomView):
    pass


class MarketView(BaseRoomView):
    pass


class BlacksmithView(BaseRoomView):
    pass


class CursedView(BaseRoomView):
    pass


class BossView(BaseRoomView):
    pass


class FinalbossView(BaseRoomView):
    pass
