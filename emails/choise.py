import discord
from emails.normal import SendNormal
from emails.spoofed import send_email_spoofed
import sqlite3

class choiseView(discord.ui.View):
    def __init__(self, owner_id, html_content, sender_email, subject, product_name, image_url, product_link=None):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.html_content = html_content
        self.sender_email = sender_email
        self.subject = subject
        self.product_name = product_name
        self.image_url = image_url
        self.product_link = product_link

        # Extract the receipt type from the sender_email
        # For example, if sender_email is "Apple <noreply@apple.com>", then receipt_type is "apple"
        if "<" in sender_email:
            self.receipt_type = sender_email.split("<")[0].strip().lower()
        else:
            self.receipt_type = "unknown"

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Spoofed Email", style=discord.ButtonStyle.danger)
    async def spoofed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Spoofed email button callback"""
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return

        from emails.spoofed import SpoofedEmailModal
        modal = SpoofedEmailModal(self.receipt_type, self.sender_email, self.subject, self.product_name, self.image_url)
        modal.html_content = self.html_content  # Pass HTML content directly
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Normal Email", style=discord.ButtonStyle.success)
    async def normal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Normal email button callback"""
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("You are not authorized to use this button.", ephemeral=True)
            return

        from emails.normal import EmailModal
        modal = EmailModal(self.receipt_type, self.sender_email, self.subject, self.product_name, self.image_url)
        modal.html_content = self.html_content  # Pass HTML content directly
        await interaction.response.send_modal(modal)