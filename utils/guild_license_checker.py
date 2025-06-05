
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
            from utils.mongodb_manager import mongo_manager
            
            # Check if MongoDB is available
            db = mongo_manager.get_database()
            if db is None:
                logging.error(f"MongoDB unavailable when checking guild access for {user_id} in {guild_id}")
                return False, {"type": "database_error", "message": "Database unavailable"}
            
            client_role_id = guild_config.get("client_role_id")
            admin_role_id = guild_config.get("admin_role_id")
            
            logging.info(f"Checking guild access for user {user_id} in guild {guild_id}")
            
            # Check database for legacy access or guild-specific licenses
            server_access = mongo_manager.get_server_access(guild_id, user_id)
            logging.info(f"Server access for {user_id} in {guild_id}: {server_access}")
            
            # Check for guild-specific user license first (more specific)
            guild_license = mongo_manager.get_guild_user_license(guild_id, user_id)
            logging.info(f"Guild license for {user_id} in {guild_id}: {guild_license}")
            
            # If both records exist, we need to check if access was removed
            # When access is removed, both records should be deleted, so if neither exists, access was removed
            if not server_access and not guild_license:
                # Check if the user ever had access by looking for any trace in credentials or email
                user_credentials = mongo_manager.get_user_credentials(user_id)
                user_email = mongo_manager.get_user_email(user_id)
                user_license = mongo_manager.get_license(user_id)
                
                # If user has no credentials, email, or license, they likely had access removed
                if not user_credentials and not user_email and not user_license:
                    logging.info(f"User {user_id} appears to have had access removed in guild {guild_id} (all data cleared)")
                    return False, {
                        "type": "access_removed",
                        "message": "Your access has been removed from this server"
                    }
                else:
                    # User never had access in this guild
                    logging.info(f"No access found for user {user_id} in guild {guild_id}")
                    return False, {"type": "no_access"}
            
            # Process server access if it exists
            if server_access:
                expiry_str = server_access.get("expiry")
                access_type = server_access.get("access_type")
                
                # Check if access was explicitly removed (access_type could be "removed" or similar)
                if access_type and access_type.lower() == "removed":
                    logging.info(f"User {user_id} access was explicitly removed in guild {guild_id}")
                    return False, {
                        "type": "access_removed",
                        "message": "Your access has been removed from this server"
                    }
                
                # Lifetime access is always valid
                if access_type == "Lifetime":
                    logging.info(f"User {user_id} has lifetime access in guild {guild_id}")
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
                            logging.info(f"User {user_id} has valid access until {expiry_date} in guild {guild_id}")
                            return True, {
                                "type": "server_access",
                                "access_type": access_type,
                                "expiry": expiry_str
                            }
                        else:
                            # Access expired
                            logging.info(f"User {user_id} access expired on {expiry_date} in guild {guild_id}")
                            return False, {
                                "type": "expired",
                                "access_type": access_type,
                                "expiry": expiry_str
                            }
                    except Exception as e:
                        logging.error(f"Error parsing expiry date: {e}")
            
            # Process guild license if it exists
            if guild_license:
                expiry_str = guild_license.get("expiry")
                subscription_type = guild_license.get("subscription_type", "Unknown")
                
                # Check if license was explicitly removed
                if subscription_type and subscription_type.lower() == "removed":
                    logging.info(f"User {user_id} guild license was explicitly removed in guild {guild_id}")
                    return False, {
                        "type": "license_removed",
                        "message": "Your license has been removed from this server"
                    }
                
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
                            logging.info(f"User {user_id} has valid guild license until {expiry_date} in guild {guild_id}")
                            return True, {
                                "type": "guild_license",
                                "subscription_type": subscription_type,
                                "expiry": expiry_str
                            }
                        else:
                            logging.info(f"User {user_id} guild license expired on {expiry_date} in guild {guild_id}")
                            return False, {
                                "type": "expired_license",
                                "subscription_type": subscription_type,
                                "expiry": expiry_str
                            }
                    except Exception as e:
                        logging.error(f"Error parsing guild license expiry: {e}")
            
            # No valid access found
            logging.info(f"No valid access found for user {user_id} in guild {guild_id}")
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
            # Check if user has any access using the same logic as check_guild_access
            has_access, access_info = await GuildLicenseChecker.check_guild_access(user_id, guild_id, {})
            
            if not has_access:
                # Check the type of denial
                if access_info.get("type") == "access_removed":
                    return "Access Removed", "Removed by Admin"
                elif access_info.get("type") == "license_removed":
                    return "License Removed", "Removed by Admin"
                elif access_info.get("type") == "expired":
                    return "Expired", access_info.get("expiry", "Unknown")
                elif access_info.get("type") == "expired_license":
                    return "Expired License", access_info.get("expiry", "Unknown")
                else:
                    return "No Access", "N/A"
            
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
            
            # No guild-specific access found but access check passed (role-based access)
            return "Role Access", "Via Role"
            
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
