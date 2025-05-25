
import os
import re
from utils.template_utils import replace_user_details

def ensure_directory(directory):
    """Ensure that the specified directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def process_receipt_content(html_content, user_details, replacements=None):
    """
    Process the HTML content of a receipt to ensure all user details are properly replaced.
    
    Args:
        html_content (str): The HTML content to process
        user_details (tuple): User details as (name, street, city, zip, country, email)
        replacements (dict, optional): Additional key-value replacements
    
    Returns:
        str: The processed HTML content
    """
    # First apply user details
    if user_details:
        html_content = replace_user_details(html_content, user_details)
    
    # Then apply any additional replacements
    if replacements:
        for key, value in replacements.items():
            html_content = html_content.replace(key, str(value))
    
    return html_content

def save_receipt(html_content, user_details, output_path, replacements=None):
    """
    Process and save a receipt to the specified output path.
    
    Args:
        html_content (str): The HTML content to process
        user_details (tuple): User details as (name, street, city, zip, country, email)
        output_path (str): Path where to save the processed HTML
        replacements (dict, optional): Additional key-value replacements
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Ensure the directory exists
        ensure_directory(os.path.dirname(output_path))
        
        # Process the content
        processed_html = process_receipt_content(html_content, user_details, replacements)
        
        # Save the processed HTML
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(processed_html)
        
        return True
    except Exception as e:
        print(f"Error saving receipt: {e}")
        return False

# Create a monkey patch for all the open() calls to intercept writes to updatedrecipies folder
original_open = open

def patched_open(file, mode='r', *args, **kwargs):
    """
    A monkey patch for the built-in open() function to intercept writes to the updatedrecipies folder
    and ensure all user details are properly replaced before saving.
    """
    # Only intercept writes to the updatedrecipies folder
    if mode.startswith('w') and 'updatedrecipies' in file:
        # Get the calling frame
        import inspect
        frame = inspect.currentframe().f_back
        
        # Try to extract user_details from the frame's locals
        user_details = None
        for var_name, var_value in frame.f_locals.items():
            if var_name == 'user_details' and isinstance(var_value, tuple) and len(var_value) >= 6:
                user_details = var_value
                break
        
        # Open the file normally
        file_obj = original_open(file, mode, *args, **kwargs)
        
        # If we found user_details, we'll need to process the content before writing
        if user_details:
            # Create a wrapper to intercept the write calls
            original_write = file_obj.write
            
            def patched_write(content):
                # Process the content to replace user details
                processed_content = replace_user_details(content, user_details)
                # Call the original write method
                return original_write(processed_content)
            
            # Replace the write method
            file_obj.write = patched_write
        
        return file_obj
    
    # For other files, just use the original open
    return original_open(file, mode, *args, **kwargs)

# Apply the monkey patch
import builtins
builtins.open = patched_open
