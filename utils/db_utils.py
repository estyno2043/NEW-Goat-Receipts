# Improved get_user_details function to include email from both tables, handling None values and updating the licenses table.
import sqlite3
import contextlib
import threading
import queue
import time

def save_user_email(user_id, email):
    """Save user email to both database tables for redundancy"""
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Save to user_emails table
        cursor.execute("INSERT OR REPLACE INTO user_emails (user_id, email) VALUES (?, ?)", 
                      (str(user_id), email))
        
        # Also update licenses table if the user exists there
        cursor.execute("SELECT 1 FROM licenses WHERE owner_id = ?", (str(user_id),))
        if cursor.fetchone():
            cursor.execute("UPDATE licenses SET email = ? WHERE owner_id = ?", 
                          (email, str(user_id)))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving user email: {str(e)}")
        return False

# Create a connection pool
class ConnectionPool:
    def __init__(self, max_connections=5, timeout=30.0):
        self.max_connections = max_connections
        self.timeout = timeout
        self.connections = queue.Queue(maxsize=max_connections)
        self.size = 0
        self.lock = threading.Lock()

    def get_connection(self):
        try:
            # Try to get an existing connection from the pool
            return self.connections.get(block=False)
        except queue.Empty:
            # If the pool is empty but not at max size, create a new connection
            with self.lock:
                if self.size < self.max_connections:
                    conn = sqlite3.connect('data.db', timeout=self.timeout)
                    conn.row_factory = sqlite3.Row
                    self.size += 1
                    return conn

            # If we've reached max connections, wait for one to become available
            try:
                return self.connections.get(block=True, timeout=self.timeout)
            except queue.Empty:
                raise sqlite3.OperationalError("Timeout waiting for database connection")

    def return_connection(self, conn):
        if conn:
            try:
                self.connections.put(conn, block=False)
            except queue.Full:
                # If the queue is full, close the connection
                conn.close()
                with self.lock:
                    self.size -= 1

# Create a global connection pool
connection_pool = ConnectionPool(max_connections=10, timeout=60.0)

@contextlib.contextmanager
def get_db_connection():
    """Context manager for database connections to prevent locking issues."""
    conn = None
    try:
        conn = connection_pool.get_connection()
        yield conn
    finally:
        if conn:
            try:
                conn.commit()
            except Exception:
                conn.rollback()
            connection_pool.return_connection(conn)

def execute_query(query, params=None, fetchone=False, fetchall=False):
    """Execute a query with proper error handling and connection management.

    Args:
        query (str): The SQL query to execute
        params (tuple, optional): Parameters for the query
        fetchone (bool, optional): Whether to fetch one result
        fetchall (bool, optional): Whether to fetch all results

    Returns:
        The query results if fetchone or fetchall is True, otherwise None
    """
    result = None
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Start a transaction with retry logic
            retry_count = 0
            max_retries = 5  # Increased retry count
            while retry_count < max_retries:
                try:
                    # Begin transaction explicitly
                    conn.execute("BEGIN IMMEDIATE")

                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)

                    if fetchone:
                        result = cursor.fetchone()
                    elif fetchall:
                        result = cursor.fetchall()
                    else:
                        conn.commit()

                    # Transaction succeeded, break out of retry loop
                    break
                except sqlite3.OperationalError as e:
                    # Handle both locked database and busy timeout errors
                    if ("database is locked" in str(e) or "database is busy" in str(e)) and retry_count < max_retries - 1:
                        print(f"Database locked/busy, retrying... (Attempt {retry_count + 1})")
                        retry_count += 1
                        # Wait with exponential backoff before retrying
                        import time
                        backoff_time = 0.5 * (2 ** retry_count)  # Exponential backoff
                        print(f"Waiting {backoff_time:.2f} seconds before retry...")
                        time.sleep(backoff_time)

                        # Try rolling back the transaction
                        try:
                            conn.rollback()
                        except Exception as rollback_error:
                            print(f"Rollback failed: {rollback_error}")
                    else:
                        # If this was our last retry or some other error, re-raise
                        print(f"Database operation failed after {retry_count} retries: {e}")
                        raise

        return result
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        # Re-raise the exception to let the caller handle it
        raise

def get_user_details(user_id):
    """Get user details from the database"""
    try:
        conn = sqlite3.connect('data.db')
        conn.row_factory = sqlite3.Row  # This allows us to access columns by name
        cursor = conn.cursor()

        # First check user_credentials table as the primary source
        # This contains the user's custom or randomized details that were set in the UI
        cursor.execute("""
            SELECT name, street, city, zip, country FROM user_credentials 
            WHERE user_id = ?
        """, (str(user_id),))
        cred_result = cursor.fetchone()
        
        if cred_result:
            # Get email from user_emails
            cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(user_id),))
            email_result = cursor.fetchone()
            email = email_result[0] if email_result else None
            
            # Build tuple from credentials and email
            user_data = (
                cred_result['name'] if 'name' in cred_result.keys() else "",
                cred_result['street'] if 'street' in cred_result.keys() else "",
                cred_result['city'] if 'city' in cred_result.keys() else "",
                cred_result['zip'] if 'zip' in cred_result.keys() else "",
                cred_result['country'] if 'country' in cred_result.keys() else "",
                email
            )
            
            # Debug output to verify data
            print(f"User details from user_credentials for {user_id}: {user_data}")
            
            # Ensure there are no None values in the tuple
            user_data = tuple(str(val) if val is not None else "" for val in user_data)
            print(f"User details for {user_id}: {user_data}")
            
            if email:
                print(f"Found email from user_details: {email}")
            
            conn.close()
            return user_data

        # If user_credentials didn't have data, fall back to licenses table
        cursor.execute("SELECT name, street, city, zipp, country, email FROM licenses WHERE owner_id = ?", (str(user_id),))
        result = cursor.fetchone()

        # If we have a result but email is None, try to get email from user_emails table
        if result:
            if result['email'] is None or result['email'] == '':
                cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(user_id),))
                email_result = cursor.fetchone()

                if email_result and email_result[0]:
                    # Update the licenses table with this email for future use
                    cursor.execute("UPDATE licenses SET email = ? WHERE owner_id = ?", (email_result[0], str(user_id)))
                    conn.commit()
                    
                    # Update our result with the new email
                    email = email_result[0]
                else:
                    email = result['email']
            else:
                email = result['email']

            # Convert Row object to tuple with proper column access
            user_data = (
                result['name'] if 'name' in result.keys() else "", 
                result['street'] if 'street' in result.keys() else "", 
                result['city'] if 'city' in result.keys() else "", 
                result['zipp'] if 'zipp' in result.keys() else "", 
                result['country'] if 'country' in result.keys() else "", 
                email
            )
            
            # Ensure there are no None values in the tuple
            user_data = tuple(str(val) if val is not None else "" for val in user_data)
            print(f"User details for {user_id}: {user_data}")
            
            if email:
                print(f"Found email from user_details: {email}")
                
            conn.close()
            return user_data
        
        conn.close()
        return None
    except Exception as e:
        print(f"Error getting user details: {str(e)}")
        return None