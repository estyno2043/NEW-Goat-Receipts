import os
import discord
import random
import datetime
import json
import logging
import sqlite3
from datetime import datetime, timedelta
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from discord import app_commands, ui
from discord.ext import commands
from dotenv import load_dotenv
from templates import get_all_templates
import asyncio

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
# Try using privileged intents if enabled in the developer portal
try:
    intents.message_content = True
except:
    print("Warning: Message content intent not available. Some features may not work.")
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize receipt processing utilities
try:
    from utils.receipt_processor import patched_open
    from utils.template_utils import replace_user_details
    from utils.guild_license_checker import GuildLicenseChecker
    print("Receipt processing utilities initialized successfully")
except Exception as e:
    print(f"Failed to initialize receipt processing utilities: {e}")

# Setup MongoDB connection
from utils.mongodb_manager import mongo_manager

# Initialize message filter
from utils.message_filter import MessageFilter
message_filter = None

# Background task to process notifications
async def process_notifications():
    """Background task to process webhook notifications"""
    await bot.wait_until_ready()

    while not bot.is_closed():
        try:
            db = mongo_manager.get_database()
            if db:
                # Get pending notifications
                notifications = list(db.notifications.find({"processed": {"$ne": True}}).limit(10))

                for notification in notifications:
                    try:
                        if notification.get("type") == "access_granted":
                            await handle_access_granted_notification(notification)

                        # Mark as processed
                        db.notifications.update_one(
                            {"_id": notification["_id"]},
                            {"$set": {"processed": True, "processed_at": datetime.utcnow()}}
                        )

                    except Exception as e:
                        logging.error(f"Error processing notification {notification.get('_id')}: {e}")
                        # Mark as failed
                        db.notifications.update_one(
                            {"_id": notification["_id"]},
                            {"$set": {"processed": True, "failed": True, "error": str(e)}}
                        )

        except Exception as e:
            logging.error(f"Error in notification processor: {e}")

        await asyncio.sleep(5)  # Check every 5 seconds

async def handle_access_granted_notification(notification):
    """Handle access granted notifications"""
    try:
        user_id = notification.get("user_id")
        username = notification.get("username", "Unknown User")
        guild_id = notification.get("guild_id")
        guild_name = notification.get("guild_name", "Unknown Guild")
        access_duration = notification.get("access_duration", 1)
        source = notification.get("source", "invite-tracker")

        # Try to get the user
        user = bot.get_user(int(user_id))
        if not user:
            try:
                user = await bot.fetch_user(int(user_id))
            except:
                user = None

        # Try to get the guild
        guild = bot.get_guild(int(guild_id))

        # Load config to get main guild ID and purchases channel
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                main_guild_id = config.get("guild_id", "1412488621293961226")
        except Exception as e:
            print(f"Error loading config: {e}")
            main_guild_id = "1412488621293961226"

        # Check if this is for the main guild
        is_main_guild = (str(guild_id) == main_guild_id)

        # Send notification to the main guild's purchases channel
        try:
            main_guild = bot.get_guild(int(main_guild_id))
            if main_guild:
                # Use the hardcoded purchases channel ID
                purchases_channel = main_guild.get_channel(1402938227962417222)

                if purchases_channel:
                    # Create "thank you for purchasing" style notification
                    embed = discord.Embed(
                        title="Thank you for purchasing",
                        description=f"{f'<@{user_id}>' if user else username}, your subscription has been updated. Check below\n"
                                  f"-# Run command /generate in <#1350413411455995904> to continue\n\n"
                                  f"**Subscription Type**\n"
                                  f"`{access_duration} Day{'s' if access_duration != 1 else ''} (Invite Reward)`\n\n"
                                  f"**Server Access**\n"
                                  f"`{guild_name}`\n\n"
                                  f"- Please consider leaving a review at <#1350413086074474558>",
                        color=discord.Color.green()
                    )

                    await purchases_channel.send(content=f"<@{user_id}>" if user else username, embed=embed)
                    logging.info(f"Sent invite reward notification to purchases channel for user {user_id}")
                else:
                    logging.warning(f"Purchases channel not found in main guild")
        except Exception as e:
            logging.error(f"Error sending notification to main guild purchases channel: {e}")

        # Send DM to user
        if user:
            try:
                embed = discord.Embed(
                    title="🎉 Thank You for Your Purchase!",
                    description=f"Your {access_duration}-day access to **{guild_name}** has been activated!",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="Access Details",
                    value=f"• **Duration:** {access_duration} days\n• **Server:** {guild_name}\n• **Source:** {source}",
                    inline=False
                )
                embed.add_field(
                    name="What's Next?",
                    value="You can now use the receipt generator bot commands in the server. Enjoy your access!",
                    inline=False
                )
                embed.set_footer(text="Thank you for your business!")

                await user.send(embed=embed)
                logging.info(f"Sent thank you DM to user {user_id}")

            except discord.Forbidden:
                logging.warning(f"Could not send DM to user {user_id} - DMs disabled")
            except Exception as e:
                logging.error(f"Error sending DM to user {user_id}: {e}")

        # Also send notification to the target guild if it's not the main guild
        if not is_main_guild and guild:
            try:
                # Look for a purchases/notifications channel in the target guild
                purchases_channel = None
                for channel in guild.text_channels:
                    if any(name in channel.name.lower() for name in ['purchase', 'notification', 'access', 'grant']):
                        purchases_channel = channel
                        break

                if purchases_channel:
                    embed = discord.Embed(
                        title="✅ Access Granted via Invite Tracker",
                        description=f"**{username}** has been granted access via invite rewards",
                        color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="User Details",
                        value=f"• **User:** <@{user_id}> ({username})\n• **User ID:** {user_id}",
                        inline=False
                    )
                    embed.add_field(
                        name="Access Details",
                        value=f"• **Duration:** {access_duration} days\n• **Source:** {source}\n• **Guild:** {guild_name}",
                        inline=False
                    )
                    embed.set_footer(text=f"Granted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                    await purchases_channel.send(embed=embed)
                    logging.info(f"Sent guild notification to {purchases_channel.name}")

            except Exception as e:
                logging.error(f"Error sending guild notification: {e}")

    except Exception as e:
        logging.error(f"Error handling access granted notification: {e}")

# Start notification processor
@bot.event
async def on_ready():
    global message_filter
    print(f'{bot.user} has connected to Discord!')

    # Initialize message filter
    message_filter = MessageFilter(bot)
    print("Message filter initialized")

    # Load command extensions
    try:
        # Load admin commands
        await bot.load_extension("commands.admin_commands")
        print("Loaded admin commands")

        # Load guild commands
        await bot.load_extension("commands.guild_commands")
        print("Loaded guild commands")
    except Exception as e:
        print(f"Failed to load commands: {e}")

    # Sync commands
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

    # Start background tasks
    bot.loop.create_task(process_notifications())
    print("Notification processor started")

# Setup MongoDB connection
def setup_database():
    """Initialize MongoDB connection and collections"""
    try:
        from utils.mongodb_manager import mongo_manager
        # Test the connection by getting the database
        db = mongo_manager.get_database()

        if db is not None:
            # Insert default system config if not exists
            try:
                system_config = db.system_config.find_one({"key": "total_brands"})
                if not system_config:
                    db.system_config.insert_one({"key": "total_brands", "value": "100"})
            except Exception as config_e:
                logging.warning(f"Could not setup system config: {config_e}")

            logging.info("MongoDB setup completed successfully")
        else:
            logging.warning("MongoDB connection failed, but bot will continue running with limited functionality")
    except Exception as e:
        logging.warning(f"MongoDB setup failed: {e}, bot will continue running with limited functionality")

# Generate random details for users
def generate_random_details():
    first_names = ["John", "Jane", "Michael", "Emma", "David", "Sarah", "Robert", "Lisa", "Kevin", "Amanda"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Taylor", "Clark"]
    streets = ["Oak Street", "Maple Avenue", "Pine Road", "Cedar Lane", "Elm Boulevard", "Willow Drive", "Birch Court", "Cypress Way", "Park Avenue", "Main Street"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas", "Boston"]
    zips = ["10001", "90001", "60601", "77001", "85001", "19101", "78201", "92101", "75201", "02108"]
    countries = ["United States", "Canada", "United Kingdom", "Australia", "Germany", "France", "Spain", "Italy", "Japan", "Sweden"]

    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    street = f"{random.randint(100, 9999)} {random.choice(streets)}"
    city = random.choice(cities)
    zip_code = random.choice(zips)
    country = random.choice(countries)

    return name, street, city, zip_code, country

# Check if user has credentials and email set
def check_user_setup(user_id):
    from utils.db_utils import check_user_setup as mongo_check_user_setup
    return mongo_check_user_setup(user_id)

# Add or update user subscription
def update_subscription(user_id, subscription_type="Unlimited", days=365):
    from utils.db_utils import update_subscription as mongo_update_subscription
    return mongo_update_subscription(user_id, subscription_type, days)

# Get user subscription info
def get_subscription(user_id):
    from utils.db_utils import get_subscription as mongo_get_subscription
    return mongo_get_subscription(user_id)

# Get total brands count
def get_total_brands():
    # Count actual available modal files
    import os
    modal_files = [f for f in os.listdir('modals') if f.endswith('.py') and not f.startswith('__')]
    count = len(modal_files)

    # Update the count in the database
    try:
        from utils.mongodb_manager import mongo_manager
        db = mongo_manager.get_database()
        if db is not None:
            db.system_config.update_one(
                {"key": "total_brands"},
                {"$set": {"key": "total_brands", "value": str(count)}},
                upsert=True
            )
    except Exception as e:
        print(f"Error updating total brands count: {e}")

    return str(count)

# Custom email form
class EmailForm(ui.Modal, title="Email Settings"):
    email = ui.TextInput(label="Email", placeholder="example@gmail.com", required=True)

    def is_icloud_email(self, email):
        """Check if the email is an iCloud email address"""
        return "@icloud" in email.lower()

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        email = self.email.value

        # Check if the email is an iCloud email address
        if self.is_icloud_email(email):
            embed = discord.Embed(
                title="Email Not Saved",
                description="Your iCloud email was not saved since receipt delivery to iCloud mail won't function. Please change it to **Gmail, Outlook or Yahoo** for successful delivery.\n\n-# This way you won't waste your limit",
                color=discord.Color.from_str("#c2ccf8")
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Save email to MongoDB with 7-day restriction check
        from utils.mongodb_manager import mongo_manager
        result = mongo_manager.save_user_email(user_id, email)

        if not result.get("success"):
            if result.get("error") == "email_change_restricted":
                days_remaining = result.get("days_remaining", 0)
                embed = discord.Embed(
                    title="Email Change Restricted",
                    description=f"You can only change your email once every 7 days. Please wait {days_remaining} more day(s) before changing your email again.\n\n-# This restriction prevents receipt sharing between accounts.",
                    color=discord.Color.orange()
                )
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Failed to save email. Please try again later.",
                    color=discord.Color.red()
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Send success message to user
        success_embed = discord.Embed(
            title="Email Saved",
            description=f"Your email has been saved successfully.\n\n-# Your email has been set to: `{email}`",
            color=discord.Color.from_str("#c2ccf8")
        )
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

        # Update the credentials panel in real-time
        try:
            # Get the original message that showed the credentials panel
            # Use followup to get the original message that opened this modal
            original_message = interaction.message

            if original_message:
                # Create updated credentials panel with refreshed data
                has_credentials, has_email = check_user_setup(user_id)

                # Create updated credentials panel
                updated_embed = discord.Embed(
                    title="Credentials",
                    description="Please make sure both options below are 'True'\n\n" +
                                "**Info**\n" +
                                f"{'True' if has_credentials else 'False'}\n\n" +
                                "**Email**\n" +
                                f"{'True' if has_email else 'False'}",
                    color=discord.Color.from_str("#c2ccf8")
                )

                # Update the original credentials panel
                await original_message.edit(embed=updated_embed)
                print(f"Successfully updated credentials panel for user {user_id}")
            else:
                print(f"Could not find original message to update for user {user_id}")

        except Exception as e:
            print(f"Failed to update credentials panel in real-time: {e}")

            # Fallback: Try to find the credentials panel in recent messages
            try:
                for channel in interaction.guild.text_channels:
                    async for message in channel.history(limit=25):
                        if (message.author == interaction.client.user and
                            message.embeds and
                            len(message.embeds) > 0 and
                            message.embeds[0].title == "Credentials"):

                            # Update found credentials panel
                            has_credentials, has_email = check_user_setup(user_id)
                            updated_embed = discord.Embed(
                                title="Credentials",
                                description="Please make sure both options below are 'True'\n\n" +
                                            "**Info**\n" +
                                            f"{'True' if has_credentials else 'False'}\n\n" +
                                            "**Email**\n" +
                                            f"{'True' if has_email else 'False'}",
                                color=discord.Color.from_str("#c2ccf8")
                            )
                            await message.edit(embed=updated_embed)
                            print(f"Found and updated credentials panel in channel history for user {user_id}")
                            break
            except Exception as search_error:
                print(f"Error while searching for credentials panel: {search_error}")

# Custom info form
class CustomInfoForm(ui.Modal, title="Set up your Information"):
    name = ui.TextInput(label="Name", placeholder="John Doe", required=True)
    street = ui.TextInput(label="Street", placeholder="123 Main St", required=True)
    city = ui.TextInput(label="City", placeholder="New York", required=True)
    zip_code = ui.TextInput(label="Zip", placeholder="10001", required=True)
    country = ui.TextInput(label="Country", placeholder="United States", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # Save custom info to MongoDB
        from utils.db_utils import save_user_credentials, clear_user_data, get_user_details, check_user_setup
        success = save_user_credentials(
            user_id,
            self.name.value,
            self.street.value,
            self.city.value,
            self.zip_code.value,
            self.country.value,
            is_random=False
        )

        if not success:
            embed = discord.Embed(
                title="Error",
                description="Failed to save credentials. Please try again later.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Send success message to the user
        success_embed = discord.Embed(
            title="Success",
            description="-# Your custom information has been saved.",
            color=discord.Color.from_str("#c2ccf8")
        )
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

        # Update the credentials panel in real-time
        has_credentials, has_email = check_user_setup(user_id)

        # Create updated credentials panel
        updated_embed = discord.Embed(
            title="Credentials",
            description="Please make sure both options below are 'True'\n\n" +
                        "**Info**\n" +
                        f"{'True' if has_credentials else 'False'}\n\n" +
                        "**Email**\n" +
                        f"{'True' if has_email else 'False'}",
            color=discord.Color.from_str("#c2ccf8")
        )

        # Get the original message that showed the credentials panel
        try:
            # Try to find the original message in the interaction's message history
            original_message = None
            for message in interaction.channel.history(limit=10):
                if message.author == interaction.client.user and message.embeds and message.embeds[0].title == "Credentials":
                    original_message = message
                    break

            if original_message:
                await original_message.edit(embed=updated_embed)
        except Exception as e:
            print(f"Failed to update credentials panel in real-time: {e}")

# Dropdown for brand selection
class BrandSelectDropdown(ui.Select):
    def __init__(self, user_id, page=1):
        self.page = page
        self.user_id = user_id  # Store the owner's user ID

        # List only the brands that have actual modal implementations
        # This automatically detects brands from the modals directory
        import os
        available_brands = []
        seen_brand_names = set()  # Track brand names to avoid duplicates

        # Get modal files from the modals directory
        modal_files = [f for f in os.listdir('modals') if f.endswith('.py') and not f.startswith('__')]

        # Extract brand names from the filenames with proper naming
        for modal_file in modal_files:
            base_name = modal_file.split('.')[0]

            # Special case handling for specific brands
            if base_name == "crtz" or base_name == "corteiz":  # Handle both crtz.py and corteiz.py
                brand_name = "Corteiz"
            elif base_name == "houseoffrasers":
                brand_name = "House of Frasers"
            elif base_name == "istores":
                brand_name = "iStores"
            elif base_name == "lv":
                brand_name = "Louis Vuitton"
            elif base_name == "tnf":
                brand_name = "The North Face"
            elif base_name == "nosauce":
                brand_name = "No Sauce The Plug"
            elif base_name == "6pm":
                brand_name = "6PM"
            elif base_name == "sixpm":
                brand_name = "6PM"
            else:
                brand_name = base_name.capitalize()

            # Only add brand name if we haven't seen it before
            if brand_name not in seen_brand_names:
                available_brands.append(brand_name)
                seen_brand_names.add(brand_name)

        # Sort alphabetically
        available_brands.sort()

        # Show only 15 brands per page
        start_idx = (page - 1) * 15
        end_idx = min(start_idx + 15, len(available_brands))

        # If page is out of bounds, reset to page 1
        if start_idx >= len(available_brands):
            self.page = 1
            start_idx = 0
            end_idx = min(15, len(available_brands))

        current_brands = available_brands[start_idx:end_idx]

        # Make sure values are unique by adding index if needed
        options = []
        used_values = set()

        for idx, brand in enumerate(current_brands):
            value = brand.lower()
            # If value already exists, make it unique by adding index
            if value in used_values:
                value = f"{value}_{idx}"
            used_values.add(value)
            options.append(discord.SelectOption(label=brand, value=value))

        super().__init__(placeholder="Choose a brand...", min_values=1, max_values=1, options=options)
        self.user_id = user_id  # Store the owner's user ID

    async def callback(self, interaction: discord.Interaction):
        # Check if interaction is from panel owner
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This is not your panel", ephemeral=True)
            return

        brand = self.values[0]
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id if interaction.guild else "0")

        # Load config to get main guild ID
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                main_guild_id = config.get("guild_id", "1412488621293961226")
        except Exception as e:
            print(f"Error loading config: {e}")
            main_guild_id = "1412488621293961226"

        # Check if this is a guild-specific instance
        is_main_guild = (guild_id == main_guild_id)

        # Store the image channel ID for later use with URL handling
        image_channel_id = None
        if not is_main_guild:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT image_channel_id FROM guild_configs WHERE guild_id = ?", (guild_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                image_channel_id = result[0]

        # Check if user has both credentials and email set up
        has_credentials, has_email = check_user_setup(user_id)

        # Also verify the actual data exists
        if not is_main_guild:
            user_details = GuildLicenseChecker.get_user_details_guild(user_id, guild_id)
        else:
            from utils.db_utils import get_user_details
            user_details = get_user_details(user_id)

        print(f"Debug - User {user_id}: has_credentials={has_credentials}, has_email={has_email}")
        print(f"Debug - User {user_id}: user_details={user_details}")

        if not has_credentials or not has_email or not user_details:
            embed = discord.Embed(
                title="Setup Required",
                description="Please complete your setup before generating receipts.\n\n" +
                            f"**Info**: {'True' if has_credentials else 'False'}\n" +
                            f"**Email**: {'True' if has_email else 'False'}\n" +
                            f"**Data Valid**: {'True' if user_details else 'False'}",
                color=discord.Color.from_str("#c2ccf8")
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Process brand selection and show appropriate modal
        try:
            # Import the appropriate modal module dynamically based on brand name
            module_name = f"modals.{brand}"
            modal_class_name = f"{brand}modal"

            # Special case handling for brands with different modal class naming patterns
            special_cases = {
                "acnestudios": "acnestudiosmodal",
                "chromehearts": "chromemodal",
                "canadagoose": "canadagoose",
                "lv": "lvmodal",
                "tnf": "tnfmodal",
                "chewforever": "Chewforevermodal",
                "corteiz": "crtzmodal",
                "loropiana": "loromodal",
                "6pm": "sixpmmodal" # Add 6PM modal handling
            }

            if brand in special_cases:
                modal_class_name = special_cases[brand]

            # Dynamic import of the module
            try:
                import importlib

                # Handle special cases for brands with spaces in their names
                if brand == "House of Frasers" or brand.lower() == "house of frasers":
                    # Ensure the modal is properly loaded
                    try:
                        from modals.houseoffrasers import houseoffrasermodal
                        modal_class = houseoffrasermodal
                        modal = modal_class()
                        await interaction.response.send_modal(modal)
                        return
                    except Exception as e:
                        print(f"Error loading House of Frasers modal: {str(e)}")
                        await interaction.response.send_message(f"Error loading House of Frasers modal: {str(e)}", ephemeral=True)
                        return
                elif brand == "Louis Vuitton" or brand.lower() == "louis vuitton":
                    # Ensure the modal is properly loaded
                    try:
                        from modals.lv import lvmodal
                        modal_class = lvmodal
                        modal = modal_class()
                        # Add guild info if available
                        if hasattr(modal, 'guild_id'):
                            modal.guild_id = guild_id
                        if hasattr(modal, 'image_channel_id'):
                            modal.image_channel_id = image_channel_id
                        await interaction.response.send_modal(modal)
                        return
                    except Exception as e:
                        print(f"Error loading Louis Vuitton modal: {str(e)}")
                        await interaction.response.send_message(f"Error loading Louis Vuitton modal: {str(e)}", ephemeral=True)
                        return
                elif brand == "The North Face" or brand.lower() == "the north face":
                    # Ensure the modal is properly loaded
                    try:
                        from modals.tnf import tnfmodal
                        modal_class = tnfmodal
                        modal = modal_class()
                        await interaction.response.send_modal(modal)
                        return
                    except Exception as e:
                        print(f"Error loading The North Face modal: {str(e)}")
                        await interaction.response.send_message(f"Error loading The North Face modal: {str(e)}", ephemeral=True)
                        return
                elif brand == "Xerjoff" or brand.lower() == "xerjoff":
                    # Special handling for Xerjoff - use the main modal
                    try:
                        from modals.xerjoff import xerjoffmodal
                        modal = xerjoffmodal()
                        await interaction.response.send_modal(modal)
                        return
                    except Exception as e:
                        print(f"Error loading Xerjoff modal: {str(e)}")
                        await interaction.response.send_message(f"Error loading Xerjoff modal: {str(e)}", ephemeral=True)
                        return
                elif brand == "Zalandous" or brand.lower() == "zalandous":
                    # Ensure the modal is properly loaded
                    try:
                        # Import the modal with proper error handling
                        from modals.zalandous import zalandomodal
                        # Create instance and send modal
                        modal = zalandomodal()
                        await interaction.response.send_modal(modal)
                        return
                    except ImportError:
                        # Try alternative class name if first attempt fails
                        try:
                            from modals.zalandous import zalandousmodal
                            modal = zalandousmodal()
                            await interaction.response.send_modal(modal)
                            return
                        except Exception as e:
                            print(f"Error loading Zalandous modal (alt method): {str(e)}")
                            await interaction.response.send_message(f"Error loading Zalandous modal: {str(e)}", ephemeral=True)
                            return
                    except Exception as e:
                        print(f"Error loading Zalandous modal: {str(e)}")
                        await interaction.response.send_message(f"Error loading Zalandous modal: {str(e)}", ephemeral=True)
                        return
                elif brand == "No Sauce The Plug" or brand.lower() == "no sauce the plug":
                    # Ensure the modal is properly loaded
                    try:
                        from modals.nosauce import nosaucemodal
                        modal_class = nosaucemodal
                        modal = modal_class()
                        await interaction.response.send_modal(modal)
                        return
                    except Exception as e:
                        print(f"Error loading No Sauce The Plug modal: {str(e)}")
                        await interaction.response.send_message(f"Error loading No Sauce The Plug modal: {str(e)}", ephemeral=True)
                        return
                elif brand == "Corteiz":
                    module_name = "modals.crtz"
                    modal_class_name = "crtzmodal"
                elif brand == "Culture Kings":
                    module_name = "modals.culturekings"
                    modal_class_name = "ckmodal"
                    # Ensure the modal is properly loaded
                    try:
                        from modals.culturekings import ckmodal
                        modal_class = ckmodal
                        modal = modal_class()
                        await interaction.response.send_modal(modal)
                        return
                    except Exception as e:
                        await interaction.response.send_message(f"Error loading Culture Kings modal: {str(e)}", ephemeral=True)
                        return
                elif brand == "Dyson":
                    module_name = "modals.dyson"
                    modal_class_name = "dysonmodal"
                    # Ensure the modal is properly loaded
                    try:
                        from modals.dyson import dysonmodal
                        modal_class = dysonmodal
                        modal = modal_class()
                        await interaction.response.send_modal(modal)
                        return
                    except Exception as e:
                        await interaction.response.send_message(f"Error loading Dyson modal: {str(e)}", ephemeral=True)
                        return
                elif brand == "Goat":
                    module_name = "modals.goat"
                    modal_class_name = "goatmodal"
                    # Ensure the modal is properly loaded
                    try:
                        from modals.goat import goatmodal
                        modal_class = goatmodal
                        modal = modal_class()
                        await interaction.response.send_modal(modal)
                        return
                    except Exception as e:
                        await interaction.response.send_message(f"Error loading Goat modal: {str(e)}", ephemeral=True)
                        return
                elif brand == "goyard" or brand.lower() == "goyard":
                    # Special handling for Goyard with Purchase/Request options
                    try:
                        from modals.goyard import GoyardTypeView
                        embed = discord.Embed(
                            title="Goyard - Select Type",
                            description="Choose the type of Goyard receipt you want to generate:",
                            color=discord.Color.from_str("#c2ccf8")
                        )
                        view = GoyardTypeView(interaction.user.id)
                        await interaction.response.edit_message(embed=embed, view=view)
                        return
                    except Exception as e:
                        await interaction.response.send_message(f"Error loading Goyard options: {str(e)}", ephemeral=True)
                        return
                elif brand == "Ebayconf" or brand.lower() == "ebayconf":
                    # Special handling for Ebayconf
                    try:
                        from modals.ebayconf import EbayConfModal
                        modal = EbayConfModal()
                        modal.guild_id = guild_id
                        modal.image_channel_id = image_channel_id
                        await interaction.response.send_modal(modal)
                        return
                    except Exception as e:
                        await interaction.response.send_message(f"Error loading Ebayconf modal: {str(e)}", ephemeral=True)
                        return
                elif brand == "Loropiana" or brand == "Loro Piana":
                    # Special handling for Loro Piana
                    try:
                        # Import the module first, then access the class
                        import importlib
                        loro_module = importlib.import_module("modals.loropiana")
                        # Make sure to access the class correctly with the right case sensitivity
                        if hasattr(loro_module, "loromodal"):
                            modal_class = getattr(loro_module, "loromodal")
                            modal = modal_class()
                            await interaction.response.send_modal(modal)
                            return
                        else:
                            # Fallback to manual import if needed
                            from modals.loropiana import loromodal
                            modal = loromodal()
                            await interaction.response.send_modal(modal)
                            return
                    except Exception as e:
                        print(f"Error loading Loro Piana modal: {str(e)}")
                        await interaction.response.send_message(f"Error loading Loro Piana modal: {str(e)}", ephemeral=True)
                        return
                elif brand == "Maison Margiela" or brand.lower() == "maisonmargiela":
                    # Special handling for Maison Margiela
                    try:
                        from modals.maisonmargiela import maisonmodal as MaisonMargielaModal
                        modal = MaisonMargielaModal()
                        await interaction.response.send_modal(modal)
                        return
                    except Exception as e:
                        print(f"Error loading Maison Margiela modal: {str(e)}")
                        # Try alternative approach
                        try:
                            from modals.maisonmargiela import maisonmargielamodal
                            modal = maisonmargielamodal()
                            await interaction.response.send_modal(modal)
                            return
                        except Exception as nested_e:
                            print(f"Alternative approach failed: {str(nested_e)}")
                            await interaction.response.send_message(f"Error loading Maison Margiela modal: {str(e)}", ephemeral=True)
                            return
                elif brand == "Amazon UK":
                    module_name = "modals.amazonuk"
                    modal_class_name = "amazonukmodal"
                elif brand == "6PM" or brand.lower() == "6pm":
                    module_name = "modals.6pm"
                    modal_class_name = "sixpmmodal"

                modal_module = importlib.import_module(module_name)

                # Get the modal class dynamically
                modal_class = getattr(modal_module, modal_class_name)

                # Create the modal instance
                modal = modal_class()

                # Store the guild and image channel info for the modal to use
                if hasattr(modal, "set_guild_info"):
                    modal.set_guild_info(guild_id, image_channel_id)

                # For modals that don't have the method, monkey patch it
                # This is needed because we can't modify all the modal classes
                modal.guild_id = guild_id
                modal.image_channel_id = image_channel_id

                # Show the modal to the user
                await interaction.response.send_modal(modal)

            except (ImportError, AttributeError) as e:
                print(f"Error loading modal for {brand}: {e}")
                # Fallback message if modal can't be loaded
                embed = discord.Embed(
                    title="Modal Unavailable",
                    description=f"The receipt form for **{brand.capitalize()}** couldn't be loaded. Please try another brand.",
                    color=discord.Color.from_str("#c2ccf8")
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Error processing brand selection: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while processing your selection. Please try again later.",
                color=discord.Color.from_str("#c2ccf8")
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

# View for the brand selection
class BrandSelectView(ui.View):
    def __init__(self, user_id, page=1):
        super().__init__(timeout=300)  # Set timeout to 5 minutes
        self.user_id = user_id
        self.page = page
        self.add_item(BrandSelectDropdown(user_id, page))
        self.last_interaction = datetime.now()
        self.message = None

    async def interaction_check(self, interaction):
        # Update last interaction time on every interaction
        self.last_interaction = datetime.now()
        # Reset timeout on interaction
        self._timeout_expiry = discord.utils.utcnow() + timedelta(seconds=self.timeout)
        # Check if the interaction is from the original user
        return interaction.user.id == int(self.user_id)

    async def on_timeout(self):
        # Create timeout embed
        timeout_embed = discord.Embed(
            title="Interaction Timeout",
            description="The panel has timed out due to inactivity and is no longer active.",
            color=discord.Color.from_str("#c2ccf8")
        )

        # Try to edit the message with the timeout embed
        try:
            if self.message:
                await self.message.edit(embed=timeout_embed, view=None)
        except Exception as e:
            print(f"Error in timeout handling: {e}")

    @ui.button(label="Previous", style=discord.ButtonStyle.blurple, custom_id="previous")
    async def previous_page(self, interaction: discord.Interaction, button: ui.Button):
        # Get total number of brands to calculate max pages
        import os
        modal_files = [f for f in os.listdir('modals') if f.endswith('.py') and not f.startswith('__')]
        total_count = len(modal_files)
        max_pages = (total_count + 14) // 15  # Ceiling division to get number of pages

        if self.page > 1:
            self.page -= 1

            # Get user info
            username = interaction.user.display_name
            total_brands = get_total_brands()

            # Create new embed and view
            embed = discord.Embed(
                title=f"{username}'s Panel",
                description=f"Choose the type of receipt from the dropdown menu below. `(Total: {total_brands})`\n-# Page {self.page}/{max_pages if max_pages > 0 else 1}",
                color=discord.Color.from_str("#c2ccf8")
            )

            new_view = BrandSelectView(self.user_id, self.page)
            await interaction.response.edit_message(embed=embed, view=new_view)
        else:
            await interaction.response.send_message("You're already on the first page!", ephemeral=True)

    @ui.button(label="Next Brands", style=discord.ButtonStyle.blurple, custom_id="next")
    async def next_page(self, interaction: discord.Interaction, button: ui.Button):
        # Get total number of brands to calculate max pages
        import os
        modal_files = [f for f in os.listdir('modals') if f.endswith('.py') and not f.startswith('__')]
        total_count = len(modal_files)
        max_pages = (total_count + 14) // 15  # Ceiling division to get number of pages

        # Only increment page if not at last page
        if self.page < max_pages or max_pages == 0:
            self.page += 1

            # Get user info
            username = interaction.user.display_name
            total_brands = get_total_brands()

            # Create new embed and view
            embed = discord.Embed(
                title=f"{username}'s Panel",
                description=f"Choose the type of receipt from the dropdown menu below. `(Total: {total_brands})`\n-# Page {self.page}/{max_pages if max_pages > 0 else 1}",
                color=discord.Color.from_str("#c2ccf8")
            )

            new_view = BrandSelectView(self.user_id, self.page)
            await interaction.response.edit_message(embed=embed, view=new_view)
        else:
            await interaction.response.send_message("You're already on the last page!", ephemeral=True)

    @ui.button(label="Close", style=discord.ButtonStyle.danger, custom_id="close")
    async def close_menu(self, interaction: discord.Interaction, button: ui.Button):
        embed = discord.Embed(
            title="Menu Closed",
            description="The panel is no longer active.",
            color=discord.Color.from_str("#c2ccf8")
        )
        await interaction.response.edit_message(embed=embed, view=None)

# View for the main menu
class MenuView(ui.View):

    async def interaction_check(self, interaction):
        # Update last interaction time on every interaction
        self.last_interaction = datetime.now()
        # Reset timeout on interaction
        self._timeout_expiry = discord.utils.utcnow() + timedelta(seconds=self.timeout)
        # Check if the interaction is from the original user
        return interaction.user.id == int(self.user_id)

    async def on_timeout(self):
        # Create timeout embed
        timeout_embed = discord.Embed(
            title="Interaction Timeout",
            description="The panel has timed out due to inactivity and is no longer active.",
            color=discord.Color.from_str("#c2ccf8")
        )

        # Try to edit the message with the timeout embed
        try:
            if self.message:
                await self.message.edit(embed=timeout_embed, view=None)
        except Exception as e:
            print(f"Error in timeout handling: {e}")

    @ui.button(label="Generate", style=discord.ButtonStyle.secondary)
    async def generate_button(self, interaction: discord.Interaction, button: ui.Button):
        # Check if user has credentials and email
        user_id = str(interaction.user.id)
        has_credentials, has_email = check_user_setup(user_id)

        if not has_credentials or not has_email:
            embed = discord.Embed(
                title="Setup Required",
                description="Please complete your setup before generating receipts.\n\n" +
                            f"**Info**: {'True' if has_credentials else 'False'}\n" +
                            f"**Email**: {'True' if has_email else 'False'}",
                color=discord.Color.from_str("#c2ccf8")
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Show generator panel
        username = interaction.user.display_name
        total_brands = get_total_brands()

        # Calculate max pages
        import os
        modal_files = [f for f in os.listdir('modals') if f.endswith('.py') and not f.startswith('__')]
        total_count = len(modal_files)
        max_pages = (total_count + 14) // 15  # Ceiling division to get number of pages

        embed = discord.Embed(
            title=f"{username}'s Panel",
            description=f"Choose the type of receipt from the dropdown menu below. `(Total: {total_brands})`\n-# Page 1/{max_pages if max_pages > 0 else 1}",
            color=discord.Color.from_str("#c2ccf8")
        )

        view = BrandSelectView(user_id)
        await interaction.response.edit_message(embed=embed, view=view)

        # Store message reference for proper timeout handling
        try:
            message = interaction.message
            view.message = message
        except Exception as e:
            print(f"Failed to get message reference: {e}")

    @ui.button(label="Credentials", style=discord.ButtonStyle.secondary)
    async def credentials_button(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        has_credentials, has_email = check_user_setup(user_id)

        embed = discord.Embed(
            title="Credentials",
            description="Please make sure both options below are 'True'\n\n" +
                        "**Info**\n" +
                        f"{'True' if has_credentials else 'False'}\n\n" +
                        "**Email**\n" +
                        f"{'True' if has_email else 'False'}",
            color=discord.Color.from_str("#c2ccf8")
        )

        view = CredentialsDropdownView(user_id)
        await interaction.response.edit_message(embed=embed, view=view)

        # Store message reference for proper timeout handling
        try:
            message = interaction.message
            view.message = message
        except Exception as e:
            print(f"Failed to get message reference: {e}")

    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.last_interaction = datetime.now()
        self.message = None

        # Add link buttons directly in __init__
        help_button = discord.ui.Button(
            label="Help",
            style=discord.ButtonStyle.link,
            url="https://discord.com/channels/1339298010169086072/1339520924596043878"
        )
        brands_button = discord.ui.Button(
            label="Brands",
            style=discord.ButtonStyle.link,
            url="https://discord.com/channels/1339298010169086072/1339306570634236038"
        )

        self.add_item(help_button)
        self.add_item(brands_button)

# View for the credentialsdropdown menu
class CredentialsDropdownView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)  # Set timeout to 3 minutes
        self.user_id = user_id
        self.last_interaction = datetime.now()
        self.message = None

        # Create dropdown menu
        self.dropdown = ui.Select(
            placeholder="Select an option to proceed...",
            options=[
                discord.SelectOption(
                    label="Custom Info",
                    description="Enter your details manually",
                    emoji="📝"
                ),
                discord.SelectOption(
                    label="Random Info",
                    description="Generate details automatically",
                    emoji="🌐"
                ),
                discord.SelectOption(
                    label="Email Settings",
                    description="Set your email address",
                    emoji="📧"
                ),
                discord.SelectOption(
                    label="Clear Info",
                    description="Clear your saved information and email",
                    emoji="🗑️"
                )
            ]
        )

        # Set the callback for the dropdown
        self.dropdown.callback = self.dropdown_callback
        self.add_item(self.dropdown)

    async def interaction_check(self, interaction):
        # Update last interaction time on every interaction
        self.last_interaction = datetime.now()
        # Reset timeout on interaction
        self._timeout_expiry = discord.utils.utcnow() + timedelta(seconds=self.timeout)
        # Check if the interaction is from the original user
        return interaction.user.id == int(self.user_id)

    async def on_timeout(self):
        # Create timeout embed
        timeout_embed = discord.Embed(
            title="Interaction Timeout",
            description="The panel has timed out due to inactivity and is no longer active.",
            color=discord.Color.from_str("#c2ccf8")
        )

        # Try to edit the message with the timeout embed
        try:
            if self.message:
                await self.message.edit(embed=timeout_embed, view=None)
        except Exception as e:
            print(f"Error in timeout handling: {e}")

    @ui.button(label="Back", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: ui.Button):
        # Get subscription info for the menu
        user_id = str(interaction.user.id)
        subscription_type, end_date = get_subscription(user_id)

        # Format subscription type for display
        display_type = subscription_type
        if subscription_type == "3day":
            display_type = "3 Days"
        elif subscription_type == "14day":
            display_type = "14 Days"
        elif subscription_type == "1month":
            display_type = "1 Month"

        # Create menu panel
        embed = discord.Embed(
            title="GOAT Menu",
            description=("Hello <@{user_id}>, you have `Lifetime` subscription.\n" if subscription_type == "Lifetime" else
                        f"Hello <@{user_id}>, you have until `{end_date}` before your subscription ends.\n") +
                        "-# pick an option below to continue\n\n" +
                        "**Subscription Type**\n" +
                        f"`{display_type}`\n\n" +
                        "**Note**\n" +
                        "-# please click \"Credentials\" and set your credentials before you try to generate",
            color=discord.Color.from_str("#c2ccf8")
        )

        view = MenuView(user_id)
        await interaction.response.edit_message(embed=embed, view=view)

        # Store message reference for proper timeout handling
        try:
            message = interaction.message
            view.message = message
        except Exception as e:
            print(f"Failed to get message reference: {e}")

    async def dropdown_callback(self, interaction: discord.Interaction):

    # Check if interaction is from panel owner
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This is not your panel", ephemeral=True)
            return

        choice = self.dropdown.values[0]

        if choice == "Custom Info":
            # Show custom info form
            modal = CustomInfoForm()
            await interaction.response.send_modal(modal)
        elif choice == "Random Info":
            # Generate random details
            name, street, city, zip_code, country = generate_random_details()
            user_id = str(interaction.user.id)

            # Save random info to MongoDB
            from utils.db_utils import save_user_credentials
            success = save_user_credentials(
                user_id, name, street, city, zip_code, country, is_random=True
            )

            if success:
                embed = discord.Embed(
                    title="Random Details Generated",
                    description=f"**Name**: {name}\n**Address**: {street}, {city}, {zip_code}\n**Country**: {country}",
                    color=discord.Color.from_str("#c2ccf8")
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Failed to save credentials. Please try again later.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        elif choice == "Email Settings":
            # Show email form
            modal = EmailForm()
            await interaction.response.send_modal(modal)
        elif choice == "Clear Info":
            # Clear user's saved information but keep email
            user_id = str(interaction.user.id)

            # Clear only user credentials from MongoDB
            from utils.mongodb_manager import mongo_manager
            success = mongo_manager.clear_user_credentials_only(user_id)

            if success:
                embed = discord.Embed(
                    title="Information Cleared",
                    description="Your saved personal information (name, address, etc.) has been successfully cleared.\n\n-# Your email address has been kept and is still saved.",
                    color=discord.Color.from_str("#c2ccf8")
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

                # Update the credentials panel in real-time
                try:
                    # Get the original message that showed the credentials panel
                    original_message = interaction.message

                    if original_message:
                        # Create updated credentials panel with refreshed data
                        has_credentials, has_email = check_user_setup(user_id)

                        # Create updated credentials panel
                        updated_embed = discord.Embed(
                            title="Credentials",
                            description="Please make sure both options below are 'True'\n\n" +
                                        "**Info**\n" +
                                        f"{'True' if has_credentials else 'False'}\n\n" +
                                        "**Email**\n" +
                                        f"{'True' if has_email else 'False'}",
                            color=discord.Color.from_str("#c2ccf8")
                        )

                        # Update the original credentials panel
                        await original_message.edit(embed=updated_embed)
                        print(f"Successfully updated credentials panel for user {user_id}")
                    else:
                        print(f"Could not find original message to update for user {user_id}")

                except Exception as e:
                    print(f"Failed to update credentials panel in real-time: {e}")
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Failed to clear information. Please try again later.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Apply message filter first
    if message_filter:
        try:
            was_filtered = await message_filter.check_message(message)
            if was_filtered:
                # Message was deleted by filter, don't process further
                return
        except Exception as e:
            print(f"Error in message filter: {e}")

    # Check if message is in a guild-specific image channel
    if message.guild and message.attachments:
        guild_id = str(message.guild.id)
        channel_id = message.channel.id

        # Load config to get main guild ID
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                main_guild_id = config.get("guild_id", "1412488621293961226")
        except Exception as e:
            print(f"Error loading config: {e}")
            main_guild_id = "1412488621293961226"

        # Check if this channel is configured as an image channel for this guild
        try:
            image_channel_found = False

            # Special hardcoded configuration for main guild
            if guild_id == main_guild_id and channel_id == 1350414860508463204:
                image_channel_found = True
                print(f"Using hardcoded main guild image channel config: {channel_id}")
            else:
                # First try MongoDB for other guilds
                try:
                    from utils.mongodb_manager import mongo_manager
                    db = mongo_manager.get_database()
                    if db is not None:
                        guild_config = db.guild_configs.find_one({"guild_id": guild_id})
                        if guild_config and str(channel_id) == guild_config.get("image_channel_id"):
                            image_channel_found = True
                            print(f"Found MongoDB image channel config for guild {guild_id}, channel {channel_id}")
                except Exception as mongo_e:
                    print(f"MongoDB check failed: {mongo_e}")

                # If not found in MongoDB, try SQLite
                if not image_channel_found:
                    try:
                        import sqlite3
                        conn = sqlite3.connect('data.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT image_channel_id FROM guild_configs WHERE guild_id = ?", (guild_id,))
                        result = cursor.fetchone()
                        conn.close()

                        if result and str(channel_id) == str(result[0]):
                            image_channel_found = True
                            print(f"Found SQLite image channel config for guild {guild_id}, channel {channel_id}")
                    except Exception as sqlite_e:
                        print(f"SQLite check failed: {sqlite_e}")

            # If this is a configured image channel, handle attachments
            if image_channel_found:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                        # Reply to the user's message with the image URL
                        await message.reply(f"```\n{attachment.url}\n```", mention_author=True)
                        print(f"Replied with image URL: {attachment.url}")
        except Exception as e:
            print(f"Error checking guild image channel config: {e}")

    # Process commands
    await bot.process_commands(message)

@bot.tree.command(name="generate", description="Generate receipts with GOAT Receipts")
async def generate_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id if interaction.guild else "0")

    # Check if user is rate limited
    from utils.mongodb_manager import mongo_manager
    is_limited, limit_expiry = mongo_manager.check_user_rate_limit(user_id)

    if is_limited:
        await interaction.response.send_message("-# **Oops... looks like you've made more than enough receipts for today, try again in 11 hours**", ephemeral=True)
        return

    # Load config to get main guild ID
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            main_guild_id = config.get("guild_id", "1412488621293961226")
            main_channel_id = 1350413411455995904
    except Exception as e:
        print(f"Error loading config: {e}")
        main_guild_id = "1412488621293961226"
        main_channel_id = 1350413411455995904

    # Check if this is a guild-specific or main guild request
    is_main_guild = (guild_id == main_guild_id)

    # If in main guild, enforce channel restriction
    if is_main_guild and interaction.channel_id != main_channel_id:
        embed = discord.Embed(
            title="Command Restricted",
            description=f"This command can only be used in <#{main_channel_id}>",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # If in a guild server, check if the channel is allowed
    if not is_main_guild:
        # Check if guild is configured
        try:
            from utils.mongodb_manager import mongo_manager
            db = mongo_manager.get_database()
            if db is None:
                embed = discord.Embed(
                    title="Database Error",
                    description="Unable to connect to database. Please try again later.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            guild_config = db.guild_configs.find_one({"guild_id": guild_id})

            if not guild_config:
                embed = discord.Embed(
                    title="Server Not Configured",
                    description="This server has not been configured to use GOAT Receipts. Please ask the server admin to use `/configure_guild`.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Check if this is the right channel
            allowed_channel_id = int(guild_config.get("generate_channel_id", 0))
            if interaction.channel_id != allowed_channel_id:
                embed = discord.Embed(
                    title="Command Restricted",
                    description=f"This command can only be used in <#{allowed_channel_id}>",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Get the guild configuration including client role
            client_role_id = guild_config.get("client_role_id")
            admin_role_id = guild_config.get("admin_role_id")
            role_config = (client_role_id, admin_role_id)
        except Exception as e:
            print(f"Error checking guild configuration: {e}")
            embed = discord.Embed(
                title="Configuration Error",
                description="There was an error checking server configuration. Please contact a server admin.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not role_config:
            embed = discord.Embed(
                title="Server Not Configured",
                description="This server has not been configured properly. Please ask the server admin to use `/configure_guild` command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        client_role_id, admin_role_id = role_config

        # Use GuildLicenseChecker to verify access
        try:
            # Check if user has admin role first
            has_admin_role = False
            if admin_role_id:
                admin_role = discord.utils.get(interaction.guild.roles, id=int(admin_role_id))
                if admin_role and admin_role in interaction.user.roles:
                    has_admin_role = True
                    print(f"User {user_id} has admin role in guild {guild_id}")

            # Check if user has client role
            has_client_role = False
            if client_role_id:
                client_role = discord.utils.get(interaction.guild.roles, id=int(client_role_id))
                if client_role and client_role in interaction.user.roles:
                    has_client_role = True
                    print(f"User {user_id} has client role in guild {guild_id}")

            # Check database using GuildLicenseChecker
            has_access, access_info = await GuildLicenseChecker.check_guild_access(user_id, guild_id, guild_config)
            print(f"Database access check for {user_id} in {guild_id}: has_access={has_access}, info={access_info}")

            # If user has admin or client role, they have access regardless of database status
            if has_admin_role or has_client_role:
                has_access = True
                print(f"User {user_id} granted access via role in guild {guild_id}")
            elif not has_access:
                # Handle different access denial scenarios
                if access_info.get("type") == "expired":
                    embed = discord.Embed(
                        title="Access Expired",
                        description=f"Your access to this server expired on {access_info.get('expiry', 'unknown date')}. Please contact a server admin.",
                        color=discord.Color.red()
                    )
                elif access_info.get("type") == "expired_license":
                    embed = discord.Embed(
                        title="License Expired",
                        description=f"Your {access_info.get('subscription_type', 'subscription')} license expired on {access_info.get('expiry', 'unknown date')}. Please contact a server admin.",
                        color=discord.Color.red()
                    )
                elif access_info.get("type") == "access_removed":
                    embed = discord.Embed(
                        title="Access Removed",
                        description="Your access to this server has been removed by an administrator. Please contact a server admin if you believe this is an error.",
                        color=discord.Color.red()
                    )
                elif access_info.get("type") == "license_removed":
                    embed = discord.Embed(
                        title="License Removed",
                        description="Your license for this server has been removed by an administrator. Please contact a server admin if you believe this is an error.",
                        color=discord.Color.red()
                    )
                elif access_info.get("type") == "database_error":
                    embed = discord.Embed(
                        title="Database Error",
                        description="There was a database error checking your access. Please try again later or contact a server admin.",
                        color=discord.Color.red()
                    )
                else:
                    embed = discord.Embed(
                        title="Access Denied",
                        description="You don't have access to use this bot in this server. Please contact a server admin to grant you access.",
                        color=discord.Color.red()
                    )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        except Exception as e:
            print(f"Error checking guild access: {e}")
            embed = discord.Embed(
                title="Access Error",
                description="There was an error verifying your access. Please contact a server admin.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Continue with generating the receipt for guild users
        # Check if user has credentials and email using guild-aware checker
        if not is_main_guild:
            has_credentials, has_email = GuildLicenseChecker.check_user_setup_guild(user_id, guild_id)
            subscription_type, end_date = await GuildLicenseChecker.get_guild_subscription_info(user_id, guild_id)
        else:
            has_credentials, has_email = check_user_setup(user_id)
            subscription_type, end_date = get_subscription(user_id)

        # Check if access was removed (indicated by specific subscription types)
        if subscription_type in ["Access Removed", "License Removed", "No Access"]:
            embed = discord.Embed(
                title="Access Denied",
                description="Your access to this server has been removed by an administrator. Please contact a server admin if you believe this is an error.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not has_credentials or not has_email:
            # Show menu panel for new users
            # Format subscription type for display
            display_type = subscription_type
            if subscription_type == "3day":
                display_type = "3 Days"
            elif subscription_type == "14day":
                display_type = "14 Days"
            elif subscription_type == "1month":
                display_type = "1 Month"

            embed = discord.Embed(
                title="GOAT Menu",
                description=(f"Hello <@{user_id}>, you have `Lifetime` subscription.\n" if subscription_type == "Lifetime" else
                            f"Hello <@{user_id}>, you have until `{end_date}` before your subscription ends.\n") +
                            "-# pick an option below to continue\n\n" +
                            "**Subscription Type**\n" +
                            f"`{display_type}`\n\n" +
                            "**Note**\n" +
                            "-# please click \"Credentials\" and set your credentials before you try to generate",
                color=discord.Color.from_str("#c2ccf8")
            )

            view = MenuView(user_id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

            # Store message reference for proper timeout handling
            try:
                message = await interaction.original_response()
                view.message = message
            except Exception as e:
                print(f"Failed to get message reference: {e}")
            return
        else:
            # Show generator panel for returning users
            username = interaction.user.display_name
            total_brands = get_total_brands()

            # Calculate max pages
            import os
            modal_files = [f for f in os.listdir('modals') if f.endswith('.py') and not f.startswith('__')]
            total_count = len(modal_files)
            max_pages = (total_count + 14) // 15  # Ceiling division to get number of pages

            embed = discord.Embed(
                title=f"{username}'s Panel",
                description=f"Choose the type of receipt from the dropdown menu below. `(Total: {total_brands})`\n-# Page 1/{max_pages if max_pages > 0 else 1}",
                color=discord.Color.from_str("#c2ccf8")
            )

            view = BrandSelectView(user_id)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

            # Store message reference for proper timeout handling
            try:
                message = await interaction.original_response()
                view.message = message
            except Exception as e:
                print(f"Failed to get message reference: {e}")
    else:
        # In main guild, check license normally
        # Check if user has a valid license
        from utils.license_manager import LicenseManager
        license_status = await LicenseManager.is_subscription_active(user_id)

        if not license_status:
            # Check if it's a lite subscription that's exhausted
            from utils.mongodb_manager import mongo_manager
            license_doc = mongo_manager.get_license(user_id)
            if license_doc and (license_doc.get("subscription_type") == "lite" or license_doc.get("subscription_type") == "litesubscription"):
                receipt_count = license_doc.get("receipt_count", 0)
                max_receipts = license_doc.get("max_receipts", 7)
                if receipt_count >= max_receipts:
                    embed = discord.Embed(
                        title="Lite Subscription Complete",
                        description=f"You have used all **{max_receipts}** receipts from your Lite subscription!\n\n**Thank you for using our service!**\n• Consider leaving a review in <#1350413086074474558>\n• If you experienced any issues, open a support ticket in <#1350417131644125226>\n\nUpgrade to unlimited receipts at https://goatreceipts.net",
                        color=discord.Color.orange()
                    )
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="Upgrade", style=discord.ButtonStyle.link, url="https://goatreceipts.net"))
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                    return

            # User never had a license or it's expired
            embed = discord.Embed(
                title="Access Denied",
                description="You need to buy a **[subscription](https://goatreceipts.net)** to use our services\n-# Be aware that it costs us money to run the bot.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

    # Check if user has a subscription or create default one
    subscription_type, end_date = get_subscription(user_id)

    # Check if user has credentials and email
    has_credentials, has_email = check_user_setup(user_id)

    if not has_credentials or not has_email:
        # Show menu panel for new users
        # Format subscription type for display
        display_type = subscription_type
        if subscription_type == "3day":
            display_type = "3 Days"
        elif subscription_type == "14day":
            display_type = "14 Days"
        elif subscription_type == "1month":
            display_type = "1 Month"

        embed = discord.Embed(
            title="GOAT Menu",
            description=(f"Hello <@{user_id}>, you have `Lifetime` subscription.\n" if subscription_type == "Lifetime" else
                        f"Hello <@{user_id}>, you have until `{end_date}` before your subscription ends.\n") +
                        "-# pick an option below to continue\n\n" +
                        "**Subscription Type**\n" +
                        f"`{display_type}`\n\n" +
                        "**Note**\n" +
                        "-# please click \"Credentials\" and set your credentials before you try to generate",
            color=discord.Color.from_str("#c2ccf8")
        )

        # Create and send the menu view
        view = MenuView(user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

        # Store message reference for proper timeout handling
        try:
            message = await interaction.original_response()
            view.message = message
        except Exception as e:
            print(f"Failed to get message reference: {e}")
        return
    else:
        # Show generator panel for returning users
        username = interaction.user.display_name
        total_brands = get_total_brands()

        # Calculate max pages
        import os
        modal_files = [f for f in os.listdir('modals') if f.endswith('.py') and not f.startswith('__')]
        total_count = len(modal_files)
        max_pages = (total_count + 14) // 15  # Ceiling division to get number of pages

        embed = discord.Embed(
            title=f"{username}'s Panel",
            description=f"Choose the type of receipt from the dropdown menu below. `(Total: {total_brands})`\n-# Page 1/{max_pages if max_pages > 0 else 1}",
            color=discord.Color.from_str("#c2ccf8")
        )

        view = BrandSelectView(user_id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

        # Store message reference for proper timeout handling
        try:
            message = await interaction.original_response()
            view.message = message
        except Exception as e:
            print(f"Failed to get message reference: {e}")

# Simple HTTP server for health checks
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running!')

def run_http_server():
    server = HTTPServer(('0.0.0.0', 8080), SimpleHTTPRequestHandler)
    print('Starting HTTP server on port 8080')
    server.serve_forever()

# Start HTTP server in a separate thread
if os.getenv('REPLIT_DEPLOYMENT'):
    print("Deployment detected, starting HTTP server")
    thread = threading.Thread(target=run_http_server)
    thread.daemon = True
    thread.start()

# Start webhook server for invite tracker integration
def run_webhook_server():
    try:
        from webhook_server import app
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"Failed to start webhook server: {e}")

webhook_thread = threading.Thread(target=run_webhook_server)
webhook_thread.daemon = True
webhook_thread.start()
print("Webhook server started on port 5000")

# Load command modules
async def load_extensions():
    try:
        await bot.load_extension('commands.admin_commands')
        print("Loaded admin commands")
    except Exception as e:
        print(f"Failed to load admin commands: {e}")

    try:
        await bot.load_extension('commands.guild_commands')
        print("Loaded guild commands")
    except Exception as e:
        print(f"Failed to load guild commands: {e}")

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await load_extensions()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

    # Start the license checker background task
    try:
        from utils.license_manager import LicenseManager
        license_manager = LicenseManager(bot)
        await license_manager.start_license_checker()
        print("License checker background task started")
    except Exception as e:
        print(f"Failed to start license checker: {e}")

# License key redemption form
class RedeemKeyModal(ui.Modal, title="Redeem License Key"):
    license_key = ui.TextInput(
        label="License Key",
        placeholder="Enter your Gumroad license key (e.g., 6F0E4C97-B72A4E69-A11BF6C4-AF6517E7)",
        required=True,
        min_length=30,
        max_length=50
    )

    def __init__(self):
        super().__init__()
        self.bot = None
        self.interaction = None

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        key = self.license_key.value.strip()

        # Process key redemption
        from utils.key_manager import KeyManager
        key_manager = KeyManager()
        result = key_manager.redeem_key(key, user_id)

        if result["success"]:
            # Key is valid, add subscription to user
            subscription_type = result["subscription_type"]
            expiry_date = result["expiry_date"]

            # Generate license key based on subscription type
            key_prefix = subscription_type
            license_key = f"{key_prefix}-{user_id}"

            # Check if this is a guild key
            is_guild_key = subscription_type.startswith("guild_")

            if is_guild_key:
                # Handle guild subscription
                guild_sub_type = "Lifetime" if "lifetime" in subscription_type.lower() else "30 Days"

                # Parse expiry date
                expiry_dt = datetime.strptime(expiry_date, '%d/%m/%Y %H:%M:%S')
                end_date = expiry_dt.strftime('%Y-%m-%d')

                # Create license data for MongoDB
                license_data = {
                    "key": license_key,
                    "expiry": expiry_date,
                    "subscription_type": guild_sub_type,
                    "start_date": datetime.now().strftime('%Y-%m-%d'),
                    "end_date": end_date,
                    "is_active": True,
                    "emailtf": "False",
                    "credentialstf": "False"
                }

                # Save to MongoDB
                from utils.mongodb_manager import mongo_manager
                success = mongo_manager.create_or_update_license(user_id, license_data)

                if not success:
                    embed = discord.Embed(
                        title="Error",
                        description="Failed to save license to database. Please try again.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                # Update cache
                from utils.license_manager import LicenseManager
                now = datetime.now()
                is_lifetime = 'lifetime' in subscription_type.lower()
                LicenseManager._license_cache[user_id] = (expiry_dt, is_lifetime)

                # Notification message for guild subscription
                try:
                    purchases_channel = interaction.client.get_channel(1412500928187203606)
                    if purchases_channel:
                        # Create guild subscription notification
                        guild_embed = discord.Embed(
                            title="Thank you for purchasing",
                            description=f"{interaction.user.mention}, your guild subscription has been updated. Check below\n"
                                       f"-# Run command **/configure_guild** in <#1412501183121068132> to continue\n\n"
                                       f"**Subscription Type**\n"
                                       f"`Guild`\n\n"
                                       f"**Consider leaving a review !**\n"
                                       f"Please consider leaving a review at <#1412500966477139990>",
                            color=discord.Color.green()
                        )

                        await purchases_channel.send(content=interaction.user.mention, embed=guild_embed)

                        # Also try to DM
                        try:
                            await interaction.user.send(embed=guild_embed)
                        except:
                            print(f"Could not send DM to {interaction.user.display_name}")
                except Exception as e:
                    print(f"Error sending guild notification: {e}")
            else:
                # Regular subscription key
                license_data = {
                    "key": license_key,
                    "expiry": expiry_date,
                    "subscription_type": subscription_type,
                    "is_active": True,
                    "emailtf": "False",
                    "credentialstf": "False"
                }

                # Create license in MongoDB
                try:
                    license_data = {
                        "subscription_type": subscription_type,
                        "start_date": datetime.now().strftime("%Y-%m-%d"),
                        "end_date": expiry_date,
                        "is_active": True,
                        "expiry": expiry_date,
                        "key": license_key
                    }

                    # Add receipt count for lite subscription
                    if subscription_type == "lite":
                        license_data["receipt_count"] = 0
                        license_data["max_receipts"] = 7

                    # Use MongoDB manager to create/update license
                    from utils.mongodb_manager import mongo_manager
                    success = mongo_manager.create_or_update_license(user_id, license_data)

                    if not success:
                        raise Exception("Failed to create license in MongoDB")
                except Exception as e:
                    logging.error(f"Failed to create license for user {user_id}: {e}")
                    embed = discord.Embed(
                        title="Error",
                        description="Failed to save license to database. Please try again.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                # Update the LicenseManager cache to recognize this license immediately
                from utils.license_manager import LicenseManager
                now = datetime.now()
                expiry_dt = datetime.strptime(expiry_date, '%d/%m/%Y %H:%M:%S')
                is_lifetime = 'lifetime' in subscription_type.lower()

                # Update the cache with the new license
                LicenseManager._license_cache[user_id] = (expiry_dt, is_lifetime)

                # Send notification to Purchases channel
                try:
                    purchases_channel = interaction.client.get_channel(1412500928187203606)
                    if purchases_channel:
                        # Clean up subscription type display
                        display_type = subscription_type
                        if subscription_type == "3day":
                            display_type = "3 Days"
                        elif subscription_type == "14day":
                            display_type = "14 Days"
                        elif subscription_type == "1month":
                            display_type = "1 Month"
                        elif subscription_type == "3month":
                            display_type = "3 Months"

                        # Create notification embed
                        notification_embed = discord.Embed(
                            title="Thank you for purchasing",
                            description=f"{interaction.user.mention}, your subscription has been updated. Check below\n"
                                      f"-# Run command /generate in <#1412501183121068132> to continue\n\n"
                                      f"**Subscription Type**\n"
                                      f"`{display_type}`\n\n"
                                      f"- Please consider leaving a review at <#1412500966477139990>",
                            color=discord.Color.green()
                        )

                        await purchases_channel.send(content=interaction.user.mention, embed=notification_embed)

                        # Send DM to user
                        try:
                            await interaction.user.send(embed=notification_embed)
                        except:
                            print(f"Could not send DM to {interaction.user.display_name}")
                except Exception as e:
                    print(f"Error sending notification: {e}")

            # Note: MongoDB operations are automatically committed
            logging.info(f"Successfully created/updated license for user {user_id}")

            # Try to add client role and new unified subscription role to the user
            try:
                with open("config.json", "r") as f:
                    import json
                    config = json.load(f)
                    client_role_id = int(config.get("Client_ID", 0))

                if client_role_id > 0:
                    guild = self.interaction.guild  # Access guild through the stored interaction
                    if guild:
                        # Add client role to ALL subscription types including lite
                        client_role = discord.utils.get(guild.roles, id=client_role_id)
                        if client_role:
                            await self.interaction.user.add_roles(client_role)
                            print(f"Added client role {client_role.name} to {self.interaction.user.display_name}")

                        # Add new unified subscription role for 1 month, 3 months, and lifetime (NOT lite)
                        if "1month" in subscription_type or "3month" in subscription_type or "30day" in subscription_type or "guild_30days" in subscription_type or "lifetime" in subscription_type.lower():
                            # Add the new unified subscription role (ID: 1402941054243831888)
                            new_role = discord.utils.get(guild.roles, id=1402941054243831888)
                            if new_role:
                                await self.interaction.user.add_roles(new_role)
                                print(f"Added new subscription role {new_role.name} to {self.interaction.user.display_name}")
            except Exception as e:
                print(f"Error adding roles: {e}")

            # Success message
            embed = discord.Embed(
                title="License Key Redeemed Successfully",
                description=f"Your subscription has been activated:\n\n**Subscription Type**: {subscription_type.replace('guild_', 'Guild ')}\n**Expires On**: {expiry_date}",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        else:
            # Error handling
            if result["error"] == "already_used":
                embed = discord.Embed(
                    title="Key Already Used",
                    description="This license key has already been redeemed.",
                    color=discord.Color.red()
                )
            elif result["error"] == "verification_failed":
                embed = discord.Embed(
                    title="Verification Failed",
                    description="Unable to verify the license key with Gumroad. Please try again later or contact support.",
                    color=discord.Color.red()
                )
            elif result["error"] == "unknown_product":
                embed = discord.Embed(
                    title="Unknown Product",
                    description="The license key is valid but the product type could not be determined. Please contact support.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="Invalid License Key",
                    description="The license key you entered is invalid. Please check and try again.",
                    color=discord.Color.red()
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

# Button view for redeem command
class RedeemKeyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Redeem",
        style=discord.ButtonStyle.primary,
        emoji="<:discordkey:1372312945521856633>",
        custom_id="redeem_key_button"
    )
    async def redeem_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Show the redemption form
        modal = RedeemKeyModal()
        modal.interaction = interaction  # Store the interaction for role assignment
        modal.bot = interaction.client   # Store the bot instance for background tasks
        await interaction.response.send_modal(modal)

# Subscription type selection for key generation
class KeygenTypeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="3 Days",
                description="Generate keys for 3-day subscriptions",
                value="3day"
            ),
            discord.SelectOption(
                label="14 Days",
                description="Generate keys for 14-day subscriptions",
                value="14day"
            ),
            discord.SelectOption(
                label="1 Month",
                description="Generate keys for 1-month subscriptions",
                value="1month"
            ),
            discord.SelectOption(
                label="3 Months",
                description="Generate keys for 3-month subscriptions",
                value="3month"
            ),
            discord.SelectOption(
                label="Lifetime",
                description="Generate keys for lifetime subscriptions",
                value="lifetime"
            ),
            discord.SelectOption(
                label="Guild 30 Days",
                description="Generate keys for 30-day guild subscriptions",
                value="guild_30days"
            ),
            discord.SelectOption(
                label="Guild Lifetime",
                description="Generate keys for lifetime guild subscriptions",
                value="guild_lifetime"
            ),
            discord.SelectOption(
                label="Lite",
                description="Generate keys for the Lite Subscription (7 receipts)",
                value="lite"
            )
        ]
        super().__init__(placeholder="Select subscription type...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Check if user is the bot owner
        with open("config.json", "r") as f:
            import json
            config = json.load(f)
            owner_id = config.get("owner_id", "0")

        if str(interaction.user.id) != owner_id:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        # Generate keys
        subscription_type = self.values[0]
        from utils.key_manager import KeyManager
        key_manager = KeyManager()
        keys = key_manager.generate_keys(subscription_type)

        # Create a formatted list of keys
        keys_text = "\n".join(keys)

        # Create embed
        embed = discord.Embed(
            title=f"Generated {len(keys)} License Keys",
            description=f"Subscription Type: **{subscription_type}**",
            color=discord.Color.from_str("#c2ccf8")
        )

        # Send keys as a file for better formatting and security
        import io
        keys_file = io.StringIO(keys_text)

        await interaction.response.send_message(
            embed=embed,
            file=discord.File(fp=keys_file, filename=f"{subscription_type}_keys.txt"),
            ephemeral=True
        )

# View for key generation
class KeygenView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(KeygenTypeSelect())

@bot.tree.command(name="redeem", description="Redeem a license key for access")
async def redeem_command(interaction: discord.Interaction):
    # Check if user is the bot owner
    with open("config.json", "r") as f:
        import json
        config = json.load(f)
        owner_id = config.get("owner_id", "0")

    if str(interaction.user.id) != owner_id:
        embed = discord.Embed(
            title="Access Denied",
            description="Only the bot owner can use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Send ephemeral acknowledgment
    await interaction.response.send_message("Command received.", ephemeral=True)

    # Send the public panel message
    embed = discord.Embed(
        title="Redeem License Key",
        description="Click on the button `Redeem` then submit your **unique Key**. You should receive access automatically. Each key can only be used **once**. If there is issue with you key head over to <#1350413411455995904> and open ticket describing your issue!",
        color=discord.Color.green()
    )

    view = RedeemKeyView()
    await interaction.followup.send(embed=embed, view=view, ephemeral=False)

@bot.tree.command(name="keygen", description="Generate license keys (Owner only)")
async def keygen_command(interaction: discord.Interaction):
    # Check if user is the bot owner
    with open("config.json", "r") as f:
        import json
        config = json.load(f)
        owner_id = config.get("owner_id", "0")

    if str(interaction.user.id) != owner_id:
        await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Generate License Keys",
        description="Select the subscription type to generate 30 new license keys.",
        color=discord.Color.from_str("#c2ccf8")
    )

    view = KeygenView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="menu", description="Open the GOAT Receipts menu")
async def menu_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    # Check if user is rate limited
    from utils.mongodb_manager import mongo_manager
    is_limited, limit_expiry = mongo_manager.check_user_rate_limit(user_id)

    if is_limited:
        await interaction.response.send_message("-# **Oops... looks like you've made more than enough receipts for today, try again in 11 hours**", ephemeral=True)
        return

    # Check channel permissions for guild servers
    from utils.command_permissions import check_channel_permission

    if not await check_channel_permission(interaction, "menu"):
        # Get the correct channel ID to show in error message
        try:
            from utils.mongodb_manager import mongo_manager
            guild_config = mongo_manager.get_guild_config(interaction.guild.id)

            if guild_config:
                generate_channel_id = int(guild_config.get("generate_channel_id", 0))
                embed = discord.Embed(
                    title="Command Restricted",
                    description=f"This command can only be used in <#{generate_channel_id}>",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        except Exception:
            pass

    # Check if user has a valid license
    from utils.license_manager import LicenseManager

    if not await LicenseManager.is_subscription_active(interaction.user.id):
        embed = discord.Embed(
            title="Invalid License",
            description="Please use `/redeem` to activate your license first.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Check if user has a subscription or create default one
    subscription_type, end_date = get_subscription(user_id)

    # Format subscription type for display
    display_type = subscription_type
    if subscription_type == "3day":
        display_type = "3 Days"
    elif subscription_type == "14day":
        display_type = "14 Days"
    elif subscription_type == "1month":
        display_type = "1 Month"

    # Create menu panel
    embed = discord.Embed(
        title="GOAT Menu",
        description=(f"Hello <@{user_id}>, you have `Lifetime` subscription.\n" if subscription_type == "Lifetime" else
                    f"Hello <@{user_id}>, you have until `{end_date}` before your subscription ends.\n") +
                    "-# pick an option below to continue\n\n" +
                    "**Subscription Type**\n" +
                    f"`{display_type}`\n\n" +
                    "**Note**\n" +
                    "-# please click \"Credentials\" and set your credentials before you try to generate",
        color=discord.Color.from_str("#c2ccf8")
    )

    await interaction.response.send_message(embed=embed, view=MenuView(user_id), ephemeral=False)



# Load the token
token = os.getenv('DISCORD_TOKEN')
if not token:
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            token = config.get("bot_token")
    except FileNotFoundError:
        print("config.json not found. Please ensure it exists.")
        exit(1)
    except json.JSONDecodeError:
        print("Error decoding config.json. Please ensure it's valid JSON.")
        exit(1)

if not token:
    print("Discord token not found. Please set DISCORD_TOKEN environment variable or provide it in config.json.")
    exit(1)

# Run the bot
bot.run(token)