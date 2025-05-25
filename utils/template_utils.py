
def replace_user_details(html_content, user_details):
    """
    Replace all user details in HTML content, including hardcoded placeholder values.
    
    Args:
        html_content (str): The HTML content to process
        user_details (tuple): A tuple containing (name, street, city, zip, country, email)
        
    Returns:
        str: The HTML content with all user details replaced
    """
    if not user_details or len(user_details) < 6:
        print("Warning: Invalid user details provided for replacement")
        return html_content
    
    name, street, city, zip_code, country, email = user_details
    
    # Replace template variables
    html_content = html_content.replace("{name}", name)
    html_content = html_content.replace("{street}", street)
    html_content = html_content.replace("{city}", city)
    html_content = html_content.replace("{zip}", zip_code)
    html_content = html_content.replace("{country}", country)
    html_content = html_content.replace("{email}", email)
    
    # Replace hardcoded default values with a comprehensive list
    # Common names used in templates
    html_content = html_content.replace("John Brown", name)
    html_content = html_content.replace("Theodore Jones", name)
    html_content = html_content.replace("John Doe", name)
    
    # Common addresses
    html_content = html_content.replace("651 Cedar Lane", street)
    html_content = html_content.replace("874 Beard Garden Suite 760\nBrandonfort, CO 89234", street)
    html_content = html_content.replace("874 Beard Garden Suite 760", street)
    html_content = html_content.replace("Brandonfort, CO 89234", city)
    
    # Common cities and zip codes
    html_content = html_content.replace("Los Angeles", city)
    html_content = html_content.replace("78201", zip_code)
    html_content = html_content.replace("89234", zip_code)
    
    # Common countries
    html_content = html_content.replace("United Kingdom", country)
    html_content = html_content.replace("United States", country)
    
    # Common emails
    html_content = html_content.replace("Theodore.Jones@gmail.com", email)
    html_content = html_content.replace("john.brown@example.com", email)
    
    # Additional address variations that might appear
    html_content = html_content.replace("Los Angeles 78201", f"{city} {zip_code}")
    html_content = html_content.replace("Los Angeles, 78201", f"{city}, {zip_code}")
    html_content = html_content.replace("East Nicolefort Oneillchester", city)
    html_content = html_content.replace("Germany", country)
    html_content = html_content.replace("53877", zip_code)
    
    # More advanced replacement for address lines
    html_content = html_content.replace("651 Cedar Lane Los Angeles", f"{street} {city}")
    
    return html_content
