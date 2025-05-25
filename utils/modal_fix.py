
import os
import re
from utils.template_utils import replace_user_details
from utils.db_utils import get_user_details

def fix_receipt_html(html_content, user_details, replacements=None):
    """
    Fix HTML content by properly replacing all user details and additional replacements.
    
    Args:
        html_content (str): The HTML content to process
        user_details (tuple): A tuple containing (name, street, city, zip, country, email)
        replacements (dict, optional): Dictionary of additional replacements
        
    Returns:
        str: The fixed HTML content
    """
    # First replace user details
    if user_details:
        html_content = replace_user_details(html_content, user_details)
    
    # Then apply additional replacements
    if replacements:
        for placeholder, value in replacements.items():
            html_content = html_content.replace(placeholder, str(value))
    
    return html_content

def process_html_template(template_path, output_path, user_details, replacements=None):
    """
    Process an HTML template by replacing user details and other placeholders,
    then save it to the output path.
    
    Args:
        template_path (str): Path to the template HTML file
        output_path (str): Path where the processed HTML should be saved
        user_details (tuple): A tuple containing (name, street, city, zip, country, email)
        replacements (dict, optional): Dictionary of additional replacements
        
    Returns:
        str: The path to the processed HTML file
    """
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Read the template
        with open(template_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        
        # Fix the HTML content
        fixed_html = fix_receipt_html(html_content, user_details, replacements)
        
        # Write the processed HTML
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(fixed_html)
        
        return output_path
    except Exception as e:
        print(f"Error processing HTML template: {e}")
        return None

def get_and_process_user_details(user_id, template_path, output_path, replacements=None):
    """
    Get user details from the database and process the template.
    
    Args:
        user_id (str): The Discord user ID
        template_path (str): Path to the template HTML file
        output_path (str): Path where the processed HTML should be saved
        replacements (dict, optional): Dictionary of additional replacements
        
    Returns:
        tuple: (success, message)
    """
    # Get user details
    user_details = get_user_details(user_id)
    
    if not user_details:
        return False, "No user details found"
    
    # Process the template
    result_path = process_html_template(template_path, output_path, user_details, replacements)
    
    if not result_path:
        return False, "Failed to process HTML template"
    
    return True, "Receipt generated successfully"
