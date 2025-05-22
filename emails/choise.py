import asyncio
import os
import re
import smtplib
import discord
import json
from discord import ui
from datetime import datetime, timedelta
from emails.normal import SendNormal
from emails.spoofed import SendSpoofed
import sqlite3
import requests

# Function to get database connection
def get_db_connection():
    conn = sqlite3.connect('data.db')
    return conn

# Initialize table if needed
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS licenses (
        owner_id TEXT PRIMARY KEY,
        email TEXT,
        address TEXT
    )
''')
conn.commit()
conn.close()


class choiseView(discord.ui.View):
    def __init__(self, owner_id, html_content, sender_email, subject, product_name, image_url, url):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.html_content = html_content
        self.sender_email = sender_email
        self.subject = subject
        self.product_name = product_name
        self.image_url = image_url
        self.url = url
        self.branding = product_name  # Add branding attribute using product_name


    @discord.ui.button(label="Spoofed Email", style=discord.ButtonStyle.danger)
    async def handle_spoofed(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            # Get user email from database. If not found, prompt the user to enter it.
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM licenses WHERE owner_id = ?", (str(interaction.user.id),))
            result = cursor.fetchone()
            conn.close()
            if result:
                receiver_email = result[0]
            else:
                await interaction.response.send_message(content="Your email is not set. Please use the `/setemail` command.", ephemeral=True)
                return

            if receiver_email: 
                from utils.rate_limiter import ReceiptRateLimiter
                rate_limiter = ReceiptRateLimiter()
                allowed, count, reset_time, remaining_time = rate_limiter.add_receipt(str(interaction.user.id))

                if not allowed:
                    time_str = rate_limiter.format_time_remaining(remaining_time)
                    rate_limit_msg = (
                        "🧾 **Whoa there, Receipt Champ!** 🏆\n\n"
                        "You've already whipped up 5 receipts in the last 3 hours.\n"
                        f"Let the printer cool down before you cook up more. 🖨️🔥\n\n"
                        f"> You can generate your next receipt in {time_str}."
                    )
                    embed = discord.Embed(title="Rate Limited", description=rate_limit_msg, color=0xf04747)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                embed = discord.Embed(title="Sending...", description="")
                await interaction.response.edit_message(embed=embed, view=None)

                try:
                    # Create a context object to pass to the email sender
                    class Context:
                        pass

                    context = Context()
                    context.user_id = interaction.user.id
                    context.guild_id = interaction.guild.id if interaction.guild else None
                    context.bot = interaction.client

                    email_sender = SendSpoofed(self.sender_email, receiver_email, self.subject, self.html_content)
                    email_sender.context = context
                    #Added this line assuming branding is available.  Adjust as needed.
                    email_sender.sender_name = self.branding
                    email_sender.image_url = self.image_url if hasattr(self, 'image_url') else None
                    
                    # Create a form_data dictionary with necessary info
                    form_data = {
                        'brandname': self.branding,
                        'imageurl': self.image_url if hasattr(self, 'image_url') else None
                    }
                    success = email_sender.send_email(interaction.client, interaction.user.id, form_data, interaction)

                    if success:
                        embed = discord.Embed(title=f"Confirmation", description=f"{interaction.user.mention} Spoofed email sent successfully!", url=self.url)
                        embed.add_field(name="", value=f"» Product: **{self.product_name}**\n")
                        # Always set the Vinted image for Vinted receipts
                        if "vinted" in self.sender_email.lower():
                            embed.set_thumbnail(url="attachment://vinted image.png")
                            
                        # Send receipt log manually to ensure it's sent
                        try:
                            from utils.utils import Utils
                            asyncio.create_task(Utils.log_receipt_generation(
                                interaction.client, 
                                interaction.user.id, 
                                self.branding or self.product_name, 
                                self.image_url if hasattr(self, 'image_url') else None,
                                interaction.guild.id if interaction.guild else None
                            ))
                        except Exception as log_error:
                            print(f"Error logging receipt from choice view: {log_error}")
                    else:
                        embed = discord.Embed(title="Error", description=f"Failed to send spoofed email. Please try again or use the normal email option.", color=0xf04747)
                        await interaction.edit_original_response(embed=embed, view=None)
                        return

                    if self.image_url and self.image_url != "None" and "vinted" not in self.sender_email.lower():
                        try:
                            # Remove triple backticks if present
                            clean_image_url = self.image_url
                            if "```" in clean_image_url:
                                clean_image_url = clean_image_url.replace("```", "")

                            # Verify URL format
                            if clean_image_url.startswith(('http://', 'https://')):
                                embed.set_thumbnail(url=clean_image_url)
                        except Exception as e:
                            print(f"Error setting thumbnail: {e}")
                            # Continue without setting a thumbnail

                    # Remove user from active_menus in GenerateCog
                    from commands.generate import GenerateCog
                    for cog in interaction.client.cogs.values():
                        if isinstance(cog, GenerateCog):
                            cog.active_menus.pop(self.owner_id, None)

                            # Try to find and edit the original menu message
                            try:
                                # Get the timestamp in readable format
                                now = datetime.now()
                                date_str = now.strftime("%d/%m/%Y %H:%M")

                                # Create a formal message for the closed panel
                                panel_closed_embed = discord.Embed(
                                    title="Receipt Generation Complete",
                                    description="Your receipt has been successfully generated and sent to your email address.",
                                    color=0x4CAF50
                                )
                                panel_closed_embed.add_field(
                                    name="Email Status", 
                                    value="Your email has been dispatched. Please allow a few moments for delivery.",
                                    inline=False
                                )
                                panel_closed_embed.add_field(
                                    name="Product Details", 
                                    value=f"» Product: **{self.product_name}**",
                                    inline=False
                                )
                                panel_closed_embed.set_footer(
                                    text=f"GOAT Receipts • {date_str}", 
                                    icon_url=interaction.guild.me.avatar.url if interaction.guild and interaction.guild.me.avatar else None
                                )

                                # Find and edit the original menu message
                                if self.owner_id in cog.active_menus:
                                    menu_data = cog.active_menus[self.owner_id]
                                    channel = interaction.client.get_channel(menu_data["channel_id"])
                                    if channel:
                                        try:
                                            original_message = await channel.fetch_message(menu_data["message_id"])
                                            await original_message.edit(embed=panel_closed_embed, view=None)
                                        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                                            print(f"Could not edit original menu: {e}")
                            except Exception as e:
                                print(f"Error updating original menu: {e}")
                            break

                    await interaction.edit_original_response(embed=embed, view=None)
                    await interaction.followup.send(content="Important: **Spoofed emails often go to spam folders**. Please check your Spam/Junk folder. If you still don't see the email, please try the **Normal Email** option instead.\n\nSome email providers (like Gmail, Outlook, Yahoo) have very strict spam filters that might block spoofed emails completely.", ephemeral=True)

                except smtplib.SMTPRecipientsRefused as e:
                    print(f"Failed to send email: {e}")
                    embed = discord.Embed(title="Error", description=f"Failed to send email. Your email provider ({receiver_email.split('@')[1]}) might be blocking our messages. Try using a different email address.")
                    await interaction.edit_original_response(embed=embed, view=None)

                except Exception as e:
                    print(f"Failed to send email: {e}")
                    embed = discord.Embed(title="Error", description=f"Failed to send email: {str(e)}\nPlease try the Normal Email option instead.")
                    await interaction.edit_original_response(embed=embed, view=None)

        else:
            await interaction.response.send_message(content="This is not your Panel", ephemeral=True)



    @discord.ui.button(label="Normal Email", style=discord.ButtonStyle.danger)
    async def handle_normal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM licenses WHERE owner_id = ?", (str(interaction.user.id),))
            result = cursor.fetchone()
            conn.close()
            if result:
                receiver_email = result[0]
            else:
                await interaction.response.send_message(content="Your email is not set. Please use the `/setemail` command.", ephemeral=True)
                return

            if receiver_email:
                from utils.rate_limiter import ReceiptRateLimiter
                rate_limiter = ReceiptRateLimiter()
                allowed, count, reset_time, remaining_time = rate_limiter.add_receipt(str(interaction.user.id))

                if not allowed:
                    time_str = rate_limiter.format_time_remaining(remaining_time)
                    rate_limit_msg = (
                        "🧾 **Whoa there, Receipt Champ!** 🏆\n\n"
                        "You've already whipped up 5 receipts in the last 3 hours.\n"
                        f"Let the printer cool down before you cook up more. 🖨️🔥\n\n"
                        f"> You can generate your next receipt in {time_str}."
                    )
                    embed = discord.Embed(title="Rate Limited", description=rate_limit_msg, color=0xf04747)
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                embed = discord.Embed(title="Sending...", description="")
                await interaction.response.edit_message(embed=embed, view=None)

                # Use dedicated vinted email if this is a Vinted receipt
                if "vinted" in self.sender_email.lower():
                    new_email = "teamvinteed@gmail.com"
                else:
                    new_email = "noreply@maisonreceipts.cc"
                formatted_sender_email = re.sub(r"<[^>]+>", f"<{new_email}>", self.sender_email)

                try:
                    email_sender = SendNormal(formatted_sender_email, receiver_email, self.subject, self.html_content)
                    success, message = email_sender.send_email()

                    if success:
                        embed = discord.Embed(title=f"Confirmation", description=f"{interaction.user.mention} Normal email sent successfully!", url=self.url)
                        embed.add_field(name="", value=f"» Product: **{self.product_name}**\n")
                        # Always set the Vinted image for Vinted receipts
                        if "vinted" in self.sender_email.lower():
                            embed.set_thumbnail(url="attachment://vinted image.png")
                            
                        # Send receipt log manually to ensure it's sent
                        try:
                            from utils.utils import Utils
                            asyncio.create_task(Utils.log_receipt_generation(
                                interaction.client, 
                                interaction.user.id, 
                                self.branding or self.product_name, 
                                self.image_url if hasattr(self, 'image_url') else None,
                                interaction.guild.id if interaction.guild else None
                            ))
                        except Exception as log_error:
                            print(f"Error logging receipt from choice view: {log_error}")
                        
                        # Set thumbnail if image URL is available (fixed syntax error)
                        if self.image_url and self.image_url != "None":
                            try:
                                # Remove triple backticks if present
                                clean_image_url = self.image_url
                                if "```" in clean_image_url:
                                    clean_image_url = clean_image_url.replace("```", "")

                                # First verify if the URL is valid before attempting to use it
                                if clean_image_url.startswith(('http://', 'https://')):
                                    # For Discord embeds, only use the base URL without query parameters
                                    clean_url = clean_image_url.split('?')[0]
                                    # Add additional validation by checking if it's an actual image URL
                                    if any(clean_url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                                        embed.set_thumbnail(url=clean_url)
                            except Exception as e:
                                print(f"Error setting thumbnail: {e}")
                                # Continue without setting a thumbnail

                        # Remove user from active_menus in GenerateCog
                        from commands.generate import GenerateCog
                        for cog in interaction.client.cogs.values():
                            if isinstance(cog, GenerateCog):
                                cog.active_menus.pop(self.owner_id, None)

                                # Try to find and edit the original menu message
                                try:
                                    # Get the timestamp in readable format
                                    now = datetime.now()
                                    date_str = now.strftime("%d/%m/%Y %H:%M")

                                    # Create a formal message for the closed panel
                                    panel_closed_embed = discord.Embed(
                                        title="Receipt Generation Complete",
                                        description="Your receipt has been successfully generated and sent to your email address.",
                                        color=0x4CAF50
                                    )
                                    panel_closed_embed.add_field(
                                        name="Email Status", 
                                        value="Your email has been dispatched. Please allow a few moments for delivery.",
                                        inline=False
                                    )
                                    panel_closed_embed.add_field(
                                        name="Product Details", 
                                        value=f"» Product: **{self.product_name}**",
                                        inline=False
                                    )
                                    panel_closed_embed.set_footer(
                                        text=f"GOAT Receipts • {date_str}", 
                                        icon_url=interaction.guild.me.avatar.url if interaction.guild and interaction.guild.me.avatar else None
                                    )

                                    # Find and edit the original menu message
                                    if self.owner_id in cog.active_menus:
                                        menu_data = cog.active_menus[self.owner_id]
                                        channel = interaction.client.get_channel(menu_data["channel_id"])
                                        if channel:
                                            try:
                                                original_message = await channel.fetch_message(menu_data["message_id"])
                                                await original_message.edit(embed=panel_closed_embed, view=None)
                                            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                                                print(f"Could not edit original menu: {e}")
                                except Exception as e:
                                    print(f"Error updating original menu: {e}")
                                break

                        await interaction.edit_original_response(embed=embed, view=None)
                    else:
                        embed = discord.Embed(title="Error", description=f"Failed to send email: {message}", color=discord.Color.red())
                        await interaction.edit_original_response(embed=embed, view=None)

                except smtplib.SMTPRecipientsRefused as e:
                    print(f"Failed to send email: {e}")
                    embed = discord.Embed(title="Error", description="Failed to send email due to SMTP recipient refusal.", color=discord.Color.red())
                    await interaction.edit_original_response(embed=embed, view=None)

                except Exception as e:
                    print(f"Failed to send email: {e}")
                    embed = discord.Embed(title="Error", description=f"Failed to send email: {str(e)}", color=discord.Color.red())
                    await interaction.edit_original_response(embed=embed, view=None)

        else:
            await interaction.response.send_message(content="This is not your Panel", ephemeral=True)