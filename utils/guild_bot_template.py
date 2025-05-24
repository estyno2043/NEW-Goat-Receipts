
import discord
from discord.ext import commands
import asyncio
import logging
import sqlite3
import os

# This is a template file for guild bots
# It will be used to generate bot files for guild users

TEMPLATE = '''
import discord
from discord.ext import commands
import asyncio
import logging
import sqlite3
import os

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

@bot.command(name="status")
async def status_command(ctx):
    if str(ctx.author.id) != OWNER_ID:
        await ctx.send("You don't have permission to use this command.", ephemeral=True)
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

# Run the bot
bot.run('{bot_token}')
'''
