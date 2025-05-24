
import discord
import sqlite3
import json
import logging
from datetime import datetime, timedelta
import asyncio

class GuildManager:
    """Manages guild subscriptions and configurations"""
    
    @staticmethod
    def setup_guild_tables():
        """Create necessary database tables for guild subscriptions"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Table for guild owners/subscribers
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_subscriptions (
            user_id TEXT PRIMARY KEY,
            subscription_type TEXT,
            start_date TEXT,
            expiry_date TEXT,
            is_active BOOLEAN DEFAULT 1,
            bot_token TEXT
        )
        ''')
        
        # Table for guild-specific configurations
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_configs (
            guild_id TEXT PRIMARY KEY,
            owner_id TEXT,
            generator_channel_id TEXT,
            admin_role_id TEXT,
            client_role_id TEXT,
            image_channel_id TEXT,
            purchases_channel_id TEXT,
            setup_date TEXT
        )
        ''')
        
        # Table for guild-specific user access
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_user_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            user_id TEXT,
            added_by TEXT,
            expiry_date TEXT,
            is_active BOOLEAN DEFAULT 1,
            UNIQUE(guild_id, user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Guild subscription tables initialized")
    
    @staticmethod
    def register_bot_token(user_id, bot_token):
        """Register a user's bot token for guild subscription"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Check if user has an active guild subscription
        cursor.execute("SELECT subscription_type, expiry_date FROM guild_subscriptions WHERE user_id = ?", (str(user_id),))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, "You don't have an active guild subscription. Please purchase one first."
        
        subscription_type, expiry_date = result
        
        # Check if subscription is still valid
        if subscription_type != "Lifetime":
            try:
                expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
                if datetime.now() > expiry:
                    conn.close()
                    return False, "Your guild subscription has expired. Please renew it."
            except Exception as e:
                logging.error(f"Error parsing expiry date: {e}")
                conn.close()
                return False, "There was an error checking your subscription. Please contact support."
        
        # Update the bot token for the user
        cursor.execute(
            "UPDATE guild_subscriptions SET bot_token = ? WHERE user_id = ?", 
            (bot_token, str(user_id))
        )
        
        conn.commit()
        conn.close()
        
        # Start the guild user's bot in a subprocess
        try:
            import subprocess
            import os
            import traceback
            
            # Create a directory for the guild bot if it doesn't exist
            guild_bot_dir = f"guild_bots/{user_id}"
            os.makedirs(guild_bot_dir, exist_ok=True)
            
            # Create a bot file using the template
            bot_file_path = f"{guild_bot_dir}/bot.py"
            
            # Import the template
            from utils.guild_bot_template import TEMPLATE
            
            # Write the bot file with the template
            with open(bot_file_path, "w") as f:
                f.write(TEMPLATE.format(
                    owner_id=user_id,
                    bot_token=bot_token
                ))
            
            # Start the bot in a subprocess with better error handling
            process = subprocess.Popen(
                ["python", bot_file_path], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                cwd=os.getcwd(),
                text=True  # Capture output as text
            )
            
            # Wait a moment to check for immediate startup errors
            import time
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is not None:
                # Process has terminated, get error output
                _, stderr = process.communicate()
                logging.error(f"Guild bot for user {user_id} failed to start: {stderr}")
                return True, "Bot token registered successfully, but the bot couldn't be started due to an error. Please contact support."
            
            logging.info(f"Started guild bot for user {user_id}")
            
            # Sync slash commands (not done here, will be done within the bot itself)
            
        except Exception as e:
            logging.error(f"Error starting guild bot: {e}")
            traceback.print_exc()
            # Still return success as the token was saved
        
        return True, "Bot token registered successfully. Your bot has been started. You can now run /configure_guild."
    
    @staticmethod
    def has_bot_registered(user_id):
        """Check if a user has registered a bot token"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT bot_token FROM guild_subscriptions WHERE user_id = ?", (str(user_id),))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None and result[0] is not None and len(result[0]) > 0
    
    @staticmethod
    def save_guild_config(guild_id, owner_id, generator_channel_id, admin_role_id, client_role_id, image_channel_id, purchases_channel_id=None):
        """Save guild-specific configuration"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Check if config already exists for this guild
        cursor.execute("SELECT * FROM guild_configs WHERE guild_id = ?", (str(guild_id),))
        existing = cursor.fetchone()
        
        setup_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if existing:
            # Update existing config
            cursor.execute('''
            UPDATE guild_configs 
            SET generator_channel_id = ?, admin_role_id = ?, client_role_id = ?, image_channel_id = ?, 
                purchases_channel_id = ?, setup_date = ?
            WHERE guild_id = ?
            ''', (
                str(generator_channel_id), 
                str(admin_role_id), 
                str(client_role_id), 
                str(image_channel_id),
                str(purchases_channel_id) if purchases_channel_id else None,
                setup_date,
                str(guild_id)
            ))
        else:
            # Insert new config
            cursor.execute('''
            INSERT INTO guild_configs 
            (guild_id, owner_id, generator_channel_id, admin_role_id, client_role_id, image_channel_id, 
             purchases_channel_id, setup_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(guild_id),
                str(owner_id),
                str(generator_channel_id),
                str(admin_role_id),
                str(client_role_id),
                str(image_channel_id),
                str(purchases_channel_id) if purchases_channel_id else None,
                setup_date
            ))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_guild_config(guild_id):
        """Get guild-specific configuration"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM guild_configs WHERE guild_id = ?", (str(guild_id),))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            # Convert to dictionary
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, result))
        return None
    
    @staticmethod
    def add_user_access(guild_id, user_id, added_by, days=0):
        """Add access for a user in a specific guild
        If days=0, add lifetime access
        """
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Calculate expiry date
        if days == 0:
            # Lifetime (10 years)
            expiry_date = (datetime.now() + timedelta(days=3650)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if user already has access
        cursor.execute(
            "SELECT id FROM guild_user_access WHERE guild_id = ? AND user_id = ?",
            (str(guild_id), str(user_id))
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing access
            cursor.execute('''
            UPDATE guild_user_access
            SET expiry_date = ?, is_active = 1, added_by = ?
            WHERE guild_id = ? AND user_id = ?
            ''', (expiry_date, str(added_by), str(guild_id), str(user_id)))
        else:
            # Add new access
            cursor.execute('''
            INSERT INTO guild_user_access
            (guild_id, user_id, added_by, expiry_date, is_active)
            VALUES (?, ?, ?, ?, 1)
            ''', (str(guild_id), str(user_id), str(added_by), expiry_date))
        
        conn.commit()
        conn.close()
        return True, expiry_date
    
    @staticmethod
    def check_user_access(guild_id, user_id):
        """Check if a user has access in a specific guild"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT expiry_date, is_active 
            FROM guild_user_access 
            WHERE guild_id = ? AND user_id = ?
            ''', (str(guild_id), str(user_id)))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False, "No access"
            
            expiry_date, is_active = result
            
            # Check if access is active
            if not is_active:
                return False, "Access revoked"
            
            # Check if access has expired
            try:
                expiry = datetime.strptime(expiry_date, "%Y-%m-%d %H:%M:%S")
                if datetime.now() > expiry:
                    return False, f"Access expired on {expiry_date}"
                return True, f"Access valid until {expiry_date}"
            except Exception as e:
                logging.error(f"Error parsing expiry date: {e}")
                return False, "Error checking access"
            
        except Exception as e:
            logging.error(f"Error checking user access: {e}")
            conn.close()
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def add_guild_subscription(user_id, subscription_type, days=30):
        """Add a guild subscription for a user"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        start_date = datetime.now().strftime("%Y-%m-%d")
        
        if subscription_type == "Lifetime" or days == 0:
            # Lifetime subscription (set to 10 years)
            expiry_date = (datetime.now() + timedelta(days=3650)).strftime("%Y-%m-%d")
            subscription_type = "Lifetime"
        else:
            # Time-limited subscription
            expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Check if user already has a subscription
        cursor.execute("SELECT user_id FROM guild_subscriptions WHERE user_id = ?", (str(user_id),))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing subscription
            cursor.execute('''
            UPDATE guild_subscriptions
            SET subscription_type = ?, start_date = ?, expiry_date = ?, is_active = 1
            WHERE user_id = ?
            ''', (subscription_type, start_date, expiry_date, str(user_id)))
        else:
            # Add new subscription
            cursor.execute('''
            INSERT INTO guild_subscriptions
            (user_id, subscription_type, start_date, expiry_date, is_active)
            VALUES (?, ?, ?, ?, 1)
            ''', (str(user_id), subscription_type, start_date, expiry_date))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def check_guild_subscription(user_id):
        """Check if a user has an active guild subscription"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT subscription_type, expiry_date, is_active 
        FROM guild_subscriptions 
        WHERE user_id = ?
        ''', (str(user_id),))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False, "No subscription"
        
        subscription_type, expiry_date, is_active = result
        
        # Check if subscription is active
        if not is_active:
            return False, "Subscription inactive"
        
        # Lifetime subscriptions are always valid
        if subscription_type == "Lifetime":
            return True, "Lifetime subscription"
        
        # Check if subscription has expired
        try:
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
            if datetime.now() > expiry:
                return False, f"Subscription expired on {expiry_date}"
            return True, f"{subscription_type} subscription valid until {expiry_date}"
        except Exception as e:
            logging.error(f"Error parsing expiry date: {e}")
            return False, "Error checking subscription"

    @staticmethod
    async def check_guild_subscriptions_loop(bot):
        """Background task to check for expired guild subscriptions"""
        await bot.wait_until_ready()
        
        while not bot.is_closed():
            try:
                # Check for expired subscriptions
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()
                
                # Get non-lifetime subscriptions that might be expired
                cursor.execute('''
                SELECT user_id, expiry_date 
                FROM guild_subscriptions 
                WHERE subscription_type != 'Lifetime' AND is_active = 1
                ''')
                
                subscriptions = cursor.fetchall()
                current_date = datetime.now()
                
                for user_id, expiry_date in subscriptions:
                    try:
                        expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
                        
                        # If expired, mark as inactive
                        if current_date > expiry:
                            logging.info(f"Guild subscription for user {user_id} has expired")
                            cursor.execute('''
                            UPDATE guild_subscriptions 
                            SET is_active = 0 
                            WHERE user_id = ?
                            ''', (user_id,))
                            
                            # Get all guild configs owned by this user
                            cursor.execute('''
                            SELECT guild_id 
                            FROM guild_configs 
                            WHERE owner_id = ?
                            ''', (user_id,))
                            
                            guilds = cursor.fetchall()
                            
                            # Notify the user if possible
                            try:
                                user = await bot.fetch_user(int(user_id))
                                if user:
                                    embed = discord.Embed(
                                        title="Guild Subscription Expired",
                                        description="Your guild subscription has expired. Your bot will no longer work in your server. Please renew your subscription to continue using the service.",
                                        color=discord.Color.red()
                                    )
                                    try:
                                        await user.send(embed=embed)
                                    except:
                                        logging.info(f"Could not DM user {user_id} about expired guild subscription")
                            except:
                                logging.info(f"Could not find user {user_id} to notify about expired guild subscription")
                    except Exception as e:
                        logging.error(f"Error processing guild subscription for {user_id}: {e}")
                
                conn.commit()
                conn.close()
            except Exception as e:
                logging.error(f"Error in guild subscription checker: {e}")
            
            # Check every 12 hours
            await asyncio.sleep(43200)
