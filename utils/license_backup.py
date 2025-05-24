
import json
import sqlite3
import os
import logging
from datetime import datetime, timedelta
import asyncio

class LicenseBackup:
    """Utility to backup and restore license data to ensure reliability during restarts"""
    
    BACKUP_PATH = "data/license_backup.json"
    
    @staticmethod
    async def backup_licenses():
        """Create a backup of all active licenses"""
        try:
            if not os.path.exists("data"):
                os.makedirs("data")
                
            # Connect to database
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            
            # Get all licenses
            cursor.execute("SELECT owner_id, expiry, key FROM licenses")
            licenses = cursor.fetchall()
            conn.close()
            
            # Format data for backup
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "licenses": {}
            }
            
            for owner_id, expiry_str, key in licenses:
                backup_data["licenses"][owner_id] = {
                    "expiry": expiry_str,
                    "key": key
                }
            
            # Save backup
            with open(LicenseBackup.BACKUP_PATH, 'w') as f:
                json.dump(backup_data, f, indent=4)
                
            logging.info(f"Successfully backed up {len(backup_data['licenses'])} licenses")
            return True
            
        except Exception as e:
            logging.error(f"Error backing up licenses: {str(e)}")
            return False
    
    @staticmethod
    async def restore_licenses_to_cache():
        """Restore license data from backup to cache during startup"""
        from utils.license_manager import LicenseManager
        
        try:
            if not os.path.exists(LicenseBackup.BACKUP_PATH):
                logging.info("No license backup found, skipping restore")
                return False
                
            # Load backup data
            with open(LicenseBackup.BACKUP_PATH, 'r') as f:
                backup_data = json.load(f)
            
            # Check if backup is recent (less than 24 hours old)
            backup_time = datetime.fromisoformat(backup_data["timestamp"])
            if (datetime.now() - backup_time).total_seconds() > 86400:  # 24 hours
                logging.warning("Backup is more than 24 hours old, using with caution")
            
            # Restore to cache
            licenses = backup_data.get("licenses", {})
            current_time = datetime.now()
            
            for owner_id, license_data in licenses.items():
                expiry_str = license_data.get("expiry")
                key = license_data.get("key")
                
                # Skip invalid entries
                if not expiry_str or not key:
                    continue
                
                # Handle lifetime keys
                if key and ("LifetimeKey" in key or "owner-key" in key):
                    # Cache for 10 years (effectively permanent)
                    LicenseManager._license_cache[owner_id] = (current_time + timedelta(days=3650), True)
                    continue
                
                # Handle regular keys
                try:
                    expiry_date = datetime.strptime(expiry_str, '%d/%m/%Y %H:%M:%S')
                    # Only cache if license is still valid
                    if current_time < expiry_date:
                        # Cache until expiry with a small buffer
                        LicenseManager._license_cache[owner_id] = (expiry_date - timedelta(hours=1), False)
                except Exception as e:
                    logging.warning(f"Error parsing expiry date for cached license {owner_id}: {str(e)}")
            
            logging.info(f"Successfully restored {len(licenses)} licenses to cache")
            return True
            
        except Exception as e:
            logging.error(f"Error restoring licenses from backup: {str(e)}")
            return False
    
    @staticmethod
    async def start_backup_scheduler(interval_hours=6):
        """Start a background task to regularly backup licenses"""
        while True:
            await LicenseBackup.backup_licenses()
            # Wait for the specified interval
            await asyncio.sleep(interval_hours * 3600)
