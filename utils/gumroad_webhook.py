
import json
import sqlite3
import discord
from datetime import datetime, timedelta
import logging
import hmac
import hashlib

class GumroadWebhook:
    def __init__(self, bot):
        self.bot = bot
        self.webhook_secret = None  # To be loaded from config
        
    async def setup(self):
        """Load configuration from config.json"""
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.webhook_secret = config.get("gumroad_webhook_secret", "")
                if not self.webhook_secret:
                    logging.warning("Gumroad webhook secret not configured in config.json")
        except Exception as e:
            logging.error(f"Error loading Gumroad webhook config: {str(e)}")
    
    def verify_signature(self, payload, signature):
        """Verify that the webhook is coming from Gumroad"""
        if not self.webhook_secret:
            logging.warning("No Gumroad webhook secret configured, skipping signature verification")
            return True
            
        computed_signature = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)
        
    async def process_webhook(self, data, signature):
        """Process the webhook data from Gumroad"""
        try:
            # Log the full webhook data and signature for debugging
            logging.info(f"Received Gumroad webhook signature: {signature}")
            logging.info(f"Received Gumroad webhook data: {json.dumps(data)}")
            
            # Verify signature if available
            if signature and not self.verify_signature(json.dumps(data), signature):
                logging.warning("Invalid Gumroad webhook signature")
                return False, "Invalid signature"
                
            # Extract data from the webhook
            event = data.get("event")
            if event != "sale.success":
                return True, f"Ignoring event type: {event}"
                
            purchase = data.get("purchase", {})
            product_id = purchase.get("product_id")
            product_name = purchase.get("product_name", "Unknown Product")
            email = purchase.get("email")
            
            logging.info(f"Processing purchase: Product ID={product_id}, Name={product_name}")
            
            # Get custom fields - this would include discord_id
            custom_fields = purchase.get("custom_fields", {})
            
            # Log the full purchase data for debugging
            logging.info(f"Full purchase data: {json.dumps(purchase)}")
            
            # Log all custom fields for debugging
            logging.info(f"Custom fields received: {json.dumps(custom_fields)}")
            
            # Check all possible locations and formats for Discord ID
            discord_id = None
            
            # Method 1: Check custom fields with standard field names
            field_names = ["discord_id", "Discord ID", "discord", "Discord", "discordid", "Discord id", 
                          "Discord User ID", "discord user id", "discorduser", "discord_user"]
                          
            for field_name in field_names:
                if field_name in custom_fields and custom_fields[field_name]:
                    value = custom_fields[field_name].strip()
                    logging.info(f"Found potential Discord ID in field '{field_name}': {value}")
                    if value.isdigit() and len(value) > 15:
                        discord_id = value
                        logging.info(f"Confirmed Discord ID in field '{field_name}': {discord_id}")
                        break
            
            # Method 2: If no discord_id was found, check if any custom field contains a discord ID pattern
            if not discord_id:
                for field_name, value in custom_fields.items():
                    if isinstance(value, str):
                        value = value.strip()
                        logging.info(f"Checking custom field '{field_name}' with value: {value}")
                        if value.isdigit() and len(value) > 15:
                            discord_id = value
                            logging.info(f"Found Discord ID pattern in field '{field_name}': {discord_id}")
                            break
            
            # Method 3: Check form fields directly in purchase data
            if not discord_id:
                for key, value in purchase.items():
                    if isinstance(value, str) and "discord" in key.lower():
                        value = value.strip()
                        logging.info(f"Found Discord-related field in purchase data: '{key}': {value}")
                        if value.isdigit() and len(value) > 15:
                            discord_id = value
                            logging.info(f"Found Discord ID in purchase field '{key}': {discord_id}")
                            break
            
            # Method 4: Look for any potential discord ID in any field (last resort)
            if not discord_id:
                for key, value in purchase.items():
                    if isinstance(value, str):
                        value = value.strip()
                        if value.isdigit() and len(value) > 15:
                            discord_id = value
                            logging.info(f"Found potential Discord ID pattern in purchase field '{key}': {discord_id}")
                            break
            
            if not discord_id:
                return False, "No Discord ID provided in purchase"
                
            # Map product IDs to access levels
            product_mapping = {
                # Map both by ID and exact product name
                "GOAT Receipts 1 day Plan": ("1dstandard", 1),
                "GOAT Receipts 14 days Plan": ("14dstandard", 14),
                "GOAT Receipts 1 month Plan": ("1mstandard", 30),
                "GOAT Receipts Lifetime Plan": ("lftstandard", 1500),
                # Add fallback matches for similar names (case insensitive)
                "goat receipts 1 day plan": ("1dstandard", 1),
                "1 day": ("1dstandard", 1),
                "14 days": ("14dstandard", 14),
                "1 month": ("1mstandard", 30),
                "lifetime": ("lftstandard", 1500)
            }
            
            # Try to match by product ID first, then by product name
            if product_id in product_mapping:
                access_type, days = product_mapping[product_id]
            elif product_name in product_mapping:
                access_type, days = product_mapping[product_name]
            else:
                # Try to match using lowercase and partial matching
                product_name_lower = product_name.lower()
                matched = False
                
                for key, value in product_mapping.items():
                    if key.lower() in product_name_lower or product_name_lower in key.lower():
                        access_type, days = value
                        matched = True
                        logging.info(f"Matched product '{product_name}' to mapping key '{key}'")
                        break
                
                if not matched:
                    # Default to 1 day plan if we can detect it contains "1 day" in the name
                    if "1 day" in product_name.lower() or "1day" in product_name.lower():
                        access_type, days = "1dstandard", 1
                        logging.info(f"Defaulting to 1 day plan for product: {product_name}")
                    else:
                        logging.warning(f"Product not recognized - ID: {product_id}, Name: {product_name}")
                        return False, f"Unknown product: {product_name}"
            
            # Grant access to the user
            success, message = await self.grant_access(discord_id, access_type, days, product_name)
            return success, message
            
        except Exception as e:
            logging.error(f"Error processing Gumroad webhook: {str(e)}")
            return False, f"Error: {str(e)}"
    
    async def grant_access(self, discord_id, access_type, days, product_name):
        """Grant access to the user based on their purchase"""
        try:
            logging.info(f"Granting access to user ID: {discord_id}, access_type: {access_type}, days: {days}")
            
            # Check if the user is in the database with improved connection handling
            conn = sqlite3.connect('data.db', timeout=30.0)
            conn.execute("PRAGMA busy_timeout = 30000")  # 30 second timeout
            cursor = conn.cursor()
            
            expiry_date = datetime.now() + timedelta(days=days)
            expiry_str = expiry_date.strftime('%d/%m/%Y %H:%M:%S')
            
            key_prefix = "1Day"
            if access_type == "14dstandard":
                key_prefix = "14Days"
            elif access_type == "1mstandard":
                key_prefix = "1Month"
            elif access_type == "lftstandard":
                key_prefix = "LifetimeKey"
            
            # Check if user exists
            cursor.execute("SELECT * FROM licenses WHERE owner_id = ?", (discord_id,))
            user_exists = cursor.fetchone()
            
            if user_exists:
                # Update existing user
                logging.info(f"User {discord_id} exists in database, updating license")
                cursor.execute('''
                UPDATE licenses 
                SET key=?, expiry=? 
                WHERE owner_id=?
                ''', (f"{key_prefix}-{discord_id}", expiry_str, discord_id))
            else:
                # Add new user
                logging.info(f"User {discord_id} does not exist in database, adding new license")
                try:
                    cursor.execute('''
                    INSERT INTO licenses (owner_id, key, expiry, emailtf, credentialstf)
                    VALUES (?, ?, ?, 'False', 'False')
                    ''', (discord_id, f"{key_prefix}-{discord_id}", expiry_str))
                except sqlite3.OperationalError as e:
                    # Handle case where columns might be different
                    logging.warning(f"Error inserting with standard columns: {str(e)}")
                    # Get column names in the licenses table
                    cursor.execute("PRAGMA table_info(licenses)")
                    columns = [row[1] for row in cursor.fetchall()]
                    logging.info(f"Available columns in licenses table: {columns}")
                    
                    # Create a base query with required columns
                    query = "INSERT INTO licenses (owner_id, key, expiry"
                    values = [discord_id, f"{key_prefix}-{discord_id}", expiry_str]
                    
                    # Add optional columns if they exist
                    if "emailtf" in columns:
                        query += ", emailtf"
                        values.append("False")
                    if "credentialstf" in columns:
                        query += ", credentialstf"
                        values.append("False")
                    
                    query += ") VALUES (" + ", ".join(["?" for _ in values]) + ")"
                    cursor.execute(query, values)
            
            conn.commit()
            conn.close()
            
            # Try to add role to user in all guilds where the bot is present
            role_added = False
            for guild in self.bot.guilds:
                try:
                    # Log the guild we're checking
                    logging.info(f"Checking guild {guild.name} ({guild.id}) for user {discord_id}")
                    
                    # Check if this is the main guild from config
                    main_guild_id = None
                    try:
                        with open("config.json", "r") as f:
                            config = json.load(f)
                            main_guild_id = config.get("guild_id")
                    except Exception as config_error:
                        logging.error(f"Error reading config.json: {str(config_error)}")
                    
                    # Get server-specific role ID
                    conn = sqlite3.connect('data.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT client_id FROM server_configs WHERE guild_id = ?", (str(guild.id),))
                    result = cursor.fetchone()
                    conn.close()
                    
                    # Set role_id based on server config or default from main config
                    role_id = None
                    if result and result[0]:
                        role_id = int(result[0])
                        logging.info(f"Found server-specific role ID: {role_id}")
                    else:
                        # No server-specific role, try to get default from config
                        with open("config.json", "r") as f:
                            config = json.load(f)
                            default_role_id = int(config.get("Client_ID", 0))
                            if default_role_id == 0:
                                logging.warning(f"No default role ID found in config for guild {guild.id}")
                                continue
                            role_id = default_role_id
                            logging.info(f"Using default role ID from config: {role_id}")
                    
                    # Try to fetch member by ID (first convert to int)
                    try:
                        member = guild.get_member(int(discord_id))
                        if member:
                            logging.info(f"Found member {member.name} ({member.id}) in guild {guild.name}")
                        else:
                            logging.warning(f"Member {discord_id} not found in guild {guild.name}")
                            # Try to fetch member if not found initially
                            try:
                                member = await guild.fetch_member(int(discord_id))
                                logging.info(f"Fetched member {member.name} ({member.id})")
                            except Exception as fetch_error:
                                logging.error(f"Could not fetch member {discord_id} in guild {guild.id}: {str(fetch_error)}")
                                continue
                    except ValueError:
                        logging.error(f"Invalid Discord ID format: {discord_id}")
                        continue
                    
                    if not member:
                        continue
                    
                    # Find the role
                    role = discord.utils.get(guild.roles, id=role_id)
                    if role:
                        logging.info(f"Found role {role.name} ({role.id})")
                    else:
                        logging.warning(f"Role {role_id} not found in guild {guild.name}")
                        # Try to list available roles for debugging
                        roles_str = ", ".join([f"{r.name} ({r.id})" for r in guild.roles[:5]])
                        logging.info(f"Some available roles: {roles_str}")
                        continue
                    
                    # Add role
                    try:
                        await member.add_roles(role)
                        logging.info(f"Successfully added role {role.name} to {member.name}")
                        role_added = True
                    except Exception as role_error:
                        logging.error(f"Error adding role {role.id} to member {member.id}: {str(role_error)}")
                    
                    # Try to send DM to user
                    try:
                        embed = discord.Embed(
                            title="Thank you for your purchase!",
                            description=f"Your access to **{product_name}** has been activated.",
                            color=discord.Color.green()
                        )
                        embed.add_field(name="Subscription Type", value=access_type, inline=True)
                        embed.add_field(name="Expires", value=expiry_str if access_type != "lftstandard" else "Never", inline=True)
                        await member.send(embed=embed)
                        logging.info(f"Sent DM to {member.name}")
                    except Exception as dm_error:
                        logging.warning(f"Could not send DM to {member.name}: {str(dm_error)}")
                    
                except Exception as e:
                    logging.error(f"Error processing guild {guild.id}: {str(e)}")
            
            # Send notification to purchase notification channel
            try:
                notification_channel_id = 1351976637260107846  # The channel you specified
                logging.info(f"Attempting to send notification to channel ID: {notification_channel_id}")
                
                # Try to get the channel directly by ID first
                notification_channel = self.bot.get_channel(notification_channel_id)
                
                # If channel not found directly, fetch it (this might work when the channel is in a different guild)
                if not notification_channel:
                    logging.warning(f"Channel {notification_channel_id} not found via get_channel, trying to fetch it")
                    try:
                        notification_channel = await self.bot.fetch_channel(notification_channel_id)
                    except Exception as fetch_error:
                        logging.error(f"Error fetching channel {notification_channel_id}: {str(fetch_error)}")
                
                if notification_channel:
                    logging.info(f"Found notification channel: {notification_channel.name} ({notification_channel.id})")
                    
                    # Get user mention if possible
                    try:
                        user_obj = await self.bot.fetch_user(int(discord_id))
                        user_mention = user_obj.mention
                        logging.info(f"Successfully fetched user: {user_obj.name} ({user_obj.id})")
                    except Exception as user_error:
                        logging.error(f"Error fetching user {discord_id}: {str(user_error)}")
                        user_mention = f"<@{discord_id}>"
                    
                    # Create notification embed similar to the screenshot
                    embed = discord.Embed(color=discord.Color.dark_gray())
                    embed.add_field(name="Thanks for choosing us!", value=f"Successfully added `{key_prefix.replace('LifetimeKey', 'Lifetime')}` access to {user_mention} subscription.", inline=False)
                    
                    # Try to find tutorial and review channels in the same guild as the notification channel
                    guild = notification_channel.guild
                    tutorial_channel = discord.utils.get(guild.channels, name="setup-guide")
                    review_channel = discord.utils.get(guild.channels, name="reviews")
                    
                    tutorial_mention = f"<#{tutorial_channel.id}>" if tutorial_channel else "#setup-guide"
                    review_mention = f"<#{review_channel.id}>" if review_channel else "#reviews"
                    
                    guide_text = f"**»** Go to {tutorial_mention} and read the setup guide.\n"
                    review_text = f"**»** Please make a vouch in this format `+rep <10/10> <experience>` \n{review_mention}"
                    
                    embed.add_field(name="", value=guide_text + review_text, inline=False)
                    embed.set_footer(text="Email can be changed once a week!", icon_url="https://cdn.discordapp.com/emojis/1278802261748879390.webp?size=96&quality=lossless")
                    
                    try:
                        await notification_channel.send(embed=embed)
                        logging.info(f"Successfully sent purchase notification to channel {notification_channel_id}")
                    except Exception as send_error:
                        logging.error(f"Error sending message to channel {notification_channel_id}: {str(send_error)}")
                else:
                    logging.error(f"Notification channel {notification_channel_id} not found or bot doesn't have access")
            except Exception as notification_error:
                logging.error(f"Error sending purchase notification: {str(notification_error)}")
                # Continue even if notification fails - this shouldn't affect the purchase process
            
            if role_added:
                return True, f"Access granted to user {discord_id}"
            else:
                return True, f"Added to database, but couldn't find user in any guild to add role"
                
        except Exception as e:
            logging.error(f"Error granting access: {str(e)}")
            return False, f"Error: {str(e)}"
