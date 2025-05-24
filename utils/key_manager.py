
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
        
        if subscription_type == "3day":
            return now + timedelta(days=3)
        elif subscription_type == "14day":
            return now + timedelta(days=14)
        elif subscription_type == "1month":
            return now + timedelta(days=30)
        elif subscription_type == "lifetime":
            # For lifetime subscriptions, set a date far in the future
            return now + timedelta(days=3650)  # ~10 years
        else:
            # Default to 1 day
            return now + timedelta(days=1)
