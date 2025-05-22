
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import discord
import sqlite3

async def send_email_spoofed(recipient_email, html_content, sender_email, subject, link=""):
    """Send an email with spoofed delivery method"""
    try:
        # Email credentials
        gmail_user = "noreply.appleconfirm@gmail.com"
        gmail_app_password = "zfxz okdo qpsd jqsa"

        if "stockx" in sender_email.lower():
            gmail_user = "noreply.stockxconfirm@gmail.com"
            gmail_app_password = "eoou kqqv asws ptrz"
        elif "vinted" in sender_email.lower():
            gmail_user = "teamvinteed@gmail.com"
            gmail_app_password = "sycj rilo rkys fzsj"

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

        # Connect to Gmail with timeout parameters
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30)
        server.login(gmail_user, gmail_app_password)

        # Send the message
        server.sendmail(gmail_user, recipient_email, message.as_string())
        server.quit()

        return "Email sent successfully"
    except Exception as e:
        return f"Failed to send email: {str(e)}"
