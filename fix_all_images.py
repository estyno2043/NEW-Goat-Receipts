
#!/usr/bin/env python3
"""
Script to fix image display issues in all receipt templates.
This will scan all receipt files and fix common image display problems.
"""

import os
import sys
from utils.image_fix import fix_all_receipt_images

def main():
    print("Starting image fix process for all receipts...")
    
    try:
        # Fix all receipt images
        fix_all_receipt_images()
        print("Image fix process completed successfully!")
        
    except Exception as e:
        print(f"Error during image fix process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
