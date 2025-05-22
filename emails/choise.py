
import discord
from discord.ui import View, Button
import asyncio
from emails.normal import send_email_normal
from emails.spoofed import send_email_spoofed

class choiseView(discord.ui.View):
    def __init__(self, owner_id, html_content, sender_email, subject, product_name, image_url, link):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.html_content = html_content
        self.sender_email = sender_email
        self.subject = subject
        self.product_name = product_name
        self.image_url = image_url
        self.link = link

    @discord.ui.button(label="Spoofed Email", style=discord.ButtonStyle.danger, custom_id="spoofed_email")
    async def spoofed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return
            
        await interaction.response.edit_message(embed=discord.Embed(title="Sending Email...", description="The email is being sent through spoofed domain. Please wait...", color=0x1e1f22), view=None)
        
        try:
            import sqlite3
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM licenses WHERE owner_id = ?", (str(self.owner_id),))
            user_email = cursor.fetchone()
            conn.close()
            
            if user_email:
                recipient_email = user_email[0]
                result = await send_email_spoofed(recipient_email, self.html_content, self.sender_email, self.subject, self.link)
                
                if result == "Email sent successfully":
                    embed = discord.Embed(title="Email Sent", description=f"Receipt has been sent to **{recipient_email}**\n\nCheck your spam folder if you don't see it in your inbox.", color=0x2ecc71)
                    embed.add_field(name="Product", value=self.product_name)
                    
                    if self.image_url and self.image_url.startswith(("http://", "https://")):
                        embed.set_thumbnail(url=self.image_url)
                    
                    await interaction.edit_original_response(embed=embed, view=None)
                else:
                    await interaction.edit_original_response(embed=discord.Embed(title="Error", description=f"Failed to send email: {result}", color=0xe74c3c), view=None)
            else:
                await interaction.edit_original_response(embed=discord.Embed(title="Error", description="No email found for your account. Please set up your email.", color=0xe74c3c), view=None)
        except Exception as e:
            await interaction.edit_original_response(embed=discord.Embed(title="Error", description=f"An error occurred: {str(e)}", color=0xe74c3c), view=None)

    @discord.ui.button(label="Normal Email", style=discord.ButtonStyle.danger, custom_id="normal_email")
    async def normal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return
        
        await interaction.response.edit_message(embed=discord.Embed(title="Sending Email...", description="The email is being sent through normal domain. Please wait...", color=0x1e1f22), view=None)
        
        try:
            import sqlite3
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM licenses WHERE owner_id = ?", (str(self.owner_id),))
            user_email = cursor.fetchone()
            conn.close()
            
            if user_email:
                recipient_email = user_email[0]
                result = await send_email_normal(recipient_email, self.html_content, self.sender_email, self.subject)
                
                if result == "Email sent successfully":
                    embed = discord.Embed(title="Email Sent", description=f"Receipt has been sent to **{recipient_email}**\n\nCheck your spam folder if you don't see it in your inbox.", color=0x2ecc71)
                    embed.add_field(name="Product", value=self.product_name)
                    
                    if self.image_url and self.image_url.startswith(("http://", "https://")):
                        embed.set_thumbnail(url=self.image_url)
                    
                    await interaction.edit_original_response(embed=embed, view=None)
                else:
                    await interaction.edit_original_response(embed=discord.Embed(title="Error", description=f"Failed to send email: {result}", color=0xe74c3c), view=None)
            else:
                await interaction.edit_original_response(embed=discord.Embed(title="Error", description="No email found for your account. Please set up your email.", color=0xe74c3c), view=None)
        except Exception as e:
            await interaction.edit_original_response(embed=discord.Embed(title="Error", description=f"An error occurred: {str(e)}", color=0xe74c3c), view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return
            
        await interaction.response.edit_message(embed=discord.Embed(title="Cancelled", description="Email sending cancelled", color=0xe74c3c), view=None)
