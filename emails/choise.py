
import discord
from emails.normal import SendNormal
from emails.spoofed import send_email_spoofed
import sqlite3

class choiseView(discord.ui.View):
    def __init__(self, owner_id, receipt_html, sender_email, subject, item_desc, image_url, link):
        super().__init__()
        self.owner_id = owner_id
        self.receipt_html = receipt_html
        self.sender_email = sender_email
        self.item_desc = item_desc
        self.subject = subject
        self.image_url = image_url
        self.link = link

    @discord.ui.button(label="Spoofed Email", style=discord.ButtonStyle.blurple, custom_id="spoofed")
    async def spoofed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Get user email from database
            try:
                from utils.db_utils import get_user_details
                user_details = get_user_details(self.owner_id)

                if user_details and len(user_details) >= 6:  # Ensure we have at least 6 elements including email
                    user_email = user_details[5]  # Email is the 6th element (index 5)
                else:
                    # Fallback to old method if needed
                    conn = sqlite3.connect('data.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(self.owner_id),))
                    result = cursor.fetchone()
                    conn.close()

                    if result:
                        user_email = result[0]
                    else:
                        user_email = None
            except Exception as e:
                print(f"Error getting user details: {str(e)}")

                # Fallback method
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(self.owner_id),))
                result = cursor.fetchone()
                conn.close()

                if result:
                    user_email = result[0]
                else:
                    user_email = None

            if user_email:
                # Send spoofed email
                await send_email_spoofed(user_email, self.receipt_html, self.sender_email, self.subject, self.link)

                # Update original message with success embed
                embed = discord.Embed(
                    title="Email Sent", 
                    description=f"{interaction.user.mention}, kindly check your Inbox/Spam folder\n-# » {self.item_desc}", 
                    color=0x2ecc71
                )
                if self.image_url:
                    embed.set_thumbnail(url=self.image_url)
                
                await interaction.edit_original_response(embed=embed, view=None)
                
                # Send additional plain text warning message for spoofed emails (ephemeral)
                warning_message = "Important: **Spoofed emails often go to spam folders**. Please check your Spam/Junk folder. If you still don't see the email, please try the **Normal Email** option instead.\n\nSome email providers (like Gmail, Outlook, Yahoo) have very strict spam filters that might block spoofed emails completely."
                await interaction.followup.send(warning_message, ephemeral=True)
            else:
                await interaction.followup.send(embed=discord.Embed(title="Error", description="No email found for your account. Please set up your email.", color=0xe74c3c), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(title="Error", description=f"An error occurred: {str(e)}", color=0xe74c3c), ephemeral=True)

    @discord.ui.button(label="Normal Email", style=discord.ButtonStyle.secondary, custom_id="normal")
    async def normal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            # Get user email from database
            try:
                from utils.db_utils import get_user_details
                user_details = get_user_details(self.owner_id)

                if user_details and len(user_details) >= 6:  # Ensure we have at least 6 elements including email
                    user_email = user_details[5]  # Email is the 6th element (index 5)
                else:
                    # Fallback to old method if needed
                    conn = sqlite3.connect('data.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(self.owner_id),))
                    result = cursor.fetchone()
                    conn.close()

                    if result:
                        user_email = result[0]
                    else:
                        user_email = None
            except Exception as e:
                print(f"Error getting user details: {str(e)}")

                # Fallback method
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(self.owner_id),))
                result = cursor.fetchone()
                conn.close()

                if result:
                    user_email = result[0]
                else:
                    user_email = None

            if user_email:
                # Send normal email
                await SendNormal.send_email(user_email, self.receipt_html, self.sender_email, self.subject)

                # Update original message with success embed
                embed = discord.Embed(
                    title="Email Sent", 
                    description=f"{interaction.user.mention}, kindly check your Inbox/Spam folder\n-# » {self.item_desc}", 
                    color=0x2ecc71
                )
                if self.image_url:
                    embed.set_thumbnail(url=self.image_url)
                
                await interaction.edit_original_response(embed=embed, view=None)
            else:
                await interaction.followup.send(embed=discord.Embed(title="Error", description="No email found for your account. Please set up your email.", color=0xe74c3c), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(title="Error", description=f"An error occurred: {str(e)}", color=0xe74c3c), ephemeral=True)
