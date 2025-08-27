
import os
import re

def fix_image_display_in_receipt(html_content, image_url, product_name="Product"):
    """
    Fix image display issues in receipt HTML content.
    
    Args:
        html_content (str): The HTML content to process
        image_url (str): The image URL to use
        product_name (str): Product name for alt text
        
    Returns:
        str: The fixed HTML content
    """
    if not image_url:
        return html_content
    
    # Common image placeholder patterns
    image_placeholders = [
        '{productimage}',
        '{imageurl}',
        '{imagelink}',
        '{productimageurl}',
        '{image}',
        '{img}',
        '{product_image}'
    ]
    
    # Replace direct placeholders first
    for placeholder in image_placeholders:
        html_content = html_content.replace(placeholder, image_url)
    
    # Fix broken image tags - look for incomplete img tags
    broken_img_patterns = [
        r'<img[^>]*src=""[^>]*>',  # Empty src
        r'<img[^>]*src="{[^}]*}"[^>]*>',  # Unreplaced placeholder in src
        r'<img[^>]*width="[^"]*"[^>]*height="[^"]*"[^>]*class="[^"]*"[^>]*>',  # Incomplete tags
    ]
    
    for pattern in broken_img_patterns:
        if re.search(pattern, html_content):
            # Create a proper image tag
            proper_img_tag = f'<img src="{image_url}" alt="{product_name}" style="max-width:200px;height:auto;" class="CToWUd" data-bit="iit">'
            html_content = re.sub(pattern, proper_img_tag, html_content)
    
    # Fix specific image styling issues
    # Ensure images have proper dimensions and styling
    img_pattern = r'<img([^>]*?)src="' + re.escape(image_url) + r'"([^>]*?)>'
    
    def replace_img(match):
        attrs_before = match.group(1)
        attrs_after = match.group(2)
        
        # Check if width/height/style attributes are missing
        if 'width=' not in attrs_before + attrs_after:
            attrs_after += ' width="160"'
        if 'height=' not in attrs_before + attrs_after:
            attrs_after += ' height="160"'
        if 'style=' not in attrs_before + attrs_after:
            attrs_after += ' style="max-width:200px;height:auto;"'
        if 'alt=' not in attrs_before + attrs_after:
            attrs_after += f' alt="{product_name}"'
        if 'class=' not in attrs_before + attrs_after:
            attrs_after += ' class="CToWUd"'
            
        return f'<img{attrs_before}src="{image_url}"{attrs_after}>'
    
    html_content = re.sub(img_pattern, replace_img, html_content)
    
    return html_content

def fix_all_receipt_images():
    """
    Scan and fix image display issues in all updated receipt files.
    """
    updated_receipts_dir = "receipt/updatedrecipies"
    
    if not os.path.exists(updated_receipts_dir):
        print(f"Directory {updated_receipts_dir} does not exist")
        return
    
    fixed_count = 0
    
    for filename in os.listdir(updated_receipts_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(updated_receipts_dir, filename)
            
            try:
                # Read the file
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Check if there are image issues
                has_issues = False
                
                # Check for common image problems
                if (re.search(r'<img[^>]*src=""[^>]*>', content) or 
                    re.search(r'<img[^>]*src="{[^}]*}"[^>]*>', content) or
                    '{productimage}' in content or
                    '{imageurl}' in content or
                    '{imagelink}' in content):
                    
                    has_issues = True
                
                if has_issues:
                    # Try to extract existing image URL or use a placeholder
                    img_url_match = re.search(r'src="(https?://[^"]+)"', content)
                    if img_url_match:
                        image_url = img_url_match.group(1)
                    else:
                        # Use a placeholder image URL
                        image_url = "https://via.placeholder.com/200x200/000000/FFFFFF?text=Product+Image"
                    
                    # Fix the content
                    fixed_content = fix_image_display_in_receipt(content, image_url, "Product")
                    
                    # Write back
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(fixed_content)
                    
                    fixed_count += 1
                    print(f"Fixed image issues in: {filename}")
            
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    print(f"Fixed image issues in {fixed_count} receipt files")

if __name__ == "__main__":
    fix_all_receipt_images()
