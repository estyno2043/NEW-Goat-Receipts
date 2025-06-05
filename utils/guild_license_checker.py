
import logging
from datetime import datetime
from utils.mongodb_manager import mongo_manager

class GuildLicenseChecker:
    """Handle guild-specific license checking logic"""
    
    @staticmethod
    async def check_guild_access(user_id, guild_id, guild_config):
        """
        Check if a user has access to generate receipts in a specific guild
        Returns: (has_access: bool, access_info: dict)
        """
        try:
            client_role_id = guild_config.get("client_role_id")
            admin_role_id = guild_config.get("admin_role_id")
            
            # Check if user has admin role (admins always have access)
            if admin_role_id:
                # This check will be done by the calling function with actual role objects
                pass
            
            # Check if user has client role
            if client_role_id:
                # This check will be done by the calling function with actual role objects
                pass
            
            # Check database for legacy access or guild-specific licenses
            server_access = mongo_manager.get_server_access(guild_id, user_id)
            
            if server_access:
                expiry_str = server_access.get("expiry")
                access_type = server_access.get("access_type")
                
                # Lifetime access is always valid
                if access_type == "Lifetime":
                    return True, {
                        "type": "server_access",
                        "access_type": access_type,
                        "expiry": "Lifetime"
                    }
                
                # Check expiry date for time-limited access
                if expiry_str:
                    try:
                        # Try multiple date formats
                        expiry_date = None
                        formats_to_try = [
                            "%Y-%m-%d %H:%M:%S",  # MongoDB format
                            "%d/%m/%Y %H:%M:%S"   # Legacy format
                        ]
                        
                        for date_format in formats_to_try:
                            try:
                                expiry_date = datetime.strptime(expiry_str, date_format)
                                break
                            except ValueError:
                                continue
                        
                        if expiry_date and datetime.now() < expiry_date:
                            return True, {
                                "type": "server_access",
                                "access_type": access_type,
                                "expiry": expiry_str
                            }
                        else:
                            # Access expired
                            return False, {
                                "type": "expired",
                                "access_type": access_type,
                                "expiry": expiry_str
                            }
                    except Exception as e:
                        logging.error(f"Error parsing expiry date: {e}")
            
            # Check for guild-specific user license
            guild_license = mongo_manager.get_guild_user_license(guild_id, user_id)
            
            if guild_license:
                expiry_str = guild_license.get("expiry")
                subscription_type = guild_license.get("subscription_type", "Unknown")
                
                if expiry_str:
                    try:
                        # Try multiple date formats
                        expiry_date = None
                        formats_to_try = [
                            "%Y-%m-%d %H:%M:%S",  # MongoDB format
                            "%d/%m/%Y %H:%M:%S"   # Legacy format
                        ]
                        
                        for date_format in formats_to_try:
                            try:
                                expiry_date = datetime.strptime(expiry_str, date_format)
                                break
                            except ValueError:
                                continue
                        
                        if expiry_date and datetime.now() < expiry_date:
                            return True, {
                                "type": "guild_license",
                                "subscription_type": subscription_type,
                                "expiry": expiry_str
                            }
                        else:
                            return False, {
                                "type": "expired_license",
                                "subscription_type": subscription_type,
                                "expiry": expiry_str
                            }
                    except Exception as e:
                        logging.error(f"Error parsing guild license expiry: {e}")
            
            # No access found
            return False, {"type": "no_access"}
            
        except Exception as e:
            logging.error(f"Error checking guild access for user {user_id} in guild {guild_id}: {e}")
            return False, {"type": "error", "message": str(e)}
    
    @staticmethod
    async def get_guild_subscription_info(user_id, guild_id):
        """
        Get subscription information for display in guild context
        Returns: (subscription_type: str, end_date: str)
        """
        try:
            # Check server access first
            server_access = mongo_manager.get_server_access(guild_id, user_id)
            
            if server_access:
                access_type = server_access.get("access_type", "Unknown")
                expiry_str = server_access.get("expiry")
                
                if access_type == "Lifetime":
                    return "Lifetime", "Never"
                elif expiry_str:
                    try:
                        # Try multiple date formats
                        expiry_date = None
                        formats_to_try = [
                            "%Y-%m-%d %H:%M:%S",  # MongoDB format
                            "%d/%m/%Y %H:%M:%S"   # Legacy format
                        ]
                        
                        for date_format in formats_to_try:
                            try:
                                expiry_date = datetime.strptime(expiry_str, date_format)
                                break
                            except ValueError:
                                continue
                        
                        if expiry_date:
                            return access_type, expiry_date.strftime("%d/%m/%Y %H:%M:%S")
                        else:
                            return access_type, expiry_str
                    except Exception:
                        return access_type, expiry_str
            
            # Check guild-specific license
            guild_license = mongo_manager.get_guild_user_license(guild_id, user_id)
            
            if guild_license:
                subscription_type = guild_license.get("subscription_type", "Unknown")
                expiry_str = guild_license.get("expiry")
                
                if "lifetime" in subscription_type.lower():
                    return subscription_type, "Never"
                elif expiry_str:
                    try:
                        # Try multiple date formats
                        expiry_date = None
                        formats_to_try = [
                            "%Y-%m-%d %H:%M:%S",  # MongoDB format
                            "%d/%m/%Y %H:%M:%S"   # Legacy format
                        ]
                        
                        for date_format in formats_to_try:
                            try:
                                expiry_date = datetime.strptime(expiry_str, date_format)
                                break
                            except ValueError:
                                continue
                        
                        if expiry_date:
                            return subscription_type, expiry_date.strftime("%d/%m/%Y %H:%M:%S")
                        else:
                            return subscription_type, expiry_str
                    except Exception:
                        return subscription_type, expiry_str
            
            # No guild-specific access found
            return "Default", "N/A"
            
        except Exception as e:
            logging.error(f"Error getting guild subscription info for user {user_id} in guild {guild_id}: {e}")
            return "Error", "N/A"
    
    @staticmethod
    def check_user_setup_guild(user_id, guild_id):
        """
        Check if user has credentials and email set up for guild context
        Returns: (has_credentials: bool, has_email: bool)
        """
        try:
            # For guild context, use regular user setup (not guild-specific)
            # This allows users to use their main credentials across guilds
            has_credentials = mongo_manager.get_user_credentials(user_id) is not None
            has_email = mongo_manager.get_user_email(user_id) is not None
            return has_credentials, has_email
        except Exception as e:
            logging.error(f"Error checking user setup for guild context {user_id}/{guild_id}: {e}")
            return False, False
    
    @staticmethod
    def get_user_details_guild(user_id, guild_id):
        """
        Get user details for receipt generation in guild context
        Returns: user details tuple or None
        """
        try:
            # For guild context, use regular user details (not guild-specific)
            # This allows users to use their main credentials across guilds
            return mongo_manager.get_user_details(user_id)
        except Exception as e:
            logging.error(f"Error getting user details for guild context {user_id}/{guild_id}: {e}")
            return None
