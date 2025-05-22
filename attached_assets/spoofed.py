import smtplib
import ssl
import re
import asyncio
import logging
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from utils.utils import Utils


class SendSpoofed:
    def __init__(self, sender_email, receiver_email, subject, html_content):
        self.sender_email = sender_email
        self.receiver_email = receiver_email
        self.subject = subject
        self.html_content = html_content

    def send_email(self, bot=None, user_id=None, form_data=None, interaction=None):
        message = MIMEMultipart('alternative')
        message.attach(MIMEText(self.html_content, "html"))

        message['Subject'] = self.subject.strip()

        if '<' in self.sender_email and '>' in self.sender_email:
            message['From'] = self.sender_email
        else:
            parts = self.sender_email.split()
            if len(parts) > 1:
                sender_name = ' '.join(parts[:-1])
                sender_email = parts[-1].strip('<>')
                message['From'] = f"{sender_name} <{sender_email}>"
            else:
                message['From'] = self.sender_email

        message['To'] = self.receiver_email
        message['X-Priority'] = '1'
        message['X-Mailer'] = 'Microsoft Outlook'
        message['MIME-Version'] = '1.0'
        message['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        message['Return-Path'] = self.sender_email
        import uuid
        message['Message-ID'] = f"<{str(uuid.uuid4())}@{self.sender_email.split('@')[1]}>"

        smtp_server = 'mail.inchiderecufolie.ro'
        smtp_port = 587
        smtp_username = 'server2556@inchiderecufolie.ro'
        smtp_password = 'AddSMTP@1337'

        print(f"Attempting to send spoofed email to: {self.receiver_email}")
        print(f"From: {self.sender_email}")
        print(f"Subject: {self.subject}")
        print(f"Using SMTP server: {smtp_server}:{smtp_port}")

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.set_debuglevel(2)
                print("Connected to SMTP server, initiating STARTTLS")
                server.starttls()
                print(f"Logging in with username: {smtp_username}")
                server.login(smtp_username, smtp_password)
                print("Login successful")
                print(f"Sending email from {self.sender_email} to {self.receiver_email}")
                server.sendmail(
                    from_addr=self.sender_email,
                    to_addrs=[self.receiver_email],
                    msg=message.as_string()
                )

                logging.info(f"Spoofed email sent successfully to {self.receiver_email}")
                print(f"✅ Spoofed email sent successfully to {self.receiver_email}")

                # Log the receipt generation if we have all parameters
                if bot and user_id and interaction:
                    guild_id = interaction.guild.id if interaction else None
                    brandname = form_data.get('brandname', self.sender_name) if form_data else self.sender_name or 'Unknown'
                    imageurl = form_data.get('imageurl', self.image_url) if form_data else self.image_url or ''
                    # Create an async task to avoid blocking
                    import asyncio
                    asyncio.create_task(Utils.log_receipt_generation(bot, user_id, brandname, imageurl, guild_id))

                return True

        except smtplib.SMTPAuthenticationError:
            error_msg = "❌ SMTP Authentication Error: Check your username and password"
            logging.error(error_msg)
            print(error_msg)
            return False

        except smtplib.SMTPServerDisconnected:
            error_msg = "❌ Server disconnected unexpectedly"
            logging.error(error_msg)
            print(error_msg)
            return False

        except smtplib.SMTPSenderRefused:
            error_msg = f"❌ SMTP Sender Refused: The sender address {self.sender_email} was refused"
            logging.error(error_msg)
            print(error_msg)
            return False

        except smtplib.SMTPRecipientsRefused:
            error_msg = f"❌ SMTP Recipients Refused: The recipient {self.receiver_email} was refused"
            logging.error(error_msg)
            print(error_msg)
            return False

        except smtplib.SMTPDataError:
            error_msg = "❌ SMTP Data Error: The server refused to accept the message data"
            logging.error(error_msg)
            print(error_msg)
            return False

        except smtplib.SMTPException as e:
            error_msg = f"❌ SMTP Error: {str(e)}"
            logging.error(error_msg)
            print(error_msg)
            return False

        except Exception as e:
            error_msg = f"❌ Unexpected error when sending email: {str(e)}"
            logging.error(error_msg)
            print(error_msg)
            return False