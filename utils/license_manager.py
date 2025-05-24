import discord
import sqlite3
from datetime import datetime, timedelta
import asyncio
import json
import logging

class LicenseManager:
    def __init__(self, bot):
        self.bot = bot
        self._running = False
        self.check_interval = 3600  # Check every hour (in seconds)

    async def start_license_checker(self):
        """Start the license checker background task."""
        if self._running:
            return

        self._running = True
        self.bot.loop.create_task(self._check_licenses_loop())
        logging.info("License checker background task started")

    async def _check_licenses_loop(self):
        """Periodically check for expired licenses and remove roles."""
        await self.bot.wait_until_ready()

        while self._running and not self.bot.is_closed():
            try:
                await self._process_expired_licenses()
            except Exception as e:
                logging.error(f"Error in license checker: {str(e)}")

            # Wait for the next check interval
            await asyncio.sleep(self.check_interval)

    async def _process_expired_licenses(self):
        """Check for expired licenses and remove roles."""
        # Get current time
        now = datetime.now()

        # Connect to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        # Get all licenses
        cursor.execute("SELECT owner_id, expiry, key FROM licenses")
        licenses = cursor.fetchall()
        conn.close()

        # Load config to get the default role ID
        with open("config.json", "r") as f:
            config = json.load(f)
            default_role_id = int(config.get("Client_ID"))

        for owner_id, expiry_str, key in licenses:
            # Skip lifetime keys
            if key and key.startswith("LifetimeKey"):
                continue

            try:
                # Parse expiry date
                expiry_date = datetime.strptime(expiry_str, '%d/%m/%Y %H:%M:%S')

                # Check if license has expired
                if now > expiry_date:
                    # Find the user in all guilds
                    user_id = int(owner_id)
                    for guild in self.bot.guilds:
                        # Get server-specific role ID if available
                        conn = sqlite3.connect('data.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT client_id FROM server_configs WHERE guild_id = ?", (str(guild.id),))
                        result = cursor.fetchone()
                        conn.close()

                        role_id = None
                        if result and result[0] and result[0].strip():
                            try:
                                role_id = int(result[0])
                                logging.info(f"Found server-specific role ID: {role_id}")
                            except (ValueError, TypeError):
                                logging.warning(f"Invalid server-specific role ID in database for guild {guild.id}: {result[0]}")
                                # Will fall back to default

                        if role_id is None:
                            # No server-specific role or invalid, try to get default from config
                            with open("config.json", "r") as f:
                                config = json.load(f)
                                try:
                                    default_role_id = int(config.get("Client_ID", 0))
                                    if default_role_id == 0:
                                        logging.warning(f"No default role ID found in config for guild {guild.id}")
                                        continue
                                    role_id = default_role_id
                                    logging.info(f"Using default role ID from config: {role_id}")
                                except (ValueError, TypeError):
                                    logging.error(f"Invalid default role ID in config: {config.get('Client_ID')}")
                                    continue


                        # Find the member in this guild
                        member = guild.get_member(user_id)
                        if not member:
                            continue

                        # Find the role
                        role = discord.utils.get(guild.roles, id=role_id)
                        if role and role in member.roles:
                            # Remove the role
                            try:
                                await member.remove_roles(role)
                                logging.info(f"Removed role {role.name} from {member.name} in {guild.name} due to expired license")

                                # Create the expiry embed with renewal button
                                embed = discord.Embed(
                                    title="Your Subscription Has Expired",
                                    description=f"Hello {member.mention}\n\nYour subscription has expired. We appreciate your support!\n\nIf you'd like to renew, click the button below.",
                                    color=discord.Color.red()
                                )
                                
                                # Create renewal button
                                view = discord.ui.View()
                                view.add_item(discord.ui.Button(label="Renew", style=discord.ButtonStyle.link, url="https://goatreceipts.com"))
                                
                                # Try to DM the user
                                try:
                                    await member.send(embed=embed, view=view)
                                except:
                                    # User may have DMs disabled, just log the info
                                    logging.info(f"Could not DM {member.name} about expired license")
                                
                                # Send notification to Purchases channel
                                try:
                                    purchases_channel = self.bot.get_channel(1374468080817803264)
                                    if purchases_channel:
                                        await purchases_channel.send(content=member.mention, embed=embed, view=view)
                                except Exception as channel_error:
                                    logging.error(f"Could not send expiry notification to Purchases channel: {channel_error}")
                            except Exception as e:
                                logging.error(f"Error removing role from {member.name}: {str(e)}")
            except Exception as e:
                logging.error(f"Error processing license for user {owner_id}: {str(e)}")

    # Cache to store known valid licenses during deployment transitions
    _license_cache = {}
    _last_cache_cleanup = datetime.now()
    _cache_cleanup_interval = 3600  # Clean cache every hour

    @staticmethod
    async def is_subscription_active(user_id):
        """Check if a user has an active subscription with improved error handling and caching for deployments."""
        logging.info(f"Checking subscription for user_id: {user_id}")

        # Check if user is in cache with valid license
        current_time = datetime.now()
        user_id_str = str(user_id)

        # Clean up expired cache entries periodically
        if (current_time - LicenseManager._last_cache_cleanup).total_seconds() > LicenseManager._cache_cleanup_interval:
            try:
                expired_keys = []
                for cached_id, (expiry_time, _) in LicenseManager._license_cache.items():
                    if current_time > expiry_time:
                        expired_keys.append(cached_id)

                for key in expired_keys:
                    LicenseManager._license_cache.pop(key, None)

                LicenseManager._last_cache_cleanup = current_time
                logging.info(f"Cleaned {len(expired_keys)} expired entries from license cache")
            except Exception as e:
                logging.error(f"Error cleaning license cache: {str(e)}")

        # Check cache first (helps during deployment transitions)
        if user_id_str in LicenseManager._license_cache:
            cache_expiry, is_lifetime = LicenseManager._license_cache[user_id_str]
            if is_lifetime or current_time < cache_expiry:
                logging.info(f"User {user_id} has valid license in cache until {cache_expiry}")
                return True

        # First check if user is whitelisted
        from utils.utils import Utils
        is_whitelisted = await Utils.is_whitelisted(user_id)
        if is_whitelisted:
            logging.info(f"User {user_id} is whitelisted - granting access")
            # Cache whitelist status (1 year validity since they're whitelisted)
            LicenseManager._license_cache[user_id_str] = (current_time + timedelta(days=365), True)
            return True

        # Check if this is the bot owner
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                if user_id_str == config.get("owner_id"):
                    logging.info(f"User {user_id} is the bot owner - granting access")
                    # Cache owner status permanently
                    LicenseManager._license_cache[user_id_str] = (current_time + timedelta(days=3650), True)
                    return True

                # Check if user has client role in any guild the bot is in
                import discord
                client_role_id = int(config.get("Client_ID", 0))

                # Get the Discord client
                import asyncio
                from discord.ext import commands
                bot = None

                # Try to get bot instance through active tasks
                for task in asyncio.all_tasks():
                    if hasattr(task, "_coro") and hasattr(task._coro, "__self__"):
                        coro_self = task._coro.__self__
                        if isinstance(coro_self, commands.Bot):
                            bot = coro_self
                            break

                if bot:
                    # Check for the user in all guilds
                    for guild in bot.guilds:
                        # Try to get server-specific role ID
                        try:
                            conn = sqlite3.connect('data.db')
                            cursor = conn.cursor()
                            cursor.execute("SELECT client_id FROM server_configs WHERE guild_id = ?", (str(guild.id),))
                            result = cursor.fetchone()
                            conn.close()

                            guild_role_id = None
                            if result and result[0] and result[0].strip():
                                try:
                                    guild_role_id = int(result[0])
                                    logging.info(f"Found server-specific role ID: {guild_role_id}")
                                except (ValueError, TypeError):
                                    logging.warning(f"Invalid server-specific role ID in database for guild {guild.id}: {result[0]}")

                            if guild_role_id is None:
                                guild_role_id = client_role_id
                                logging.info(f"Using default role ID from config: {guild_role_id}")


                            # Check if user has the role in this guild
                            member = guild.get_member(int(user_id))
                            if member:
                                role = discord.utils.get(guild.roles, id=guild_role_id)
                                if role and role in member.roles:
                                    logging.info(f"User {user_id} has client role in guild {guild.id}")
                                    # Cache role-based access for 30 minutes (in case role is removed)
                                    LicenseManager._license_cache[user_id_str] = (current_time + timedelta(minutes=30), False)
                                    return True
                        except Exception as e:
                            logging.error(f"Error checking roles in guild {guild.id}: {str(e)}")
        except Exception as e:
            logging.error(f"Error checking config for owner: {str(e)}")

        # Check if deployment is active or transitioning
        import os
        is_deployment = bool(os.environ.get("REPL_DEPLOYMENT_ID"))
        is_starting = False
        try:
            # Check if bot started in last 5 minutes (fresh deployment)
            uptime_file = ".bot_start_time"
            if os.path.exists(uptime_file):
                with open(uptime_file, "r") as f:
                    start_time = datetime.fromisoformat(f.read().strip())
                    is_starting = (current_time - start_time).total_seconds() < 300
            else:
                # If uptime file doesn't exist, create it and assume starting
                with open(uptime_file, "w") as f:
                    f.write(current_time.isoformat())
                is_starting = True
        except Exception as e:
            logging.error(f"Error checking start time: {str(e)}")
            is_starting = True  # Assume starting if error

        # Try multiple times to connect to the database, in case it's still initializing
        max_attempts = 7 if is_starting else 3  # More attempts during startup
        for attempt in range(max_attempts):
            try:
                # Use connection with improved settings and a longer timeout
                with sqlite3.connect('data.db', timeout=120.0) as conn:  # Increased timeout
                    # Set pragmas for better concurrency handling
                    conn.execute("PRAGMA busy_timeout = 60000")  # Increased to 60 second timeout
                    conn.execute("PRAGMA journal_mode = WAL")    # Write-Ahead Logging
                    conn.execute("PRAGMA synchronous = NORMAL")  # Balance between speed and safety
                    conn.execute("PRAGMA locking_mode = NORMAL") # Explicit locking mode

                    cursor = conn.cursor()

                    # Log the query for debugging
                    logging.info(f"Checking license for user_id: {user_id} (attempt {attempt+1}/{max_attempts})")

                    # Force file sync before query to ensure we're reading latest data
                    if attempt > 0:
                        conn.execute("PRAGMA wal_checkpoint(FULL)")

                    # Try both string and integer user_id to be safer
                    cursor.execute("SELECT expiry, key FROM licenses WHERE owner_id = ? OR owner_id = ?", 
                                  (user_id_str, user_id))
                    result = cursor.fetchone()

                    if not result:
                        # Try one more time with an explicit transaction
                        conn.execute("BEGIN IMMEDIATE")
                        cursor.execute("SELECT expiry, key FROM licenses WHERE owner_id = ? OR owner_id = ?", 
                                      (user_id_str, user_id))
                        result = cursor.fetchone()
                        conn.commit()

                        if not result:
                            logging.info(f"No license found for user_id: {user_id}")
                            if attempt == max_attempts - 1:
                                # On the last attempt, check if any licenses exist at all
                                # This helps diagnose database access issues
                                cursor.execute("SELECT COUNT(*) FROM licenses")
                                count = cursor.fetchone()[0]
                                logging.warning(f"Final license check failed for {user_id}. Database has {count} total licenses.")
                                # Only grant access during actual deployment or startup
                                if is_deployment or is_starting:
                                    logging.warning(f"Temporarily granting access for {user_id} - deployment: {is_deployment}, starting: {is_starting}")
                                    # Cache for 15 minutes during deployment transitions
                                    LicenseManager._license_cache[user_id_str] = (current_time + timedelta(minutes=15), False)
                                    return {"active": True}
                                # In normal operation, properly deny access
                                logging.info(f"Access denied for user {user_id} - no valid license found")
                                return False
                            continue

                    expiry_str, key = result

                    # Check if license is explicitly marked as expired
                    if key and key.startswith("EXPIRED-"):
                        logging.info(f"Expired key found for user_id: {user_id}")
                        return {"active": False, "expired_date": expiry_str}

                    # Lifetime keys are always active
                    if key and ("LifetimeKey" in key or "owner-key" in key):
                        logging.info(f"Lifetime key found for user_id: {user_id}")
                        # Cache lifetime keys
                        LicenseManager._license_cache[user_id_str] = (current_time + timedelta(days=3650), True)
                        return True

                    # Check expiry date
                    try:
                        expiry_date = datetime.strptime(expiry_str, '%d/%m/%Y %H:%M:%S')
                        is_active = current_time < expiry_date
                        logging.info(f"License for user_id {user_id} active: {is_active}, expires: {expiry_str}")

                        # Cache valid licenses
                        if is_active:
                            # Use actual expiry date with small buffer (1 hour)
                            LicenseManager._license_cache[user_id_str] = (expiry_date - timedelta(hours=1), False)
                        else:
                            # Return expired date information
                            return {"active": False, "expired_date": expiry_str}

                        return is_active
                    except Exception as e:
                        logging.warning(f"Error parsing expiry date for user_id {user_id}: {str(e)}")
                        # More lenient - if we can't parse the date but have a key, consider it valid
                        if key:
                            # Cache for 1 day since we can't determine expiry
                            LicenseManager._license_cache[user_id_str] = (current_time + timedelta(days=1), False)
                            return True

            except sqlite3.Error as e:
                if "database is locked" in str(e) or "busy" in str(e).lower():
                    logging.warning(f"Database is locked/busy, retrying (attempt {attempt+1}/{max_attempts}): {str(e)}")
                else:
                    logging.error(f"Database error checking license for user_id {user_id}: {str(e)}")

                if attempt < max_attempts - 1:
                    # Progressive backoff with randomization to prevent thundering herd
                    import random
                    retry_delay = (attempt+1)*2 + random.uniform(0, 1)  
                    logging.info(f"Retrying in {retry_delay:.2f} seconds...")
                    import asyncio
                    await asyncio.sleep(retry_delay)
                else:
                    # On last attempt, temporarily grant access rather than blocking users
                    logging.warning(f"All database attempts failed for user {user_id}, temporarily allowing access")
                    # Special handling for deployment transitions - grant longer temp access
                    cache_duration = timedelta(minutes=30) if (is_deployment or is_starting) else timedelta(minutes=5)
                    LicenseManager._license_cache[user_id_str] = (current_time + cache_duration, False)
                    return True
            except Exception as e:
                logging.error(f"Unexpected error checking license for user_id {user_id}: {str(e)}")
                if attempt == max_attempts - 1:
                    # Only grant access during deployment or startup
                    if is_deployment or is_starting:
                        cache_duration = timedelta(minutes=15)
                        LicenseManager._license_cache[user_id_str] = (current_time + cache_duration, False)
                        return {"active": True}
                    # Properly deny access in normal operation
                    logging.info(f"Access denied for user {user_id} - unexpected error during license check")
                    return False

                retry_delay = (attempt+1)*1.5
                await asyncio.sleep(retry_delay)

        # This shouldn't be reached normally, but just in case
        logging.warning(f"License check for user {user_id} fell through to default case")
        # Only grant temporary access during deployment or startup
        if is_deployment or is_starting:
            # Cache for 10 minutes during uncertain times
            LicenseManager._license_cache[user_id_str] = (current_time + timedelta(minutes=10), False)
            return True
        # Properly deny access in normal operation
        logging.info(f"Access denied for user {user_id} - license check reached default case")
        return False