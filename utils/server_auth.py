import sqlite3
import json

class ServerAuth:
    @staticmethod
    async def is_authorized_server(guild_id: int) -> bool:
        """Check if a server is authorized to use the bot."""
        # First check if it's the main guild from config
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                if str(guild_id) == config.get("guild_id"):
                    print(f"Main guild authorized: {guild_id}")
                    return True
                    
            # Check if server is in the authorized servers database
            import sqlite3
            try:
                with sqlite3.connect('data.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM server_configs WHERE guild_id = ?", (str(guild_id),))
                    server_config = cursor.fetchone()
                    
                    if server_config:
                        print(f"Authorized server found in config: {guild_id}")
                        return True
            except Exception as db_error:
                print(f"Database error checking server auth: {db_error}, allowing access by default")
                return True
        except Exception as config_error:
            print(f"Config error: {config_error}, allowing access by default")
            return True

        # Handle direct messages (no guild)
        if not guild_id:
            print("Direct message interaction - allowing")
            return True

        try:
            # Using try/except to handle any database connection issues
            # Then check the database with proper connection handling
            conn = sqlite3.connect('data.db', timeout=30.0)
            cursor = conn.cursor()
            
            # Check if the server is in authorized_servers table
            try:
                cursor.execute("SELECT 1 FROM authorized_servers WHERE guild_id = ?", (str(guild_id),))
                is_authorized = cursor.fetchone() is not None
                
                # For debugging
                print(f"Server authorization check for {guild_id}: {is_authorized}")
                
                # For non-authorized servers, allow core functionality for better UX
                if not is_authorized:
                    print(f"Server {guild_id} not explicitly authorized, but allowing email/credentials setup")
                    return True  # Allow all servers to use email/credentials setup
                
                return is_authorized
            except Exception as e:
                print(f"Error in database query for server auth: {e}")
                # If there's a query error, we'll allow access to prevent disruption
                return True
            finally:
                cursor.close()
                conn.close()
        except Exception as e:
            print(f"Error connecting to database for server auth: {e}")
            # If we can't connect to the database, we'll allow access to prevent disruption
            return True

    @staticmethod
    async def is_server_authorized_by_user(guild_id: int, user_id: int) -> bool:
        """Check if a server was authorized by this specific user."""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM authorized_servers WHERE guild_id = ? AND authorized_by = ?", 
                     (str(guild_id), str(user_id)))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    @staticmethod
    async def add_authorized_server(guild_id: int, authorized_by: int = None) -> bool:
        """Add a server to the authorized list

        Parameters:
            guild_id (int): The ID of the guild to authorize
            authorized_by (int, optional): The ID of the user who authorized the server
        """
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM authorized_servers WHERE guild_id = ?", (str(guild_id),))
            if cursor.fetchone()[0] > 0:
                conn.close()
                return False  # Already authorized

            cursor.execute("INSERT INTO authorized_servers (guild_id, authorized_by) VALUES (?, ?)", 
                          (str(guild_id), str(authorized_by) if authorized_by else None))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding authorized server: {e}")
            conn.close()
            return False

    @staticmethod
    async def remove_authorized_server(guild_id: int) -> bool:
        """Remove a server from the authorized list"""
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM authorized_servers WHERE guild_id = ?", (str(guild_id),))
            if cursor.fetchone()[0] == 0:
                conn.close()
                return False  # Not authorized to begin with

            cursor.execute("DELETE FROM authorized_servers WHERE guild_id = ?", (str(guild_id),))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error removing authorized server: {e}")
            conn.close()
            return False

    @staticmethod
    async def add_user_to_server_access(guild_id: int, user_id: int, added_by: int = None) -> bool:
        """Add a user to the server's access list

        Parameters:
            guild_id (int): The ID of the guild
            user_id (int): The ID of the user to add access for
            added_by (int, optional): The ID of the user who added the access

        Returns:
            bool: True if added successfully, False if user already has access
        """
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        try:
            # Create the server_access table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS server_access (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT,
                    user_id TEXT,
                    added_by TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Check if user already has access
            cursor.execute(
                "SELECT COUNT(*) FROM server_access WHERE guild_id = ? AND user_id = ?", 
                (str(guild_id), str(user_id))
            )
            if cursor.fetchone()[0] > 0:
                conn.close()
                return False  # User already has access

            # Add user to access list
            cursor.execute(
                "INSERT INTO server_access (guild_id, user_id, added_by) VALUES (?, ?, ?)",
                (str(guild_id), str(user_id), str(added_by) if added_by else None)
            )
            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error adding user to server access: {e}")
            conn.close()
            return False

    @staticmethod
    async def remove_user_from_server_access(guild_id: int, user_id: int, removed_by: int = None) -> bool:
        """Remove a user from the server's access list

        Parameters:
            guild_id (int): The ID of the guild
            user_id (int): The ID of the user to remove access from
            removed_by (int, optional): The ID of the user who removed the access

        Returns:
            bool: True if removed successfully, False if user doesn't have access or if removed_by
                 doesn't match the added_by
        """
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        try:
            # Check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='server_access'")
            if not cursor.fetchone():
                conn.close()
                return False  # Table doesn't exist

            # If removed_by is provided, check if the user was added by the same person
            if removed_by:
                cursor.execute(
                    "SELECT COUNT(*) FROM server_access WHERE guild_id = ? AND user_id = ? AND added_by = ?",
                    (str(guild_id), str(user_id), str(removed_by))
                )
                if cursor.fetchone()[0] == 0:
                    conn.close()
                    return False  # User wasn't added by the person trying to remove

            # Remove user from access list
            cursor.execute(
                "DELETE FROM server_access WHERE guild_id = ? AND user_id = ?",
                (str(guild_id), str(user_id))
            )

            # Check if any rows were affected
            if cursor.rowcount == 0:
                conn.close()
                return False  # User didn't have access

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error removing user from server access: {e}")
            conn.close()
            return False

    @staticmethod
    async def has_server_access(guild_id: int, user_id: int) -> bool:
        """Check if a user has access to a server

        Parameters:
            guild_id (int): The ID of the guild
            user_id (int): The ID of the user to check

        Returns:
            bool: True if user has access, False otherwise
        """
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        try:
            # Check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='server_access'")
            if not cursor.fetchone():
                conn.close()
                return False  # Table doesn't exist

            # Check if user has access
            cursor.execute(
                "SELECT COUNT(*) FROM server_access WHERE guild_id = ? AND user_id = ?",
                (str(guild_id), str(user_id))
            )
            has_access = cursor.fetchone()[0] > 0
            conn.close()
            return has_access

        except Exception as e:
            print(f"Error checking server access: {e}")
            conn.close()
            return False