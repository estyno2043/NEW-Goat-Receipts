import re
import sqlite3
import discord
import json


class MessageFilter:
    def __init__(self, bot):
        self.bot = bot
        self.invite_pattern = re.compile(r'(discord\.gg|discord\.com\/invite)\/[a-zA-Z0-9]+')

    async def check_message(self, message):
        # Skip messages from the bot itself
        if message.author == self.bot.user:
            return False

        # Skip messages from the server owner
        if message.guild and message.author.id == message.guild.owner_id:
            return False

        # Load config to get main guild ID and generate channel ID
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                main_guild_id = config.get("guild_id", "1339298010169086072")
                main_generate_channel_id = 1374468007472009216
        except Exception as e:
            print(f"Error loading config: {e}")
            main_guild_id = "1339298010169086072"
            main_generate_channel_id = 1374468007472009216

        # Check if this is the main guild generate channel
        if (message.guild and 
            str(message.guild.id) == main_guild_id and 
            message.channel.id == main_generate_channel_id):

            try:
                # Delete any message that isn't from a slash command interaction
                # This includes regular messages, bot messages from other bots, etc.
                if not message.interaction or message.interaction.user != message.author:
                    await message.delete()
                    print(f"Deleted message from {message.author} in main generate channel: {message.content[:50]}...")
                    return True
            except Exception as e:
                print(f"Error deleting message from main generate channel: {e}")

        # Check for guild-specific generate channels
        if message.guild and str(message.guild.id) != main_guild_id:
            try:
                # Check MongoDB for guild configuration
                from utils.mongodb_manager import mongo_manager
                db = mongo_manager.get_database()
                if db is not None:
                    guild_config = db.guild_configs.find_one({"guild_id": str(message.guild.id)})
                    if guild_config:
                        generate_channel_id = int(guild_config.get("generate_channel_id", 0))
                        if message.channel.id == generate_channel_id:
                            try:
                                # Delete any message that isn't from a slash command interaction
                                if not message.interaction or message.interaction.user != message.author:
                                    await message.delete()
                                    print(f"Deleted message from {message.author} in guild generate channel: {message.content[:50]}...")
                                    return True
                            except Exception as e:
                                print(f"Error deleting message from guild generate channel: {e}")
            except Exception as e:
                print(f"Error checking guild generate channel: {e}")

        # Specific channels to enforce message deletion (legacy support)
        commands_only_channels = ["1359498078482075759", "1374468007472009216"]
        if message.guild and str(message.channel.id) in commands_only_channels:
            try:
                # Delete any message in these specific channels unless it's a valid slash command
                if not message.interaction or message.interaction.user != message.author:
                    await message.delete()
                    print(f"Deleted message from {message.author} in commands-only channel: {message.content[:50]}...")
                    return True
            except Exception as e:
                print(f"Error deleting message from specific channel: {e}")

        # Check if this is a commands-only channel from database config
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
                        # Delete any message that isn't from a slash command interaction
                        if not message.interaction or message.interaction.user != message.author:
                            await message.delete()
                            print(f"Deleted message from {message.author} in configured commands-only channel: {message.content[:50]}...")
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

                if result and result[0]:
                    await message.delete()
                    print(f"Deleted invite link from {message.author}")
                    return True
            except Exception as e:
                print(f"Error in invite filter: {e}")

        return False