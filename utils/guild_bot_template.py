
import discord
from discord.ext import commands
import asyncio
import logging
import sqlite3
import os
import json

# This is a template file for guild bots
# It will be used to generate bot files for guild users

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [GUILD BOT] %(levelname)s: %(message)s')

TEMPLATE = '''
import discord
from discord.ext import commands
import asyncio
import logging
import sqlite3
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [GUILD BOT] %(levelname)s: %(message)s')

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# Store the guild owner ID
OWNER_ID = "{owner_id}"
GUILD_ID = None  # Will be set when the bot joins a guild

@bot.event
async def on_ready():
    logging.info(f'Guild Bot logged in as {{bot.user.name}} ({{bot.user.id}})')
    logging.info('------')
    
    # Get the configured guild
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT guild_id FROM guild_configs WHERE owner_id = ?", (OWNER_ID,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            global GUILD_ID
            GUILD_ID = result[0]
            logging.info(f"Found configured guild: {{GUILD_ID}}")
        
        # Set up status message
        await bot.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="for commands"
        ))
    except Exception as e:
        logging.error(f"Error in on_ready: {{e}}")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Process image URLs if in the configured image channel
    if message.guild and str(message.guild.id) == GUILD_ID:
        try:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT image_channel_id FROM guild_configs WHERE guild_id = ?", (GUILD_ID,))
            result = cursor.fetchone()
            conn.close()
            
            if result and str(message.channel.id) == result[0]:
                # Process attachments
                if message.attachments:
                    for attachment in message.attachments:
                        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                            # Reply to the user's message with the image URL
                            await message.reply(f"```\\n{{attachment.url}}\\n```", mention_author=False)
        except Exception as e:
            logging.error(f"Error processing image: {{e}}")
        
    # Process commands
    await bot.process_commands(message)

@bot.tree.command(name="generate", description="Generate receipts")
async def generate_command(interaction: discord.Interaction):
    # Check if this is the configured guild
    if not interaction.guild or str(interaction.guild.id) != GUILD_ID:
        await interaction.response.send_message("This command can only be used in the configured guild.", ephemeral=True)
        return
    
    # Check if this is the configured generator channel
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT generator_channel_id FROM guild_configs WHERE guild_id = ?", (GUILD_ID,))
        result = cursor.fetchone()
        conn.close()
        
        if result and str(interaction.channel_id) != result[0]:
            await interaction.response.send_message(f"This command can only be used in <#{result[0]}>", ephemeral=True)
            return
    except Exception as e:
        logging.error(f"Error checking generator channel: {{e}}")
        await interaction.response.send_message("There was an error processing your command.", ephemeral=True)
        return
    
    # Check if user has access
    user_id = str(interaction.user.id)
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''
        SELECT expiry_date, is_active 
        FROM guild_user_access 
        WHERE guild_id = ? AND user_id = ?
        ''', (GUILD_ID, user_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[1]:
            await interaction.response.send_message("You don't have access to use this command.", ephemeral=True)
            return
    except Exception as e:
        logging.error(f"Error checking user access: {{e}}")
        await interaction.response.send_message("There was an error checking your access.", ephemeral=True)
        return
    
    # Forward the request to the main bot (simulated here with a message)
    await interaction.response.send_message("Generation request received. Redirecting to generator...", ephemeral=True)
    
    # In a real implementation, this would connect to the main bot's API or database

@bot.tree.command(name="menu", description="Open the receipts menu")
async def menu_command(interaction: discord.Interaction):
    # Similar implementation as generate_command
    await interaction.response.send_message("Menu request received. Opening menu...", ephemeral=True)

@bot.tree.command(name="configure_guild", description="Configure your guild settings")
async def configure_guild_command(interaction: discord.Interaction):
    # Only allow the owner to configure
    if str(interaction.user.id) != OWNER_ID:
        await interaction.response.send_message("Only the guild owner can use this command.", ephemeral=True)
        return
    
    await interaction.response.send_message("Please use the main bot's `/configure_guild` command to set up your guild.", ephemeral=True)

@bot.tree.command(name="add_access", description="Add user access to the guild")
@discord.app_commands.describe(
    user="The user to grant access to",
    days="Number of days for access (0 for lifetime)"
)
async def add_access_command(interaction: discord.Interaction, user: discord.Member, days: int = 30):
    # Only allow the owner or admins to add access
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT admin_role_id FROM guild_configs WHERE guild_id = ?", (GUILD_ID,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            await interaction.response.send_message("Guild not properly configured.", ephemeral=True)
            return
        
        admin_role_id = result[0]
        admin_role = interaction.guild.get_role(int(admin_role_id))
        
        if str(interaction.user.id) != OWNER_ID and (not admin_role or admin_role not in interaction.user.roles):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return
            
        # Forward to main bot's add_access functionality
        await interaction.response.send_message("Please use the main bot's `/add_access` command to add user access.", ephemeral=True)
    except Exception as e:
        logging.error(f"Error in add_access: {{e}}")
        await interaction.response.send_message("There was an error processing your command.", ephemeral=True)

@bot.command(name="status")
async def status_command(ctx):
    if str(ctx.author.id) != OWNER_ID:
        await ctx.send("You don't have permission to use this command.")
        return
    
    embed = discord.Embed(
        title="Bot Status",
        description="Your guild bot is running correctly.",
        color=discord.Color.green()
    )
    
    embed.add_field(name="Bot ID", value=bot.user.id, inline=True)
    embed.add_field(name="Owner ID", value=OWNER_ID, inline=True)
    
    # Get guild config
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM guild_configs WHERE owner_id = ?", (OWNER_ID,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ["guild_id", "owner_id", "generator_channel_id", "admin_role_id", 
                       "client_role_id", "image_channel_id", "purchases_channel_id", "setup_date"]
            config = dict(zip(columns, result))
            
            embed.add_field(name="Guild ID", value=config["guild_id"], inline=True)
            embed.add_field(name="Generator Channel", value=f"<#{config['generator_channel_id']}>", inline=True)
            embed.add_field(name="Image Channel", value=f"<#{config['image_channel_id']}>", inline=True)
            embed.add_field(name="Setup Date", value=config["setup_date"], inline=False)
    except Exception as e:
        embed.add_field(name="Error", value=str(e), inline=False)
    
    await ctx.send(embed=embed)

async def setup_commands():
    try:
        # Sync commands with Discord
        await bot.tree.sync()
        logging.info("Commands synced successfully")
    except Exception as e:
        logging.error(f"Error syncing commands: {{e}}")

# Run the bot
bot.run('{bot_token}')
'''
