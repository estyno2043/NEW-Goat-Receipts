
import json
import hmac
import hashlib
import logging
import sqlite3
from datetime import datetime, timedelta
import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class SellAuthWebhook:
    def __init__(self, bot):
        self.bot = bot
        self.webhook_secret = "6bb97db8939291a64aec94163411947f44d06da7d70a09464f77323b0415a98e"
        self.purchases_channel_id = 1374468080817803264
        self.commands_channel_id = 1369426783153160304
        self.reviews_channel_id = 1339306483816337510

    def verify_signature(self, payload, signature):
        """Verify the webhook signature from SellAuth"""
        if not signature:
            return False
            
        # Calculate expected signature
        computed_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)

    async def process_webhook(self, data, signature=None):
        """Process incoming webhook from SellAuth"""
        try:
            logging.info(f"Processing SellAuth webhook: {data}")
            
            # Verify signature if provided
            if signature and not self.verify_signature(json.dumps(data), signature):
                logging.warning("Invalid SellAuth webhook signature")
                return False, "Invalid signature"
                
            # Extract relevant data from the webhook
            customer_discord_id = data.get("discord_id")
            if not customer_discord_id:
                # Try to find Discord ID in custom fields or other locations
                custom_fields = data.get("custom_fields", {})
                for field_name, field_value in custom_fields.items():
                    if "discord" in field_name.lower() and field_value:
                        customer_discord_id = field_value
                        break
            
            # Clean up Discord ID (remove @ or other non-numeric characters)
            if customer_discord_id:
                customer_discord_id = ''.join(c for c in customer_discord_id if c.isdigit())
            
            if not customer_discord_id:
                logging.warning("No Discord ID found in webhook data")
                return False, "No Discord ID found"
            
            # Grant access for 1 day
            success, message = await self.grant_access(customer_discord_id)
            return success, message
            
        except Exception as e:
            logging.error(f"Error processing SellAuth webhook: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return False, f"Error: {str(e)}"
    
    async def grant_access(self, discord_id):
        """Grant 1-day access to the user"""
        try:
            logging.info(f"Granting 1-day access to user ID: {discord_id}")
            
            # Connect to the database
            conn = sqlite3.connect('data.db', timeout=30.0)
            conn.execute("PRAGMA busy_timeout = 30000")  # 30 second timeout
            cursor = conn.cursor()
            
            # Set expiry date (1 day from now)
            expiry_date = datetime.now() + timedelta(days=1)
            expiry_str = expiry_date.strftime('%d/%m/%Y %H:%M:%S')
            
            key_prefix = "1Day-SellAuth"
            
            # Check if user exists in licenses table
            cursor.execute("SELECT * FROM licenses WHERE owner_id = ?", (discord_id,))
            user_exists = cursor.fetchone()
            
            if user_exists:
                # Update existing license
                cursor.execute("""
                UPDATE licenses 
                SET expiry = ?, key = ? 
                WHERE owner_id = ?
                """, (expiry_str, f"{key_prefix}-{discord_id}", discord_id))
            else:
                # Create new license
                cursor.execute("""
                INSERT INTO licenses (owner_id, expiry, key)
                VALUES (?, ?, ?)
                """, (discord_id, expiry_str, f"{key_prefix}-{discord_id}"))
            
            conn.commit()
            conn.close()
            
            # Send notification to purchase channel and DM
            await self.send_notifications(discord_id, "1 (Email Access Only)")
            
            return True, f"Access granted to user {discord_id} until {expiry_str}"
            
        except Exception as e:
            logging.error(f"Error granting access: {str(e)}")
            return False, f"Error granting access: {str(e)}"
    
    async def send_notifications(self, discord_id, subscription_type):
        """Send notification to purchase channel and user DM"""
        try:
            # Get bot instance
            if not self.bot:
                logging.error("Bot instance not available")
                return
            
            # Create the embed message
            embed = discord.Embed(
                title="Thank you for purchasing",
                description=f"<@{discord_id}>, your subscription has been updated. Check below\n\n"
                           f"-# Run command /generate in <#{self.commands_channel_id}> to continue\n"
                           f"Subscription Consider leaving a review\n"
                           f"{subscription_type} Please consider leaving a review at ⁠<#{self.reviews_channel_id}>",
                color=discord.Color.from_str("#c2ccf8")
            )
            
            # Current date for the footer
            current_date = datetime.now().strftime('%m/%d/%Y %H:%M')
            embed.set_footer(text=f"Bot • {current_date}")
            
            # Send to purchase channel
            purchase_channel = self.bot.get_channel(self.purchases_channel_id)
            if purchase_channel:
                try:
                    await purchase_channel.send(content=f"<@{discord_id}>", embed=embed)
                    logging.info(f"Sent purchase notification to channel for user {discord_id}")
                except Exception as channel_error:
                    logging.error(f"Error sending to channel: {str(channel_error)}")
            
            # Send DM to user
            try:
                # Try to get the user
                user = await self.bot.fetch_user(int(discord_id))
                if user:
                    await user.send(content=f"<@{discord_id}>", embed=embed)
                    logging.info(f"Sent DM to user {discord_id}")
            except Exception as dm_error:
                logging.error(f"Error sending DM to user {discord_id}: {str(dm_error)}")
            
            return True
        except Exception as e:
            logging.error(f"Error sending notifications: {str(e)}")
            return False
