import os
import discord
import random
import sqlite3
import datetime
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

# Create a database to store user data
def setup_database():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Table for user emails
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_emails (
        user_id TEXT PRIMARY KEY,
        email TEXT
    )
    ''')

    # Table for user custom credentials
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_credentials (
        user_id TEXT PRIMARY KEY,
        name TEXT,
        street TEXT,
        city TEXT,
        zip TEXT,
        country TEXT,
        is_random BOOLEAN DEFAULT 0
    )
    ''')

    # Table for user subscriptions - now with unlimited access by default
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_subscriptions (
        user_id TEXT PRIMARY KEY,
        subscription_type TEXT DEFAULT 'Unlimited',
        start_date TEXT,
        end_date TEXT,
        is_active BOOLEAN DEFAULT 1
    )
    ''')

    # Table to store total number of brands available
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')

    # Insert default value for total brands if not exists
    cursor.execute("INSERT OR IGNORE INTO system_config (key, value) VALUES (?, ?)", 
                  ("total_brands", "100"))

    conn.commit()
    conn.close()

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
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Check credentials
    cursor.execute("SELECT * FROM user_credentials WHERE user_id = ?", (user_id,))
    has_credentials = cursor.fetchone() is not None

    # Check email
    cursor.execute("SELECT * FROM user_emails WHERE user_id = ?", (user_id,))
    has_email = cursor.fetchone() is not None

    conn.close()

    return has_credentials, has_email

# Add or update user subscription
def update_subscription(user_id, subscription_type="Unlimited", days=365):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)

    # Format dates as strings
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    # Insert or update subscription
    cursor.execute('''
    INSERT OR REPLACE INTO user_subscriptions
    (user_id, subscription_type, start_date, end_date, is_active)
    VALUES (?, ?, ?, ?, 1)
    ''', (user_id, subscription_type, start_str, end_str))

    conn.commit()
    conn.close()

# Get user subscription info
def get_subscription(user_id):
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        # Check if the licenses table has the required columns
        try:
            # First check licenses table for expiry and key
            cursor.execute("SELECT key, expiry FROM licenses WHERE owner_id = ?", (str(user_id),))
            license_data = cursor.fetchone()

            if license_data:
                key, expiry_str = license_data
                # Check if lifetime key
                if key and key.startswith("LifetimeKey"):
                    return "Lifetime", "Lifetime"
                else:
                    return "Premium", expiry_str
        except sqlite3.OperationalError as e:
            # Handle missing columns
            print(f"License table error: {e}")
            # Continue to fallback method

        # Check old subscriptions table as fallback
        try:
            cursor.execute("SELECT subscription_type, end_date FROM user_subscriptions WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                return result[0], result[1]
        except sqlite3.OperationalError:
            # Table might not exist
            pass

        # Create default subscription if none exists
        return "Default", "1 Year"
    except Exception as e:
        print(f"Error in get_subscription: {e}")
        return "Default", "1 Year"
    finally:
        try:
            conn.close()
        except:
            pass

# Get total brands count
def get_total_brands():
    # Count actual available modal files
    import os
    modal_files = [f for f in os.listdir('modals') if f.endswith('.py') and not f.startswith('__')]
    count = len(modal_files)

    # Update the count in the database
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    cursor.execute("INSERT OR REPLACE INTO system_config (key, value) VALUES (?, ?)", 
                  ("total_brands", str(count)))
    conn.commit()
    conn.close()

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
                description="Your iCloud email was not saved since receipt delivery to iCloud mail won't function. Please change it to **Gmail, Outlook or Yahoo** for successful delivery.\n\n-# This way you won't waste your credits",
                color=discord.Color.from_str("#c2ccf8")
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        # Save email to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO user_emails (user_id, email) VALUES (?, ?)", (user_id, email))
        conn.commit()
        conn.close()

        # Send success message to user
        success_embed = discord.Embed(
            title="Success",
            description=f"-# Your email has been set to: `{email}`",
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

        # Save custom info to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO user_credentials 
        (user_id, name, street, city, zip, country, is_random) 
        VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (user_id, self.name.value, self.street.value, self.city.value, 
              self.zip_code.value, self.country.value))
        conn.commit()
        conn.close()

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
    def __init__(self, page=1):
        self.page = page

        # List only the brands that have actual modal implementations
        # This automatically detects brands from the modals folder
        import os
        available_brands = []

        # Get modal files from the modals directory
        modal_files = [f for f in os.listdir('modals') if f.endswith('.py') and not f.startswith('__')]

        # Extract brand names from the filenames
        for modal_file in modal_file:
            brand_name = modal_file.split('.')[0].capitalize()
            available_brands.append(brand_name)

        # Sort alphabetically
        available_brands.sort()

        # Show only 10 brands per page
        start_idx = (page - 1) * 15
        end_idx = min(start_idx + 15, len(available_brands))

        # If page is out of bounds, reset to page 1
        if start_idx >= len(available_brands):
            self.page = 1
            start_idx = 0
            end_idx = min(15, len(available_brands))

        current_brands = available_brands[start_idx:end_idx]

        options = [discord.SelectOption(label=brand, value=brand.lower()) for brand in current_brands]

        super().__init__(placeholder="Choose a brand...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        brand = self.values[0]

        user_id = str(interaction.user.id)

        # Check if user has both credentials and email set up
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
                "chewforever": "Chewforevermodal"
                # Add other special cases as needed
            }

            if brand in special_cases:
                modal_class_name = special_cases[brand]

            # Dynamic import of the module
            try:
                import importlib
                modal_module = importlib.import_module(module_name)

                # Get the modal class dynamically
                modal_class = getattr(modal_module, modal_class_name)

                # Create the modal instance
                modal = modal_class()

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
        self.add_item(BrandSelectDropdown(page))
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

# View for the credentials dropdown menu
class CredentialsDropdownView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)  # Set timeout to 3 minutes
        self.user_id = user_id
        self.last_interaction = datetime.now()
        self.message = None

        # Create dropdown menu (moved from on_timeout to init)
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
                    description="Generate random details",
                    emoji="🌐"
                ),
                discord.SelectOption(
                    label="Clear Info", 
                    description="Remove all saved data",
                    emoji="🗑️"
                ),
                discord.SelectOption(
                    label="Email", 
                    description="Update your email address",
                    emoji="📧"
                )
            ]
        )

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

    @ui.button(label="Go Back", style=discord.ButtonStyle.danger, custom_id="go_back")
    async def go_back(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return

        # Create menu panel (with updated format)
        subscription_type, end_date = get_subscription(self.user_id)

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
            description=(f"Hello <@{self.user_id}>, you have `Lifetime` subscription.\n" if subscription_type == "Lifetime" else
                        f"Hello <@{self.user_id}>, you have until `{end_date}` before your subscription ends.\n") +
                        "-# pick an option below to continue\n\n" +
                        "**Subscription Type**\n" +
                        f"`{display_type}`\n\n" +
                        "**Note**\n" +
                        "-# please click \"Credentials\" and set your credentials before you try to generate",
            color=discord.Color.from_str("#c2ccf8")
        )

        await interaction.response.edit_message(embed=embed, view=MenuView(self.user_id))

    async def dropdown_callback(self, interaction: discord.Interaction):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return

        selected = self.dropdown.values[0]

        if selected == "Custom Info":
            # Show custom info form
            await interaction.response.send_modal(CustomInfoForm())

        elif selected == "Random Info":
            # Generate random info
            name, street, city, zip_code, country = generate_random_details()

            # Save to database
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO user_credentials 
            (user_id, name, street, city, zip, country, is_random) 
            VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (self.user_id, name, street, city, zip_code, country))
            conn.commit()
            conn.close()

            # Display random info to the user
            success_embed = discord.Embed(
                title="Success",
                description=f"Randomized Information for <@{self.user_id}>.\n\n" +
                            f"Name: {name}\n" +
                            f"Street: {street}\n" +
                            f"City: {city}\n" +
                            f"ZIP: {zip_code}\n" +
                            f"Country: {country}",
                color=discord.Color.from_str("#c2ccf8")
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)

            # Update the credentials panel in real-time
            has_credentials, has_email = check_user_setup(self.user_id)

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

            # Try to update the original message, catch permission errors
            try:
                await interaction.message.edit(embed=updated_embed)
            except discord.errors.Forbidden:
                # Send as a new message instead if we can't edit the original
                await interaction.followup.send(embed=updated_embed, ephemeral=True)

        elif selected == "Clear Info":
            # Clear user data
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_credentials WHERE user_id = ?", (self.user_id,))
            cursor.execute("DELETE FROM user_emails WHERE user_id = ?", (self.user_id,))
            conn.commit()
            conn.close()

            # Send success message to the user
            success_embed = discord.Embed(
                title="Success",
                description="-# Your saved info has been cleared.",
                color=discord.Color.from_str("#c2ccf8")
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)

            # Update the credentials panel in real-time
            has_credentials, has_email = check_user_setup(self.user_id)

            # Create updated credentials panel with current status
            updated_embed = discord.Embed(
                title="Credentials",
                description="Please make sure both options below are 'True'\n\n" +
                            "**Info**\n" +
                            f"{'True' if has_credentials else 'False'}\n\n" +
                            "**Email**\n" +
                            f"{'True' if has_email else 'False'}",
                color=discord.Color.from_str("#c2ccf8")
            )

            # Try to update the original message, catch permission errors
            try:
                await interaction.message.edit(embed=updated_embed)
            except discord.errors.Forbidden:
                # Send as a new message instead if we can't edit the original
                await interaction.followup.send(embed=updated_embed, ephemeral=True)

        elif selected == "Email":
            # Show email form
            await interaction.response.send_modal(EmailForm())

# View for the credentials panel
class CredentialsView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)  # Set timeout to 3 minutes
        self.user_id = user_id
        self.last_interaction = datetime.now()

    async def interaction_check(self, interaction):
        # Update last interaction time on every interaction
        self.last_interaction = datetime.now()
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
            await self.message.edit(embed=timeout_embed, view=None)
        except Exception as e:
            print(f"Error in timeout handling: {e}")

    @ui.button(label="Go Back", style=discord.ButtonStyle.danger, custom_id="go_back")
    async def go_back(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return

        # Create menu panel (with updated format)
        subscription_type, end_date = get_subscription(self.user_id)

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
                        f"Hello <@{user_id}>, you have until `{end_date}` before your subscriptionends.\n") +
                        "-# pick an option below to continue\n\n" +
                        "**Subscription Type**\n" +
                        f"`{display_type}`\n\n" +
                        "**Note**\n" +
                        "-# please click \"Credentials\" and set your credentials before you try to generate",
            color=discord.Color.from_str("#c2ccf8")
        )

        await interaction.response.edit_message(embed=embed, view=MenuView(self.user_id))

# View for the main menu
class MenuView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180)  # Set timeout to 3 minutes
        self.user_id = user_id
        self.last_interaction = datetime.now()
        self.message = None # Store the message object

    async def interaction_check(self, interaction):
        # Update last interaction time on everyinteraction
        self.last_interaction = datetime.now()
        ## Reset timeout on interaction
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

        # Add URL buttons for Help and Brands
        help_button = ui.Button(
            label="Help", 
            style=discord.ButtonStyle.gray, 
            url="https://discord.com/channels/1339298010169086072/1339520924596043878"
        )
        brands_button = ui.Button(
            label="Brands", 
            style=discord.ButtonStyle.gray, 
            url="https://discord.com/channels/1339298010169086072/1339306570634236038"
        )
        self.add_item(help_button)
        self.add_item(brands_button)

    @ui.button(label="Generate", style=discord.ButtonStyle.gray, custom_id="generate")
    async def generate(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return

        # Check if user has credentials and email
        has_credentials, has_email = check_user_setup(self.user_id)

        if not has_credentials or not has_email:
            embed = discord.Embed(
                title="Setup Required",
                description="**Note**\n-# Please click on \"Credentials\" button and set up your credentials before you try to generate.",
                color=discord.Color.from_str("#c2ccf8")
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Create generator panel
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

        view = BrandSelectView(self.user_id)
        message = await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

        # Store the message for proper timeout handling
        try:
            # Get the message if it's not already available directly
            if not message:
                message = await interaction.original_response()
            view.message = message
        except Exception as e:
            print(f"Failed to get message reference: {e}")

    @ui.button(label="Credentials", style=discord.ButtonStyle.gray, custom_id="credentials")
    async def credentials(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return

        # Get user setup status
        has_credentials, has_email = check_user_setup(self.user_id)

        # Create credentials panel
        embed = discord.Embed(
            title="Credentials",
            description="Please make sure both options below are 'True'\n\n" +
                        "**Info**\n" +
                        f"{'True' if has_credentials else 'False'}\n\n" +
                        "**Email**\n" +
                        f"{'True' if has_email else 'False'}",
            color=discord.Color.from_str("#c2ccf8")
        )

        # Create view and store message reference
        view = CredentialsDropdownView(self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

        # Store message reference for proper timeout handling
        try:
            message = await interaction.original_response()
            view.message = message
        except Exception as e:
            print(f"Failed to get message reference for credentials panel: {e}")

    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.message = None # Initialize message attribute

        # Add URL buttons for Help and Brands
        help_button = ui.Button(
            label="Help", 
            style=discord.ButtonStyle.gray, 
            url="https://discord.com/channels/1339298010169086072/1339520924596043878"
        )
        self.add_item(help_button)

        brands_button = ui.Button(
            label="Brands", 
            style=discord.ButtonStyle.gray, 
            url="https://discord.com/channels/1339298010169086072/1339306570634236038"
        )
        self.add_item(brands_button)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

    # Set up database
    setup_database()
    
    # Set up guild subscription tables
    from utils.guild_manager import GuildManager
    GuildManager.setup_guild_tables()
    
    # Start guild subscription checker
    bot.loop.create_task(GuildManager.check_guild_subscriptions_loop(bot))
    
    # Start all registered guild bots
    async def start_all_guild_bots():
        await bot.wait_until_ready()
        
        try:
            import os
            import subprocess
            import sqlite3
            
            # Create directory for guild bots if it doesn't exist
            os.makedirs("guild_bots", exist_ok=True)
            
            # Get all active guild subscriptions with bot tokens
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute('''
            SELECT user_id, bot_token 
            FROM guild_subscriptions 
            WHERE is_active = 1 AND bot_token IS NOT NULL AND bot_token != ''
            ''')
            
            guild_bots = cursor.fetchall()
            conn.close()
            
            for user_id, bot_token in guild_bots:
                try:
                    # Create a directory for this guild bot if it doesn't exist
                    guild_bot_dir = f"guild_bots/{user_id}"
                    os.makedirs(guild_bot_dir, exist_ok=True)
                    
                    # Create bot file using the template
                    bot_file_path = f"{guild_bot_dir}/bot.py"
                    
                    # Import the template
                    from utils.guild_bot_template import TEMPLATE
                    
                    # Write the bot file with the template
                    with open(bot_file_path, "w") as f:
                        f.write(TEMPLATE.format(
                            owner_id=user_id,
                            bot_token=bot_token
                        ))
                    
                    # Start the bot in a subprocess
                    subprocess.Popen(["python", bot_file_path], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE,
                                    cwd=os.getcwd())
                    
                    print(f"Started guild bot for user {user_id}")
                except Exception as e:
                    print(f"Error starting guild bot for user {user_id}: {e}")
            
            print(f"Started {len(guild_bots)} guild bots")
        except Exception as e:
            print(f"Error starting guild bots: {e}")
    
    # Start all guild bots when the main bot starts
    bot.loop.create_task(start_all_guild_bots())
    
@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check if message is in a guild (server)
    if message.guild:
        guild_id = str(message.guild.id)
        
        # Check if the guild has been configured
        from utils.guild_manager import GuildManager
        guild_config = GuildManager.get_guild_config(guild_id)
        
        if guild_config and guild_config.get("image_channel_id"):
            # Check if the message is in the guild's configured image channel
            if str(message.channel.id) == guild_config.get("image_channel_id"):
                # Check if the message has an attachment
                if message.attachments:
                    for attachment in message.attachments:
                        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                            # Reply to the user's message with the image URL
                            await message.reply(f"```\n{attachment.url}\n```", mention_author=True)
                            return
    
    # Check if the message is in the main bot's image URL channel
    if message.channel.id == 1375843777406570516:
        # Check if the message has an attachment
        if message.attachments:
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                    # Reply to the user's message with the image URL
                    await message.reply(f"```\n{attachment.url}\n```", mention_author=True)
                    
    # Process commands
    await bot.process_commands(message)

    # Initialize license database tables if needed
    import os
    if os.path.exists('utils/db_init.py'):
        from utils.db_init import init_db
        init_db()

    # Restore license cache from backup for faster startup validation
    try:
        from utils.license_backup import LicenseBackup
        # Restore existing licenses to cache
        await LicenseBackup.restore_licenses_to_cache()
        # Start backup scheduler in background
        bot.loop.create_task(LicenseBackup.start_backup_scheduler())
        print("License backup system initialized")
    except Exception as e:
        print(f"Failed to initialize license backup system: {e}")

    # Initialize license checker for expired subscriptions
    try:
        from utils.license_manager import LicenseManager
        license_manager = LicenseManager(bot)
        await license_manager.start_license_checker()
        print("License checker started")
    except Exception as e:
        print(f"Failed to start license checker: {e}")

    # Load admin commands
    try:
        if not os.path.exists('commands'):
            os.makedirs('commands')
        await bot.load_extension('commands.admin_commands')
        print("Admin commands loaded")
    except Exception as e:
        print(f"Failed to load admin commands: {e}")

    # Sync commands with Discord
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="generate", description="Generate receipts with GOAT Receipts")
async def generate_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    # If in a guild, check if it's configured and if we should use the guild-specific settings
    if interaction.guild:
        guild_id = str(interaction.guild.id)
        
        # Check if guild is configured
        from utils.guild_manager import GuildManager
        guild_config = GuildManager.get_guild_config(guild_id)
        
        if guild_config:
            # Check if this is the configured generator channel
            generator_channel_id = guild_config.get("generator_channel_id")
            
            if generator_channel_id and str(interaction.channel_id) != generator_channel_id:
                embed = discord.Embed(
                    title="Command Restricted",
                    description=f"This command can only be used in <#{generator_channel_id}> in this server.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Check if user has access in this guild
            has_access, message = GuildManager.check_user_access(guild_id, user_id)
            
            if not has_access:
                embed = discord.Embed(
                    title="Access Denied",
                    description=f"You don't have access to use this command in this server. {message}",
                    color=discord.Color.red()
                )
                
                # Add a button for server admins to grant access
                view = discord.ui.View()
                view.add_item(discord.ui.Button(
                    label="Contact Admin", 
                    style=discord.ButtonStyle.link, 
                    url=f"https://discord.com/channels/{guild_id}/{generator_channel_id}"
                ))
                
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                return
    else:
        # For DMs or the main bot server, check the original allowed channel
        allowed_channel_id = 1374468007472009216
        if interaction.channel_id != allowed_channel_id:
            embed = discord.Embed(
                title="Command Restricted",
                description=f"This command can only be used in <#{allowed_channel_id}>",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Check if user has a valid license for the main bot
        try:
            from utils.license_manager import LicenseManager
            license_status = await LicenseManager.is_subscription_active(user_id)

            # Handle different return types - could be bool or dict
            is_active = False
            if isinstance(license_status, dict):
                is_active = license_status.get("active", False)
            else:
                is_active = bool(license_status)

            if not is_active:
                # Check if it's an expired license with expiry date (if license_status is dict)
                if isinstance(license_status, dict) and "expired_date" in license_status:
                    expired_date = license_status["expired_date"]
                    embed = discord.Embed(
                        title="Subscription Expired",
                        description=f"Your subscription expired on `{expired_date}`. Please renew your subscription to continue using our services.",
                        color=discord.Color.red()
                    )

                    # Create a view with a "Renew" button that redirects to goatreceipts.com
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label="Renew", style=discord.ButtonStyle.link, url="https://goatreceipts.com"))
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                else:
                    # User never had a license
                    embed = discord.Embed(
                        title="Access Denied",
                        description="You need to buy a **[subscription](https://goatreceipts.com)** to use our services\n-# Be aware that it costs us money to run the bot.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        except Exception as e:
            print(f"Error checking license for {user_id}: {e}")
            # Always deny access if there's any error
            embed = discord.Embed(
                title="Access Denied",
                description="There was an error checking your subscription. Please try again later or contact support.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

    # Check if user has credentials and email
    has_credentials, has_email = check_user_setup(user_id)

    if not has_credentials or not has_email:
        # Show menu panel for new users
        # Create menu panel (with updated format)
        subscription_type, end_date = get_subscription(user_id)

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

# License key redemption form
class RedeemKeyModal(ui.Modal, title="Redeem License Key"):
    license_key = ui.TextInput(
        label="License Key",
        placeholder="Enter your unique license key",
        required=True,
        min_length=3,
        max_length=20
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
            is_guild_key = result.get("is_guild_key", False)

            if is_guild_key:
                # Handle guild subscription key
                embed = discord.Embed(
                    title="Guild License Key Redeemed Successfully",
                    description=f"Your guild subscription has been activated:\n\n**Subscription Type**: {subscription_type}\n**Expires On**: {expiry_date}",
                    color=discord.Color.green()
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # Send notification to Purchases channel
                try:
                    purchases_channel = interaction.client.get_channel(1374468080817803264)
                    if purchases_channel:
                        # Create notification embed for guild subscription
                        notification_embed = discord.Embed(
                            title="Thank you for purchasing",
                            description=f"{interaction.user.mention}, your guild subscription has been updated. Check below\n"
                                       f"-# Run command **/register_bot** in <#1374468007472009216> to continue\n\n"
                                       f"**Subscription**\n"
                                       f"`Guild`\n\n"
                                       f"**Consider leaving a review!**\n"
                                       f"Please consider leaving a review at <#1339306483816337510>",
                            color=discord.Color.green()
                        )

                        await purchases_channel.send(content=interaction.user.mention, embed=notification_embed)

                        # Send DM to user
                        try:
                            await interaction.user.send(embed=notification_embed)
                        except:
                            print(f"Could not send DM to {interaction.user.display_name}")
                except Exception as e:
                    print(f"Error sending guild subscription notification: {e}")
                
            else:
                # Handle regular subscription key
                # Connect to database
                import sqlite3
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()

                # Generate license key based on subscription type
                key_prefix = subscription_type
                license_key = f"{key_prefix}-{user_id}"

                # Add user to licenses table with correct fields
                cursor.execute('''
                INSERT OR REPLACE INTO licenses 
                (owner_id, key, expiry, emailtf, credentialstf) 
                VALUES (?, ?, ?, 'False', 'False')
                ''', (user_id, license_key, expiry_date))

                # Update the LicenseManager cache to recognize this license immediately
                from utils.license_manager import LicenseManager
                now = datetime.now()
                expiry_dt = datetime.strptime(expiry_date, '%d/%m/%Y %H:%M:%S')
                is_lifetime = 'lifetime' in subscription_type.lower()

                # Update the cache with the new license
                LicenseManager._license_cache[user_id] = (expiry_dt, is_lifetime)

                # Trigger a backup of licenses
                try:
                    from utils.license_backup import LicenseBackup
                    self.bot.loop.create_task(LicenseBackup.backup_licenses())
                except Exception as e:
                    print(f"Error backing up licenses: {e}")

                conn.commit()
                conn.close()

                # Success message
                embed = discord.Embed(
                    title="License Key Redeemed Successfully",
                    description=f"Your subscription has been activated:\n\n**Subscription Type**: {subscription_type}\n**Expires On**: {expiry_date}",
                    color=discord.Color.green()
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)

                # Try to add client role to the user
                try:
                    with open("config.json", "r") as f:
                        import json
                        config = json.load(f)
                        client_role_id = int(config.get("Client_ID", 0))

                    if client_role_id > 0:
                        guild = self.interaction.guild  # Access guild through the stored interaction
                        if guild:
                            role = discord.utils.get(guild.roles, id=client_role_id)
                            if role:
                                await self.interaction.user.add_roles(role)  # Use stored interaction to add roles
                                print(f"Added role {role.name} to {self.interaction.user.display_name}")
                except Exception as e:
                    print(f"Error adding role: {e}")

                # Send notification to Purchases channel
                try:
                    purchases_channel = interaction.client.get_channel(1374468080817803264)
                    if purchases_channel:
                        # Clean up subscription type display
                        display_type = subscription_type
                        if subscription_type == "3day":
                            display_type = "3 Days"
                        elif subscription_type == "14day":
                            display_type = "14 Days"
                        elif subscription_type == "1month":
                            display_type = "1 Month"

                        # Create notification embed
                        notification_embed = discord.Embed(
                            title="Thank you for purchasing",
                            description=f"{interaction.user.mention}, your subscription has been updated. Check below\n"
                                       f"-# Run command /generate in <#1369426783153160304> to continue\n\n"
                                       f"**Subscription Type**\n"
                                       f"`{display_type}`\n\n"
                                       f"- Please consider leaving a review at ⁠<#1339306483816337510>",
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

        else:
            # Error handling
            if result["error"] == "already_used":
                embed = discord.Embed(
                    title="Key Already Used",
                    description="This license key has already been redeemed.",
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
        
        # Check if this is a guild key
        is_guild_key = False
        actual_type = subscription_type
        
        if subscription_type == "guild_30days":
            is_guild_key = True
            actual_type = "30days"
        elif subscription_type == "guild_lifetime":
            is_guild_key = True
            actual_type = "lifetime"
        
        # Generate the keys
        keys = key_manager.generate_keys(actual_type, guild_key=is_guild_key)

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

    embed = discord.Embed(
        title="Redeem License Key",
        description="Click on the button `Redeem` then submit your **unique Key**. You should receive access automatically. Each key can only be used **once**. If there is issue with you key head over to <#1339335959652602010> and open ticket describing your issue!",
        color=discord.Color.green()
    )

    view = RedeemKeyView()
    await interaction.response.send_message(embed=embed, view=view)

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

# Register Bot Token Modal
class RegisterBotModal(ui.Modal, title="Register Bot Token"):
    bot_token = ui.TextInput(
        label="Bot Token",
        placeholder="Enter your Discord bot token",
        style=discord.TextStyle.paragraph,
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        token = self.bot_token.value.strip()
        
        # Register the bot token
        from utils.guild_manager import GuildManager
        success, message = GuildManager.register_bot_token(user_id, token)
        
        if success:
            embed = discord.Embed(
                title="Bot Token Registered",
                description=message,
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Registration Failed",
                description=message,
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Guild Configuration Modal
class GuildConfigModal(ui.Modal, title="Configure Guild"):
    generator_channel = ui.TextInput(
        label="Generator Channel ID",
        placeholder="Channel ID for the /generate command",
        required=True
    )
    
    admin_role = ui.TextInput(
        label="Admin Role ID",
        placeholder="Role ID for administrators",
        required=True
    )
    
    client_role = ui.TextInput(
        label="Client Role ID",
        placeholder="Role ID for clients with access",
        required=True
    )
    
    image_channel = ui.TextInput(
        label="Image Link Channel ID",
        placeholder="Channel ID for image links",
        required=True
    )
    
    purchases_channel = ui.TextInput(
        label="Purchases Channel ID (Optional)",
        placeholder="Channel ID for purchase notifications",
        required=False
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild_id = str(interaction.guild.id)
        
        # Get input values
        generator_channel_id = self.generator_channel.value.strip()
        admin_role_id = self.admin_role.value.strip()
        client_role_id = self.client_role.value.strip()
        image_channel_id = self.image_channel.value.strip()
        purchases_channel_id = self.purchases_channel.value.strip() if self.purchases_channel.value else None
        
        # Validate channel and role IDs
        valid_ids = True
        try:
            # Check if channels exist
            for channel_id in [generator_channel_id, image_channel_id]:
                channel = interaction.guild.get_channel(int(channel_id))
                if not channel:
                    valid_ids = False
                    break
            
            # Check purchases channel if provided
            if purchases_channel_id:
                channel = interaction.guild.get_channel(int(purchases_channel_id))
                if not channel:
                    valid_ids = False
            
            # Check if roles exist
            for role_id in [admin_role_id, client_role_id]:
                role = interaction.guild.get_role(int(role_id))
                if not role:
                    valid_ids = False
                    break
        except (ValueError, TypeError):
            valid_ids = False
        
        if not valid_ids:
            embed = discord.Embed(
                title="Configuration Failed",
                description="One or more of the provided IDs are invalid. Please make sure all IDs are correct.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Save the configuration
        from utils.guild_manager import GuildManager
        success = GuildManager.save_guild_config(
            guild_id, user_id, generator_channel_id, admin_role_id, 
            client_role_id, image_channel_id, purchases_channel_id
        )
        
        if success:
            embed = discord.Embed(
                title="Success",
                description="-# Information saved successfully",
                color=discord.Color.from_str("#c2ccf8")
            )
        else:
            embed = discord.Embed(
                title="Configuration Failed",
                description="There was an error saving your configuration. Please try again.",
                color=discord.Color.red()
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Configure Guild button view
class ConfigureGuildView(ui.View):
    def __init__(self):
        super().__init__(timeout=180)  # Set timeout to 3 minutes
    
    @ui.button(label="Start", style=discord.ButtonStyle.primary)
    async def start_setup(self, interaction: discord.Interaction, button: ui.Button):
        # Show the configuration modal
        await interaction.response.send_modal(GuildConfigModal())

@bot.tree.command(name="register_bot", description="Register your bot token for guild subscription")
async def register_bot_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    # Check if user has a guild subscription
    from utils.guild_manager import GuildManager
    has_subscription, message = GuildManager.check_guild_subscription(user_id)
    
    if not has_subscription:
        embed = discord.Embed(
            title="Access Denied",
            description=f"You don't have an active guild subscription. {message}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Show the register bot token modal
    await interaction.response.send_modal(RegisterBotModal())

@bot.tree.command(name="configure_guild", description="Configure your guild for the bot")
async def configure_guild_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    
    # Check if user has a guild subscription
    from utils.guild_manager import GuildManager
    has_subscription, _ = GuildManager.check_guild_subscription(user_id)
    
    if not has_subscription:
        embed = discord.Embed(
            title="Access Denied",
            description="You don't have an active guild subscription. Please purchase one first.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Check if user has registered a bot token
    if not GuildManager.has_bot_registered(user_id):
        embed = discord.Embed(
            title="Bot Token Required",
            description="You need to register your bot token first using the `/register_bot` command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # If this is a DM, show the bot invite link
    if not interaction.guild:
        # Generate bot invite link with required permissions
        invite_link = "https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=8"
        
        embed = discord.Embed(
            title="Invite Bot to Server",
            description=f"Please invite the bot to your server and then run the command there. You can do so by clicking the link below:\n\n{invite_link}",
            color=discord.Color.from_str("#c2ccf8")
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Show configuration panel
    embed = discord.Embed(
        title="Configure Your Guild",
        description="-# Click the button below to start the setup process.",
        color=discord.Color.from_str("#c2ccf8")
    )
    
    view = ConfigureGuildView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="add_access", description="Add access for a user in your guild")
@app_commands.describe(
    user="The user to grant access to",
    days="Number of days for access (0 for lifetime)"
)
async def add_access_command(interaction: discord.Interaction, user: discord.Member, days: int = 30):
    # Check if command is used in a guild
    if not interaction.guild:
        embed = discord.Embed(
            title="Command Failed",
            description="This command can only be used in a server.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    guild_id = str(interaction.guild.id)
    user_id = str(interaction.user.id)
    target_user_id = str(user.id)
    
    # Get guild configuration
    from utils.guild_manager import GuildManager
    guild_config = GuildManager.get_guild_config(guild_id)
    
    if not guild_config:
        embed = discord.Embed(
            title="Server Not Configured",
            description="This server has not been configured for the bot. Please run `/configure_guild` first.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Check if user has admin role
    admin_role_id = guild_config.get("admin_role_id")
    if not admin_role_id:
        embed = discord.Embed(
            title="Configuration Error",
            description="Admin role not properly configured. Please run `/configure_guild` again.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Check if user has admin role
    try:
        admin_role = interaction.guild.get_role(int(admin_role_id))
        if not admin_role or admin_role not in interaction.user.roles:
            embed = discord.Embed(
                title="Access Denied",
                description="You need the admin role to use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
    except (ValueError, TypeError):
        embed = discord.Embed(
            title="Configuration Error",
            description="Invalid admin role ID. Please run `/configure_guild` again.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Add access for user
    success, expiry_date = GuildManager.add_user_access(guild_id, target_user_id, user_id, days)
    
    if success:
        # Try to add client role to the user
        client_role_id = guild_config.get("client_role_id")
        if client_role_id:
            try:
                client_role = interaction.guild.get_role(int(client_role_id))
                if client_role:
                    await user.add_roles(client_role)
            except Exception as e:
                print(f"Error adding role to user: {e}")
        
        # Get generator channel for mention
        generator_channel_id = guild_config.get("generator_channel_id")
        generator_channel_mention = f"<#{generator_channel_id}>" if generator_channel_id else "the generator channel"
        
        # Create success message
        display_days = "Lifetime" if days == 0 else f"{days} Days"
        
        embed = discord.Embed(
            title="Access Granted",
            description=f"Successfully added `{display_days}` access to {user.mention}\n\n" +
                        f"» Go to {generator_channel_mention} and Run command **/generate**\n",
            color=discord.Color.green()
        )
        
        # Send public notification
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="Error",
            description="There was an error adding access for the user. Please try again.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="menu", description="Open the GOAT Receipts menu")
async def menu_command(interaction: discord.Interaction):
    # Check if command is used in the allowed channel
    allowed_channel_id = 1374468007472009216
    if interaction.channel_id != allowed_channel_id:
        embed = discord.Embed(
            title="Command Restricted",
            description=f"This command can only be used in <#{allowed_channel_id}>",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
        
    user_id = str(interaction.user.id)

    # Check if user has a valid license
    from utils.license_manager import LicenseManager
    license_status = await LicenseManager.is_subscription_active(user_id)

    # Handle different return types - could be bool or dict
    is_active = False
    if isinstance(license_status, dict):
        is_active = license_status.get("active", False)
    else:
        is_active = bool(license_status)

    if not is_active:
        # Check if it's an expired license with expiry date (if license_status is dict)
        if isinstance(license_status, dict) and "expired_date" in license_status:
            expired_date = license_status["expired_date"]
            embed = discord.Embed(
                title="Subscription Expired",
                description=f"Your subscription expired on `{expired_date}`. Please renew your subscription to continue using our services.",
                color=discord.Color.red()
            )

            # Create a view with a "Renew" button that redirects to goatreceipts.com
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Renew", style=discord.ButtonStyle.link, url="https://goatreceipts.com"))

            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        else:
            # User never had a license
            embed = discord.Embed(
                title="Access Denied",
                description="You need to buy a **[subscription](https://goatreceipts.com)** to use our services\n-# Be aware that it costs us money to run the bot.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
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

# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))