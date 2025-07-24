# The KeyManager class is updated to include database initialization and schema management.
import json
import os
import random
import string
import sqlite3
from datetime import datetime, timedelta
import logging
import requests

class KeyManager:
    def __init__(self):
        self.valid_keys_file = 'data/valid_keys.json'
        self.used_keys_file = 'data/used_keys.json'
        # Load Gumroad access token from environment variables (Replit Secrets)
        import os
        self.gumroad_access_token = os.getenv("GUMROAD_ACCESS_TOKEN")
        
        if not self.gumroad_access_token:
            logging.error("GUMROAD_ACCESS_TOKEN not found in environment variables")
            # Fallback to config.json for backward compatibility
            try:
                with open("config.json", "r") as f:
                    config = json.load(f)
                    self.gumroad_access_token = config.get("gumroad_access_token")
                    if self.gumroad_access_token:
                        logging.warning("Using Gumroad token from config.json - consider moving to Secrets")
            except Exception as e:
                logging.error(f"Error loading config: {str(e)}")
            
            if not self.gumroad_access_token:
                logging.error("No Gumroad access token found in environment variables or config.json")

        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)

        # Create empty files if they don't exist
        if not os.path.exists(self.valid_keys_file):
            with open(self.valid_keys_file, 'w') as f:
                json.dump({}, f)

        if not os.path.exists(self.used_keys_file):
            with open(self.used_keys_file, 'w') as f:
                json.dump({}, f)

        # Initialize the database
        self._init_database()

    def _init_database(self):
        """Ensure the database has the required tables and columns"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        # Make sure server_access table has the expiry column
        try:
            cursor.execute("SELECT expiry FROM server_access LIMIT 1")
        except sqlite3.OperationalError:
            # Add the missing column
            try:
                cursor.execute("ALTER TABLE server_access ADD COLUMN expiry TEXT")
                print("Added missing expiry column to server_access table")
            except sqlite3.OperationalError:
                # Table might not exist yet, that's okay
                pass

        conn.commit()
        conn.close()

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
        """Redeem a license key using Gumroad API verification"""
        try:
            # First check if key was already used locally
            used_keys = self._load_keys(self.used_keys_file)
            if key in used_keys:
                return {
                    "success": False,
                    "error": "already_used",
                    "redeemed_by": used_keys[key].get("redeemed_by", "Unknown"),
                    "redeemed_at": used_keys[key].get("redeemed_at", "Unknown")
                }

            # Verify key with Gumroad API
            verification_result = self._verify_gumroad_key(key)

            if not verification_result["success"]:
                return {
                    "success": False,
                    "error": "invalid_key"
                }

            # Determine subscription type from product name
            product_name = verification_result.get("product_name", "").lower()
            subscription_type = self._determine_subscription_type(product_name)

            if not subscription_type:
                return {
                    "success": False,
                    "error": "unknown_product"
                }

            # Mark key as used locally
            used_keys[key] = {
                "subscription_type": subscription_type,
                "redeemed_by": str(user_id),
                "redeemed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "redeemed": True,
                "product_name": verification_result.get("product_name", "Unknown Product"),
                "gumroad_verified": True
            }

            self._save_keys(self.used_keys_file, used_keys)

            # Calculate expiry date based on subscription type
            expiry_date = self._calculate_expiry(subscription_type)

            return {
                "success": True,
                "subscription_type": subscription_type,
                "expiry_date": expiry_date.strftime('%d/%m/%Y %H:%M:%S')
            }

        except Exception as e:
            logging.error(f"Error redeeming Gumroad key: {str(e)}")
            return {
                "success": False,
                "error": "verification_failed"
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
        elif subscription_type == "guild_30days" or subscription_type == "guild30":
            return now + timedelta(days=30)
        elif "lifetime" in subscription_type.lower() or subscription_type == "guild_lifetime":
            # For lifetime subscriptions, set a date far in the future
            return now + timedelta(days=3650)  # ~10 years
        else:
            # Default to 1 day
            return now + timedelta(days=1)


    def _verify_gumroad_key(self, license_key):
        """Verify license key with Gumroad API"""
        try:
            # Get all products first to find the correct product_id
            products = self._get_gumroad_products()

            for product in products:
                product_id = product.get("id")
                if not product_id:
                    continue

                # Try to verify the key with this product
                url = "https://api.gumroad.com/v2/licenses/verify"
                headers = {
                    "Authorization": f"Bearer {self.gumroad_access_token}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }

                data = {
                    "product_id": product_id,
                    "license_key": license_key,
                    "increment_uses_count": "true"
                }

                response = requests.post(url, headers=headers, data=data)

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success", False):
                        return {
                            "success": True,
                            "product_name": product.get("name", "Unknown Product"),
                            "product_id": product_id,
                            "license_data": result
                        }

            # If no product matched, the key is invalid
            return {"success": False, "error": "invalid_key"}

        except Exception as e:
            logging.error(f"Error verifying Gumroad key: {str(e)}")
            return {"success": False, "error": "api_error"}

    def _get_gumroad_products(self):
        """Get all products from Gumroad"""
        try:
            url = "https://api.gumroad.com/v2/products"
            headers = {
                "Authorization": f"Bearer {self.gumroad_access_token}"
            }

            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                return result.get("products", [])
            else:
                logging.error(f"Failed to get Gumroad products: {response.status_code}")
                return []

        except Exception as e:
            logging.error(f"Error getting Gumroad products: {str(e)}")
            return []

    def _determine_subscription_type(self, product_name):
        """Determine subscription type from product name"""
        product_name = product_name.lower()

        # Map product names to subscription types
        if "3 day" in product_name or "3day" in product_name or "3-day" in product_name:
            return "3day"
        elif "14 day" in product_name or "14day" in product_name or "14-day" in product_name or "2 week" in product_name:
            return "14day"
        elif "1 month" in product_name or "1month" in product_name or "1-month" in product_name or "30 day" in product_name:
            return "1month"
        elif "lifetime" in product_name or "permanent" in product_name or "forever" in product_name:
            return "lifetime"
        elif "1 day" in product_name or "1day" in product_name or "1-day" in product_name:
            return "1day"
        else:
            # Default fallback - try to extract from common patterns
            if "day" in product_name:
                return "3day"  # Default to 3 days for day-based plans
            elif "month" in product_name:
                return "1month"  # Default to 1 month for month-based plans
            else:
                return None  # Unknown product type

    def _migrate_used_keys_to_mongo(self):
        """Migrate existing used keys from local file to MongoDB"""
        try:
            # Check if local used keys file exists
            if not os.path.exists(self.used_keys_file):
                return

            used_keys = self._load_keys(self.used_keys_file)
            if not used_keys:
                return

            from utils.mongodb_manager import mongo_manager
            db = mongo_manager.get_database()
            if db is None:
                return

            migrated_count = 0
            for key, key_data in used_keys.items():
                # Check if key already exists in MongoDB
                if not self._is_key_used_in_mongo(key):
                    # Add the key field to the data
                    key_data["key"] = key
                    key_data["created_at"] = datetime.utcnow()

                    try:
                        db.used_keys.insert_one(key_data)
                        migrated_count += 1
                    except Exception as e:
                        logging.error(f"Error migrating key {key}: {str(e)}")

            if migrated_count > 0:
                logging.info(f"Successfully migrated {migrated_count} used keys to MongoDB")

                # Optionally backup and clear local file after successful migration
                backup_file = f"{self.used_keys_file}.backup"
                os.rename(self.used_keys_file, backup_file)
                logging.info(f"Local used keys file backed up to {backup_file}")

        except Exception as e:
            logging.error(f"Error during used keys migration: {str(e)}")