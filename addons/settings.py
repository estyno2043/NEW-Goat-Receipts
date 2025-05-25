class SettingsView(discord.ui.View):
    def __init__(self, owner_id, user_roles):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.user_roles = user_roles

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return False
        return True