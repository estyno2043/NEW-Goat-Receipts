class ReceiptTemplate:
    def __init__(self, name, template_id, description, preview_url):
        self.name = name
        self.template_id = template_id
        self.description = description
        self.preview_url = preview_url

# Default templates
DEFAULT_TEMPLATES = [
    ReceiptTemplate(
        "Amazon", 
        "amazon_basic", 
        "Basic Amazon receipt template", 
        "https://example.com/amazon_preview.png"
    ),
    ReceiptTemplate(
        "Walmart", 
        "walmart_basic", 
        "Basic Walmart receipt template", 
        "https://example.com/walmart_preview.png"
    ),
    ReceiptTemplate(
        "Apple Store", 
        "apple_basic", 
        "Basic Apple Store receipt template", 
        "https://example.com/apple_preview.png"
    )
]

def get_template_by_id(template_id):
    """Get template by ID"""
    for template in DEFAULT_TEMPLATES:
        if template.template_id == template_id:
            return template
    return None

def get_all_templates():
    """Get all available templates"""
    return DEFAULT_TEMPLATES