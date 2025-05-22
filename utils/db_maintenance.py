
import sqlite3
import os
import shutil
import logging
import time
from datetime import datetime

def optimize_database(db_path='data.db'):
    """Optimize the SQLite database for better performance."""
    try:
        print(f"Starting database optimization for {db_path}")
        
        # Create a backup first
        backup_file = f"{db_path}.backup-{int(time.time())}"
        shutil.copy2(db_path, backup_file)
        print(f"Created backup at {backup_file}")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # VACUUM to reclaim space and defragment
        print("Running VACUUM...")
        cursor.execute("VACUUM")
        
        # ANALYZE to update statistics
        print("Running ANALYZE...")
        cursor.execute("ANALYZE")
        
        # Create indexes if they don't exist
        print("Optimizing indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_licenses_owner_id ON licenses(owner_id)")
        
        conn.commit()
        conn.close()
        print("Database optimization complete")
        return True
        
    except Exception as e:
        print(f"Error during database optimization: {e}")
        return False

def repair_database():
    """Attempt to repair the database if it's corrupted or has lock issues."""
    try:
        print("Starting database repair process")
        db_path = 'data.db'
        
        # Check if WAL files exist and are causing problems
        if os.path.exists(f"{db_path}-wal") or os.path.exists(f"{db_path}-shm"):
            print("Found WAL/SHM files, attempting recovery...")
            
            # Create a backup first
            backup_time = int(time.time())
            backup_main = f"{db_path}.backup-{backup_time}"
            backup_wal = f"{db_path}-wal.backup-{backup_time}" if os.path.exists(f"{db_path}-wal") else None
            backup_shm = f"{db_path}-shm.backup-{backup_time}" if os.path.exists(f"{db_path}-shm") else None
            
            shutil.copy2(db_path, backup_main)
            if backup_wal:
                shutil.copy2(f"{db_path}-wal", backup_wal)
            if backup_shm:
                shutil.copy2(f"{db_path}-shm", backup_shm)
            
            print(f"Created backups with timestamp {backup_time}")
            
            # Attempt to recover by forcing checkpoint and journal mode reset
            try:
                print("Attempting to force WAL checkpoint...")
                conn = sqlite3.connect(db_path, timeout=60.0)
                conn.execute("PRAGMA wal_checkpoint(FULL)")
                conn.close()
                
                # Change journal mode to DELETE temporarily
                conn = sqlite3.connect(db_path, timeout=60.0)
                conn.execute("PRAGMA journal_mode = DELETE")
                conn.execute("PRAGMA journal_mode = WAL")  # Switch back to WAL
                conn.close()
                
                print("WAL checkpoint complete")
            except sqlite3.Error as e:
                print(f"Error during WAL checkpoint: {e}")
                
                # More aggressive recovery: try to recreate database structure
                # Only if we have backups
                if all([os.path.exists(backup_main), 
                       (not backup_wal or os.path.exists(backup_wal)),
                       (not backup_shm or os.path.exists(backup_shm))]):
                    
                    print("Attempting more aggressive recovery...")
                    
                    # Close any existing connections
                    try:
                        conn = sqlite3.connect(db_path, timeout=10.0)
                        conn.close()
                    except:
                        pass
                    
                    # Remove WAL files
                    if os.path.exists(f"{db_path}-wal"):
                        os.remove(f"{db_path}-wal")
                    if os.path.exists(f"{db_path}-shm"):
                        os.remove(f"{db_path}-shm")
                    
                    # Initialize the database
                    from utils.db_init import init_db
                    init_db()
                    print("Database structure rebuilt")
                
        # Verify database integrity
        print("Verifying database integrity...")
        conn = sqlite3.connect(db_path, timeout=60.0)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        
        if integrity_result != 'ok':
            print(f"Database integrity check failed: {integrity_result}")
            
            # Make another backup before attempting repair
            backup_file = f"{db_path}.corrupted-{int(time.time())}"
            shutil.copy2(db_path, backup_file)
            
            # Export and reimport data (drastic repair)
            # This is commented out for safety, but can be uncommented if needed
            """
            # Export all data to memory
            data = {}
            for table in ["licenses", "authorized_servers", "server_configs", "whitelisted_users", "blacklisted_users"]:
                try:
                    cursor.execute(f"SELECT * FROM {table}")
                    data[table] = cursor.fetchall()
                except:
                    data[table] = []
            
            # Initialize a new database
            conn.close()
            
            # Backup the corrupted file
            backup_file = f"{db_path}.corrupted-{int(time.time())}"
            shutil.copy2(db_path, backup_file)
            
            # Remove the corrupted database
            os.remove(db_path)
            if os.path.exists(f"{db_path}-wal"):
                os.remove(f"{db_path}-wal")
            if os.path.exists(f"{db_path}-shm"):
                os.remove(f"{db_path}-shm")
            
            # Create a new database
            from utils.db_init import init_db
            init_db()
            
            # Restore data
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Import data back
            # Implement import logic here based on your schema
            conn.commit()
            conn.close()
            """
        else:
            print("Database integrity check passed")
            conn.close()
            
        # Final optimization
        optimize_database()
        
        return True
    except Exception as e:
        print(f"Error during database repair: {e}")
        return False


import sqlite3
import os
import logging
import time
import sys

def optimize_database(db_path='data.db', backup=True):
    """
    Performs maintenance on the SQLite database to improve performance
    
    Args:
        db_path: Path to the database file
        backup: Whether to create a backup before optimizing
    """
    if not os.path.exists(db_path):
        print(f"Database file {db_path} does not exist")
        return False
        
    print(f"Starting database optimization for {db_path}")
    
    # Create backup if requested
    if backup:
        backup_path = f"{db_path}.backup-{int(time.time())}"
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"Created backup at {backup_path}")
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")
            if input("Continue without backup? (y/N): ").lower() != 'y':
                return False
    
    try:
        # Connect with extended timeout
        conn = sqlite3.connect(db_path, timeout=60.0)
        conn.execute("PRAGMA busy_timeout = 60000")
        
        # Run VACUUM to rebuild the database file
        print("Running VACUUM...")
        conn.execute("VACUUM")
        
        # Run ANALYZE to update statistics
        print("Running ANALYZE...")
        conn.execute("ANALYZE")
        
        # Check and optimize indexes
        print("Optimizing indexes...")
        cursor = conn.cursor()
        
        # Create any missing indexes that might help performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_licenses_owner_id ON licenses(owner_id)")
        
        conn.commit()
        conn.close()
        print("Database optimization complete")
        return True
        
    except Exception as e:
        print(f"Error during database optimization: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--no-backup":
        optimize_database(backup=False)
    else:
        optimize_database()
