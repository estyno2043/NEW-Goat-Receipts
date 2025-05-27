import time
import sqlite3
from datetime import datetime, timedelta
import discord
from utils.db_utils import execute_query

class ReceiptRateLimiter:
    def __init__(self):
        self.limit = 5  # 5 receipts
        self.window = 10800  # 3 hours in seconds

    def _initialize_table(self):
        """Create the rate_limit table if it doesn't exist"""
        try:
            execute_query("""
                CREATE TABLE IF NOT EXISTS receipt_rate_limits (
                    user_id TEXT PRIMARY KEY,
                    receipts_generated INTEGER DEFAULT 0,
                    first_receipt_time INTEGER,
                    last_receipt_time INTEGER
                )
            """)
            execute_query("""
                CREATE TABLE IF NOT EXISTS review_requests (
                    user_id TEXT PRIMARY KEY,
                    review_sent BOOLEAN DEFAULT FALSE,
                    receipts_at_request INTEGER
                )
            """)
            return True
        except Exception as e:
            print(f"Error initializing rate limit table: {e}")
            return False

    def add_receipt(self, user_id):
        """
        Record a new receipt generation for a user
        Returns (is_allowed, count, reset_time, remaining_time)
        """
        try:
            # Check if user is owner (exempt from rate limits)
            import json
            with open("config.json", "r") as f:
                config = json.load(f)
                if str(user_id) == config.get("owner_id"):
                    return True, 0, 0, 0
                    
            # Add the actual rate limiting logic here if needed
            return True, 0, 0, 0
            
        except Exception as e:
            print(f"Error in add_receipt: {e}")
            return True, 0, 0, 0

    def record_successful_email(self, user_id):
        """
        Record a successful email send for rate limiting
        Returns (count, reset_time, remaining_time)
        """
        try:
            # Check if user is owner (exempt from rate limits)
            import json
            with open("config.json", "r") as f:
                config = json.load(f)
                if str(user_id) == config.get("owner_id"):
                    return 0, 0, 0  # Owner is always allowed, no counting needed

            self._initialize_table()
            user_id = str(user_id)  # Ensure user_id is string
            current_time = int(time.time())

            # Get current user data
            user_data = execute_query(
                "SELECT receipts_generated, first_receipt_time, last_receipt_time FROM receipt_rate_limits WHERE user_id = ?",
                params=(user_id,),
                fetchone=True
            )

            # If user has no record or it's been more than 3 hours since first receipt
            if not user_data or (current_time - user_data[1]) > self.window:
                # Start a new counting period
                execute_query(
                    "INSERT OR REPLACE INTO receipt_rate_limits (user_id, receipts_generated, first_receipt_time, last_receipt_time) VALUES (?, ?, ?, ?)",
                    params=(user_id, 1, current_time, current_time)
                )
                return 1, current_time + self.window, self.window

            # User has an existing record within the time window
            receipts_generated = user_data[0]
            first_receipt_time = user_data[1]

            # Increment count
            execute_query(
                "UPDATE receipt_rate_limits SET receipts_generated = receipts_generated + 1, last_receipt_time = ? WHERE user_id = ?",
                params=(current_time, user_id)
            )

            new_count = receipts_generated + 1
            reset_time = first_receipt_time + self.window
            remaining_time = reset_time - current_time

            return new_count, reset_time, remaining_time

        except Exception as e:
            print(f"Error recording email send: {e}")
            return 0, 0, 0
        except Exception as e:
            print(f"Error in rate limiter: {e}")
            # In case of error, allow the operation to proceed
            return True, 0, 0, 0

    def format_time_remaining(self, seconds):
        """Format seconds into a human-readable time string"""
        if seconds <= 0:
            return "now"

        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if hours > 0:
            parts.append(f"{int(hours)} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            parts.append(f"{int(minutes)} minute{'s' if minutes > 1 else ''}")
        if seconds > 0 and not hours and minutes < 5:
            parts.append(f"{int(seconds)} second{'s' if seconds > 1 else ''}")

        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return f"{parts[0]}, {parts[1]} and {parts[2]}"

    def get_rate_limit_message(self, user_id):
        """Get the rate limit message if user is rate limited"""
        try:
            # Check if user is owner (exempt from rate limits)
            import json
            with open("config.json", "r") as f:
                config = json.load(f)
                if str(user_id) == config.get("owner_id"):
                    return None  # Owner is exempt from rate limits

            user_id = str(user_id)
            current_time = int(time.time())

            user_data = execute_query(
                "SELECT first_receipt_time FROM receipt_rate_limits WHERE user_id = ? AND receipts_generated >= ?",
                params=(user_id, self.limit),
                fetchone=True
            )

            if not user_data:
                return None

            first_receipt_time = user_data[0]
            reset_time = first_receipt_time + self.window
            remaining_time = reset_time - current_time

            if remaining_time <= 0:
                return None

            time_str = self.format_time_remaining(remaining_time)

            return (
                "🧾 **Whoa there, Receipt Champ!** 🏆\n\n"
                "You've already whipped up 5 receipts in the last 3 hours.\n"
                "Let the printer cool down before you cook up more. 🖨️🔥\n\n"
                f"> -# You can generate your next receipt in {time_str}."
            )

        except Exception as e:
            print(f"Error getting rate limit message: {e}")
            return None

    def check_review_request(self, user_id, current_count, bot, channel):
        """
        Check if user should receive a review request after generating 3 receipts
        Only sends once per user and only in main guild
        Returns True if review message was sent, False otherwise
        """
        try:
            # Check if user is owner (exempt from review requests)
            import json
            with open("config.json", "r") as f:
                config = json.load(f)
                if str(user_id) == config.get("owner_id"):
                    return False

                # Check if we're in the main guild
                main_guild_id = config.get("guild_id", "1339298010169086072")
                if not channel or not channel.guild or str(channel.guild.id) != main_guild_id:
                    return False

            user_id = str(user_id)

            # Check if user has already received a review request
            review_data = execute_query(
                "SELECT review_sent, receipts_at_request FROM review_requests WHERE user_id = ?",
                params=(user_id,),
                fetchone=True
            )

            # If user already received review request, don't send again
            if review_data and review_data[0]:  # review_sent is True
                return False

            # Check if user has generated exactly 3 receipts
            if current_count == 3:
                # Mark review as sent
                execute_query(
                    "INSERT OR REPLACE INTO review_requests (user_id, review_sent, receipts_at_request) VALUES (?, ?, ?)",
                    params=(user_id, True, current_count)
                )

                # Send review request message
                import asyncio
                asyncio.create_task(self._send_review_message(channel, user_id))
                return True

            return False

        except Exception as e:
            print(f"Error checking review request: {e}")
            return False

    async def _send_review_message(self, channel, user_id=None):
        """Send the review request message to the channel"""
        try:
            import discord
            embed = discord.Embed(
                title="⭐ We'd appreciate your feedback !",
                description="**Please consider leaving a review in** <#1339306483816337510>\n-# Your input helps us improve.",
                color=discord.Color.gold()
            )

            # Send with user mention if provided
            content = f"<@{user_id}>" if user_id else None
            await channel.send(content=content, embed=embed)
        except Exception as e:
            print(f"Error sending review message: {e}")