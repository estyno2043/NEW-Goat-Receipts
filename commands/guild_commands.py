import discord
from discord import app_commands
from discord.ext import commands
from discord import ui
import sqlite3
import json
import logging
from datetime import datetime, timedelta
import asyncio

# Setup database for guild configuration
def setup_guild_database():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Table for guild configurations
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS guild_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT UNIQUE,
        owner_id TEXT,
        generate_channel_id TEXT,
        admin_role_id TEXT,
        client_role_id TEXT,
        image_channel_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Table for guild subscriptions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS guild_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        subscription_type TEXT,
        start_date TEXT,
        end_date TEXT,
        is_active INTEGER DEFAULT 1
    )
    ''')

    # Table for guild user access
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS server_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT,
        user_id TEXT,
        added_by TEXT,
        access_type TEXT,
        expiry TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(guild_id, user_id)
    )
    ''')

    conn.commit()
    conn.close()

# Guild configuration modal
class GuildConfigModal(ui.Modal, title="Guild Configuration"):
    generate_channel = ui.TextInput(
        label="Generate Channel ID",
        placeholder="Enter the channel ID for /generate command",
        required=True
    )

    admin_role = ui.TextInput(
        label="Admin Role ID",
        placeholder="Enter the admin role ID",
        required=True
    )

    client_role = ui.TextInput(
        label="Client Role ID",
        placeholder="Enter the client role ID",
        required=True
    )

    image_channel = ui.TextInput(
        label="Image Link Channel ID",
        placeholder="Enter the channel ID for image links",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Validate IDs
        try:
            generate_channel_id = int(self.generate_channel.value.strip())
            admin_role_id = int(self.admin_role.value.strip())
            client_role_id = int(self.client_role.value.strip())
            image_channel_id = int(self.image_channel.value.strip())

            # Save to database
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            # Check if already configured
            cursor.execute("SELECT * FROM guild_configs WHERE guild_id = ?", (str(interaction.guild.id),))
            existing_config = cursor.fetchone()

            if existing_config:
                # Update existing configuration
                cursor.execute('''
                UPDATE guild_configs 
                SET generate_channel_id = ?, admin_role_id = ?, client_role_id = ?, image_channel_id = ?
                WHERE guild_id = ?
                ''', (str(generate_channel_id), str(admin_role_id), str(client_role_id), 
                      str(image_channel_id), str(interaction.guild.id)))
            else:
                # Create new configuration
                cursor.execute('''
                INSERT INTO guild_configs 
                (guild_id, owner_id, generate_channel_id, admin_role_id, client_role_id, image_channel_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (str(interaction.guild.id), str(interaction.user.id), str(generate_channel_id),
                     str(admin_role_id), str(client_role_id), str(image_channel_id)))

            conn.commit()
            conn.close()

            # Send success message
            embed = discord.Embed(
                title="Success",
                description="-# Information saved successfully!",
                color=discord.Color.from_str("#c2ccf8")
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError:
            # Handle invalid IDs
            embed = discord.Embed(
                title="Error",
                description="All IDs must be valid numbers.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logging.error(f"Error in guild configuration: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

# Button view for guild configuration
class GuildConfigView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)  # 3 minute timeout

    @ui.button(label="Start", style=discord.ButtonStyle.primary)
    async def start_config(self, interaction: discord.Interaction, button: ui.Button):
        # Show the configuration modal
        await interaction.response.send_modal(GuildConfigModal())

class GuildCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        setup_guild_database()

    async def is_guild_admin(self, interaction: discord.Interaction):
        """Check if the user is a guild admin based on configured role"""
        if interaction.guild is None:
            return False

        # Check if this is the main guild owner
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                if str(interaction.user.id) == config.get("owner_id"):
                    return True
        except Exception as e:
            logging.error(f"Error checking owner status: {e}")

        # Check if user has guild admin role
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT admin_role_id FROM guild_configs WHERE guild_id = ?", 
                      (str(interaction.guild.id),))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return False

        admin_role_id = int(result[0])
        admin_role = discord.utils.get(interaction.guild.roles, id=admin_role_id)

        if admin_role and admin_role in interaction.user.roles:
            return True

        return False

    async def has_guild_subscription(self, user_id):
        """Check if a user has an active guild subscription"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        cursor.execute("SELECT subscription_type, end_date FROM guild_subscriptions WHERE user_id = ? AND is_active = 1", 
                      (str(user_id),))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return False

        subscription_type, end_date = result

        # Lifetime subscriptions are always valid
        if subscription_type.lower() == "lifetime":
            return True

        # Check if subscription is still valid
        try:
            expiry_date = datetime.strptime(end_date, "%Y-%m-%d")
            if datetime.now() < expiry_date:
                return True
        except Exception as e:
            logging.error(f"Error checking subscription expiry: {e}")

        return False

    @app_commands.command(name="configure_guild", description="Configure the bot for your guild")
    async def configure_guild(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # First check if user has guild subscription
        has_subscription = await self.has_guild_subscription(user_id)

        # If this is the main guild owner, allow configuration regardless
        is_owner = False
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                if user_id == config.get("owner_id"):
                    is_owner = True
                    has_subscription = True
        except Exception as e:
            logging.error(f"Error checking owner status: {e}")

        if not has_subscription and not is_owner:
            embed = discord.Embed(
                title="Access Denied",
                description="You need a Guild subscription to configure the bot for your server.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check the guild context
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                main_guild_id = config.get("guild_id", "1339298010169086072")

            # Get bot application info for invite link
            app_info = await self.bot.application_info()
            client_id = app_info.id

            # Create invite link with proper permissions
            invite_permissions = discord.Permissions(
                send_messages=True,
                embed_links=True,
                attach_files=True,
                read_messages=True,
                read_message_history=True,
                manage_roles=True,
                use_application_commands=True
            )
            invite_link = discord.utils.oauth_url(
                client_id, 
                permissions=invite_permissions,
                scopes=["bot", "applications.commands"]
            )

            # Check if we're in the main guild or a user guild
            if str(interaction.guild.id) == main_guild_id:
                # If in main guild, show invite link
                embed = discord.Embed(
                    title="Configure Your Guild Bot",
                    description=f"Please invite the bot to your server and then run the command there. You can do so by clicking the link below:",
                    color=discord.Color.from_str("#c2ccf8")
                )
                embed.add_field(
                    name="Bot Invite Link", 
                    value=f"[Click here to invite the bot]({invite_link})"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                # If in user guild, show configuration
                embed = discord.Embed(
                    title="Configure Your Guild",
                    description="-# Click the button below to start the setup process.",
                    color=discord.Color.from_str("#c2ccf8")
                )
                view = GuildConfigView()
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            logging.error(f"Error in configure_guild command: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="add_access", description="Add access for a user in your guild")
    @app_commands.describe(
        user="The user to grant access to",
        days="Number of days for access (0 for lifetime)"
    )
    async def add_access(self, interaction: discord.Interaction, user: discord.Member, days: int):
        # Check if user is a guild admin
        is_admin = await self.is_guild_admin(interaction)

        if not is_admin:
            embed = discord.Embed(
                title="Access Denied",
                description="You must have the admin role to use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Get guild configuration
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("""
        SELECT generate_channel_id, client_role_id 
        FROM guild_configs 
        WHERE guild_id = ?
        """, (str(interaction.guild.id),))

        config = cursor.fetchone()

        if not config:
            embed = discord.Embed(
                title="Error",
                description="This server has not been configured yet. Please use `/configure_guild` first.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            conn.close()
            return

        generate_channel_id, client_role_id = config

        # Calculate expiry date
        if days == 0:
            # Lifetime access
            expiry_date = datetime.now() + timedelta(days=3650)  # ~10 years
            access_type = "Lifetime"
        else:
            # Temporary access
            expiry_date = datetime.now() + timedelta(days=days)
            access_type = f"{days} Days"

        # Add or update user access
        expiry_str = expiry_date.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        INSERT OR REPLACE INTO server_access
        (guild_id, user_id, added_by, access_type, expiry, added_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (str(interaction.guild.id), str(user.id), str(interaction.user.id), 
              access_type, expiry_str))

        conn.commit()
        conn.close()

        # Try to add client role to the user
        try:
            client_role = discord.utils.get(interaction.guild.roles, id=int(client_role_id))
            if client_role:
                await user.add_roles(client_role)
                print(f"Added client role {client_role_id} to user {user.id} in guild {interaction.guild.id}")
            else:
                print(f"Client role {client_role_id} not found in guild {interaction.guild.id}")
        except Exception as e:
            logging.error(f"Error adding client role: {e}")
            print(f"Failed to add role {client_role_id} to user {user.id}: {e}")

        # Send public notification
        embed = discord.Embed(
            title="Access Granted",
            description=f"Successfully added `{access_type}` access to {user.mention}\n\n"
                        f"» Go to <#{generate_channel_id}> and Run command `/generate`",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(GuildCommands(bot))