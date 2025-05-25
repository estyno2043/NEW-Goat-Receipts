
import os
import re
from utils.template_utils import replace_user_details
from utils.db_utils import get_user_details

def fix_all_receipts():
    """
    Find and fix all receipt templates in the updatedrecipies folder.
    This can be run manually to ensure all templates are fixed.
    """
    print("Starting to fix all receipt templates...")
    
    # Define paths
    template_dir = "receipt"
    updated_dir = os.path.join(template_dir, "updatedrecipies")
    
    # Create the directory if it doesn't exist
    if not os.path.exists(updated_dir):
        os.makedirs(updated_dir)
        print(f"Created directory: {updated_dir}")
    
    # Get a list of all HTML files in the updatedrecipies directory
    receipt_files = [f for f in os.listdir(updated_dir) if f.endswith('.html')]
    
    # Sample user details to use for fixing - replace these with actual test data
    test_user_details = (
        "Test User",
        "123 Test Street",
        "Test City",
        "12345",
        "Test Country",
        "test@example.com"
    )
    
    # Process each file
    count = 0
    for filename in receipt_files:
        try:
            filepath = os.path.join(updated_dir, filename)
            
            # Read the file
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Fix the content
            fixed_content = replace_user_details(content, test_user_details)
            
            # Write back to the file
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(fixed_content)
            
            count += 1
            print(f"Fixed: {filename}")
        except Exception as e:
            print(f"Error fixing {filename}: {e}")
    
    print(f"Finished fixing {count} receipt templates.")

if __name__ == "__main__":
    fix_all_receipts()
