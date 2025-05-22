import os
import discord
import random
import sqlite3
import datetime
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
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Create a database to store user emails
def setup_database():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_emails (
        user_id TEXT PRIMARY KEY,
        email TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS licenses (
        owner_id TEXT PRIMARY KEY,
        name TEXT,
        street TEXT,
        city TEXT,
        zipp TEXT,
        country TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vouches (
        user_id TEXT PRIMARY KEY,
        vouch_content TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_credits (
        user_id TEXT PRIMARY KEY,
        credits INTEGER DEFAULT 3
    )
    ''')
    conn.commit()
    conn.close()

# Generate random details for non-premium users
def generate_random_details():
    first_names = ["John", "Jane", "Michael", "Emma", "David", "Sarah", "Robert", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson"]
    streets = ["Oak Street", "Maple Avenue", "Pine Road", "Cedar Lane", "Elm Boulevard", "Willow Drive", "Birch Court", "Cypress Way"]
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego"]
    zips = ["10001", "90001", "60601", "77001", "85001", "19101", "78201", "92101"]
    countries = ["United States", "Canada", "United Kingdom", "Australia", "Germany", "France", "Spain", "Italy"]

    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    street = f"{random.randint(1, 999)} {random.choice(streets)}"
    city = random.choice(cities)
    zipp = random.choice(zips)
    country = random.choice(countries)

    return name, street, city, zipp, country

# Dropdown for receipt brand selection
class BrandSelectDropdown(ui.Select):
    def __init__(self, user_id, panel_interaction=None, panel_message=None):
        self.user_id = user_id
        self.panel_interaction = panel_interaction
        self.panel_message = panel_message

        # Get user's current credits
        remaining_credits = 0
        if user_id != "1339295766828552365":  # Skip for owner
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            # Check if user exists in credits table
            cursor.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()

            if not result:
                # Add user with default 3 credits
                cursor.execute("INSERT INTO user_credits (user_id, credits) VALUES (?, 3)", (user_id,))
                conn.commit()
                remaining_credits = 3
            else:
                remaining_credits = result[0]
            conn.close()

        options = [
            discord.SelectOption(label="Apple", value="apple", emoji="<:applelogo:1371071241351462922>"),
            discord.SelectOption(label="StockX", value="stockx", emoji="<:stockx:1371099893963423934>"),
            discord.SelectOption(label="Vinted", value="vinted", emoji="<:vinted:1371112668441743390>")
        ]

        # Show credits in the placeholder if not owner
        if user_id == "1339295766828552365":
            placeholder = "Choose a brand..."
        else:
            placeholder = f"Choose a brand... ({remaining_credits} credits remaining)"

        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)

    async def has_client_role(self, interaction: discord.Interaction):
        # Owner ID exemption
        if interaction.user.id == 1339295766828552365:
            return False

        # Client role ID
        client_role_id = 1339305923545403442

        # Check if user has the client role
        user = interaction.user
        if not isinstance(user, discord.Member):
            # If interaction.user is not a Member object (DM context), fetch the member
            try:
                user = await interaction.guild.fetch_member(user.id)
            except:
                # If we can't fetch member info, assume they don't have the role
                return False

        # Check if user has the client role
        return any(role.id == client_role_id for role in user.roles)

    async def has_left_vouch(self, interaction: discord.Interaction):
        # Owner ID exemption
        if interaction.user.id == 1339295766828552365:
            return True

        # Check database for vouch from this user
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT vouch_content FROM vouches WHERE user_id = ?", (str(interaction.user.id),))
        result = cursor.fetchone()
        conn.close()

        return result is not None

    async def callback(self, interaction: discord.Interaction):
        # Check if user has client role
        if await self.has_client_role(interaction):
            embed = discord.Embed(
                title="Premium Plan Detected",
                description="You are already a <@&1339305923545403442> with a plan. Head over to <#1369426783153160304>",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not await self.has_left_vouch(interaction):
            embed = discord.Embed(
                title="⚠️ Vouch To Continue",
                description="- Leave a **Vouch** message in <#1371111858114658314> To continue",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        brand = self.values[0]

        # Store panel information for later closing
        try:
            # Always create a fresh _panel_data dictionary
            interaction._panel_data = {}

            # Store the original panel interaction if available
            if self.panel_interaction:
                interaction._panel_data['panel_interaction'] = self.panel_interaction

            # Store the panel message if available (from constructor)
            if self.panel_message:
                interaction._panel_data['panel_message'] = self.panel_message

            # If we have the current interaction message, store it too
            if hasattr(interaction, 'message') and interaction.message:
                interaction._panel_data['panel_message'] = interaction.message

            print(f"Successfully stored panel data for user {interaction.user.id}")
        except Exception as e:
            print(f"Failed to store panel message: {e}")

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

        # Reset the select menu to show placeholder again
        self.placeholder = "Choose a brand..."
        # We can't directly reset values as it's a read-only property

# View for brand selection dropdown
class BrandSelectView(ui.View):
    def __init__(self, user_id, panel_interaction=None, panel_message=None):
        super().__init__(timeout=300)
        # Store the panel message/interaction for closing later
        self.panel_interaction = panel_interaction
        self.panel_message = panel_message
        dropdown = BrandSelectDropdown(user_id, panel_interaction, panel_message)
        self.add_item(dropdown)

# Email setting modal
class SetEmailModal(ui.Modal, title="Set Your Email"):
    email = ui.TextInput(label="Email Address", placeholder="example@email.com", required=True)

    def is_icloud_email(self, email):
        """Check if the email is an iCloud email address"""
        return "@icloud" in email.lower()

    async def has_client_role(self, interaction: discord.Interaction):
        # Owner ID exemption
        if interaction.user.id == 1339295766828552365:
            return False

        # Client role ID
        client_role_id = 1339305923545403442

        # Check if user has the client role
        user = interaction.user
        if not isinstance(user, discord.Member):
            # If interaction.user is not a Member object (DM context), fetch the member
            try:
                user = await interaction.guild.fetch_member(user.id)
            except:
                # If we can't fetch member info, assume they don't have the role
                return False

        # Check if user has the client role
        return any(role.id == client_role_id for role in user.roles)

    async def has_left_vouch(self, interaction: discord.Interaction):
        # Owner ID exemption
        if interaction.user.id == 1339295766828552365:
            return True

        # Check database for vouch from this user
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT vouch_content FROM vouches WHERE user_id = ?", (str(interaction.user.id),))
        result = cursor.fetchone()
        conn.close()

        return result is not None

    async def on_submit(self, interaction: discord.Interaction):
        # Check if user has client role
        if await self.has_client_role(interaction):
            embed = discord.Embed(
                title="Premium Plan Detected",
                description="You are already a <@&1339305923545403442> with a plan. Head over to <#1369426783153160304>",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not await self.has_left_vouch(interaction):
            embed = discord.Embed(
                title="⚠️ Vouch To Continue",
                description="- Leave a **Vouch** message in <#1371111858114658314> To continue",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        user_id = str(interaction.user.id)
        email = self.email.value

        # Check if the email is an iCloud email address
        if self.is_icloud_email(email):
            embed = discord.Embed(
                title="Email not saved",
                description="Your icloud email was not saved since receipt delivery to icloud mail won't function. Please change it to **gmail, outlook or yahoo** for successfull delivery.\n\n-# this way you won't waste your credits <:okay:1371142412755402912>",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO user_emails (user_id, email) VALUES (?, ?)", (user_id, email))
        conn.commit()
        conn.close()

        class ChangeEmailView(ui.View):
            def __init__(self):
                super().__init__(timeout=300)

            @ui.button(label="Change Email", style=discord.ButtonStyle.gray)
            async def change_email(self, interaction: discord.Interaction, button: ui.Button):
                await interaction.response.send_modal(SetEmailModal())

        embed = discord.Embed(
            title="Email Set Successfully",
            description=f"Your email is set to: `{email}`",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, view=ChangeEmailView(), ephemeral=True)

# Button view for the panel
class ReceiptPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # Helper method to check if user has client role
    async def has_client_role(self, interaction: discord.Interaction):
        # Owner ID exemption
        if interaction.user.id == 1339295766828552365:
            return False

        # Client role ID
        client_role_id = 1339305923545403442

        # Check if user has the client role
        user = interaction.user
        if not isinstance(user, discord.Member):
            # If interaction.user is not a Member object (DM context), fetch the member
            try:
                user = await interaction.guild.fetch_member(user.id)
            except:
                # If we can't fetch member info, assume they don't have the role
                return False

        # Check if user has the client role
        return any(role.id == client_role_id for role in user.roles)

    async def has_left_vouch(self, interaction: discord.Interaction):
        # Owner ID exemption
        if interaction.user.id == 1339295766828552365:
            return True

        # Check database for vouch from this user
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT vouch_content FROM vouches WHERE user_id = ?", (str(interaction.user.id),))
        result = cursor.fetchone()
        conn.close()

        return result is not None

    @ui.button(label="Generate Receipt", style=discord.ButtonStyle.gray, custom_id="generate_receipt")
    async def generate_receipt(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)

        # Check if user has client role
        if await self.has_client_role(interaction):
            embed = discord.Embed(
                title="Premium Plan Detected",
                description="You are already a <@&1339305923545403442> with a plan. Head over to <#1369426783153160304>",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not await self.has_left_vouch(interaction):
            embed = discord.Embed(
                title="⚠️ Vouch To Continue",
                description="- Leave a **Vouch** message in <#1371111858114658314> To continue",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if user has credits (skip for owner)
        if interaction.user.id != 1339295766828552365:  # Owner ID exemption
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            # Check if user exists in credits table
            cursor.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()

            if not result:
                # Add user with default 3 credits
                cursor.execute("INSERT INTO user_credits (user_id, credits) VALUES (?, 3)", (user_id,))
                conn.commit()
                credits = 3
            else:
                credits = result[0]

            conn.close()

            # Check if user has enough credits
            if credits <= 0:
                embed = discord.Embed(
                    title="Limit Reached",
                    description="Oops... you have used all of your remaining **credits**. You will need to buy a **[premium plan](https://goatreceipts.xyz)** to continue generating receipts for over **80** available brands.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Check if user has set an email
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            # User hasn't set an email
            embed = discord.Embed(
                title="No Email",
                description="```Click button \"Set Email\" and configure your email where you would like to receive this receipt```",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Generate random details for the user if they don't have custom credentials
        name, street, city, zipp, country = generate_random_details()

        # Store these details in the database for the apple.py modal to use
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO licenses (owner_id, name, street, city, zipp, country) VALUES (?, ?, ?, ?, ?, ?)",
                      (user_id, name, street, city, zipp, country))
        conn.commit()
        conn.close()

        # Show brand selection dropdown with remaining credits information
        # Get user's remaining credits (skip for owner)
        if interaction.user.id != 1339295766828552365:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            credits_info = f"You have **{result[0]}** credits remaining."
            conn.close()

            embed = discord.Embed(
                title="Choose from free available receipts",
                description=f"Please choose a brand to continue\n\n{credits_info}",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="Choose from free available receipts",
                description="Please choose a brand to continue",
                color=discord.Color.blue()
            )

        # Send message with the view and store it for later reference
        response = await interaction.response.send_message(embed=embed, view=BrandSelectView(user_id, interaction), ephemeral=True)

        # Try to get the message for future reference
        try:
            message = await interaction.original_response()
            if message:
                print(f"Successfully captured original message in generate_receipt for user {interaction.user.id}")
        except Exception as e:
            print(f"Could not get original message: {e}")

        # Create an attribute dictionary on the interaction to store panel data
        try:
            # Initialize panel data dictionary
            interaction._panel_data = {}

            # Store the interaction object itself
            interaction._panel_data['original_interaction'] = interaction

            # Store the panel message if we can get it
            if hasattr(interaction, 'message') and interaction.message:
                interaction._panel_data['panel_message'] = interaction.message

            print(f"Successfully stored panel data in generate_receipt for user {interaction.user.id}")
        except Exception as e:
            print(f"Failed to store panel message: {e}")

    @ui.button(label="Set Email", style=discord.ButtonStyle.blurple, custom_id="set_email")
    async def set_email(self, interaction: discord.Interaction, button: ui.Button):
        user_id = str(interaction.user.id)

        # Check if user has client role
        if await self.has_client_role(interaction):
            embed = discord.Embed(
                title="Premium Plan Detected",
                description="You are already a <@&1339305923545403442> with a plan. Head over to <#1369426783153160304>",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if not await self.has_left_vouch(interaction):
            embed = discord.Embed(
                title="⚠️ Vouch To Continue",
                description="- Leave a **Vouch** message in <#1371111858114658314> To continue",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Check if user has credits (skip for owner)
        if interaction.user.id != 1339295766828552365:  # Owner ID exemption
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            # Check if user exists in credits table
            cursor.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()

            if not result:
                # Add user with default 3 credits
                cursor.execute("INSERT INTO user_credits (user_id, credits) VALUES (?, 3)", (user_id,))
                conn.commit()
                credits = 3
            else:
                credits = result[0]

            conn.close()

            # Check if user has enough credits
            if credits <= 0:
                embed = discord.Embed(
                    title="Limit Reached",
                    description="Oops... you have used all of your remaining **credits**. You will need to buy a **[premium plan](https://goatreceipts.xyz)** to continue generating receipts for over **80** available brands.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

        # Check if user already has an email set
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            # User already has an email set, show it with option to change
            email = result[0]

            class ChangeEmailView(ui.View):
                def __init__(self):
                    super().__init__(timeout=300)

                @ui.button(label="Change Email", style=discord.ButtonStyle.gray)
                async def change_email(self, interaction: discord.Interaction, button: ui.Button):
                    await interaction.response.send_modal(SetEmailModal())

            embed = discord.Embed(
                title="Email Settings",
                description=f"Your email is set to: `{email}`",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, view=ChangeEmailView(), ephemeral=True)
        else:
            # User doesn't have an email set, show the modal
            await interaction.response.send_modal(SetEmailModal())

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

@bot.event
async def on_message(message: discord.Message):
    # Skip if the message is from the bot itself
    if message.author.bot:
        return

    # Check if the message is in the vouch channel
    if message.channel.id == 1371111858114658314:
        # If message starts with +vouch, save it
        if message.content.startswith("+vouch"):
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO vouches (user_id, vouch_content) VALUES (?, ?)", (str(message.author.id), message.content))
            conn.commit()
            conn.close()
        # If message doesn't start with +, delete it
        elif not message.content.startswith("+"):
            try:
                await message.delete()
                # Optional: Send a temporary notification to the user
                warning = await message.channel.send(f"{message.author.mention} Please use the format `+vouch [your message]` in this channel.")
                await asyncio.sleep(5)  # Wait 5 seconds
                await warning.delete()  # Delete the warning message
            except discord.errors.NotFound:
                pass  # Message was already deleted
            except discord.errors.Forbidden:
                pass  # Bot doesn't have permission to delete

    # Process commands after message handling
    await bot.process_commands(message)

@bot.event
async def on_message_delete(message: discord.Message):
    # Skip message deletions from the bot itself
    if message.author.bot:
        return

    # Only track deletions in the vouch channel for user messages that start with +vouch
    if message.channel.id == 1371111858114658314 and message.content.startswith("+vouch"):
        await message.channel.send(f"{message.author.mention} Deleted a Vouch: {message.content}")

@bot.tree.command(name="stick", description="Display vouch format information")
async def stick(interaction: discord.Interaction):
    # Check if command user is the owner
    if interaction.user.id != 1339295766828552365:  # Owner ID
        embed = discord.Embed(
            title="Nice Try",
            description="HaHa... Nice try",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Create embed
    embed = discord.Embed(
        title="Vouch Format",
        description="Vouch Format `+vouch VouchMessageHere`\nExample `+vouch 100% legit and works`",
        color=discord.Color.blue()
    )

    # Send the message to the channel (not ephemeral)
    await interaction.response.send_message("Creating vouch format message...", ephemeral=True)
    await interaction.channel.send(embed=embed)

@bot.tree.command(name="resetcredits", description="Reset a user's credits to the default value (3)")
@app_commands.describe(user="The user whose credits you want to reset")
async def resetcredits(interaction: discord.Interaction, user: discord.Member):
    # Check if command user is the owner
    if interaction.user.id != 1339295766828552365:  # Owner ID
        embed = discord.Embed(
            title="Nice Try",
            description="HaHa... Nice try",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Reset the selected user's credits
    target_user_id = str(user.id)
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Insert or replace the user's credits with the default value (3)
    cursor.execute("INSERT OR REPLACE INTO user_credits (user_id, credits) VALUES (?, 3)", (target_user_id,))
    conn.commit()
    conn.close()

    # Send confirmation
    embed = discord.Embed(
        title="Credits Reset",
        description=f"Reset {user.mention}'s credits to 3.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="freepanel", description="Create a free receipt generator panel")
async def freepanel(interaction: discord.Interaction):
    # Check if command user is the owner
    if interaction.user.id != 1339295766828552365:  # Owner ID
        embed = discord.Embed(
            title="Nice Try",
            description="HaHa... Nice try",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Get user credits
    user_id = str(interaction.user.id)
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Check if user exists in credits table, if not add them with default 3 credits
    cursor.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    if not result:
        cursor.execute("INSERT INTO user_credits (user_id, credits) VALUES (?, 3)", (user_id,))
        conn.commit()
        credits = 3
    else:
        credits = result[0]

    conn.close()

    # Create embed
    embed = discord.Embed(
        title="Free Receipt Generator",
        description=f"```Interact with the buttons below to get started```\n**Note:**\n- To Fully customize your own **credentials** & get access to over **80 Brands** you need to purchase a **[premium access](https://goatreceipts.cc)**",
        color=discord.Color.blue()
    )

    # Set images
    embed.set_image(url="https://media.discordapp.net/attachments/1339298010169086075/1371061598000775258/Untitled_design_20.png?ex=6821c41e&is=6820729e&hm=4c39ba7ba3612a13bd86e5cc31847106a2e98d7ccd343f42ffcd0f415b6aa4b3&=&format=webp&quality=lossless")

    # Set footer with the icon (moved from author to footer)
    embed.set_footer(text="GOAT Receipts", icon_url="https://media.discordapp.net/attachments/1339298010169086075/1371061649884057642/GOAT.png?ex=6821c42a&is=682072aa&hm=e4ecaaf1b15fb6ff567c9c631a69010f0706425c0df3f197cf917e394b350f9c&=&format=webp&quality=lossless")

    # Send an ephemeral acknowledgment to the user 
    await interaction.response.send_message("Creating panel...", ephemeral=True)

    # Send the panel to the channel directly (not as a reply)
    await interaction.channel.send(embed=embed, view=ReceiptPanelView())

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