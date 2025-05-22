import imaplib
import email
import re
import json
import logging
import sqlite3
from datetime import datetime, timedelta
import discord
import asyncio
import time
import os
from email.utils import parsedate_to_datetime

class GumroadEmailChecker:
    def __init__(self, bot):
        self.bot = bot
        self.imap_server = "imap.gmail.com"  # Gmail's IMAP server
        self.email_address = None
        self.email_password = None
        self._running = False
        self.check_interval = 60  # Check every minute (reduced from 5 minutes)
        self.last_checked_time = None
        self.notification_channel_id = 1351976637260107846  # Your notification channel

    async def setup(self):
        """Load configuration from config.json and environment variables"""
        try:
            # Get email credentials from environment variables
            self.email_address = os.environ.get("GUMROAD_EMAIL")
            self.email_password = os.environ.get("GMAIL_APP_PASSWORD")

            # Set log level to INFO for more detailed logs
            logging.getLogger().setLevel(logging.INFO)
            logging.info(f"Setting up email checker with email: {self.email_address}")

            if not self.email_address:
                logging.warning("Email address not configured in environment variables")
                return False

            if not self.email_password:
                logging.warning("Gmail app password not configured in environment variables")
                return False

            logging.info("Email checker credentials loaded successfully")
            return True
        except Exception as e:
            logging.error(f"Error loading email checker config: {str(e)}")
            return False

    async def start_checker(self):
        """Start the email checker background task."""
        if self._running:
            return

        setup_success = await self.setup()
        if not setup_success:
            logging.error("Failed to set up email checker - missing credentials")
            return

        self._running = True
        self.bot.loop.create_task(self._check_emails_loop())
        logging.info("Gumroad email checker background task started")

    async def _check_emails_loop(self):
        """Periodically check for new emails from Gumroad."""
        await self.bot.wait_until_ready()

        # Initialize the last checked time to now
        self.last_checked_time = datetime.now() - timedelta(hours=24)  # Start by checking emails from the last 24 hours
        logging.info(f"Starting to check emails from {self.last_checked_time}")

        while self._running and not self.bot.is_closed():
            try:
                await self._process_new_emails()
            except Exception as e:
                logging.error(f"Error in email checker: {str(e)}")
                logging.error(f"Exception details: {type(e).__name__} - {e}")
                import traceback
                logging.error(traceback.format_exc())

            # Wait for the next check interval
            await asyncio.sleep(self.check_interval)

    async def _process_new_emails(self):
        """Check for new emails and process purchases."""
        logging.info(f"Checking for new Gumroad purchase emails since {self.last_checked_time}")

        try:
            # Connect to the email server
            mail = imaplib.IMAP4_SSL(self.imap_server)

            try:
                # Log in to the email account
                logging.info(f"Logging in to {self.email_address}")

                # For Gmail, make sure to use the correct authentication method
                # Gmail may require OAuth2 or an App Password for less secure apps
                try:
                    mail.login(self.email_address, self.email_password)
                    logging.info("Login successful")
                except imaplib.IMAP4.error as e:
                    error_msg = str(e)
                    if "AUTHENTICATIONFAILED" in error_msg:
                        logging.error(f"IMAP login failed: {error_msg}")
                        logging.error("This may be due to one of the following reasons:")
                        logging.error("1. Incorrect email or password")
                        logging.error("2. Less secure app access is disabled in Gmail")
                        logging.error("3. You need to use an App Password instead of your regular password")
                        logging.error("Please check your Gmail settings and update the GMAIL_APP_PASSWORD secret")
                    else:
                        logging.error(f"IMAP login failed: {error_msg}")
                    return

            except Exception as e:
                logging.error(f"An unexpected error occurred during login: {str(e)}")
                return


            # Select the inbox
            mail.select("inbox")

            # Search for emails from Gumroad after the last checked time
            date_format = self.last_checked_time.strftime("%d-%b-%Y")
            search_criteria = f'(FROM "support@gumroad.com" SINCE "{date_format}")'
            logging.info(f"Searching with criteria: {search_criteria}")

            status, email_ids = mail.search(None, search_criteria)

            if status != "OK":
                logging.error(f"Search failed with status: {status}")
                mail.logout()
                return

            if not email_ids[0]:
                logging.info("No new emails from Gumroad found")
                # Update last checked time
                self.last_checked_time = datetime.now()
                mail.logout()
                return

            # Process each email
            email_id_list = email_ids[0].split()
            logging.info(f"Found {len(email_id_list)} new emails from Gumroad")

            for email_id in email_id_list:
                try:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        logging.error(f"Failed to fetch email ID {email_id}: {status}")
                        continue

                    msg = email.message_from_bytes(msg_data[0][1])

                    # Get email date
                    email_date = parsedate_to_datetime(msg["Date"])
                    logging.info(f"Processing email: {msg['Subject']} from {email_date}")

                    # Skip emails older than last checked time
                    if email_date <= self.last_checked_time:
                        logging.info(f"Skipping older email: {msg['Subject']} from {email_date}")
                        continue

                    # Check if this is a purchase notification
                    subject = msg["Subject"] or ""
                    if "You sold" in subject or "New sale" in subject or "purchase" in subject.lower():
                        logging.info(f"Processing purchase email: {subject}")

                        # Extract email body
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == "text/plain" or content_type == "text/html":
                                    try:
                                        payload = part.get_payload(decode=True)
                                        if payload:
                                            body += payload.decode('utf-8', errors='ignore')
                                    except Exception as e:
                                        logging.error(f"Error decoding email part: {str(e)}")
                        else:
                            try:
                                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                            except Exception as e:
                                logging.error(f"Error decoding email body: {str(e)}")

                        # Process the email body
                        if body:
                            # Save email body to a file for debugging (first 10000 chars)
                            with open("last_gumroad_email.txt", "w") as f:
                                f.write(body[:10000])

                            await self._process_purchase_email(body)
                        else:
                            logging.error("Failed to extract email body")
                    else:
                        logging.info(f"Skipping non-purchase email: {subject}")

                except Exception as e:
                    logging.error(f"Error processing email ID {email_id}: {str(e)}")

            # Update last checked time
            self.last_checked_time = datetime.now()
            logging.info(f"Updated last checked time to {self.last_checked_time}")
            mail.logout()

        except Exception as e:
            logging.error(f"Error in email checking process: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())

    async def _process_purchase_email(self, email_body):
        """Process the Gumroad purchase email to extract details and grant access."""
        try:
            logging.info("Processing purchase email content")

            # Extract product name/id
            product_name = None

            # Try multiple patterns to find product name
            patterns = [
                r'GOAT\s+Receipts\s+(\w+)\s+Plan',
                r'Product:\s*(.+?)(?:\n|<br>|</)',
                r'Product\s+Name:?\s*(.+?)(?:\n|<br>|</)',
                r'You\s+sold\s+(.+?)(?:\s+to|\.|\n|<br>|</)',
                r'purchased\s+(.+?)(?:\s+for|\.|,|\n|<br>|</)'
            ]

            for pattern in patterns:
                product_match = re.search(pattern, email_body, re.IGNORECASE)
                if product_match:
                    product_name = product_match.group(1).strip()
                    logging.info(f"Found product: {product_name}")
                    break

            if not product_name:
                logging.warning("Could not find product name in email")
                # Default to "GOAT Receipts" if we can't find a specific product
                product_name = "GOAT Receipts Plan"

            # Extract Discord ID - look for it in multiple formats
            discord_id = None

            # Try multiple patterns to find Discord ID
            id_patterns = [
                r'Discord\s+ID\s*(?:<[^>]*>)?\s*(\d{17,20})',
                r'Discord\s+ID:?\s*(\d{17,20})',
                r'Discord:?\s*(\d{17,20})',
                r'discord\s+id\s*[=:]?\s*(\d{17,20})'
            ]

            for pattern in id_patterns:
                discord_id_match = re.search(pattern, email_body, re.IGNORECASE | re.DOTALL)
                if discord_id_match:
                    discord_id = discord_id_match.group(1).strip()
                    logging.info(f"Found Discord ID: {discord_id}")
                    break

            # If no Discord ID found yet, try to find any 17-20 digit number
            if not discord_id:
                logging.info("No Discord ID found with standard patterns, searching for numeric IDs...")
                all_numbers = re.findall(r'\b(\d{17,20})\b', email_body)
                for num in all_numbers:
                    if len(num) >= 17 and len(num) <= 20:
                        discord_id = num
                        logging.info(f"Found potential Discord ID from numeric pattern: {discord_id}")
                        break

            if not discord_id:
                logging.warning("Could not find Discord ID in email")
                # Save a sample of the email for debugging
                with open("discord_id_not_found.txt", "w") as f:
                    f.write(email_body[:5000])  # First 5000 chars
                return

            # Map product to access type and duration
            product_mapping = {
                "1 day": ("1dstandard", 1),
                "14 days": ("14dstandard", 14),
                "1 month": ("1mstandard", 30),
                "lifetime": ("lftstandard", 1500),
                # Add more variations
                "1day": ("1dstandard", 1),
                "14day": ("14dstandard", 14),
                "1 day plan": ("1dstandard", 1),
                "14 days plan": ("14dstandard", 14),
                "1 month plan": ("1mstandard", 30),
                "lifetime plan": ("lftstandard", 1500)
            }

            # Try to match by product name
            access_type, days = None, None
            product_name_lower = product_name.lower()

            for key, value in product_mapping.items():
                if key.lower() in product_name_lower:
                    access_type, days = value
                    logging.info(f"Matched product to: {key} - {access_type} for {days} days")
                    break

            if not access_type:
                # Default based on patterns in the product name
                if "lifetime" in product_name_lower:
                    access_type, days = "lftstandard", 1500
                elif "month" in product_name_lower:
                    access_type, days = "1mstandard", 30
                elif "14" in product_name_lower or "fourteen" in product_name_lower:
                    access_type, days = "14dstandard", 14
                else:
                    # Default to 1 day
                    access_type, days = "1dstandard", 1

                logging.info(f"Using default product mapping: {access_type} for {days} days")

            # Grant access to user
            logging.info(f"Granting {access_type} access for {days} days to user {discord_id}")
            success, message = await self._grant_access(discord_id, access_type, days, product_name)
            logging.info(f"Access grant result: {success} - {message}")

        except Exception as e:
            logging.error(f"Error processing purchase email: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())

    async def _grant_access(self, discord_id, access_type, days, product_name):
        """Grant access to the user based on their purchase - reused from gumroad_webhook.py"""
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
                notification_channel_id = self.notification_channel_id
                logging.info(f"Attempting to send notification to channel ID: {notification_channel_id}")

                # Try to get the channel directly by ID first
                notification_channel = self.bot.get_channel(notification_channel_id)

                # If channel not found directly, fetch it
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

                    # Create notification embed
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

            if role_added:
                return True, f"Access granted to user {discord_id}"
            else:
                return True, f"Added to database, but couldn't find user in any guild to add role"

        except Exception as e:
            logging.error(f"Error granting access: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return False, f"Error: {str(e)}"