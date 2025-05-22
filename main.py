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
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    cursor.execute("SELECT subscription_type, end_date FROM user_subscriptions WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0], result[1]
    else:
        # Create default subscription if none exists
        update_subscription(user_id)
        return "1 (Email Access Only)", (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

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
        for modal_file in modal_files:
            brand_name = modal_file.split('.')[0].capitalize()
            available_brands.append(brand_name)

        # Sort alphabetically
        available_brands.sort()

        # Show only 10 brands per page
        start_idx = (page - 1) * 10
        end_idx = min(start_idx + 10, len(available_brands))

        # If page is out of bounds, reset to page 1
        if start_idx >= len(available_brands):
            self.page = 1
            start_idx = 0
            end_idx = min(10, len(available_brands))

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
            await interaction.response.send_message(embed=embed, ephemeral=False)
            return

        # Simulate receipt generation process
        embed = discord.Embed(
            title="Generating Receipt",
            description=f"Generating a receipt for **{brand.capitalize()}**. Please wait...",
            color=discord.Color.from_str("#c2ccf8")
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)

        # Here you would add your actual receipt generation logic
        # For specific brands like Apple, StockX, Vinted, etc.

        # Example placeholder for receipt generation:
        if brand == "apple":
            from modals.apple import applemodal
            modal = applemodal()
            await interaction.response.send_modal(modal)
        elif brand == "stockx":
            from modals.stockx import stockxmodal
            modal = stockxmodal()
            await interaction.response.send_modal(modal)
        elif brand == "vinted":
            from modals.vinted import vintedmodal
            modal = vintedmodal()
            await interaction.response.send_modal(modal)
        else:
            # Generic success message for demo purposes
            await asyncio.sleep(2)  # Simulate processing time
            success_embed = discord.Embed(
                title="Receipt Generated",
                description=f"Your {brand.capitalize()} receipt has been sent to your email.",
                color=discord.Color.from_str("#c2ccf8")
            )
            await interaction.edit_original_response(embed=success_embed)

# View for the brand selection
class BrandSelectView(ui.View):
    def __init__(self, user_id, page=1):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.page = page
        self.add_item(BrandSelectDropdown(page))

    @ui.button(label="Previous", style=discord.ButtonStyle.blurple, custom_id="previous")
    async def previous_page(self, interaction: discord.Interaction, button: ui.Button):
        # Get total number of brands to calculate max pages
        import os
        modal_files = [f for f in os.listdir('modals') if f.endswith('.py') and not f.startswith('__')]
        total_count = len(modal_files)
        max_pages = (total_count + 9) // 10  # Ceiling division to get number of pages

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
        max_pages = (total_count + 9) // 10  # Ceiling division to get number of pages

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
        super().__init__(timeout=300)
        self.user_id = user_id

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

    @ui.button(label="Go Back", style=discord.ButtonStyle.danger, custom_id="go_back")
    async def go_back(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return

        # Create menu panel (with updated format)
        subscription_type, end_date = get_subscription(self.user_id)

        embed = discord.Embed(
            title="GOAT Menu",
            description=f"Hello <@{self.user_id}>, you have until `{end_date}` before your subscription ends.\n" +
                        "-# pick an option below to continue\n\n" +
                        "**Subscription Type**\n" +
                        f"`{subscription_type}`",
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

            # Update the original message
            await interaction.message.edit(embed=updated_embed)

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

            # Update the original message
            await interaction.message.edit(embed=updated_embed)

        elif selected == "Email":
            # Show email form
            await interaction.response.send_modal(EmailForm())

# View for the credentials panel
class CredentialsView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

    @ui.button(label="Go Back", style=discord.ButtonStyle.danger, custom_id="go_back")
    async def go_back(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return

        # Create menu panel (with updated format)
        subscription_type, end_date = get_subscription(self.user_id)

        embed = discord.Embed(
            title="GOAT Menu",
            description=f"Hello <@{self.user_id}>, you have until `{end_date}` before your subscription ends.\n" +
                        "-# pick an option below to continue\n\n" +
                        "**Subscription Type**\n" +
                        f"`{subscription_type}`",
            color=discord.Color.from_str("#c2ccf8")
        )

        await interaction.response.edit_message(embed=embed, view=MenuView(self.user_id))

# View for the main menu
class MenuView(ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.user_id = user_id

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
                description="Please click \"Credentials\" and set up your credentials first",
                color=discord.Color.from_str("#c2ccf8")
            )
            
            view = ui.View()
            credentials_button = ui.Button(label="Credentials", style=discord.ButtonStyle.gray)
            help_button = ui.Button(label="Help", style=discord.ButtonStyle.gray, url="https://discord.com/channels/1339298010169086072/1339520924596043878")
            brands_button = ui.Button(label="Brands", style=discord.ButtonStyle.gray, url="https://discord.com/channels/1339298010169086072/1339306570634236038")
            
            async def credentials_callback(interaction: discord.Interaction):
                if interaction.user.id != int(self.user_id):
                    await interaction.response.send_message("This is not your menu!", ephemeral=True)
                    return
                
                has_credentials, has_email = check_user_setup(self.user_id)
                
                embed = discord.Embed(
                    title="Credentials",
                    description="Please make sure both options below are 'True'\n\n" +
                                "**Info**\n" +
                                f"{'True' if has_credentials else 'False'}\n\n" +
                                "**Email**\n" +
                                f"{'True' if has_email else 'False'}",
                    color=discord.Color.from_str("#c2ccf8")
                )
                
                await interaction.response.send_message(embed=embed, view=CredentialsDropdownView(self.user_id), ephemeral=True)
                
            credentials_button.callback = credentials_callback
            
            view.add_item(credentials_button)
            view.add_item(help_button)
            view.add_item(brands_button)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
            return

        # Create generator panel
        username = interaction.user.display_name
        total_brands = get_total_brands()

        embed = discord.Embed(
            title=f"{username}'s Panel",
            description=f"Choose the type of receipt from the dropdown menu below. `(Total: {total_brands})`\n-# Click \"Next Brands\" to see next page",
            color=discord.Color.from_str("#c2ccf8")
        )

        await interaction.response.send_message(embed=embed, view=BrandSelectView(self.user_id), ephemeral=True)

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

        await interaction.response.edit_message(embed=embed, view=CredentialsDropdownView(self.user_id))

    @ui.button(label="Help", style=discord.ButtonStyle.gray, custom_id="help")
    async def help(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return

        embed = discord.Embed(
            title="Help",
            description="**How to use GOAT Receipts:**\n\n" +
                        "1. Click **Credentials** to set up your information and email\n" +
                        "2. Click **Generate** to create receipts\n" +
                        "3. Choose a brand from the dropdown menu\n" +
                        "4. Fill in any required information\n" +
                        "5. Receive your receipt via email\n\n" +
                        "For more help, contact support.",
            color=discord.Color.from_str("#c2ccf8")
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="Brands", style=discord.ButtonStyle.gray, custom_id="brands")
    async def brands(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return

        # For demo purposes, just show a list of some brands
        brands = [
            "Apple", "StockX", "Vinted", "Amazon", "Nike", 
            "Adidas", "eBay", "Walmart", "Target", "Best Buy"
        ]

        brand_list = "\n".join([f"- {brand}" for brand in brands])

        embed = discord.Embed(
            title="Available Brands",
            description=f"Here are some of our available brands:\n\n{brand_list}\n\n" +
                        "And many more! Use the dropdown menu in the Generator to see all brands.",
            color=discord.Color.from_str("#c2ccf8")
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    print('------')

    # Set up database
    setup_database()

    # Sync commands with Discord
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

@bot.tree.command(name="generate", description="Generate receipts with GOAT Receipts")
async def generate_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    # Check if user has a subscription or create default one
    subscription_type, end_date = get_subscription(user_id)

    # Check if user has credentials and email
    has_credentials, has_email = check_user_setup(user_id)

    if not has_credentials or not has_email:
        # Show menu panel for new users
        embed = discord.Embed(
            title="GOAT Menu",
            description=f"Hello <@{user_id}>, you have until `{end_date}` before your subscription ends.\n" +
                        "-# pick an option below to continue\n\n" +
                        "**Subscription Type**\n" +
                        f"`{subscription_type}`",
            color=discord.Color.from_str("#c2ccf8")
        )
        
        view = ui.View()
        credentials_button = ui.Button(label="Credentials", style=discord.ButtonStyle.gray)
        help_button = ui.Button(label="Help", style=discord.ButtonStyle.gray, url="https://discord.com/channels/1339298010169086072/1339520924596043878")
        brands_button = ui.Button(label="Brands", style=discord.ButtonStyle.gray, url="https://discord.com/channels/1339298010169086072/1339306570634236038")
        
        async def credentials_callback(interaction: discord.Interaction):
            if interaction.user.id != int(user_id):
                await interaction.response.send_message("This is not your menu!", ephemeral=True)
                return
            
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
            
            await interaction.response.send_message(embed=embed, view=CredentialsDropdownView(user_id), ephemeral=True)
            
        credentials_button.callback = credentials_callback
        
        view.add_item(credentials_button)
        view.add_item(help_button)
        view.add_item(brands_button)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    else:
        # Show generator panel for returning users
        username = interaction.user.display_name
        total_brands = get_total_brands()

        # Calculate max pages
        import os
        modal_files = [f for f in os.listdir('modals') if f.endswith('.py') and not f.startswith('__')]
        total_count = len(modal_files)
        max_pages = (total_count + 9) // 10  # Ceiling division to get number of pages

        embed = discord.Embed(
            title=f"{username}'s Panel",
            description=f"Choose the type of receipt from the dropdown menu below. `(Total: {total_brands})`\n-# Page 1/{max_pages if max_pages > 0 else 1}",
            color=discord.Color.from_str("#c2ccf8")
        )

        await interaction.response.send_message(embed=embed, view=BrandSelectView(user_id), ephemeral=True)

@bot.tree.command(name="menu", description="Open the GOAT Receipts menu")
async def menu_command(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    # Check if user has a subscription or create default one
    subscription_type, end_date = get_subscription(user_id)

    # Create menu panel
    embed = discord.Embed(
        title="GOAT Menu",
        description=f"Hello <@{user_id}>, you have until `{end_date}` before your subscription ends.\n" +
                    "-# pick an option below to continue\n\n" +
                    "**Subscription Type**\n" +
                    f"`{subscription_type}`",
        color=discord.Color.from_str("#c2ccf8")
    )

    await interaction.response.send_message(embed=embed, view=MenuView(user_id))

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