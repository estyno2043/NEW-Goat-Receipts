import discord
from datetime import datetime, timedelta
import asyncio
import json
import logging
from utils.mongodb_manager import mongo_manager

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
        now = datetime.utcnow()

        # Get all expired licenses from MongoDB
        expired_licenses = mongo_manager.get_expired_licenses()

        # Load config to get the default role ID
        with open("config.json", "r") as f:
            config = json.load(f)
            default_role_id = int(config.get("Client_ID"))

        for license_doc in expired_licenses:
            owner_id = license_doc.get("owner_id")
            expiry_str = license_doc.get("expiry")
            key = license_doc.get("key", "")

            try:
                # Parse expiry date
                expiry_date = datetime.strptime(expiry_str, '%d/%m/%Y %H:%M:%S')

                # Check if license has expired
                if now > expiry_date:
                    user_id = int(owner_id)

                    # Determine subscription type for display
                    display_type = "Unknown"
                    if key:
                        if "LifetimeKey" in key:
                            display_type = "Lifetime"
                        elif "1Month" in key or "1month" in key:
                            display_type = "1 Month"
                        elif "14Days" in key or "14day" in key:
                            display_type = "14 Days"
                        elif "3Days" in key or "3day" in key:
                            display_type = "3 Days"
                        elif "1Day" in key or "1day" in key:
                            display_type = "1 Day"

                    # COMPLETELY REMOVE USER FROM DATABASE
                    try:
                        # Remove from MongoDB
                        mongo_manager.delete_license(owner_id)
                        mongo_manager.delete_user_credentials(owner_id)
                        mongo_manager.delete_user_email(owner_id)

                        # Clear from license cache
                        if owner_id in self._license_cache:
                            del self._license_cache[owner_id]

                        logging.info(f"Completely removed user {owner_id} from database due to expired license")
                    except Exception as db_error:
                        logging.error(f"Error removing user {owner_id} from database: {db_error}")

                    # Find the user in all guilds and remove roles
                    member_found = False
                    for guild in self.bot.guilds:
                        # Get server-specific role ID if available
                        db = mongo_manager.get_database()
                        if db:
                            server_config = db.server_configs.find_one({"guild_id": str(guild.id)})
                            role_id = None
                            if server_config and server_config.get("client_id"):
                                try:
                                    role_id = int(server_config["client_id"])
                                except (ValueError, TypeError):
                                    pass

                        if role_id is None:
                            role_id = default_role_id

                        # Find the member in this guild
                        member = guild.get_member(user_id)
                        if not member:
                            continue

                        member_found = True

                        # Remove all relevant roles
                        try:
                            # Remove client role
                            role = discord.utils.get(guild.roles, id=role_id)
                            if role and role in member.roles:
                                await member.remove_roles(role)
                                logging.info(f"Removed client role {role.name} from {member.name} due to expired license")

                            # Remove subscription-specific roles
                            month_role = discord.utils.get(guild.roles, id=1372256426684317909)
                            if month_role and month_role in member.roles:
                                await member.remove_roles(month_role)
                                logging.info(f"Removed 1 month role from {member.name} due to expired license")

                            lifetime_role = discord.utils.get(guild.roles, id=1372256491729453168)
                            if lifetime_role and lifetime_role in member.roles:
                                await member.remove_roles(lifetime_role)
                                logging.info(f"Removed lifetime role from {member.name} due to expired license")

                        except Exception as role_error:
                            logging.error(f"Error removing roles from {member.name}: {role_error}")

                    # Send expiration notifications (only once, not per guild)
                    if member_found:
                        try:
                            # Get the member object for notifications (from any guild)
                            notification_member = None
                            for guild in self.bot.guilds:
                                member = guild.get_member(user_id)
                                if member:
                                    notification_member = member
                                    break

                            if notification_member:
                                # Create DM embed
                                dm_embed = discord.Embed(
                                    title="Your Subscription Has Expired",
                                    description=f"Hello {notification_member.mention},\n\nYour subscription has expired. We appreciate your support!\n\nIf you'd like to renew, click the button below.",
                                    color=discord.Color.default()
                                )

                                # Create purchases channel embed
                                purchases_embed = discord.Embed(
                                    title="Subscription Expired",
                                    description=f"{notification_member.mention}, your subscription has expired. Thank you for purchasing.\n-# Consider renewing below!\n\n**Subscription Type**\n`{display_type}`\n\nPlease consider leaving a review at <#1339306483816337510>",
                                    color=discord.Color.default()
                                )

                                # Create renewal buttons
                                dm_view = discord.ui.View()
                                dm_view.add_item(discord.ui.Button(label="Renew", style=discord.ButtonStyle.link, url="https://goatreceipts.com"))

                                purchases_view = discord.ui.View()
                                purchases_view.add_item(discord.ui.Button(label="Renew", style=discord.ButtonStyle.link, url="https://goatreceipts.com"))

                                # Try to DM the user
                                try:
                                    await notification_member.send(embed=dm_embed, view=dm_view)
                                    logging.info(f"Sent expiration DM to {notification_member.name}")
                                except:
                                    logging.info(f"Could not DM {notification_member.name} about expired license")

                                # Send notification to Purchases channel
                                try:
                                    purchases_channel = self.bot.get_channel(1374468080817803264)
                                    if purchases_channel:
                                        await purchases_channel.send(content=notification_member.mention, embed=purchases_embed, view=purchases_view)
                                        logging.info(f"Sent expiration notification to purchases channel for {notification_member.name}")
                                except Exception as channel_error:
                                    logging.error(f"Could not send expiry notification to Purchases channel: {channel_error}")

                        except Exception as notification_error:
                            logging.error(f"Error sending expiration notifications: {notification_error}")

                except Exception as e:
                    logging.error(f"Error processing license for user {owner_id}: {str(e)}")

        except Exception as e:
            logging.error(f"Error in check_expired_licenses: {str(e)}")

    # Cache to store known valid licenses during deployment transitions
    _license_cache = {}
    _last_cache_cleanup = datetime.utcnow()
    _cache_cleanup_interval = 3600  # Clean cache every hour
    _initialization_complete = False
    _cache_lock = asyncio.Lock()

    @staticmethod
    async def is_subscription_active(user_id):
        """Check if a user has an active subscription using MongoDB."""
        logging.info(f"Checking subscription for user_id: {user_id}")

        # Check if user is in cache with valid license
        current_time = datetime.utcnow()
        user_id_str = str(user_id)

        # Clean up expired cache entries periodically
        if (current_time - LicenseManager._last_cache_cleanup).total_seconds() > LicenseManager._cache_cleanup_interval:
            try:
                async with LicenseManager._cache_lock:
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

        # Check cache first
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
            LicenseManager._license_cache[user_id_str] = (current_time + timedelta(days=365), True)
            return True

        # Check if this is the bot owner
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                if user_id_str == config.get("owner_id"):
                    logging.info(f"User {user_id} is the bot owner - granting access")
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
                        try:
                            # Try to get server-specific role ID from MongoDB
                            db = mongo_manager.get_database()
                            server_config = db.server_configs.find_one({"guild_id": str(guild.id)})

                            guild_role_id = None
                            if server_config and server_config.get("client_id"):
                                try:
                                    guild_role_id = int(server_config["client_id"])
                                    logging.info(f"Found server-specific role ID: {guild_role_id}")
                                except (ValueError, TypeError):
                                    logging.warning(f"Invalid server-specific role ID for guild {guild.id}")

                            if guild_role_id is None:
                                guild_role_id = client_role_id
                                logging.info(f"Using default role ID from config: {guild_role_id}")

                            # Check if user has the role in this guild
                            member = guild.get_member(int(user_id))
                            if member:
                                role = discord.utils.get(guild.roles, id=guild_role_id)
                                if role and role in member.roles:
                                    logging.info(f"User {user_id} has client role in guild {guild.id}")
                                    LicenseManager._license_cache[user_id_str] = (current_time + timedelta(minutes=30), False)
                                    return True
                        except Exception as e:
                            logging.error(f"Error checking roles in guild {guild.id}: {str(e)}")
        except Exception as e:
            logging.error(f"Error checking config for owner: {str(e)}")

        # Check MongoDB for license
        try:
            license_doc = mongo_manager.get_license(user_id)

            if not license_doc:
                logging.info(f"No license found for user_id: {user_id}")
                return False

            expiry_str = license_doc.get("expiry")
            key = license_doc.get("key", "")

            # Check if license is explicitly marked as expired
            if key and key.startswith("EXPIRED-"):
                logging.info(f"Expired key found for user_id: {user_id}")
                return {"active": False, "expired_date": expiry_str}

            # Lifetime keys are always active
            if key and ("LifetimeKey" in key or "lifetime" in key.lower() or "owner-key" in key):
                logging.info(f"Lifetime key found for user_id: {user_id}")
                LicenseManager._license_cache[user_id_str] = (current_time + timedelta(days=3650), True)
                return True

            # Check expiry date
            try:
                if not expiry_str:
                    logging.warning(f"Empty expiry date for user_id {user_id}, treating as expired")
                    return False

                expiry_date = datetime.strptime(expiry_str, '%d/%m/%Y %H:%M:%S')
                is_active = current_time < expiry_date
                logging.info(f"License for user_id {user_id} active: {is_active}, expires: {expiry_str}")

                # Cache valid licenses
                if is_active:
                    LicenseManager._license_cache[user_id_str] = (expiry_date - timedelta(hours=1), False)
                else:
                    return {"active": False, "expired_date": expiry_str}

                return is_active
            except Exception as e:
                logging.warning(f"Error parsing expiry date for user_id {user_id}: {str(e)}")
                if key:
                    LicenseManager._license_cache[user_id_str] = (current_time + timedelta(days=1), False)
                    return True

        except Exception as e:
            logging.error(f"Error checking license in MongoDB for user_id {user_id}: {str(e)}")
            return False

        logging.info(f"Access denied for user {user_id} - no valid license found")
        return False