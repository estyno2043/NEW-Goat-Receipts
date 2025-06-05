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
        # Check for guild-specific access first
        from utils.mongodb_manager import mongo_manager
        
        try:
            # Check if this guild has configuration
            guild_config = mongo_manager.get_guild_config(interaction.guild.id)
            
            if guild_config:
                # This is a configured guild, check for guild-specific access
                
                # Check if user has server access in this guild
                server_access = mongo_manager.get_server_access(interaction.guild.id, interaction.user.id)
                if server_access:
                    # Check if access is still valid
                    expiry_str = server_access.get("expiry")
                    access_type = server_access.get("access_type")
                    
                    if access_type == "Lifetime":
                        # Check for client role
                        try:
                            client_role_id = int(guild_config.get("client_role_id"))
                            client_role = discord.utils.get(interaction.guild.roles, id=client_role_id)
                            if client_role and client_role in interaction.user.roles:
                                return True
                        except (ValueError, TypeError):
                            pass
                    else:
                        try:
                            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
                            if datetime.now() < expiry_date:
                                # Check for client role
                                try:
                                    client_role_id = int(guild_config.get("client_role_id"))
                                    client_role = discord.utils.get(interaction.guild.roles, id=client_role_id)
                                    if client_role and client_role in interaction.user.roles:
                                        return True
                                except (ValueError, TypeError):
                                    pass
                        except Exception:
                            pass
                
                # Guild has config but user doesn't have access
                return False
            
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
                    
        except Exception as e:
            print(f"Error checking role permissions: {e}")

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