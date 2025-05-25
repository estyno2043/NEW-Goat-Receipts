import sqlite3
import contextlib
import threading
import queue
import time

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

def save_user_email(user_id, email):
    """Save user email to both database tables for redundancy"""
    try:
        # Save to user_emails table
        query1 = "INSERT OR REPLACE INTO user_emails (user_id, email) VALUES (?, ?)"
        execute_query(query1, (str(user_id), email))
        
        # Also update licenses table if the user exists there
        query2 = "SELECT 1 FROM licenses WHERE owner_id = ?"
        result = execute_query(query2, (str(user_id),), fetchone=True)
        
        if result:
            query3 = "UPDATE licenses SET email = ? WHERE owner_id = ?"
            execute_query(query3, (email, str(user_id)))
        
        return True
    except Exception as e:
        print(f"Error saving user email: {str(e)}")
        return False

def get_user_details(user_id):
    """Get user details from the database for receipt generation

    Args:
        user_id: The Discord user ID

    Returns:
        Tuple containing (name, street, city, zip, country, email) or None if not found
    """
    try:
        # First check user_credentials table which contains the most up-to-date info
        query1 = "SELECT name, street, city, zip as zipp, country FROM user_credentials WHERE user_id = ?"
        cred_result = execute_query(query1, (str(user_id),), fetchone=True)
        
        # Get email from user_emails table
        query2 = "SELECT email FROM user_emails WHERE user_id = ?"
        email_result = execute_query(query2, (str(user_id),), fetchone=True)
        
        if cred_result and email_result:
            email = email_result['email']
            return (cred_result['name'], cred_result['street'], cred_result['city'], 
                   cred_result['zipp'], cred_result['country'], email)
        
        # Fallback to licenses table if credentials not found in dedicated tables
        query3 = "SELECT name, street, city, zipp, country, email FROM licenses WHERE owner_id = ?"
        license_result = execute_query(query3, (str(user_id),), fetchone=True)
        if license_result:
            return (license_result['name'], license_result['street'], license_result['city'], 
                   license_result['zipp'], license_result['country'], license_result['email'])
        
        return None
    except Exception as e:
        print(f"Error getting user details: {e}")
        return None