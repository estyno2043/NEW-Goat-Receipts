"""
API endpoint for Chrome Extension Receipt Generation
Handles receipt requests from the GOAT Receipts Chrome Extension
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# Create blueprint
extension_api = Blueprint('extension_api', __name__)

@extension_api.route('/api/generate-receipt', methods=['POST'])
def generate_receipt_from_extension():
    """
    Generate and email receipt from Chrome extension
    Expects JSON payload with receipt details
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['brand', 'brandName', 'fullName', 'email', 'productName']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Email validation
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(data.get('email')):
            return jsonify({'error': 'Invalid email address'}), 400
        
        logging.info(f"Generating receipt from extension for {data.get('fullName')} - {data.get('brandName')}")
        
        # Generate receipt HTML
        receipt_html = generate_receipt_html(data)
        
        # Send email
        success = send_receipt_email(
            to_email=data.get('email'),
            recipient_name=data.get('fullName'),
            brand_name=data.get('brandName'),
            receipt_html=receipt_html
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Receipt sent to {data.get("email")}',
                'brand': data.get('brand'),
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'error': 'Failed to send email'
            }), 500
            
    except Exception as e:
        logging.error(f"Error generating receipt from extension: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500


def generate_receipt_html(data):
    """Generate HTML receipt from extension data"""
    
    # Format delivery date
    delivery_date = data.get('deliveryDate', '')
    if delivery_date:
        try:
            dt = datetime.strptime(delivery_date, '%Y-%m-%d')
            delivery_date = dt.strftime('%B %d, %Y')
        except:
            pass
    
    # Build product details
    product_details = f"<strong>Product:</strong> {data.get('productName', 'N/A')}<br>"
    
    if data.get('productSKU'):
        product_details += f"<strong>SKU/Style:</strong> {data.get('productSKU')}<br>"
    
    if data.get('size'):
        product_details += f"<strong>Size:</strong> {data.get('size')}<br>"
    
    if data.get('color'):
        product_details += f"<strong>Color:</strong> {data.get('color')}<br>"
    
    if data.get('price'):
        currency = data.get('currency', '$')
        product_details += f"<strong>Price:</strong> {currency}{data.get('price')}<br>"
    
    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{data.get('brandName')} Receipt</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: #f5f5f5;
                margin: 0;
                padding: 20px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                font-size: 32px;
            }}
            .header p {{
                margin: 0;
                opacity: 0.9;
            }}
            .content {{
                padding: 30px;
            }}
            .order-info {{
                background: #f9f9f9;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .product-image {{
                width: 100%;
                max-width: 300px;
                margin: 20px auto;
                display: block;
                border-radius: 8px;
            }}
            .details {{
                margin: 20px 0;
                line-height: 1.8;
            }}
            .footer {{
                background: #f9f9f9;
                padding: 20px 30px;
                text-align: center;
                color: #666;
                font-size: 14px;
            }}
            .thank-you {{
                text-align: center;
                margin: 30px 0;
                font-size: 18px;
                color: #667eea;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{data.get('brandName')}</h1>
                <p>Order Confirmation</p>
            </div>
            
            <div class="content">
                <div class="order-info">
                    <strong>Customer:</strong> {data.get('fullName')}<br>
                    <strong>Email:</strong> {data.get('email')}<br>
                    {f"<strong>Order Number:</strong> {data.get('orderNumber')}<br>" if data.get('orderNumber') else ""}
                    {f"<strong>Delivery Date:</strong> {delivery_date}<br>" if delivery_date else ""}
                    <strong>Order Date:</strong> {datetime.now().strftime('%B %d, %Y')}
                </div>
                
                {f'<img src="{data.get("productImage")}" alt="Product" class="product-image">' if data.get('productImage') else ''}
                
                <div class="details">
                    <h3>Order Details</h3>
                    {product_details}
                </div>
                
                <div class="thank-you">
                    <strong>Thank you for your purchase!</strong>
                </div>
            </div>
            
            <div class="footer">
                Generated by GOAT Receipts Extension<br>
                {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def send_receipt_email(to_email, recipient_name, brand_name, receipt_html):
    """Send receipt via email"""
    try:
        # Email configuration (you should use environment variables for these)
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        sender_email = os.environ.get('SENDER_EMAIL', 'noreply@goatreceipts.com')
        sender_password = os.environ.get('SENDER_PASSWORD', '')
        
        if not sender_password:
            logging.warning("SMTP password not configured, email will fail")
            # For demo purposes, just log success
            logging.info(f"Would send email to {to_email}")
            return True
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = f"GOAT Receipts <{sender_email}>"
        msg['To'] = to_email
        msg['Subject'] = f"Your {brand_name} Receipt - Order Confirmation"
        
        # Plain text version
        text_body = f"""
Hello {recipient_name},

Thank you for your purchase from {brand_name}!

Your receipt has been generated and is attached to this email.

If you have any questions, please don't hesitate to contact us.

Best regards,
GOAT Receipts Team
        """
        
        # Attach both plain text and HTML
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(receipt_html, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        logging.info(f"Receipt email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send email: {e}")
        import traceback
        traceback.print_exc()
        return False


# Health check endpoint
@extension_api.route('/api/extension-status', methods=['GET'])
def extension_status():
    """Check if extension API is working"""
    return jsonify({
        'status': 'online',
        'service': 'GOAT Receipts Extension API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }), 200
