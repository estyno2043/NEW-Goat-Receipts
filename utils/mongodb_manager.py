
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
            return result.acknowledged
        except Exception as e:
            logging.error(f"Error saving email for user {user_id}: {e}")
            return False
    
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
            if not credentials:
                return None
            
            # Get email
            email = self.get_user_email(user_id)
            if not email:
                return None
            
            return (
                credentials.get("name"),
                credentials.get("street"),
                credentials.get("city"),
                credentials.get("zip"),
                credentials.get("country"),
                email
            )
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
        """Clear all user data (credentials and email)"""
        try:
            creds_deleted = self.delete_user_credentials(user_id)
            email_deleted = self.delete_user_email(user_id)
            return creds_deleted or email_deleted
        except Exception as e:
            logging.error(f"Error clearing user data for {user_id}: {e}")
            return False

# Create global instance
mongo_manager = MongoDBManager()
