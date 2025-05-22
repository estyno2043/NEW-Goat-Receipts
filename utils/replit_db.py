
import os
import json
import time
from datetime import datetime

# Check if we're using Replit's environment
try:
    from replit import db
    USING_REPLIT_DB = True
except ImportError:
    # Fallback to a file-based solution if not on Replit
    USING_REPLIT_DB = False
    import json
    import os
    
    class FallbackDB:
        def __init__(self):
            self.db_file = "replit_db_fallback.json"
            if os.path.exists(self.db_file):
                with open(self.db_file, 'r') as f:
                    self.data = json.load(f)
            else:
                self.data = {}
                
        def __getitem__(self, key):
            return self.data.get(key)
            
        def __setitem__(self, key, value):
            self.data[key] = value
            with open(self.db_file, 'w') as f:
                json.dump(self.data, f)
                
        def __delitem__(self, key):
            if key in self.data:
                del self.data[key]
                with open(self.db_file, 'w') as f:
                    json.dump(self.data, f)
                    
        def get(self, key, default=None):
            return self.data.get(key, default)
            
        def prefix(self, prefix):
            return [k for k in self.data.keys() if k.startswith(prefix)]
    
    db = FallbackDB()

def user_key(user_id):
    """Generate a key for storing user data"""
    return f"user_{user_id}"

def user_email_key(user_id):
    """Generate a key for storing user email"""
    return f"user_email_{user_id}"

def user_credentials_key(user_id):
    """Generate a key for storing user credentials status"""
    return f"user_credentials_{user_id}"

def save_user_data(user_id, data_dict):
    """
    Save user data to the Replit database
    
    Args:
        user_id: The Discord user ID
        data_dict: Dictionary containing user data
    """
    key = user_key(user_id)
    
    # Add timestamp for when data was last updated
    data_dict['last_updated'] = datetime.now().isoformat()
    
    # Store the data
    db[key] = json.dumps(data_dict)
    
    return True

def get_user_data(user_id):
    """
    Get user data from the Replit database
    
    Args:
        user_id: The Discord user ID
        
    Returns:
        Dictionary containing user data or None if not found
    """
    key = user_key(user_id)
    data = db.get(key)
    
    if data:
        return json.loads(data)
    return None

def update_user_email(user_id, email):
    """Set user email and update the timestamp"""
    email_key = user_email_key(user_id)
    db[email_key] = email
    
    # Also update last_email_update timestamp
    timestamp_key = f"last_email_update_{user_id}"
    db[timestamp_key] = datetime.now().isoformat()
    
    # Set email flag to True
    db[f"emailtf_{user_id}"] = "True"
    
    return True

def get_user_email(user_id):
    """Get user email"""
    email_key = user_email_key(user_id)
    return db.get(email_key)

def get_email_status(user_id):
    """Check if user has set up their email"""
    key = f"emailtf_{user_id}"
    status = db.get(key, "False")
    return status == "True"

def update_credentials_status(user_id, status=True):
    """Update user credentials status"""
    key = f"credentialstf_{user_id}"
    db[key] = "True" if status else "False"
    return True

def get_credentials_status(user_id):
    """Check if user has set up their credentials"""
    key = f"credentialstf_{user_id}"
    status = db.get(key, "False")
    return status == "True"

def save_user_receipt_info(user_id, name, street, city, zipp, country):
    """Save user's receipt information"""
    data = {
        'name': name,
        'street': street,
        'city': city,
        'zip': zipp,
        'country': country
    }
    key = user_key(user_id)
    db[key] = json.dumps(data)
    
    # Update credentials status
    update_credentials_status(user_id)
    
    return True

def get_user_receipt_info(user_id):
    """Get user's receipt information"""
    data = get_user_data(user_id)
    if data:
        return {
            'name': data.get('name', ''),
            'street': data.get('street', ''),
            'city': data.get('city', ''),
            'zip': data.get('zip', ''),
            'country': data.get('country', '')
        }
    return None
