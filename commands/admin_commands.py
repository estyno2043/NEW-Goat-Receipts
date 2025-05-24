import discord
from discord import app_commands
from discord.ext import commands
import json
import sqlite3
from datetime import datetime
import logging

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="edit", description="Admin panel to edit user subscription and details")
    async def edit(self, interaction: discord.Interaction, user: discord.Member):
        # Check if the command invoker is the bot owner
        with open("config.json", "r") as f:
            config = json.load(f)
            owner_id = int(config.get("owner_id", 1339295766828552365))

        if interaction.user.id != owner_id:
            embed = discord.Embed(
                title="Access Denied",
                description="Only the bot owner can use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Create the admin panel view
        view = AdminPanelView(interaction.user.id, user, self.bot)

        # Send response with panel
        embed = discord.Embed(
            title=f"Admin Panel | User Connected: {user.display_name}",
            description="Select an option below to use the Panel",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class UserInfoModal(discord.ui.Modal, title="User Information"):
    def __init__(self, user, bot):
        super().__init__()
        self.user = user
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        # Get user subscription info
        try:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            # Get license info
            cursor.execute("SELECT key, expiry FROM licenses WHERE owner_id = ?", (str(self.user.id),))
            license_data = cursor.fetchone()

            # Get guild subscription info
            cursor.execute('''
            SELECT subscription_type, expiry_date, is_active, bot_token 
            FROM guild_subscriptions 
            WHERE user_id = ?
            ''', (str(self.user.id),))

            guild_data = cursor.fetchone()

            # Get guilds configured by this user
            configured_guilds = []
            if guild_data:
                cursor.execute('''
                SELECT guild_id, generator_channel_id, setup_date 
                FROM guild_configs 
                WHERE owner_id = ?
                ''', (str(self.user.id),))

                guild_configs = cursor.fetchall()

                for guild_id, channel_id, setup_date in guild_configs:
                    guild_name = "Unknown Guild"
                    try:
                        # Try to get guild info from bot's cache
                        guild = self.bot.get_guild(int(guild_id))
                        if guild:
                            guild_name = guild.name
                    except:
                        pass

                    configured_guilds.append({
                        "id": guild_id,
                        "name": guild_name,
                        "channel_id": channel_id,
                        "setup_date": setup_date
                    })

            conn.close()

            # Create embed with user info
            embed = discord.Embed(
                title=f"User Information: {self.user.name}",
                description=f"ID: {self.user.id}",
                color=discord.Color.blue()
            )

            # Add license info
            if license_data:
                key, expiry = license_data
                embed.add_field(name="License Key", value=key, inline=False)
                embed.add_field(name="Expiry Date", value=expiry, inline=False)

                # Check if key is lifetime
                if key and key.startswith("LifetimeKey"):
                    embed.add_field(name="License Type", value="Lifetime", inline=False)
                else:
                    embed.add_field(name="License Type", value="Regular", inline=False)
            else:
                embed.add_field(name="License", value="No license found", inline=False)

            # Add guild subscription info
            if guild_data:
                subscription_type, expiry_date, is_active, bot_token = guild_data

                status = "Active" if is_active else "Inactive"
                has_token = "Yes" if bot_token else "No"

                embed.add_field(name="Guild Subscription", value=f"Type: {subscription_type}\nExpiry: {expiry_date}\nStatus: {status}\nBot Registered: {has_token}", inline=False)

                # Add configured guilds
                if configured_guilds:
                    guilds_text = ""
                    for idx, guild in enumerate(configured_guilds, 1):
                        guilds_text += f"{idx}. {guild['name']} (ID: {guild['id']})\n"
                        guilds_text += f"   Channel: <#{guild['channel_id']}>\n"
                        guilds_text += f"   Setup: {guild['setup_date']}\n\n"

                    embed.add_field(name="Configured Servers", value=guilds_text if len(guilds_text) <= 1024 else f"{len(configured_guilds)} servers configured", inline=False)
            else:
                embed.add_field(name="Guild Subscription", value="No guild subscription found", inline=False)

            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logging.error(f"Error retrieving user info: {e}")
            await interaction.response.send_message(f"Error retrieving user information: {str(e)}", ephemeral=True)

class AdminPanelView(discord.ui.View):
    def __init__(self, admin_id, target_user, bot):
        super().__init__(timeout=300)
        self.admin_id = admin_id
        self.user = target_user
        self.bot = bot

    @discord.ui.button(label="Information", style=discord.ButtonStyle.primary)
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not your admin panel.", ephemeral=True)
            return

        # Open the user info modal
        modal = UserInfoModal(self.user, self.bot)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Edit License", style=discord.ButtonStyle.secondary)
    async def edit_license_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not your admin panel.", ephemeral=True)
            return

        await interaction.response.send_message("License editing feature will be implemented soon.", ephemeral=True)

    @discord.ui.button(label="Reset", style=discord.ButtonStyle.danger)
    async def reset_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.admin_id:
            await interaction.response.send_message("This is not your admin panel.", ephemeral=True)
            return

        await interaction.response.send_message("Reset feature will be implemented soon.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))