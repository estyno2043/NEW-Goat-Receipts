
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
                    return True, 0, 0, 0  # Owner is always allowed, no counting needed
                    
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
                return True, 1, current_time + self.window, self.window
            
            # User has an existing record within the time window
            receipts_generated = user_data[0]
            first_receipt_time = user_data[1]
            
            # Check if user has reached the limit
            if receipts_generated >= self.limit:
                # Calculate remaining time
                reset_time = first_receipt_time + self.window
                remaining_time = reset_time - current_time
                
                if remaining_time <= 0:
                    # Time window has passed, reset counter
                    execute_query(
                        "UPDATE receipt_rate_limits SET receipts_generated = 1, first_receipt_time = ?, last_receipt_time = ? WHERE user_id = ?",
                        params=(current_time, current_time, user_id)
                    )
                    return True, 1, current_time + self.window, self.window
                else:
                    # Still within rate limit window and at limit
                    return False, receipts_generated, reset_time, remaining_time
            
            # User hasn't reached limit, increment count
            execute_query(
                "UPDATE receipt_rate_limits SET receipts_generated = receipts_generated + 1, last_receipt_time = ? WHERE user_id = ?",
                params=(current_time, user_id)
            )
            
            new_count = receipts_generated + 1
            reset_time = first_receipt_time + self.window
            remaining_time = reset_time - current_time
            
            return True, new_count, reset_time, remaining_time
            
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
