import os
import json


import discord
import json
import os
import os

class Utils:
    @staticmethod
    async def log_receipt_generation(bot, user_id, brand_name, image_url, guild_id=None):
        """Send a log entry to the receipt log channel"""
        try:
            # Load config
            with open("config.json", "r") as f:
                config = json.load(f)
            
            print(f"Logging receipt generation - brand: {brand_name}, user: {user_id}, guild: {guild_id}")
            
            # Get log channel ID
            log_channel_id = None
            
            # Check for server-specific log channel first
            if guild_id:
                import sqlite3
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT receipt_log_channel FROM server_configs WHERE guild_id = ?", (str(guild_id),))
                result = cursor.fetchone()
                conn.close()
                
                if result and result[0]:
                    log_channel_id = result[0]
                    print(f"Found server-specific log channel: {log_channel_id} for guild {guild_id}")
            
            # Fall back to global log channel if no server-specific one
            if not log_channel_id:
                log_channel_id = config.get("receipt_log_channel")
                print(f"Using global log channel: {log_channel_id}")
                
            if not log_channel_id:
                print("No receipt log channel configured")
                return False
                
            # Check if the log channel ID is valid
            try:
                channel_id_int = int(log_channel_id)
                print(f"Parsed channel ID: {channel_id_int}")
            except (ValueError, TypeError):
                print(f"Invalid channel ID format: {log_channel_id}")
                return False
                
            # List all available channels for debugging
            print(f"Bot is in {len(bot.guilds)} guilds with these channels:")
            for guild in bot.guilds:
                print(f"Guild: {guild.name} ({guild.id})")
                for ch in guild.channels:
                    if isinstance(ch, discord.TextChannel):
                        print(f"  - {ch.name} ({ch.id})")
                
            # Try fetching channel if not found directly
            channel = bot.get_channel(channel_id_int)
            if not channel:
                print(f"Channel not found with get_channel, trying to fetch channel: {channel_id_int}")
                try:
                    channel = await bot.fetch_channel(channel_id_int)
                    print(f"Successfully fetched channel: {channel.name}")
                except discord.errors.NotFound:
                    print(f"Channel {channel_id_int} not found")
                    return False
                except discord.errors.Forbidden:
                    print(f"No permission to access channel {channel_id_int}")
                    return False
                except Exception as fetch_error:
                    print(f"Error fetching channel {channel_id_int}: {str(fetch_error)}")
                    return False
                    
            if not channel:
                print(f"Could not find receipt log channel: {channel_id_int}")
                return False
                
            print(f"Attempting to send log to channel {channel.name} ({channel.id})")
            
            embed = discord.Embed(
                title=f"<:receipt:1370002832283013170> Receipt Generated - {brand_name}",
                description=f"<@{user_id}> **has generated a receipt.**",
                color=0x4CAF50
            )
            
            # Use provided image URL if it exists and is properly formatted
            # Otherwise, use a default fallback image
            fallback_image_url = "https://cdn.discordapp.com/attachments/1339298010169086075/1370019337695396030/image.png?ex=681df96f&is=681ca7ef&hm=361fe0fa3e3a2b1bf17b1d23e0aab3a0153e7d6a0c1cfc0124e67c77b8e6fac0&"
            
            if image_url and image_url.startswith(('http://', 'https://')) and '.' in image_url.split('/')[-1]:
                try:
                    embed.set_thumbnail(url=image_url)
                except Exception as e:
                    print(f"Error setting custom thumbnail, using fallback: {e}")
                    embed.set_thumbnail(url=fallback_image_url)
            else:
                # Use fallback image if no valid image URL is provided
                embed.set_thumbnail(url=fallback_image_url)
                
            await channel.send(embed=embed)
            print(f"Successfully sent receipt log to channel {channel.name}")
            return True
        except Exception as e:
            print(f"Error sending receipt log: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False
    
    @staticmethod
    async def is_whitelisted(user_id):
        """Check if a user is whitelisted with improved error handling"""
        try:
            # Make sure the user ID is a string for comparison
            user_id_str = str(user_id)

            # Check if whitelist file exists
            if not os.path.exists("whitelist.txt"):
                print("Warning: whitelist.txt does not exist")
                return False

            with open("whitelist.txt", "r") as f:
                whitelisted_users = f.read().splitlines()

            # Check if user is in whitelist (removing any whitespace)
            whitelisted_users = [user.strip() for user in whitelisted_users]
            is_whitelisted = user_id_str in whitelisted_users

            if is_whitelisted:
                print(f"User {user_id} is in whitelist")

            return is_whitelisted
        except Exception as e:
            print(f"Error checking whitelist for user {user_id}: {str(e)}")
            # In case of error, default to not whitelisted for security
            return False

    @staticmethod
    async def is_blacklisted(user_id: int) -> bool:
        with open("blacklist.txt", "r") as f:
            blacklisted_users = f.read().splitlines()
            return str(user_id) in blacklisted_users

    @staticmethod
    async def add_to_whitelist(user_id: int) -> bool:
        with open("whitelist.txt", "r+") as f:
            whitelisted_users = f.read().splitlines()
            if str(user_id) in whitelisted_users:
                return False
            f.write(str(user_id) + "\n")
            return True

    @staticmethod
    async def add_to_blacklist(user_id: int) -> bool:
        with open("blacklist.txt", "r+") as f:
            blacklisted_users = f.read().splitlines()
            if str(user_id) in blacklisted_users:
                return False
            f.write(str(user_id) + "\n")
            return True

    @staticmethod
    async def remove_from_blacklist(user_id: int) -> bool:
        with open("blacklist.txt", "r+") as f:
            lines = f.readlines()
            f.seek(0)
            user_removed = False
            for line in lines:
                if str(user_id) not in line.strip():
                    f.write(line)
                else:
                    user_removed = True
            f.truncate()
            return user_removed

    @staticmethod
    async def remove_from_whitelist(user_id: int) -> bool:
        with open("whitelist.txt", "r+") as f:
            lines = f.readlines()
            f.seek(0)
            user_removed = False
            for line in lines:
                if str(user_id) not in line.strip():
                    f.write(line)
                else:
                    user_removed = True
            f.truncate()

            # If user was removed, also check if they have authorized servers
            if user_removed:
                from utils.server_auth import ServerAuth
                # We want to keep the database record but enforce they can't use the bot there
                # This is handled in the authorization check, not by removing the authorization

            return user_removed

    @staticmethod
    async def is_valid_server_authorization(guild_id: int, user_id: int) -> bool:
        """
        Checks if a server's authorization is valid and if the user has access.

        A user has access if they meet any of these conditions:
        1. They are the bot owner
        2. They are whitelisted
        3. They authorized the server themselves (and are still whitelisted)
        4. They were specifically granted access to this server by the authorizing user

        Returns:
            bool: True if the user has valid access to the server
        """
        from utils.server_auth import ServerAuth

        # Load config to check if user is bot owner
        with open("config.json", "r") as f:
            config = json.load(f)

        # Bot owner always has access everywhere
        if str(user_id) == config["owner_id"]:
            return True

        # Blacklisted users can't use the bot anywhere
        if await Utils.is_blacklisted(user_id):
            return False

        # Check if server is authorized at all
        if not await ServerAuth.is_authorized_server(guild_id):
            return False

        # Whitelisted users have access to all authorized servers
        if await Utils.is_whitelisted(user_id):
            return True

        # If user authorized this server themselves, they need to still be whitelisted
        if await ServerAuth.is_server_authorized_by_user(guild_id, user_id):
            return await Utils.is_whitelisted(user_id)

        # Finally, check if the user was specifically granted access to this server
        return await ServerAuth.has_server_access(guild_id, user_id)


def get_user_details(owner_id):
    try:
        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, street, city, zip, country FROM user_details WHERE owner_id = ?", (str(owner_id),))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting user details: {str(e)}")
        return None

def send_html(recipient_email, html_content, sender_email, subject, save_file_name=None, attachment_path=None):
    try:
        # This function will be implemented to send HTML emails
        # For now it's a placeholder to fix the import
        print(f"Sending email to {recipient_email} from {sender_email} with subject {subject}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')
def save_receipt_html(html_content, brand_name):
    """
    Save HTML receipt content to the updatedreceipts folder.
    
    Args:
        html_content (str): The HTML content to save
        brand_name (str): The name of the brand (used for filename)
        
    Returns:
        str: The full path to the saved file
    """
    # Ensure the directory exists
    receipts_dir = "receipt/updatedreceipts"
    os.makedirs(receipts_dir, exist_ok=True)
    
    # Create the file path
    file_path = f"{receipts_dir}/updated{brand_name.lower()}.html"
    
    # Write the content to the file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)
    
    print(f"Receipt saved to: {file_path}")
    return file_path
