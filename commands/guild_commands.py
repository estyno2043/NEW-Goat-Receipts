import discord
from discord import app_commands
from discord.ext import commands
from discord import ui
import sqlite3
import json
import logging
from datetime import datetime, timedelta
import asyncio
import random

# Import modal classes
from modals.farfetch import farfetchmodal
from modals.flannels import flannelsmodal
from modals.futbolemotion import futbolemotionmodal

# Setup database for guild configuration
def setup_guild_database():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Table for guild configurations
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS guild_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT UNIQUE,
        owner_id TEXT,
        generate_channel_id TEXT,
        admin_role_id TEXT,
        client_role_id TEXT,
        image_channel_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Table for guild subscriptions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS guild_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        subscription_type TEXT,
        start_date TEXT,
        end_date TEXT,
        is_active INTEGER DEFAULT 1
    )
    ''')

    # Table for guild user access
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS server_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT,
        user_id TEXT,
        added_by TEXT,
        access_type TEXT,
        expiry TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(guild_id, user_id)
    )
    ''')

    conn.commit()
    conn.close()

# Guild configuration modal
class GuildConfigModal(ui.Modal, title="Guild Configuration"):
    generate_channel = ui.TextInput(
        label="Generate Channel ID",
        placeholder="Enter the channel ID for /generate command",
        required=True
    )

    admin_role = ui.TextInput(
        label="Admin Role ID",
        placeholder="Enter the admin role ID",
        required=True
    )

    client_role = ui.TextInput(
        label="Client Role ID",
        placeholder="Enter the client role ID",
        required=True
    )

    image_channel = ui.TextInput(
        label="Image Link Channel ID",
        placeholder="Enter the channel ID for image links",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Validate IDs
        try:
            generate_channel_id = int(self.generate_channel.value.strip())
            admin_role_id = int(self.admin_role.value.strip())
            client_role_id = int(self.client_role.value.strip())
            image_channel_id = int(self.image_channel.value.strip())

            # Save to MongoDB
            from utils.mongodb_manager import mongo_manager

            success = mongo_manager.save_guild_config(
                interaction.guild.id,
                interaction.user.id,
                generate_channel_id,
                admin_role_id,
                client_role_id,
                image_channel_id
            )

            if success:
                # Send success message
                embed = discord.Embed(
                    title="Success",
                    description="-# Information saved successfully!",
                    color=discord.Color.from_str("#c2ccf8")
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Failed to save configuration to database.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError:
            # Handle invalid IDs
            embed = discord.Embed(
                title="Error",
                description="All IDs must be valid numbers.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logging.error(f"Error in guild configuration: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

# Button view for guild configuration
class GuildConfigView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)  # 3 minute timeout

    @ui.button(label="Start", style=discord.ButtonStyle.primary)
    async def start_config(self, interaction: discord.Interaction, button: ui.Button):
        # Show the configuration modal
        await interaction.response.send_modal(GuildConfigModal())

class GuildCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        setup_guild_database()

    async def is_guild_admin(self, interaction: discord.Interaction):
        """Check if the user is a guild admin based on configured role"""
        if interaction.guild is None:
            return False

        # Check if this is the main guild owner
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                if str(interaction.user.id) == config.get("owner_id"):
                    return True
        except Exception as e:
            logging.error(f"Error checking owner status: {e}")

        # Check if user has guild admin role
        from utils.mongodb_manager import mongo_manager
        guild_config = mongo_manager.get_guild_config(interaction.guild.id)

        if not guild_config:
            return False

        admin_role_id = int(guild_config.get("admin_role_id"))
        admin_role = discord.utils.get(interaction.guild.roles, id=admin_role_id)

        if admin_role and admin_role in interaction.user.roles:
            return True

        return False

    async def has_guild_subscription(self, user_id):
        """Check if a user has an active guild subscription"""
        try:
            from utils.mongodb_manager import mongo_manager

            # Get user's license from MongoDB
            license_doc = mongo_manager.get_license(user_id)

            if not license_doc:
                return False

            key = license_doc.get("key", "")
            expiry_str = license_doc.get("expiry")

            # Check if it's a guild subscription key
            if not (key and ("guild" in key.lower() or "guild_30days" in key or "guild_lifetime" in key)):
                return False

            # Check if it's a lifetime guild subscription
            if "guild_lifetime" in key or "lifetime" in key.lower():
                return True

            # Check expiry for time-limited guild subscriptions
            if expiry_str:
                try:
                    expiry_date = datetime.strptime(expiry_str, '%d/%m/%Y %H:%M:%S')
                    return datetime.now() < expiry_date
                except Exception as e:
                    logging.error(f"Error parsing expiry date: {e}")

            return False

        except Exception as e:
            logging.error(f"Error checking guild subscription: {e}")
            return False

    @app_commands.command(name="configure_guild", description="Configure the bot for your guild")
    async def configure_guild(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # First check if user has guild subscription
        has_subscription = await self.has_guild_subscription(user_id)

        # If this is the main guild owner, allow configuration regardless
        is_owner = False
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                if user_id == config.get("owner_id"):
                    is_owner = True
                    has_subscription = True
        except Exception as e:
            logging.error(f"Error checking owner status: {e}")

        if not has_subscription and not is_owner:
            embed = discord.Embed(
                title="Access Denied",
                description="You need a Guild subscription to configure the bot for your server.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check the guild context
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                main_guild_id = config.get("guild_id", "1412488621293961226")

            # Get bot application info for invite link
            app_info = await self.bot.application_info()
            client_id = app_info.id

            # Create invite link with proper permissions
            invite_permissions = discord.Permissions(
                send_messages=True,
                embed_links=True,
                attach_files=True,
                read_messages=True,
                read_message_history=True,
                manage_roles=True,
                use_application_commands=True
            )
            invite_link = discord.utils.oauth_url(
                client_id, 
                permissions=invite_permissions,
                scopes=["bot", "applications.commands"]
            )

            # Check if we're in the main guild or a user guild
            if str(interaction.guild.id) == main_guild_id:
                # If in main guild, show invite link
                embed = discord.Embed(
                    title="Configure Your Guild Bot",
                    description=f"Please invite the bot to your server and then run the command there. You can do so by clicking the link below:",
                    color=discord.Color.from_str("#c2ccf8")
                )
                embed.add_field(
                    name="Bot Invite Link", 
                    value=f"[Click here to invite the bot]({invite_link})"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                # If in user guild, show configuration
                embed = discord.Embed(
                    title="Configure Your Guild",
                    description="-# Click the button below to start the setup process.",
                    color=discord.Color.from_str("#c2ccf8")
                )
                view = GuildConfigView()
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            logging.error(f"Error in configure_guild command: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


    @app_commands.command(name="timeleft", description="Check how much time a user has left in this guild")
    @app_commands.describe(user="The user to check time remaining for")
    async def timeleft(self, interaction: discord.Interaction, user: discord.Member):
        # Check if user is a guild admin
        is_admin = await self.is_guild_admin(interaction)

        if not is_admin:
            embed = discord.Embed(
                title="Access Denied",
                description="You must have the admin role to use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Get guild configuration
        from utils.mongodb_manager import mongo_manager
        guild_config = mongo_manager.get_guild_config(interaction.guild.id)

        if not guild_config:
            embed = discord.Embed(
                title="Error",
                description="This server has not been configured yet. Please use `/configure_guild` first.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check both server access and guild-specific license
        server_access = mongo_manager.get_server_access(interaction.guild.id, user.id)
        guild_license = mongo_manager.get_guild_user_license(interaction.guild.id, user.id)

        if not server_access and not guild_license:
            embed = discord.Embed(
                title="No Access",
                description=f"{user.mention} does not have access in this guild.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Prioritize server_access if it exists, otherwise use guild_license
        access_record = server_access if server_access else guild_license

        try:
            expiry_str = access_record.get("expiry")
            access_type = access_record.get("access_type") or access_record.get("subscription_type", "Unknown")

            if expiry_str:
                # Try multiple date formats
                expiry_date = None
                formats_to_try = [
                    "%Y-%m-%d %H:%M:%S",  # MongoDB format
                    "%d/%m/%Y %H:%M:%S"   # Legacy format
                ]

                for date_format in formats_to_try:
                    try:
                        expiry_date = datetime.strptime(expiry_str, date_format)
                        break
                    except ValueError:
                        continue

                if expiry_date:
                    current_date = datetime.now()

                    if current_date > expiry_date:
                        embed = discord.Embed(
                            title="Access Expired",
                            description=f"{user.mention}'s access expired on {expiry_date.strftime('%d/%m/%Y %H:%M:%S')}",
                            color=discord.Color.red()
                        )
                    else:
                        time_left = expiry_date - current_date
                        days_left = time_left.days
                        hours_left = time_left.seconds // 3600
                        minutes_left = (time_left.seconds % 3600) // 60

                        if "lifetime" in access_type.lower():
                            time_display = "Lifetime Access"
                        else:
                            time_display = f"{days_left} days, {hours_left} hours, {minutes_left} minutes"

                        embed = discord.Embed(
                            title="Time Remaining",
                            description=f"**User:** {user.mention}\n**Access Type:** {access_type}\n**Time Left:** {time_display}\n**Expires:** {expiry_date.strftime('%d/%m/%Y %H:%M:%S')}",
                            color=discord.Color.green()
                        )
                else:
                    embed = discord.Embed(
                        title="Error",
                        description="Could not parse expiry date format for this user.",
                        color=discord.Color.red()
                    )
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Could not determine expiry time for this user.",
                    color=discord.Color.red()
                )

        except Exception as e:
            logging.error(f"Error checking time left for user {user.id}: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while checking user access: {str(e)}",
                color=discord.Color.red()
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="remove_access", description="Remove access for a user in this guild")
    @app_commands.describe(user="The user to remove access from")
    async def remove_access(self, interaction: discord.Interaction, user: discord.Member):
        # Check if user is a guild admin
        is_admin = await self.is_guild_admin(interaction)

        if not is_admin:
            embed = discord.Embed(
                title="Access Denied",
                description="You must have the admin role to use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Get guild configuration
        from utils.mongodb_manager import mongo_manager
        guild_config = mongo_manager.get_guild_config(interaction.guild.id)

        if not guild_config:
            embed = discord.Embed(
                title="Error",
                description="This server has not been configured yet. Please use `/configure_guild` first.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        client_role_id = guild_config.get("client_role_id")

        # Check if user has guild access (either server access or guild license)
        server_access = mongo_manager.get_server_access(interaction.guild.id, user.id)
        guild_license = mongo_manager.get_guild_user_license(interaction.guild.id, user.id)

        if not server_access and not guild_license:
            embed = discord.Embed(
                title="No Access Found",
                description=f"{user.mention} does not have access in this guild.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        try:
            # Remove guild-specific license
            mongo_manager.delete_guild_user_license(interaction.guild.id, user.id)

            # Remove server access record
            mongo_manager.delete_server_access(interaction.guild.id, user.id)

            # Clear user's main credentials and email to prevent access
            mongo_manager.delete_user_credentials(user.id)
            mongo_manager.delete_user_email(user.id)

            # Also clear the main user license to ensure complete access removal
            mongo_manager.delete_license(user.id)

            # Update license manager cache to remove cached license
            try:
                from utils.license_manager import LicenseManager
                if hasattr(LicenseManager, '_license_cache') and str(user.id) in LicenseManager._license_cache:
                    del LicenseManager._license_cache[str(user.id)]
                    logging.info(f"Cleared license cache for user {user.id}")
            except Exception as cache_error:
                logging.warning(f"Could not clear license cache for user {user.id}: {cache_error}")

            # Remove client role
            try:
                client_role = discord.utils.get(interaction.guild.roles, id=int(client_role_id))
                if client_role and client_role in user.roles:
                    await user.remove_roles(client_role)
                    logging.info(f"Removed client role from {user.name} in guild {interaction.guild.id}")
            except Exception as role_error:
                logging.error(f"Error removing client role: {role_error}")

            embed = discord.Embed(
                title="Access Removed",
                description=f"Successfully removed guild access for {user.mention}.\n\n**Note:** User's credentials and license have been completely cleared to prevent further access.",
                color=discord.Color.green()
            )

            await interaction.response.send_message(embed=embed)

            # Try to DM the user
            try:
                dm_embed = discord.Embed(
                    title="Guild Access Removed",
                    description=f"Your access to **{interaction.guild.name}** has been removed by an administrator.\n\nYour credentials and license have been cleared.",
                    color=discord.Color.orange()
                )
                await user.send(embed=dm_embed)
            except:
                logging.info(f"Could not DM {user.name} about access removal")

        except Exception as e:
            logging.error(f"Error removing guild access for user {user.id}: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while removing access: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="generate", description="Generate a receipt for a product")
    @app_commands.describe(
        productname="Name of the product",
        productprice="Price of the product",
        currency="Currency of the product (e.g., USD, EUR)",
        productsize="Size of the product (e.g., UK 8, M)",
        imagelink="Link to the product image"
    )
    async def generate(self, interaction: discord.Interaction, productname: str, productprice: float, currency: str, productsize: str, imagelink: str):
        # Check if user has access
        from utils.mongodb_manager import mongo_manager
        guild_id = interaction.guild.id
        user_id = interaction.user.id

        # Check server access
        server_access = mongo_manager.get_server_access(guild_id, user_id)
        # Check guild-specific license
        guild_license = mongo_manager.get_guild_user_license(guild_id, user_id)

        if not server_access and not guild_license:
            embed = discord.Embed(
                title="Access Denied",
                description="You do not have access to use this command. Please contact a server administrator.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Get guild configuration to retrieve generate_channel_id and client_role_id
        guild_config = mongo_manager.get_guild_config(guild_id)
        if not guild_config:
            embed = discord.Embed(
                title="Configuration Error",
                description="This server is not configured. Please run `/configure_guild` first.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        generate_channel_id = guild_config.get("generate_channel_id")
        client_role_id = guild_config.get("client_role_id")

        # Check if the command is run in the designated generate channel
        if str(interaction.channel.id) != generate_channel_id:
            embed = discord.Embed(
                title="Wrong Channel",
                description=f"Please use the `/generate` command in the <#{generate_channel_id}> channel.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Generate a unique reference number
        ref_number = f"REF-{random.randint(100000, 999999)}"

        # Format product price to always have 2 decimal places
        formatted_price = f"{productprice:.2f}"

        # Create embed for the receipt
        embed = discord.Embed(
            title="Your Order Has Shipped!",
            description=f"**Subject:** Your Fútbol Emotion order has been shipped.\n\n"
                        f"Dear {interaction.user.mention.split('#')[0]},\n\n"
                        f"We're excited to let you know that your order from Fútbol Emotion has been shipped!\n\n"
                        f"**Order Details:**\n"
                        f"- **Product:** {productname}\n"
                        f"- **Price:** {currency} {formatted_price}\n"
                        f"- **Size (UK):** {productsize}\n"
                        f"- **Reference:** {ref_number}\n\n"
                        f"**Shipping Information:**\n"
                        f"- **Shipping Cost:** {currency} 0.00\n"
                        f"- **Total:** {currency} {formatted_price}\n\n"
                        f"You can track your order using the reference number provided.\n\n"
                        f"Thank you for shopping with Fútbol Emotion!",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=imagelink)
        embed.set_footer(text="Shipped via Fútbol Emotion")

        # Send the receipt to the generate channel
        await interaction.response.send_message(embed=embed)

        # Optionally, send a confirmation to the user via DM
        try:
            dm_embed = discord.Embed(
                title="Order Shipped!",
                description=f"Your Fútbol Emotion order for **{productname}** has been shipped.\n"
                            f"Details have been sent to the generate channel.",
                color=discord.Color.blue()
            )
            await interaction.user.send(embed=dm_embed)
        except discord.Forbidden:
            logging.warning(f"Cannot DM user {interaction.user.name} about order shipment.")
        except Exception as e:
            logging.error(f"Error sending DM for order shipment: {e}")

    @app_commands.command(name="brands", description="Select a brand to generate a receipt")
    async def brands(self, interaction: discord.Interaction):
        # Check if user has access
        from utils.mongodb_manager import mongo_manager
        guild_id = interaction.guild.id
        user_id = interaction.user.id

        # Check server access
        server_access = mongo_manager.get_server_access(guild_id, user_id)
        # Check guild-specific license
        guild_license = mongo_manager.get_guild_user_license(guild_id, user_id)

        if not server_access and not guild_license:
            embed = discord.Embed(
                title="Access Denied",
                description="You do not have access to use this command. Please contact a server administrator.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Get guild configuration
        guild_config = mongo_manager.get_guild_config(guild_id)
        if not guild_config:
            embed = discord.Embed(
                title="Configuration Error",
                description="This server is not configured. Please run `/configure_guild` first.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if the command is run in the designated generate channel
        generate_channel_id = guild_config.get("generate_channel_id")
        if str(interaction.channel.id) != generate_channel_id:
            embed = discord.Embed(
                title="Wrong Channel",
                description=f"Please use the `/brands` command in the <#{generate_channel_id}> channel.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Dynamically create brand options from modals directory
        brand_files = []
        try:
            import os
            modals_dir = "modals"
            for filename in os.listdir(modals_dir):
                if filename.endswith('.py') and filename != '__init__.py' and filename != 'requirements.txt':
                    brand_name = filename[:-3]  # Remove .py extension
                    # Skip certain utility files
                    if brand_name not in ['stockx', 'requirements']:
                        brand_files.append(brand_name)
        except Exception as e:
            print(f"Error loading brands: {e}")
            brand_files = ["farfetch", "flannels", "futbolemotion", "arcteryx"]  # fallback
        
        # Create select options from available brands
        options = []
        for brand in sorted(brand_files)[:25]:  # Discord limit of 25 options
            # Capitalize brand names and add special handling for certain brands
            if brand == "farfetch":
                options.append(discord.SelectOption(label="Farfetch (Unavailable)", emoji="❌", value="farfetch"))
            elif brand == "arcteryx":
                options.append(discord.SelectOption(label="Arc'teryx", emoji="⛰️", value="arcteryx"))
            elif brand == "futbolemotion":
                options.append(discord.SelectOption(label="Fútbol Emotion", emoji="⚽", value="futbolemotion"))
            else:
                # Capitalize first letter for display
                display_name = brand.capitalize()
                options.append(discord.SelectOption(label=display_name, emoji="🛍️", value=brand))

        view = BrandSelectView(options)
        embed = discord.Embed(
            title="Select a Brand",
            description="Choose a brand from the dropdown below to start generating a receipt.",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# View for brand selection
class BrandSelectView(ui.View):
    def __init__(self, options):
        super().__init__(timeout=180)
        self.add_item(BrandSelectMenu(options))

# Select menu for brands
class BrandSelectMenu(ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Choose a brand...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        brand = self.values[0]

        try:
            if brand == "farfetch":
                # Farfetch is marked as unavailable
                embed = discord.Embed(
                    title="Brand Unavailable", 
                    description="Farfetch is currently unavailable. Please choose a different brand.", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Dynamically import and create modal based on brand selection
            modal_name = f"{brand}modal"
            
            # Import the modal from the corresponding brand module
            try:
                module = __import__(f'modals.{brand}', fromlist=[modal_name])
                modal_class = getattr(module, modal_name)
                modal = modal_class()
                await interaction.response.send_modal(modal)
            except ImportError as e:
                embed = discord.Embed(
                    title="Brand Module Not Found", 
                    description=f"The {brand.capitalize()} brand module could not be loaded. Please contact an administrator.", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except AttributeError as e:
                embed = discord.Embed(
                    title="Brand Modal Not Found", 
                    description=f"The {brand.capitalize()} modal class could not be found. Please contact an administrator.", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="Error", 
                description=f"An error occurred while processing your selection: {str(e)}", 
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(GuildCommands(bot))

# Setup database for guild configuration
def setup_guild_database():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Table for guild configurations
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS guild_configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT UNIQUE,
        owner_id TEXT,
        generate_channel_id TEXT,
        admin_role_id TEXT,
        client_role_id TEXT,
        image_channel_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Table for guild subscriptions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS guild_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        subscription_type TEXT,
        start_date TEXT,
        end_date TEXT,
        is_active INTEGER DEFAULT 1
    )
    ''')

    # Table for guild user access
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS server_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT,
        user_id TEXT,
        added_by TEXT,
        access_type TEXT,
        expiry TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(guild_id, user_id)
    )
    ''')

    conn.commit()
    conn.close()

# Guild configuration modal
class GuildConfigModal(ui.Modal, title="Guild Configuration"):
    generate_channel = ui.TextInput(
        label="Generate Channel ID",
        placeholder="Enter the channel ID for /generate command",
        required=True
    )

    admin_role = ui.TextInput(
        label="Admin Role ID",
        placeholder="Enter the admin role ID",
        required=True
    )

    client_role = ui.TextInput(
        label="Client Role ID",
        placeholder="Enter the client role ID",
        required=True
    )

    image_channel = ui.TextInput(
        label="Image Link Channel ID",
        placeholder="Enter the channel ID for image links",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Validate IDs
        try:
            generate_channel_id = int(self.generate_channel.value.strip())
            admin_role_id = int(self.admin_role.value.strip())
            client_role_id = int(self.client_role.value.strip())
            image_channel_id = int(self.image_channel.value.strip())

            # Save to MongoDB
            from utils.mongodb_manager import mongo_manager

            success = mongo_manager.save_guild_config(
                interaction.guild.id,
                interaction.user.id,
                generate_channel_id,
                admin_role_id,
                client_role_id,
                image_channel_id
            )

            if success:
                # Send success message
                embed = discord.Embed(
                    title="Success",
                    description="-# Information saved successfully!",
                    color=discord.Color.from_str("#c2ccf8")
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(
                    title="Error",
                    description="Failed to save configuration to database.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)

        except ValueError:
            # Handle invalid IDs
            embed = discord.Embed(
                title="Error",
                description="All IDs must be valid numbers.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            logging.error(f"Error in guild configuration: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

# Button view for guild configuration
class GuildConfigView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)  # 3 minute timeout

    @ui.button(label="Start", style=discord.ButtonStyle.primary)
    async def start_config(self, interaction: discord.Interaction, button: ui.Button):
        # Show the configuration modal
        await interaction.response.send_modal(GuildConfigModal())

class GuildCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        setup_guild_database()

    async def is_guild_admin(self, interaction: discord.Interaction):
        """Check if the user is a guild admin based on configured role"""
        if interaction.guild is None:
            return False

        # Check if this is the main guild owner
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                if str(interaction.user.id) == config.get("owner_id"):
                    return True
        except Exception as e:
            logging.error(f"Error checking owner status: {e}")

        # Check if user has guild admin role
        from utils.mongodb_manager import mongo_manager
        guild_config = mongo_manager.get_guild_config(interaction.guild.id)

        if not guild_config:
            return False

        admin_role_id = int(guild_config.get("admin_role_id"))
        admin_role = discord.utils.get(interaction.guild.roles, id=admin_role_id)

        if admin_role and admin_role in interaction.user.roles:
            return True

        return False

    async def has_guild_subscription(self, user_id):
        """Check if a user has an active guild subscription"""
        try:
            from utils.mongodb_manager import mongo_manager

            # Get user's license from MongoDB
            license_doc = mongo_manager.get_license(user_id)

            if not license_doc:
                return False

            key = license_doc.get("key", "")
            expiry_str = license_doc.get("expiry")

            # Check if it's a guild subscription key
            if not (key and ("guild" in key.lower() or "guild_30days" in key or "guild_lifetime" in key)):
                return False

            # Check if it's a lifetime guild subscription
            if "guild_lifetime" in key or "lifetime" in key.lower():
                return True

            # Check expiry for time-limited guild subscriptions
            if expiry_str:
                try:
                    expiry_date = datetime.strptime(expiry_str, '%d/%m/%Y %H:%M:%S')
                    return datetime.now() < expiry_date
                except Exception as e:
                    logging.error(f"Error parsing expiry date: {e}")

            return False

        except Exception as e:
            logging.error(f"Error checking guild subscription: {e}")
            return False

    @app_commands.command(name="configure_guild", description="Configure the bot for your guild")
    async def configure_guild(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # First check if user has guild subscription
        has_subscription = await self.has_guild_subscription(user_id)

        # If this is the main guild owner, allow configuration regardless
        is_owner = False
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                if user_id == config.get("owner_id"):
                    is_owner = True
                    has_subscription = True
        except Exception as e:
            logging.error(f"Error checking owner status: {e}")

        if not has_subscription and not is_owner:
            embed = discord.Embed(
                title="Access Denied",
                description="You need a Guild subscription to configure the bot for your server.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check the guild context
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                main_guild_id = config.get("guild_id", "1412488621293961226")

            # Get bot application info for invite link
            app_info = await self.bot.application_info()
            client_id = app_info.id

            # Create invite link with proper permissions
            invite_permissions = discord.Permissions(
                send_messages=True,
                embed_links=True,
                attach_files=True,
                read_messages=True,
                read_message_history=True,
                manage_roles=True,
                use_application_commands=True
            )
            invite_link = discord.utils.oauth_url(
                client_id,
                permissions=invite_permissions,
                scopes=["bot", "applications.commands"]
            )

            # Check if we're in the main guild or a user guild
            if str(interaction.guild.id) == main_guild_id:
                # If in main guild, show invite link
                embed = discord.Embed(
                    title="Configure Your Guild Bot",
                    description=f"Please invite the bot to your server and then run the command there. You can do so by clicking the link below:",
                    color=discord.Color.from_str("#c2ccf8")
                )
                embed.add_field(
                    name="Bot Invite Link",
                    value=f"[Click here to invite the bot]({invite_link})"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                # If in user guild, show configuration
                embed = discord.Embed(
                    title="Configure Your Guild",
                    description="-# Click the button below to start the setup process.",
                    color=discord.Color.from_str("#c2ccf8")
                )
                view = GuildConfigView()
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            logging.error(f"Error in configure_guild command: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="add_access", description="Add access for a user in your guild")
    @app_commands.describe(
        user="The user to grant access to",
        days="Number of days for access (0 for lifetime)"
    )
    async def add_access(self, interaction: discord.Interaction, user: discord.Member, days: int):
        # Check if user is a guild admin
        is_admin = await self.is_guild_admin(interaction)

        if not is_admin:
            embed = discord.Embed(
                title="Access Denied",
                description="You must have the admin role to use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Get guild configuration
        from utils.mongodb_manager import mongo_manager
        guild_config = mongo_manager.get_guild_config(interaction.guild.id)

        if not guild_config:
            embed = discord.Embed(
                title="Error",
                description="This server has not been configured yet. Please use `/configure_guild` first.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        generate_channel_id = guild_config.get("generate_channel_id")
        client_role_id = guild_config.get("client_role_id")

        # Calculate expiry date
        if days == 0:
            # Lifetime access
            expiry_date = datetime.now() + timedelta(days=3650)  # ~10 years
            access_type = "Lifetime"
        else:
            # Temporary access
            expiry_date = datetime.now() + timedelta(days=days)
            access_type = f"{days} Days"

        # Add or update user access in MongoDB
        expiry_str = expiry_date.strftime("%Y-%m-%d %H:%M:%S")

        # Save server access record
        mongo_manager.save_server_access(
            interaction.guild.id,
            user.id,
            interaction.user.id,
            access_type,
            expiry_str
        )

        # Create guild-specific license for the user
        license_data = {
            "key": f"guild-access-{interaction.guild.id}-{user.id}",
            "expiry": expiry_date.strftime('%d/%m/%Y %H:%M:%S'),
            "subscription_type": access_type.lower().replace(" ", ""),
            "redeemed": True,
            "redeemed_at": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            "granted_by": str(interaction.user.id)
        }

        mongo_manager.save_guild_user_license(interaction.guild.id, user.id, license_data)

        # Try to add client role to the user
        try:
            client_role = discord.utils.get(interaction.guild.roles, id=int(client_role_id))
            if client_role:
                await user.add_roles(client_role)
                print(f"Added client role {client_role_id} to user {user.id} in guild {interaction.guild.id}")
            else:
                print(f"Client role {client_role_id} not found in guild {interaction.guild.id}")
        except Exception as e:
            logging.error(f"Error adding client role: {e}")
            print(f"Failed to add role {client_role_id} to user {user.id}: {e}")

        # Send public notification
        embed = discord.Embed(
            title="Access Granted",
            description=f"Successfully added `{access_type}` access to {user.mention}\n\n"
                        f"» Go to <#{generate_channel_id}> and Run command `/generate`",
            color=discord.Color.green()
        )

        await interaction.response.send_message(embed=embed)


# View for brand selection
class BrandSelectView(ui.View):
    def __init__(self, options):
        super().__init__(timeout=180)
        self.add_item(BrandSelectMenu(options))

# Select menu for brands
class BrandSelectMenu(ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Choose a brand...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        brand = self.values[0]

        try:
            if brand == "farfetch":
                # Farfetch is marked as unavailable
                embed = discord.Embed(
                    title="Brand Unavailable", 
                    description="Farfetch is currently unavailable. Please choose a different brand.", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Dynamically import and create modal based on brand selection
            modal_name = f"{brand}modal"
            
            # Import the modal from the corresponding brand module
            try:
                module = __import__(f'modals.{brand}', fromlist=[modal_name])
                modal_class = getattr(module, modal_name)
                modal = modal_class()
                await interaction.response.send_modal(modal)
            except ImportError as e:
                embed = discord.Embed(
                    title="Brand Module Not Found", 
                    description=f"The {brand.capitalize()} brand module could not be loaded. Please contact an administrator.", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except AttributeError as e:
                embed = discord.Embed(
                    title="Brand Modal Not Found", 
                    description=f"The {brand.capitalize()} modal class could not be found. Please contact an administrator.", 
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="Error", 
                description=f"An error occurred while processing your selection: {str(e)}", 
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(GuildCommands(bot))