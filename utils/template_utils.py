
"""
Utility functions for handling template replacements in receipts
"""

def replace_user_details(html_content, user_details):
    """
    Replace user details placeholders in HTML content with actual user data
    
    Args:
        html_content (str): The HTML template content
        user_details (tuple): User details from the database (name, street, city, zip, country, email)
        
    Returns:
        str: The HTML content with user details replaced
    """
    if not user_details or len(user_details) < 5:
        return html_content
    
    # Extract user details
    name, street, city, zip_code, country, email = user_details if len(user_details) >= 6 else (*user_details, "")
    
    # Replace placeholder variables
    replacements = {
        "{name}": name,
        "{street}": street,
        "{city}": city,
        "{zip}": zip_code,
        "{zipp}": zip_code,  # Some templates use zipp instead of zip
        "{country}": country,
        "{email}": email,
        
        # Also replace common hardcoded values in templates
        "John Brown": name,
        "651 Cedar Lane": street,
        "Los Angeles": city,
        "78201": zip_code,
        "Theodore Jones": name,
        "874 Beard Garden Suite 760\nBrandonfort, CO 89234": street,
        "East Nicolefort Oneillchester": city,
        "53877": zip_code,
        "Germany": country,
    }
    
    # Perform replacements
    for placeholder, value in replacements.items():
        html_content = html_content.replace(placeholder, value)
    
    return html_content
