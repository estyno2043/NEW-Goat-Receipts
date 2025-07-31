
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import discord
import sqlite3

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

        # Create message
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = subject

        # Add Reply-To header to improve deliverability
        message['Reply-To'] = gmail_user

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
