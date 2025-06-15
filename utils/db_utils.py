import logging
from utils.mongodb_manager import mongo_manager

def save_user_email(user_id, email):
    """Save user email using MongoDB"""
    result = mongo_manager.save_user_email(user_id, email)
    # Return boolean for backward compatibility
    if isinstance(result, dict):
        return result.get("success", False)
    return result

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

def validate_user_for_receipt(user_id):
    """Validate if user has all required information for receipt generation"""
    try:
        user_details = get_user_details(user_id)
        if user_details is None:
            return False, "No user details found. Please ensure your information is set up."

        name, street, city, zip_code, country, email = user_details

        if not all([name, street, city, zip_code, country, email]):
            return False, "Incomplete user information. Please update your credentials and email."

        return True, "User validation successful"
    except Exception as e:
        logging.error(f"Error validating user for receipt: {e}")
        return False, f"Validation error: {str(e)}"

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