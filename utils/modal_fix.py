
"""
Script to update all modal files to use the new template_utils for user details replacement
"""
import os
import re

def fix_all_modals():
    """Update all modal files to use the template_utils for proper user details replacement"""
    modals_dir = "modals"
    
    # Skip these files as they might have custom implementations
    skip_files = ["__init__.py", "__pycache__"]
    
    # Count of files updated
    updated_count = 0
    
    for filename in os.listdir(modals_dir):
        if filename in skip_files or not filename.endswith(".py"):
            continue
        
        filepath = os.path.join(modals_dir, filename)
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
        
        # Check if the file has user_details handling
        if "user_details" in content and ("html_content =" in content or "html_content=" in content):
            # Check if it already has the template_utils import
            if "from utils.template_utils import replace_user_details" not in content:
                # Add the import if needed
                import_regex = r"import .*\n|from .* import .*\n"
                last_import_match = list(re.finditer(import_regex, content))
                if last_import_match:
                    last_import_pos = last_import_match[-1].end()
                    content = (content[:last_import_pos] + 
                               "from utils.template_utils import replace_user_details\n" + 
                               content[last_import_pos:])
                
                # Find where to add the user details replacement
                # Look for patterns where the HTML content is manipulated
                patterns = [
                    # After HTML placeholders are replaced
                    r"(html_content = html_content\.replace\(.*?\)[^\n]*\n)(?![^\n]*html_content = html_content\.replace)",
                    # Before writing the HTML file
                    r"(with open\([^)]*\"w\"[^)]*\) as file:)",
                    # After opening the HTML template
                    r"(html_content = file\.read\(\)[^\n]*\n)"
                ]
                
                replacement_added = False
                for pattern in patterns:
                    if re.search(pattern, content) and not replacement_added:
                        replacement = r"\1\n            # Use the template utility to replace user details properly\n            html_content = replace_user_details(html_content, user_details)\n"
                        new_content = re.sub(pattern, replacement, content, count=1)
                        
                        # Only update if a change was made
                        if new_content != content:
                            content = new_content
                            replacement_added = True
                            updated_count += 1
                            
                            # Write the updated file
                            with open(filepath, "w", encoding="utf-8") as file:
                                file.write(content)
                            print(f"Updated {filename}")
    
    print(f"Total modal files updated: {updated_count}")
    return updated_count

if __name__ == "__main__":
    fix_all_modals()
