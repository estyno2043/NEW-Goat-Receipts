import sqlite3

def init_db():
    """Initialize database and ensure all required tables and columns exist"""
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    # Ensure licenses table exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS licenses (
        owner_id TEXT PRIMARY KEY,
        name TEXT,
        street TEXT,
        city TEXT,
        zipp TEXT,
        country TEXT,
        email TEXT,
        last_email_update TEXT,
        credentialstf TEXT DEFAULT 'False',
        emailtf TEXT DEFAULT 'False',
        emailwhite TEXT DEFAULT 'False',
        key TEXT,
        expiry TEXT
    )
    ''')

    # Create licenses table if it doesn't exist with all necessary columns
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS licenses (
        owner_id TEXT PRIMARY KEY,
        name TEXT,
        street TEXT,
        city TEXT,
        zipp TEXT,
        country TEXT,
        email TEXT,
        last_email_update TEXT,
        credentialstf TEXT DEFAULT 'False',
        emailtf TEXT DEFAULT 'False',
        emailwhite TEXT DEFAULT 'False',
        key TEXT,
        expiry TEXT
    )
    ''')
    
    # Make sure key and expiry columns exist
    try:
        cursor.execute("SELECT key, expiry FROM licenses LIMIT 1")
    except sqlite3.OperationalError:
        # Add missing columns
        cursor.execute("ALTER TABLE licenses ADD COLUMN key TEXT")
        cursor.execute("ALTER TABLE licenses ADD COLUMN expiry TEXT")
        print("Added missing key and expiry columns to licenses table")

    # Make sure all columns exist (for backward compatibility)
    columns_to_check = [
        ("last_email_update", "TEXT"),
        ("email", "TEXT"),
        ("credentialstf", "TEXT"),
        ("emailtf", "TEXT"),
        ("emailwhite", "TEXT")
    ]

    for column_name, column_type in columns_to_check:
        try:
            cursor.execute(f"SELECT {column_name} FROM licenses LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute(f"ALTER TABLE licenses ADD COLUMN {column_name} {column_type}")

    # Create table for authorized servers if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS authorized_servers (
        guild_id TEXT PRIMARY KEY,
        authorized_by TEXT,
        authorized_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create server_configs table to store per-server settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS server_configs (
            guild_id TEXT PRIMARY KEY,
            client_id TEXT,
            owner_id TEXT,
            activity TEXT,
            avatar_url TEXT,
            pic_channel TEXT,
            general_channel TEXT,
            generator_channel TEXT,
            review_channel TEXT,
            tutorial_channel TEXT,
            filter_invites INTEGER DEFAULT 1,
            log_channel TEXT,
            commands_only_channels TEXT,
            receipt_log_channel TEXT
        )
    ''')

    # Add missing columns if they don't exist (for backward compatibility)
    try:
        # Check if review_channel exists
        cursor.execute("PRAGMA table_info(server_configs)")
        columns = [column[1] for column in cursor.fetchall()]

        # Add missing columns if needed
        if "review_channel" not in columns:
            cursor.execute("ALTER TABLE server_configs ADD COLUMN review_channel TEXT")
        if "tutorial_channel" not in columns:
            cursor.execute("ALTER TABLE server_configs ADD COLUMN tutorial_channel TEXT")
    except Exception as e:
        print(f"Error adding columns to server_configs: {e}")


    # Check if we need to add new columns to server_configs
    cursor.execute("PRAGMA table_info(server_configs)")
    columns = [column[1] for column in cursor.fetchall()]

    # Add new columns if they don't exist
    new_columns = {
        'bot_name': 'TEXT',
        'interface_name': 'TEXT',
        'activity': 'TEXT', 
        'avatar_url': 'TEXT',
        'review_channel': 'TEXT',
        'tutorial_channel': 'TEXT',
        'filter_invites': 'INTEGER DEFAULT 1',
        'log_channel': 'TEXT',
        'receipt_log_channel': 'TEXT'
    }

    for column_name, column_type in new_columns.items():
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE server_configs ADD COLUMN {column_name} {column_type}")

    # Create table for whitelisted users if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS whitelisted_users (
        user_id TEXT PRIMARY KEY,
        added_by TEXT,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create table for blacklisted users if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blacklisted_users (
        user_id TEXT PRIMARY KEY,
        added_by TEXT,
        reason TEXT,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auto_bumps (
        guild_id TEXT,
        channel_id TEXT,
        message TEXT,
        interval INTEGER,
        last_bump TEXT,
        enabled INTEGER DEFAULT 1,
        PRIMARY KEY (guild_id, channel_id)
    )
    ''')

    # Create the server_access table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS server_access (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT,
        user_id TEXT,
        added_by TEXT,
        access_type TEXT,
        expiry TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(guild_id, user_id)
    )
    ''')

    # Check if expiry column exists in server_access table
    try:
        cursor.execute("SELECT expiry FROM server_access LIMIT 1")
    except sqlite3.OperationalError:
        # Add missing column
        cursor.execute("ALTER TABLE server_access ADD COLUMN expiry TEXT")
        cursor.execute("ALTER TABLE server_access ADD COLUMN access_type TEXT")
        print("Added missing expiry and access_type columns to server_access table")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()