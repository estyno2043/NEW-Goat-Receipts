
import json
import os
import random
import string
import discord
from datetime import datetime, timedelta
import logging

class KeyManager:
    def __init__(self):
        self.valid_keys_file = 'data/valid_keys.json'
        self.used_keys_file = 'data/used_keys.json'
        
        # Create data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
        
        # Initialize files if they don't exist
        if not os.path.exists(self.valid_keys_file):
            with open(self.valid_keys_file, 'w') as f:
                json.dump({}, f)
                
        if not os.path.exists(self.used_keys_file):
            with open(self.used_keys_file, 'w') as f:
                json.dump({}, f)
    
    def generate_keys(self, subscription_type, count=30):
        """Generate unique license keys for a specific subscription type"""
        keys = []
        
        # Load existing keys to ensure uniqueness
        valid_keys = self._load_keys(self.valid_keys_file)
        used_keys = self._load_keys(self.used_keys_file)
        
        # All existing keys (both valid and used)
        all_keys = list(valid_keys.keys()) + list(used_keys.keys())
        
        # Generate unique keys
        for _ in range(count):
            key = self._generate_unique_key(all_keys)
            keys.append(key)
            all_keys.append(key)  # Add to list to avoid duplicates
            
            # Add key to valid keys with subscription info
            valid_keys[key] = {
                "subscription_type": subscription_type,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "redeemed": False
            }
        
        # Save updated valid keys
        self._save_keys(self.valid_keys_file, valid_keys)
        
        return keys
    
    def redeem_key(self, key, user_id):
        """Redeem a license key and return subscription details if valid"""
        valid_keys = self._load_keys(self.valid_keys_file)
        used_keys = self._load_keys(self.used_keys_file)
        
        # Check if key exists in valid keys
        if key in valid_keys:
            subscription_info = valid_keys[key]
            
            # Move key from valid to used keys
            used_keys[key] = {
                **subscription_info,
                "redeemed_by": str(user_id),
                "redeemed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "redeemed": True
            }
            
            # Remove from valid keys
            del valid_keys[key]
            
            # Save changes
            self._save_keys(self.valid_keys_file, valid_keys)
            self._save_keys(self.used_keys_file, used_keys)
            
            # Calculate expiry date based on subscription type
            subscription_type = subscription_info["subscription_type"]
            expiry_date = self._calculate_expiry(subscription_type)
            
            return {
                "success": True,
                "subscription_type": subscription_type,
                "expiry_date": expiry_date.strftime('%d/%m/%Y %H:%M:%S')
            }
            
        # Check if key was already used
        elif key in used_keys:
            return {
                "success": False,
                "error": "already_used",
                "redeemed_by": used_keys[key].get("redeemed_by", "Unknown"),
                "redeemed_at": used_keys[key].get("redeemed_at", "Unknown")
            }
            
        else:
            return {
                "success": False,
                "error": "invalid_key"
            }
    
    def _generate_unique_key(self, existing_keys, length=16):
        """Generate a unique license key"""
        while True:
            # Generate a random key with letters and numbers
            key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
            
            # Make sure it's unique
            if key not in existing_keys:
                return key
    
    def _load_keys(self, file_path):
        """Load keys from JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Return empty dict if file doesn't exist or is corrupted
            return {}
    
    def _save_keys(self, file_path, keys):
        """Save keys to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(keys, f, indent=4)
    
    def _calculate_expiry(self, subscription_type):
        """Calculate expiry date based on subscription type"""
        now = datetime.now()
        
        # Handle both formats (with and without "day" suffix)
        if subscription_type == "3day" or subscription_type == "3days" or subscription_type == "3_days":
            return now + timedelta(days=3)
        elif subscription_type == "14day" or subscription_type == "14days" or subscription_type == "14_days":
            return now + timedelta(days=14)
        elif subscription_type == "1month" or subscription_type == "1_month":
            return now + timedelta(days=30)
        elif "lifetime" in subscription_type.lower():
            # For lifetime subscriptions, set a date far in the future
            return now + timedelta(days=3650)  # ~10 years
        else:
            # Default to 1 day
            return now + timedelta(days=1)
import random
import string
import json
import os
import sqlite3
from datetime import datetime, timedelta
import logging

class KeyManager:
    """Manages license key generation and redemption"""
    
    def __init__(self):
        # Create data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
        
        # Initialize key files if they don't exist
        if not os.path.exists('data/valid_keys.json'):
            with open('data/valid_keys.json', 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists('data/used_keys.json'):
            with open('data/used_keys.json', 'w') as f:
                json.dump({}, f)
    
    def generate_keys(self, subscription_type, key_count=30, guild_key=False):
        """Generate a specified number of license keys
        
        Args:
            subscription_type (str): Type of subscription (3day, 14day, 1month, lifetime, guild)
            key_count (int): Number of keys to generate (default: 30)
            guild_key (bool): Whether these are guild subscription keys
            
        Returns:
            list: List of generated keys
        """
        # Load existing valid keys
        with open('data/valid_keys.json', 'r') as f:
            valid_keys = json.load(f)
        
        generated_keys = []
        
        for _ in range(key_count):
            # Generate a random key with prefix based on subscription type
            if guild_key:
                prefix = "G"  # Guild keys start with G
                if subscription_type.lower() == "lifetime":
                    prefix = "GL"  # Guild Lifetime
                else:
                    prefix = "G30"  # Guild 30-day
            else:
                if subscription_type.lower() == "3day":
                    prefix = "A"
                elif subscription_type.lower() == "14day":
                    prefix = "B"
                elif subscription_type.lower() == "1month":
                    prefix = "C"
                elif subscription_type.lower() == "lifetime":
                    prefix = "D"
                else:
                    prefix = "X"  # Default/unknown
            
            # Generate a 14-character alphanumeric code (excluding prefix)
            chars = string.ascii_uppercase + string.digits
            code = ''.join(random.choice(chars) for _ in range(14))
            key = f"{prefix}-{code}"
            
            # Add to valid keys
            valid_keys[key] = {
                "subscription_type": subscription_type,
                "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_guild_key": guild_key
            }
            
            generated_keys.append(key)
        
        # Save updated valid keys
        with open('data/valid_keys.json', 'w') as f:
            json.dump(valid_keys, f, indent=4)
        
        return generated_keys
    
    def redeem_key(self, key, user_id):
        """Redeem a license key
        
        Args:
            key (str): The license key to redeem
            user_id (str): The Discord user ID
            
        Returns:
            dict: Result of the redemption with success, subscription_type, and expiry_date
        """
        # Load valid and used keys
        with open('data/valid_keys.json', 'r') as f:
            valid_keys = json.load(f)
        
        with open('data/used_keys.json', 'r') as f:
            used_keys = json.load(f)
        
        # Check if key is valid
        if key not in valid_keys:
            return {
                "success": False,
                "error": "invalid_key",
                "message": "Invalid key."
            }
        
        # Check if key has already been used
        if key in used_keys:
            return {
                "success": False,
                "error": "already_used",
                "message": "This key has already been used."
            }
        
        # Get key data
        key_data = valid_keys[key]
        subscription_type = key_data["subscription_type"]
        is_guild_key = key_data.get("is_guild_key", False)
        
        # Calculate expiry date
        start_date = datetime.now()
        
        if subscription_type.lower() == "3day":
            expiry_date = start_date + timedelta(days=3)
        elif subscription_type.lower() == "14day":
            expiry_date = start_date + timedelta(days=14)
        elif subscription_type.lower() == "1month":
            expiry_date = start_date + timedelta(days=30)
        else:  # Lifetime
            # Set a far future date for lifetime keys (10 years)
            expiry_date = start_date + timedelta(days=3650)
        
        # Format dates
        expiry_str = expiry_date.strftime("%d/%m/%Y %H:%M:%S")
        
        # Add key to used keys
        used_keys[key] = {
            "subscription_type": subscription_type,
            "user_id": user_id,
            "redeemed_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expiry_date": expiry_str,
            "is_guild_key": is_guild_key
        }
        
        # Save used keys
        with open('data/used_keys.json', 'w') as f:
            json.dump(used_keys, f, indent=4)
        
        # If it's a guild key, add guild subscription
        if is_guild_key:
            try:
                from utils.guild_manager import GuildManager
                days = 30
                if subscription_type.lower() == "lifetime":
                    days = 0  # Lifetime
                GuildManager.add_guild_subscription(user_id, subscription_type, days)
            except Exception as e:
                logging.error(f"Error adding guild subscription: {e}")
        
        # Return success and key data
        return {
            "success": True,
            "subscription_type": subscription_type,
            "expiry_date": expiry_str,
            "is_guild_key": is_guild_key
        }
