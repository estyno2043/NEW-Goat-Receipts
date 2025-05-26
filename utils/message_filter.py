
import discord
import re
import sqlite3
from datetime import datetime

class MessageFilter:
    def __init__(self, bot):
        self.bot = bot
        self.invite_pattern = re.compile(r'(discord\.gg|discord\.com\/invite)\/[a-zA-Z0-9]+')
    
    async def check_message(self, message):
        # Skip bot messages
        if message.author.bot:
            return False
            
        # Skip messages from the server owner
        if message.guild and message.author.id == message.guild.owner_id:
            return False
        
        # Specific channels to enforce message deletion
        commands_only_channels = ["1359498078482075759", "1374468007472009216"]
        if message.guild and str(message.channel.id) in commands_only_channels:
            try:
                # Delete any message in these specific channels unless it's a valid slash command
                if not message.interaction:
                    await message.delete()
                    return True
            except Exception as e:
                print(f"Error deleting message from specific channel: {e}")
                
        # Check if this is a commands-only channel
        if message.guild:
            try:
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT commands_only_channels FROM server_configs WHERE guild_id = ?", 
                             (str(message.guild.id),))
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0]:
                    commands_only_channels = result[0].split(',')
                    if str(message.channel.id) in commands_only_channels:
                        # Check if the message starts with a slash command but isn't processed by Discord
                        # or starts with a prefix but isn't a valid command
                        # This covers messages that look like commands but aren't valid
                        if (message.content.startswith('/') or message.content.startswith('!')) and not message.interaction:
                            await message.delete()
                            return True
                        
                        # If it's a regular message (not a slash command)
                        if not message.interaction:
                            await message.delete()
                            return True
            except Exception as e:
                print(f"Error in commands-only channel filter: {e}")
            
        # Check for invite links
        if self.invite_pattern.search(message.content):
            try:
                # Load the bot configuration to see if filtering is enabled for this server
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT filter_invites FROM server_configs WHERE guild_id = ?", 
                             (str(message.guild.id),))
                result = cursor.fetchone()
                conn.close()
                
                # If filtering is enabled (1) or if there's no setting (default to True)
                if not result or result[0] == 1:
                    # Delete the message
                    await message.delete()
                    
                    # Ban the user
                    ban_reason = "Automatic ban: Posting invite links"
                    await message.guild.ban(message.author, reason=ban_reason)
                    
                    # Log the action
                    log_channel_id = await self.get_log_channel(message.guild.id)
                    if log_channel_id:
                        log_channel = message.guild.get_channel(int(log_channel_id))
                        if log_channel:
                            embed = discord.Embed(
                                title="User Banned - Invite Link",
                                description=f"User {message.author.mention} was banned for posting an invite link.",
                                color=discord.Color.red(),
                                timestamp=datetime.now()
                            )
                            embed.add_field(name="Message Content", value=message.content[:1000] + "..." if len(message.content) > 1000 else message.content)
                            embed.set_footer(text=f"User ID: {message.author.id}")
                            await log_channel.send(embed=embed)
                    
                    return True
            except Exception as e:
                print(f"Error in invite filter: {e}")
        
        return False
        
    async def get_log_channel(self, guild_id):
        try:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT log_channel FROM server_configs WHERE guild_id = ?", (str(guild_id),))
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return result[0]
        except Exception as e:
            print(f"Error getting log channel: {e}")
        
        return None
