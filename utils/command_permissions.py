"""
Utility for command permissions
"""
import discord
from discord import app_commands, Interaction
import json
import functools
import sqlite3
from datetime import datetime

async def check_permission(interaction: discord.Interaction):
    """
    Check if a user has permission to use the bot in the current server.

    Returns:
    - True if user has permission
    - False if user does not have permission
    """
    # Load config
    with open("config.json", "r") as f:
        config = json.load(f)

    # Get main guild ID and owner ID from config
    main_guild_id = config.get("guild_id")
    owner_id = config.get("owner_id")

    # Automatically allow the bot owner
    if str(interaction.user.id) == owner_id:
        return True

    # Check if user is whitelisted
    from utils.utils import Utils
    if await Utils.is_whitelisted(interaction.user.id):
        return True

    # Check if user has the appropriate client role
    if interaction.guild:
        # Check for server-specific client role first
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        try:
            # First check if server has a specific configuration
            cursor.execute("SELECT client_id FROM server_configs WHERE guild_id = ?", (str(interaction.guild.id),))
            result = cursor.fetchone()

            server_has_config = result is not None

            # Determine the correct role ID to check
            if server_has_config and result[0]:
                # Use server-specific role from config
                try:
                    client_role_id = int(result[0])
                    # Find and check the role
                    client_role = discord.utils.get(interaction.guild.roles, id=client_role_id)
                    if client_role and client_role in interaction.user.roles:
                        print(f"User {interaction.user.id} ({interaction.user.name}) has server-specific role {client_role_id}")
                        return True
                    # If we get here, user doesn't have the configured role
                except (ValueError, TypeError):
                    # Invalid role ID in database, will fall back to default
                    print(f"Invalid server-specific role ID for guild {interaction.guild.id}")
                    pass

            # Check if this is the main guild
            if str(interaction.guild.id) == main_guild_id:
                # Use the main guild client role from config
                try:
                    main_client_role_id = int(config.get("Client_ID", 0))
                    if main_client_role_id > 0:
                        main_client_role = discord.utils.get(interaction.guild.roles, id=main_client_role_id)
                        if main_client_role and main_client_role in interaction.user.roles:
                            return True
                except (ValueError, TypeError):
                    # Invalid role ID in config
                    pass

            # If we get to this point and server has a configuration, 
            # but user doesn't have the required role - deny access
            if server_has_config:
                print(f"User {interaction.user.id} denied access: server has config but user lacks required role")
                # If in chat, send a direct message about lacking access
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message("You do not have access.", ephemeral=True)
                except Exception:
                    pass
                return False
        except Exception as e:
            print(f"Error checking role permissions: {e}")
        finally:
            conn.close()

    return False

def admin_only():
    """
    Decorator to make a command visible only to admins and whitelisted users.
    This will hide the command from regular users' slash command list.
    """
    async def check_permissions(interaction: discord.Interaction) -> bool:
        if await check_permission(interaction):
            return True
        else:
            return False

    def decorator(func):
        func.check_permissions = check_permissions  # Attach the check function
        return func

    return decorator

def public_command():
    """
    Decorator for commands that can be used by regular users in authorized servers.
    Makes commands visible to all users in authorized servers.
    """
    async def check_permissions(interaction: discord.Interaction) -> bool:
        if await check_permission(interaction):
            return True
        else:
            return False

    def decorator(func):
        func.check_permissions = check_permissions  # Attach the check function

        @functools.wraps(func)
        async def wrapper(self, interaction, *args, **kwargs):
            if await check_permissions(interaction):
                return await func(self, interaction, *args, **kwargs)
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="Authorization Invalid",
                        description="You are not authorized to use the bot in this server.",
                        color=discord.Colour.red()
                    ),
                    ephemeral=True
                )

        return wrapper

    return decorator