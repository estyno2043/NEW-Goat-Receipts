import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import discord
import sqlite3
import time
import uuid
import logging
from utils.db_utils import get_user_details

async def send_email_spoofed(recipient_email, html_content, sender_email, sender_name, subject, link=""):
    """Send an email with spoofed delivery method"""
    try:
        # Email server configuration
        smtp_host = "mail.inchiderecufolie.ro"
        smtp_port = 587
        username = "server2556@inchiderecufolie.ro"
        password = "AddSMTP@1337"

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

        # Connect to SMTP server
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()  # Upgrade to encrypted connection
        server.login(username, password)

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

class SpoofedEmailModal(discord.ui.Modal):
    def __init__(self, receipt_type, sender_email, subject, product_name, image_url):
        super().__init__(title="Spoofed Email")
        self.receipt_type = receipt_type
        self.sender_email = sender_email
        self.subject = subject
        self.product_name = product_name
        self.image_url = image_url
        self.html_content = None

        self.recipient_email = discord.ui.TextInput(
            label="Recipient Email",
            placeholder="Enter recipient email address",
            required=True
        )

        self.sender_name = discord.ui.TextInput(
            label="Sender Name",
            placeholder="Enter sender name (e.g. Apple, Nike)",
            required=True,
            default=self.receipt_type.capitalize() if self.receipt_type != "unknown" else ""
        )

        self.add_item(self.recipient_email)
        self.add_item(self.sender_name)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Get values from the form
            recipient_email = self.recipient_email.value
            sender_name = self.sender_name.value

            # Get user details
            user_details = get_user_details(interaction.user.id)
            if user_details:
                name, street, city, zip_code, country, _ = user_details

                # Replace placeholders in the HTML template
                html_content = self.html_content

                # Common replacements - replace if these placeholders exist
                replacements = {
                    '{name}': name,
                    '{street}': street,
                    '{city}': city,
                    '{zip}': zip_code,
                    '{country}': country,
                    '{product_name}': self.product_name,
                    '{email}': recipient_email
                }

                for placeholder, value in replacements.items():
                    if placeholder in html_content:
                        html_content = html_content.replace(placeholder, value)

                # Send the email
                result = await send_email_spoofed(recipient_email, html_content, self.sender_email, sender_name, self.subject)

                if "successfully" in result:
                    await interaction.response.send_message(f"✅ Spoofed email sent successfully to {recipient_email}", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ {result}", ephemeral=True)
            else:
                await interaction.response.send_message("❌ User details not found. Please set up your information first.", ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)