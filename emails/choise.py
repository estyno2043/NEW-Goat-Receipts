import discord
from emails.normal import send_email
from emails.spoofed import send_email_spoofed
import sqlite3

class choiseView(discord.ui.View):
    def __init__(self, owner_id, receipt_html, spoofed, item_desc, order_id):
        super().__init__()
        self.owner_id = owner_id
        self.receipt_html = receipt_html
        self.spoofed = spoofed
        self.item_desc = item_desc
        self.order_id = order_id

    @discord.ui.button(label="Normal Email", style=discord.ButtonStyle.blurple, custom_id="normal")
    async def normal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Get user email from database
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(self.owner_id),))
            result = cursor.fetchone()
            conn.close()

            if result:
                user_email = result[0]

                # Send normal email
                send_email(user_email, self.receipt_html, self.item_desc, self.order_id)

                await interaction.edit_original_response(embed=discord.Embed(title="Success", description="Email sent successfully to your email address.", color=0x2ecc71), view=None)
            else:
                await interaction.edit_original_response(embed=discord.Embed(title="Error", description="No email found for your account. Please set up your email.", color=0xe74c3c), view=None)
        except Exception as e:
            await interaction.edit_original_response(embed=discord.Embed(title="Error", description=f"An error occurred: {str(e)}", color=0xe74c3c), view=None)

    @discord.ui.button(label="Spoofed Email", style=discord.ButtonStyle.green, custom_id="spoofed")
    async def spoofed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Get user email from database
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(self.owner_id),))
            result = cursor.fetchone()
            conn.close()

            if result:
                user_email = result[0]

                # Send spoofed email
                send_email_spoofed(user_email, self.receipt_html, self.spoofed, self.item_desc, self.order_id)

                await interaction.edit_original_response(embed=discord.Embed(title="Success", description="Spoofed email sent successfully to your email address.", color=0x2ecc71), view=None)
            else:
                await interaction.edit_original_response(embed=discord.Embed(title="Error", description="No email found for your account. Please set up your email.", color=0xe74c3c), view=None)
        except Exception as e:
            await interaction.edit_original_response(embed=discord.Embed(title="Error", description=f"An error occurred: {str(e)}", color=0xe74c3c), view=None)