import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import discord
import sqlite3
import time
import uuid
import logging

class SendSpoofed:
    def __init__(self, sender_email, receiver_email, subject, html_content):
        self.sender_email = sender_email
        self.receiver_email = receiver_email
        self.subject = subject
        self.html_content = html_content

    def send_email(self, bot=None, user_id=None, form_data=None, interaction=None):
        message = MIMEMultipart('alternative')
        
        # Add both text and HTML parts for better deliverability
        # Create a simple text version by stripping HTML tags
        import re
        text_content = re.sub('<[^<]+?>', '', self.html_content)
        text_content = text_content.replace('&nbsp;', ' ').replace('&amp;', '&')
        
        # Attach both plain text and HTML versions
        message.attach(MIMEText(text_content, 'plain'))
        message.attach(MIMEText(self.html_content, 'html'))

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
        message['X-Priority'] = '3'  # Changed from 1 to 3 (normal priority)
        message['X-Mailer'] = 'Microsoft Outlook 16.0'
        message['MIME-Version'] = '1.0'
        message['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        # Return-Path will be set by receiving server based on envelope sender
        
        # Generate a unique Message-ID based on the domain in the sender email
        sender_domain = self.sender_email.split('@')[-1].split('>')[-1].strip()
        message['Message-ID'] = f"<{str(uuid.uuid4())}@{sender_domain}>"
        
        # Add additional legitimate headers to improve deliverability
        message['X-Entity-Ref-ID'] = str(uuid.uuid4())
        message['List-Unsubscribe'] = '<mailto:unsubscribe@anteagarden.com>'
        message['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
        
        # Add content-related headers
        message['Content-Transfer-Encoding'] = '7bit'
        message['X-Auto-Response-Suppress'] = 'DR, NDR, RN, NRN, OOF, AutoReply'

        # Enhanced SMTP configuration
        smtp_server = 'anteagarden.com'
        smtp_port = 587
        smtp_username = 'admin@anteagarden.com'
        smtp_password = '123123'
        smtp_timeout = 30  # Add timeout for better connection handling

        print(f"Attempting to send spoofed email to: {self.receiver_email}")
        print(f"From: {self.sender_email}")
        print(f"Subject: {self.subject}")
        print(f"Using SMTP server: {smtp_server}:{smtp_port}")

        try:
            # Enhanced SMTP connection with better error handling
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=smtp_timeout)
            server.set_debuglevel(0)  # Set to 1 for debugging
            
            # EHLO/HELO greeting
            server.ehlo()
            
            # Enable TLS encryption
            if server.has_extn('STARTTLS'):
                server.starttls()
                server.ehlo()  # Re-identify after STARTTLS
            
            # Authenticate
            server.login(smtp_username, smtp_password)
            
            # Use the sender email as envelope sender for better alignment
            # Note: This may still fail DMARC for third-party domains
            envelope_from = self.sender_email if '<' in self.sender_email else self.sender_email.split()[-1].strip('<>')
            
            # Send the email
            server.sendmail(
                from_addr=envelope_from,
                to_addrs=[self.receiver_email],
                msg=message.as_string()
            )
            
            server.quit()

            logging.info(f"Spoofed email sent successfully to {self.receiver_email}")
            print(f"✅ Spoofed email sent successfully to {self.receiver_email}")
            return True

        except Exception as e:
            logging.error(f"❌ Error sending spoofed email: {str(e)}")
            print(f"❌ Error sending spoofed email: {str(e)}")
            return False

async def send_email_spoofed(recipient_email, html_content, sender_email, subject, link=""):
    """Send an email with spoofed delivery method"""
    try:
        # Create message
        message = MIMEMultipart('alternative')
        
        # Add both text and HTML parts for better deliverability
        # Create a simple text version by stripping HTML tags
        import re
        text_content = re.sub('<[^<]+?>', '', html_content)
        text_content = text_content.replace('&nbsp;', ' ').replace('&amp;', '&')
        
        # Attach both plain text and HTML versions
        message.attach(MIMEText(text_content, 'plain'))
        message.attach(MIMEText(html_content, 'html'))

        message['Subject'] = subject.strip()

        # Properly format sender email
        if '<' in sender_email and '>' in sender_email:
            message['From'] = sender_email
        else:
            parts = sender_email.split()
            if len(parts) > 1:
                sender_name = ' '.join(parts[:-1])
                sender_email_address = parts[-1].strip('<>')
                message['From'] = f"{sender_name} <{sender_email_address}>"
            else:
                message['From'] = sender_email

        message['To'] = recipient_email
        message['X-Priority'] = '3'  # Changed from 1 to 3 (normal priority)
        message['X-Mailer'] = 'Microsoft Outlook 16.0'
        message['MIME-Version'] = '1.0'
        message['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        # Return-Path will be set by receiving server based on envelope sender
        
        # Generate a unique Message-ID based on the domain in the sender email
        sender_domain = sender_email.split('@')[-1].split('>')[-1].strip()
        message['Message-ID'] = f"<{str(uuid.uuid4())}@{sender_domain}>"
        
        # Add additional legitimate headers to improve deliverability
        message['X-Entity-Ref-ID'] = str(uuid.uuid4())
        message['List-Unsubscribe'] = '<mailto:unsubscribe@anteagarden.com>'
        message['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
        
        # Add content-related headers
        message['Content-Transfer-Encoding'] = '7bit'
        message['X-Auto-Response-Suppress'] = 'DR, NDR, RN, NRN, OOF, AutoReply'

        # Use custom SMTP settings as specified
        # Enhanced SMTP configuration
        smtp_server = 'anteagarden.com'
        smtp_port = 587
        smtp_username = 'admin@anteagarden.com'
        smtp_password = '123123'
        smtp_timeout = 30  # Add timeout for better connection handling

        print(f"Attempting to send spoofed email to: {recipient_email}")
        print(f"From: {sender_email}")
        print(f"Subject: {subject}")
        print(f"Using SMTP server: {smtp_server}:{smtp_port}")

        # Enhanced SMTP connection with better error handling
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=smtp_timeout)
        server.set_debuglevel(0)  # Set to 1 for debugging
        
        # EHLO/HELO greeting
        server.ehlo()
        
        # Enable TLS encryption
        if server.has_extn('STARTTLS'):
            server.starttls()
            server.ehlo()  # Re-identify after STARTTLS
        
        # Authenticate
        server.login(smtp_username, smtp_password)
        
        # Set the actual envelope sender to match authentication
        envelope_from = smtp_username  # Use authenticated user as envelope sender
        
        # Send the email
        server.sendmail(
            from_addr=envelope_from,
            to_addrs=[recipient_email],
            msg=message.as_string()
        )
        
        server.quit()

        print(f"✅ Spoofed email sent successfully to {recipient_email}")
        return "Email sent successfully"
    except Exception as e:
        print(f"❌ Error sending spoofed email: {str(e)}")
        return f"Failed to send email: {str(e)}"