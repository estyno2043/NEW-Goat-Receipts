import sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os
import asyncio
import re

class SendNormal:
    def __init__(self, sender_email, receiver_email, subject, html_content):
        self.sender_email = sender_email
        self.receiver_email = receiver_email
        self.subject = subject
        self.html_content = html_content


    def send_email(self, bot=None, user_id=None, form_data=None, interaction=None):
        if self.sender_email is None:
            print("Cannot send email: Sender email not found.")
            return False, "Sender email not found"

        message = MIMEMultipart()
        message.attach(MIMEText(self.html_content, "html"))

        message['Subject'] = self.subject
        message['From'] = self.sender_email
        message['To'] = self.receiver_email

        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Check which type of email and use dedicated credentials
        if "vinted" in self.sender_email.lower():
            smtp_username = "teamvinteed@gmail.com"
            smtp_password = "sycj rilo rkys fzsj"
            print("Using Vinted-specific email credentials")
        elif "stockx" in self.sender_email.lower():
            smtp_username = "noreply.stockxconfirm@gmail.com"
            smtp_password = "eoou kqqv asws ptrz"
            print("Using StockX-specific email credentials")
        elif "apple" in self.sender_email.lower():
            smtp_username = "noreply.appleconfirm@gmail.com"
            smtp_password = "zfxz okdo qpsd jqsa"
            print("Using Apple-specific email credentials")
        else:
            smtp_username = "ord3rnotification@gmail.com"
            # Get password from environment variables
            smtp_password = os.getenv("GMAIL_APP_PASSWORD")

        if not smtp_password:
            print("ERROR: GMAIL_APP_PASSWORD environment variable not set")
            return False, "Gmail app password not configured. Please contact an administrator."

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                print(f"Attempting login with username: {smtp_username}")
                server.login(smtp_username, smtp_password)
                server.sendmail(self.sender_email, self.receiver_email, message.as_string())
                print(f"Email sent successfully!")

                # Log the receipt generation if successful
                try:
                    from utils.utils import Utils
                    # Get guild ID if available from the interaction context
                    guild_id = getattr(self, 'guild_id', None) if hasattr(self, 'guild_id') else None

                    # Extract brand name from subject or default to "Receipt"
                    brand_name = getattr(self, 'sender_name', None) if hasattr(self, 'sender_name') else "Receipt"
                    if not brand_name:
                        # Try to extract from subject
                        match = re.search(r'(.*?)\s+Order', self.subject)
                        if match:
                            brand_name = match.group(1).strip()
                        else:
                            brand_name = "Receipt"

                    # Extract user ID from context or default to None
                    user_id = getattr(self, 'user_id', None) if hasattr(self, 'user_id') else None

                    # Use image URL if available
                    image_url = getattr(self, 'image_url', None) if hasattr(self, 'image_url') else None

                    # Get bot instance -  assuming bot is passed to send_email now.
                    bot = bot

                    if bot and user_id:
                        print(f"Logging receipt generation for {brand_name}, user {user_id}, guild {guild_id}")
                        asyncio.create_task(Utils.log_receipt_generation(bot, user_id, brand_name, image_url, guild_id))
                except Exception as log_error:
                    print(f"Error logging receipt generation: {log_error}")
                    import traceback
                    print(traceback.format_exc())

                return True, "Email sent successfully"
        except smtplib.SMTPAuthenticationError as e:
            print(f"SMTP Authentication Error: {e}")
            return False, "Email authentication failed. Please contact an administrator."
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False, "Failed to send email: " + str(e)