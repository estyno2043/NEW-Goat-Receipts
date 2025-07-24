import os
import logging
from datetime import datetime, timedelta
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, OperationFailure
import asyncio

class MongoDBManager:
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self.connect()

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            # MongoDB connection string with credentials and SSL configuration
            uri = "mongodb+srv://kuboestok:oPb8iDVVzRwKe1RX@cluster0.gxc5mt1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&ssl=true&tlsAllowInvalidCertificates=true"

            # Create client with additional SSL options for Replit compatibility
            self._client = MongoClient(
                uri, 
                server_api=ServerApi('1'),
                ssl=True,
                tlsAllowInvalidCertificates=True,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                serverSelectionTimeoutMS=30000,
                maxPoolSize=10,
                retryWrites=True
            )

            # Test connection with timeout
            self._client.admin.command('ping')
            print("✅ Successfully connected to MongoDB")
            logging.info("Successfully connected to MongoDB!")

            # Select database
            self._db = self._client.goat_receipts

            # Create indexes for better performance
            self._create_indexes()

        except Exception as e:
            print("❌ MongoDB connection failed:")
            print(e)
            logging.error(f"Failed to connect to MongoDB: {e}")
            # Don't raise the exception, allow the bot to continue running
            # We'll handle MongoDB operations with proper error checking
            self._client = None
            self._db = None

    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Create indexes on commonly queried fields
            self._db.licenses.create_index("owner_id", unique=True)
            self._db.user_credentials.create_index("user_id", unique=True)
            self._db.user_emails.create_index("user_id", unique=True)
            # Guild-specific indexes
            self._db.guild_configs.create_index("guild_id", unique=True)
            self._db.guild_user_licenses.create_index([("guild_id", 1), ("user_id", 1)], unique=True)
            self._db.guild_user_credentials.create_index([("guild_id", 1), ("user_id", 1)], unique=True)
            self._db.guild_user_emails.create_index([("guild_id", 1), ("user_id", 1)], unique=True)
            self._db.server_access.create_index([("guild_id", 1), ("user_id", 1)], unique=True)
            # Used keys index
            self._db.used_keys.create_index("key", unique=True)
            logging.info("MongoDB indexes created successfully")
        except Exception as e:
            logging.warning(f"Error creating indexes: {e}")

    def get_database(self):
        """Get database instance"""
        if self._db is None:
            self.connect()

        # If still None after connection attempt, return None
        if self._db is None:
            logging.warning("MongoDB database is not available")
            return None
        return self._db

    def close_connection(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

    # License operations
    def get_license(self, user_id):
        """Get license for a user"""
        try:
            db = self.get_database()
            if db is None:
                return None
            license_doc = db.licenses.find_one({"owner_id": str(user_id)})
            return license_doc
        except Exception as e:
            logging.error(f"Error getting license for user {user_id}: {e}")
            return None

    def create_or_update_license(self, user_id, license_data):
        """Create or update license for a user"""
        try:
            db = self.get_database()
            if db is None:
                return False
            license_data["owner_id"] = str(user_id)
            license_data["updated_at"] = datetime.utcnow()

            result = db.licenses.update_one(
                {"owner_id": str(user_id)},
                {"$set": license_data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logging.error(f"Error creating/updating license for user {user_id}: {e}")
            return False

    def delete_license(self, user_id):
        """Delete license for a user"""
        try:
            db = self.get_database()
            result = db.licenses.delete_one({"owner_id": str(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting license for user {user_id}: {e}")
            return False

    def get_all_licenses(self):
        """Get all licenses"""
        try:
            db = self.get_database()
            return list(db.licenses.find())
        except Exception as e:
            logging.error(f"Error getting all licenses: {e}")
            return []

    def get_expired_licenses(self):
        """Get expired licenses"""
        try:
            db = self.get_database()
            current_time = datetime.utcnow()

            # Find licenses that have expired
            expired_licenses = []
            for license_doc in db.licenses.find():
                expiry_str = license_doc.get("expiry")
                key = license_doc.get("key", "")

                # Skip lifetime keys
                if key and ("LifetimeKey" in key or "lifetime" in key.lower()):
                    continue

                if expiry_str:
                    try:
                        expiry_date = datetime.strptime(expiry_str, '%d/%m/%Y %H:%M:%S')
                        if current_time > expiry_date:
                            expired_licenses.append(license_doc)
                    except ValueError:
                        continue

            return expired_licenses
        except Exception as e:
            logging.error(f"Error getting expired licenses: {e}")
            return []

    # User credentials operations
    def get_user_credentials(self, user_id):
        """Get user credentials"""
        try:
            db = self.get_database()
            if db is None:
                return None
            return db.user_credentials.find_one({"user_id": str(user_id)})
        except Exception as e:
            logging.error(f"Error getting credentials for user {user_id}: {e}")
            return None

    def save_user_credentials(self, user_id, name, street, city, zip_code, country, is_random=False):
        """Save user credentials"""
        try:
            db = self.get_database()
            if db is None:
                return False
            credentials_data = {
                "user_id": str(user_id),
                "name": name,
                "street": street,
                "city": city,
                "zip": zip_code,
                "country": country,
                "is_random": is_random,
                "updated_at": datetime.utcnow()
            }

            result = db.user_credentials.update_one(
                {"user_id": str(user_id)},
                {"$set": credentials_data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logging.error(f"Error saving credentials for user {user_id}: {e}")
            return False

    def delete_user_credentials(self, user_id):
        """Delete user credentials"""
        try:
            db = self.get_database()
            result = db.user_credentials.delete_one({"user_id": str(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting credentials for user {user_id}: {e}")
            return False

    # User email operations
    def get_user_email(self, user_id):
        """Get user email"""
        try:
            db = self.get_database()
            if db is None:
                return None
            email_doc = db.user_emails.find_one({"user_id": str(user_id)})
            return email_doc.get("email") if email_doc else None
        except Exception as e:
            logging.error(f"Error getting email for user {user_id}: {e}")
            return None

    def save_user_email(self, user_id, email):
        """Save user email"""
        try:
            db = self.get_database()
            if db is None:
                return False

            # Check if user already has an email and if it's within 7 days
            existing_email = db.user_emails.find_one({"user_id": str(user_id)})
            if existing_email:
                last_updated = existing_email.get("updated_at")
                if last_updated:
                    # Calculate days since last update
                    time_diff = datetime.utcnow() - last_updated
                    if time_diff.days < 7:
                        return {"success": False, "error": "email_change_restricted", "days_remaining": 7 - time_diff.days}

            email_data = {
                "user_id": str(user_id),
                "email": email,
                "updated_at": datetime.utcnow()
            }

            result = db.user_emails.update_one(
                {"user_id": str(user_id)},
                {"$set": email_data},
                upsert=True
            )
            return {"success": result.acknowledged}
        except Exception as e:
            logging.error(f"Error saving email for user {user_id}: {e}")
            return {"success": False, "error": "database_error"}

    def delete_user_email(self, user_id):
        """Delete user email"""
        try:
            db = self.get_database()
            result = db.user_emails.delete_one({"user_id": str(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting email for user {user_id}: {e}")
            return False

    # Combined operations
    def get_user_details(self, user_id):
        """Get complete user details for receipt generation"""
        try:
            # Get credentials
            credentials = self.get_user_credentials(user_id)
            logging.info(f"Retrieved credentials for user {user_id}: {credentials is not None}")
            if not credentials:
                logging.warning(f"No credentials found for user {user_id}")
                return None

            # Get email
            email = self.get_user_email(user_id)
            logging.info(f"Retrieved email for user {user_id}: {email is not None}")
            if not email:
                logging.warning(f"No email found for user {user_id}")
                return None

            # Ensure all required fields are present
            name = credentials.get("name")
            street = credentials.get("street") 
            city = credentials.get("city")
            zip_code = credentials.get("zip")
            country = credentials.get("country")

            if not all([name, street, city, zip_code, country, email]):
                missing_fields = []
                if not name: missing_fields.append("name")
                if not street: missing_fields.append("street")
                if not city: missing_fields.append("city")
                if not zip_code: missing_fields.append("zip")
                if not country: missing_fields.append("country")
                if not email: missing_fields.append("email")
                logging.warning(f"Missing required fields for user {user_id}: {missing_fields}")
                return None

            user_details = (name, street, city, zip_code, country, email)
            logging.info(f"Complete user details for {user_id}: {user_details}")
            return user_details
        except Exception as e:
            logging.error(f"Error getting user details for {user_id}: {e}")
            return None

    def check_user_setup(self, user_id):
        """Check if user has both credentials and email set up"""
        try:
            has_credentials = self.get_user_credentials(user_id) is not None
            has_email = self.get_user_email(user_id) is not None
            return has_credentials, has_email
        except Exception as e:
            logging.error(f"Error checking user setup for {user_id}: {e}")
            return False, False

    def clear_user_data(self, user_id):
        """Clear all user data"""
        try:
            db = self.get_database()
            if db is None:
                return False

            # Clear from all collections
            db.user_credentials.delete_many({"user_id": str(user_id)})
            db.user_emails.delete_many({"user_id": str(user_id)})
            db.licenses.delete_many({"user_id": str(user_id)})

            return True
        except Exception as e:
            logging.error(f"Error clearing user data: {e}")
            return False

    def clear_user_credentials_only(self, user_id):
        """Clear only user credentials (not email)"""
        try:
            db = self.get_database()
            if db is None:
                return False

            # Clear only credentials, keep email
            db.user_credentials.delete_many({"user_id": str(user_id)})

            return True
        except Exception as e:
            logging.error(f"Error clearing user credentials: {e}")
            return False

    def set_user_rate_limit(self, user_id, rate_limit_data):
        """Set rate limit for a user"""
        try:
            db = self.get_database()
            if db is None:
                return False

            # Update or insert rate limit record
            result = db.rate_limits.update_one(
                {"user_id": str(user_id)},
                {"$set": rate_limit_data},
                upsert=True
            )

            return result.acknowledged
        except Exception as e:
            logging.error(f"Error setting rate limit: {e}")
            return False

    def check_user_rate_limit(self, user_id):
        """Check if user is currently rate limited"""
        try:
            db = self.get_database()
            if db is None:
                return False

            from datetime import datetime
            current_time = datetime.now()

            rate_limit = db.rate_limits.find_one({"user_id": str(user_id)})

            if rate_limit:
                limit_expiry_str = rate_limit.get("limit_expiry")
                if limit_expiry_str:
                    limit_expiry = datetime.fromisoformat(limit_expiry_str)
                    if current_time < limit_expiry:
                        return True, limit_expiry
                    else:
                        # Rate limit expired, remove it
                        db.rate_limits.delete_one({"user_id": str(user_id)})
                        return False, None

            return False, None
        except Exception as e:
            logging.error(f"Error checking rate limit: {e}")
            return False, None

    def remove_user_rate_limit(self, user_id):
        """Remove rate limit for a user"""
        try:
            db = self.get_database()
            if db is None:
                return False

            result = db.rate_limits.delete_one({"user_id": str(user_id)})
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error removing rate limit: {e}")
            return False

    def reset_email_change_limit(self, user_id):
        """Reset email change limitation for a user, allowing them to change email once"""
        try:
            db = self.get_database()
            if db is None:
                return False

            # Check if user has an email record
            existing_email = db.user_emails.find_one({"user_id": str(user_id)})
            
            if existing_email:
                # Reset the updated_at timestamp to allow immediate email change
                # Set it to 8 days ago to bypass the 7-day restriction
                from datetime import datetime, timedelta
                reset_date = datetime.utcnow() - timedelta(days=8)
                
                result = db.user_emails.update_one(
                    {"user_id": str(user_id)},
                    {"$set": {"updated_at": reset_date}},
                    upsert=False
                )
                
                logging.info(f"Reset email change limit for user {user_id} - set updated_at to {reset_date}")
                return result.acknowledged
            else:
                # No email record exists, so no restriction to reset
                logging.info(f"No email record found for user {user_id} - no restriction to reset")
                return True
                
        except Exception as e:
            logging.error(f"Error resetting email change limit: {e}")
            return False

    # Guild configuration operations
    def save_guild_config(self, guild_id, owner_id, generate_channel_id, admin_role_id, client_role_id, image_channel_id):
        """Save guild configuration to MongoDB"""
        try:
            db = self.get_database()
            if db is None:
                return False

            config_data = {
                "guild_id": str(guild_id),
                "owner_id": str(owner_id),
                "generate_channel_id": str(generate_channel_id),
                "admin_role_id": str(admin_role_id),
                "client_role_id": str(client_role_id),
                "image_channel_id": str(image_channel_id),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = db.guild_configs.update_one(
                {"guild_id": str(guild_id)},
                {"$set": config_data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logging.error(f"Error saving guild config for {guild_id}: {e}")
            return False

    def get_guild_config(self, guild_id):
        """Get guild configuration from MongoDB"""
        try:
            db = self.get_database()
            if db is None:
                return None
            return db.guild_configs.find_one({"guild_id": str(guild_id)})
        except Exception as e:
            logging.error(f"Error getting guild config for {guild_id}: {e}")
            return None

    # Guild user operations (separate from main guild)
    def save_guild_user_license(self, guild_id, user_id, license_data):
        """Save license for a user in a specific guild"""
        try:
            db = self.get_database()
            if db is None:
                return False

            license_data.update({
                "guild_id": str(guild_id),
                "user_id": str(user_id),
                "updated_at": datetime.utcnow()
            })

            result = db.guild_user_licenses.update_one(
                {"guild_id": str(guild_id), "user_id": str(user_id)},
                {"$set": license_data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logging.error(f"Error saving guild user license for {guild_id}/{user_id}: {e}")
            return False

    def get_guild_user_license(self, guild_id, user_id):
        """Get license for a user in a specific guild"""
        try:
            db = self.get_database()
            if db is None:
                return None
            return db.guild_user_licenses.find_one({"guild_id": str(guild_id), "user_id": str(user_id)})
        except Exception as e:
            logging.error(f"Error getting guild user license for {guild_id}/{user_id}: {e}")
            return None

    def delete_guild_user_license(self, guild_id, user_id):
        """Delete license for a user in a specific guild"""
        try:
            db = self.get_database()
            if db is None:
                return False

            result = db.guild_user_licenses.delete_one({
                "guild_id": str(guild_id), 
                "user_id": str(user_id)
            })
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting guild user license for {guild_id}/{user_id}: {e}")
            return False

    def delete_server_access(self, guild_id, user_id):
        """Delete server access record for a user"""
        try:
            db = self.get_database()
            if db is None:
                return False

            result = db.server_access.delete_one({
                "guild_id": str(guild_id), 
                "user_id": str(user_id)
            })
            return result.deleted_count > 0
        except Exception as e:
            logging.error(f"Error deleting server access for {guild_id}/{user_id}: {e}")
            return False

    def save_guild_user_credentials(self, guild_id, user_id, name, street, city, zip_code, country, is_random=False):
        """Save credentials for a user in a specific guild"""
        try:
            db = self.get_database()
            if db is None:
                return False

            credentials_data = {
                "guild_id": str(guild_id),
                "user_id": str(user_id),
                "name": name,
                "street": street,
                "city": city,
                "zip": zip_code,
                "country": country,
                "is_random": is_random,
                "updated_at": datetime.utcnow()
            }

            result = db.guild_user_credentials.update_one(
                {"guild_id": str(guild_id), "user_id": str(user_id)},
                {"$set": credentials_data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logging.error(f"Error saving guild user credentials for {guild_id}/{user_id}: {e}")
            return False

    def get_guild_user_credentials(self, guild_id, user_id):
        """Get credentials for a user in a specific guild"""
        try:
            db = self.get_database()
            if db is None:
                return None
            return db.guild_user_credentials.find_one({"guild_id": str(guild_id), "user_id": str(user_id)})
        except Exception as e:
            logging.error(f"Error getting guild user credentials for {guild_id}/{user_id}: {e}")
            return None

    def save_guild_user_email(self, guild_id, user_id, email):
        """Save email for a user in a specific guild"""
        try:
            db = self.get_database()
            if db is None:
                return False

            email_data = {
                "guild_id": str(guild_id),
                "user_id": str(user_id),
                "email": email,
                "updated_at": datetime.utcnow()
            }

            result = db.guild_user_emails.update_one(
                {"guild_id": str(guild_id), "user_id": str(user_id)},
                {"$set": email_data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logging.error(f"Error saving guild user email for {guild_id}/{user_id}: {e}")
            return False

    def get_guild_user_email(self, guild_id, user_id):
        """Get email for a user in a specific guild"""
        try:
            db = self.get_database()
            if db is None:
                return None
            email_doc = db.guild_user_emails.find_one({"guild_id": str(guild_id), "user_id": str(user_id)})
            return email_doc.get("email") if email_doc else None
        except Exception as e:
            logging.error(f"Error getting guild user email for {guild_id}/{user_id}: {e}")
            return None

    def save_server_access(self, guild_id, user_id, added_by, access_type, expiry):
        """Save server access record"""
        try:
            db = self.get_database()
            if db is None:
                return False

            access_data = {
                "guild_id": str(guild_id),
                "user_id": str(user_id),
                "added_by": str(added_by),
                "access_type": access_type,
                "expiry": expiry,
                "added_at": datetime.utcnow()
            }

            result = db.server_access.update_one(
                {"guild_id": str(guild_id), "user_id": str(user_id)},
                {"$set": access_data},
                upsert=True
            )
            return result.acknowledged
        except Exception as e:
            logging.error(f"Error saving server access for {guild_id}/{user_id}: {e}")
            return False

    def get_server_access(self, guild_id, user_id):
        """Get server access record"""
        try:
            db = self.get_database()
            if db is None:
                return None
            return db.server_access.find_one({"guild_id": str(guild_id), "user_id": str(user_id)})
        except Exception as e:
            logging.error(f"Error getting server access for {guild_id}/{user_id}: {e}")
            return None

# Create global instance
mongo_manager = MongoDBManager()