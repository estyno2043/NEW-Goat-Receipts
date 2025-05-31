import logging
from utils.mongodb_manager import mongo_manager

def save_user_email(user_id, email):
    """Save user email to MongoDB"""
    try:
        success = mongo_manager.save_user_email(user_id, email)

        # Also update license document if it exists
        license_doc = mongo_manager.get_license(user_id)
        if license_doc:
            license_doc["email"] = email
            mongo_manager.create_or_update_license(user_id, license_doc)

        return success
    except Exception as e:
        logging.error(f"Error saving user email: {str(e)}")
        return False

def get_user_details(user_id):
    """Get user details from MongoDB for receipt generation

    Args:
        user_id: The Discord user ID

    Returns:
        Tuple containing (name, street, city, zip, country, email) or None if not found
    """
    try:
        return mongo_manager.get_user_details(user_id)
    except Exception as e:
        logging.error(f"Error getting user details: {e}")
        return None

def check_user_setup(user_id):
    """Check if user has both credentials and email set up"""
    try:
        return mongo_manager.check_user_setup(user_id)
    except Exception as e:
        logging.error(f"Error checking user setup: {e}")
        return False, False

def save_user_credentials(user_id, name, street, city, zip_code, country, is_random=False):
    """Save user credentials to MongoDB"""
    try:
        return mongo_manager.save_user_credentials(user_id, name, street, city, zip_code, country, is_random)
    except Exception as e:
        logging.error(f"Error saving user credentials: {str(e)}")
        return False

def clear_user_data(user_id):
    """Clear all user data from MongoDB"""
    try:
        return mongo_manager.clear_user_data(user_id)
    except Exception as e:
        logging.error(f"Error clearing user data: {str(e)}")
        return False

def get_user_email(user_id):
    """Get user email from MongoDB"""
    try:
        return mongo_manager.get_user_email(user_id)
    except Exception as e:
        logging.error(f"Error getting user email: {e}")
        return None

def update_subscription(user_id, subscription_type="Unlimited", days=365):
    """Add or update user subscription in MongoDB"""
    try:
        from datetime import datetime, timedelta

        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=days)

        # Format dates as strings
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # Create license data
        license_data = {
            "subscription_type": subscription_type,
            "start_date": start_str,
            "end_date": end_str,
            "is_active": True,
            "expiry": end_date.strftime('%d/%m/%Y %H:%M:%S'),
            "key": f"{subscription_type}-{user_id}"
        }

        return mongo_manager.create_or_update_license(user_id, license_data)
    except Exception as e:
        logging.error(f"Error updating subscription: {str(e)}")
        return False

def get_subscription(user_id):
    """Get user subscription info from MongoDB"""
    try:
        license_doc = mongo_manager.get_license(user_id)

        if license_doc:
            key = license_doc.get("key", "")
            expiry_str = license_doc.get("expiry")

            # Check if lifetime key
            if key and ("LifetimeKey" in key or "lifetime" in key.lower()):
                return "Lifetime", "Lifetime"
            else:
                subscription_type = license_doc.get("subscription_type", "Premium")
                return subscription_type, expiry_str

        # Default subscription if none exists
        return "Default", "1 Year"
    except Exception as e:
        logging.error(f"Error in get_subscription: {e}")
        return "Default", "1 Year"