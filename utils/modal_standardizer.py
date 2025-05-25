
import os
import re
import glob

def standardize_all_modals():
    """
    Updates all modal files to use the standardized AmazonUK pattern for user details.
    """
    # Get all modal files
    modal_files = glob.glob("modals/*.py")
    
    # Patterns to find direct database access
    db_connect_pattern = re.compile(r'import sqlite3\s+conn = sqlite3\.connect\(\'data\.db\'\)\s+cursor = conn\.cursor\(\)\s+cursor\.execute\("SELECT name, street, city, zipp, country(, email)? FROM licenses WHERE owner_id = \?", \(str\(owner_id\),\)\)\s+user_details = cursor\.fetchone\(\)')
    
    # Pattern to replace with
    replacement = "from utils.db_utils import get_user_details\n        user_details = get_user_details(owner_id)"
    
    count = 0
    for file_path in modal_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if this file needs updating
            if 'import sqlite3' in content and 'cursor.execute("SELECT name, street, city, zipp, country' in content:
                # Replace using regex to handle various formatting
                new_content = db_connect_pattern.sub(replacement, content)
                
                # If regex didn't work, try a more manual approach
                if new_content == content:
                    # Find the beginning of the SQLite code
                    sqlite_start = content.find('import sqlite3')
                    if sqlite_start != -1:
                        # Find the end of the fetchone line
                        fetchone_end = content.find('user_details = cursor.fetchone()', sqlite_start)
                        if fetchone_end != -1:
                            end_of_block = fetchone_end + len('user_details = cursor.fetchone()')
                            # Get line ending character
                            next_char_index = min(end_of_block + 1, len(content) - 1)
                            line_ending = content[end_of_block:next_char_index + 1]
                            
                            # Replace the block
                            block_to_replace = content[sqlite_start:end_of_block + len(line_ending)]
                            new_content = content.replace(block_to_replace, 
                                                         "from utils.db_utils import get_user_details\n        user_details = get_user_details(owner_id)" + line_ending)
                
                # Write the updated content back
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    count += 1
                    print(f"Updated {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print(f"Standardized {count} modal files to use the AmazonUK pattern")
    
if __name__ == "__main__":
    standardize_all_modals()
