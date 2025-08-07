
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import discord
import sqlite3

def format_sender_display_name(sender_email):
    """Format sender email to show brand name properly"""
    if '<' in sender_email and '>' in sender_email:
        # Already properly formatted like "Brand Name <email@domain.com>"
        return sender_email
    
    # Extract domain and create display name
    if '@' in sender_email:
        domain = sender_email.split('@')[1]
        if domain == 'amazon.com':
            return f"Amazon.com <{sender_email}>"
        elif domain == 'apple.com':
            return f"Apple <{sender_email}>"
        elif domain == 'stockx.com':
            return f"StockX <{sender_email}>"
        elif domain == 'nike.com':
            return f"Nike <{sender_email}>"
        else:
            # Capitalize first letter of domain for generic cases
            brand_name = domain.split('.')[0].capitalize()
            return f"{brand_name} <{sender_email}>"
    
    return sender_email

async def send_email_normal(recipient_email, html_content, sender_email, subject):
    """Send an email with normal delivery method"""
    try:
        # Default email for most brands
        gmail_user = "goatreceiptss@gmail.com"
        gmail_app_password = "wvgf ehnr cyek dvun"

        # Specific email addresses for certain brands
        if "apple" in sender_email.lower():
            gmail_user = "noreply.appleconfirm@gmail.com"
            gmail_app_password = "zfxz okdo qpsd jqsa"
        elif "stockx" in sender_email.lower():
            gmail_user = "noreply.stockxconfirm@gmail.com"
            gmail_app_password = "eoou kqqv asws ptrz"
        elif "vinted" in sender_email.lower():
            gmail_user = "teamvinteed@gmail.com"
            gmail_app_password = "sycj rilo rkys fzsj"

        print(f"Attempting to send email from {gmail_user} to {recipient_email}")
        print(f"Subject: {subject}")

        # Format sender email to show brand name properly
        formatted_sender = format_sender_display_name(sender_email)
        
        # Create message
        message = MIMEMultipart()
        message['From'] = formatted_sender
        message['To'] = recipient_email
        message['Subject'] = subject

        # Add Reply-To header to improve deliverability
        message['Reply-To'] = gmail_user
        
        # Set the Sender header to the actual Gmail account for authentication
        message['Sender'] = gmail_user

        # Add additional headers to reduce spam probability
        message['X-Priority'] = '1'
        message['X-MSMail-Priority'] = 'High'
        message['Importance'] = 'High'

        # Attach HTML content
        message.attach(MIMEText(html_content, 'html'))

        print("Connecting to Gmail SMTP server...")
        # Connect to Gmail with timeout parameters
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30)
        
        print("Attempting login...")
        server.login(gmail_user, gmail_app_password)
        print("Login successful!")

        print("Sending email...")
        # Send the message
        server.sendmail(gmail_user, recipient_email, message.as_string())
        server.quit()
        print("Email sent successfully!")

        # Check if user has a lite subscription and increment receipt count
        try:
            from utils.mongodb_manager import mongo_manager
            license_doc = mongo_manager.get_license(recipient_email.split('@')[0] if '@' in recipient_email else None)
            
            # Try to find user by checking if this is a receipt generation (look for user in calling context)
            import inspect
            frame = inspect.currentframe()
            try:
                # Look through the call stack to find user_id
                user_id = None
                for i in range(10):  # Check up to 10 frames back
                    frame = frame.f_back
                    if frame is None:
                        break
                    if 'user_id' in frame.f_locals:
                        user_id = frame.f_locals['user_id']
                        break
                    elif 'interaction' in frame.f_locals and hasattr(frame.f_locals['interaction'], 'user'):
                        user_id = str(frame.f_locals['interaction'].user.id)
                        break
                
                if user_id:
                    license_doc = mongo_manager.get_license(user_id)
                    if license_doc and license_doc.get("subscription_type") == "lite":
                        mongo_manager.increment_receipt_count(user_id)
                        receipt_usage = mongo_manager.get_receipt_usage(user_id)
                        if receipt_usage:
                            print(f"Lite subscription: {receipt_usage['used']}/{receipt_usage['max']} receipts used")
                            
                            # If user has used all receipts, send completion message
                            if receipt_usage['used'] >= receipt_usage['max']:
                                try:
                                    import discord
                                    from main import bot
                                    user = await bot.fetch_user(int(user_id))
                                    if user:
                                        embed = discord.Embed(
                                            title="Lite Subscription Complete",
                                            description=f"You have successfully used all **{receipt_usage['max']}** receipts from your Lite subscription!\n\n**Please consider:**\n• Leaving a review in <#1350413086074474558>\n• If you experienced any issues, open a support ticket in <#1350417131644125226>\n\nThank you for using our service!",
                                            color=discord.Color.green()
                                        )
                                        await user.send(embed=embed)
                                except Exception as dm_error:
                                    print(f"Could not send completion DM: {dm_error}")
                
            finally:
                del frame
        except Exception as e:
            print(f"Error tracking lite subscription usage: {e}")

        return "Email sent successfully"
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Authentication failed: {str(e)}. Check app password and 2FA settings."
        print(error_msg)
        return error_msg
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {str(e)}"
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        print(error_msg)
        return error_msg

class SendNormal:
    @staticmethod
    async def send_email(recipient_email, html_content, sender_email, subject):
        return await send_email_normal(recipient_email, html_content, sender_email, subject)
