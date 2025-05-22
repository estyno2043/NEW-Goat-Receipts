
import discord
import asyncio
import sqlite3
import datetime
import json
from discord.ext import tasks

class AutoBumper:
    def __init__(self, bot):
        self.bot = bot
        # Load config to get main server ID
        with open("config.json", "r") as f:
            self.config = json.load(f)
        self.main_server_id = self.config["guild_id"]
        self.bump_scheduler.start()
        
    def cog_unload(self):
        self.bump_scheduler.cancel()
        
    @tasks.loop(hours=2)
    async def bump_scheduler(self):
        """Automatically bumps the main server if auto-bump is enabled"""
        try:
            # Get only the main server with auto-bump enabled
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            
            # Create the table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auto_bump (
                    guild_id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    last_bump TEXT,
                    enabled INTEGER DEFAULT 1
                )
            ''')
            conn.commit()
            
            # Get main server if auto-bump is enabled
            cursor.execute("SELECT channel_id, last_bump FROM auto_bump WHERE guild_id = ? AND enabled = 1", 
                          (self.main_server_id,))
            server = cursor.fetchone()
            conn.close()
            
            if server:
                channel_id, last_bump = server
                try:
                    # Convert to int
                    channel_id = int(channel_id)
                    
                    # Get the guild and channel
                    guild = self.bot.get_guild(int(self.main_server_id))
                    if not guild:
                        print(f"Could not find main guild ID: {self.main_server_id}")
                        return
                        
                    channel = guild.get_channel(channel_id)
                    if not channel:
                        print(f"Could not find channel ID: {channel_id} in guild: {guild.name}")
                        return
                    
                    # Find the DISBOARD bot's /bump command in the guild
                    # Rather than sending a text command, we need to create a proper application command
                    disboard_command = await self.bot.tree.sync(guild=guild)
                    
                    # Create a dummy interaction context to invoke the bump command
                    ctx = await self.bot.get_context(await channel.send("Bumping server..."))
                    
                    # Use the Discord command system
                    try:
                        # DISBOARD bot's ID
                        disboard_id = 302050872383242240
                        
                        try:
                            # Find the DISBOARD bot in the guild
                            disboard_bot = discord.utils.get(guild.members, id=disboard_id)
                            
                            if disboard_bot:
                                # Create an interaction with the DISBOARD bot's bump command
                                # We'll use the Discord API directly to invoke the slash command
                                interaction = await self.bot.http.request(
                                    discord.http.Route('POST', '/interactions'),
                                    json={
                                        'type': 2,  # APPLICATION_COMMAND
                                        'application_id': disboard_id,
                                        'guild_id': guild.id,
                                        'channel_id': channel.id,
                                        'data': {
                                            'id': '947088344167366698',
                                            'name': 'bump',
                                            'type': 1  # CHAT_INPUT
                                        }
                                    }
                                )
                                print(f"Automatically triggered DISBOARD bump command in {guild.name}")
                            else:
                                # Fallback to sending clickable message
                                await channel.send("!d bump", allowed_mentions=discord.AllowedMentions.none())
                                print(f"DISBOARD bot not found in {guild.name}, sent fallback command")
                            
                            # Add confirmation message
                            await channel.send("🤖 Auto-bumping server with DISBOARD...")
                        except Exception as e:
                            print(f"Error executing bump command: {e}")
                            # Log the error but don't send a fallback message that requires clicking
                            print(f"Auto-bump error details: {str(e)}")
                        
                        # Update last bump time
                        conn = sqlite3.connect('data.db')
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE auto_bump SET last_bump = ? WHERE guild_id = ?", 
                            (datetime.datetime.now().isoformat(), self.main_server_id)
                        )
                        conn.commit()
                        conn.close()
                        
                        print(f"Auto-bumped main server: {guild.name}")
                        
                    except Exception as e:
                        print(f"Error bumping main server: {e}")
                except Exception as e:
                    print(f"Error accessing channel: {e}")
            else:
                print("Auto-bump not enabled for main server or main server not configured for auto-bump")
                    
        except Exception as e:
            print(f"Error in bump scheduler: {e}")
    
    @bump_scheduler.before_loop
    async def before_bump_scheduler(self):
        await self.bot.wait_until_ready()
        # Wait random time between 1-10 minutes to avoid bumping exactly on the hour
        await asyncio.sleep(60 * 5)  # Start 5 minutes after bot is ready
