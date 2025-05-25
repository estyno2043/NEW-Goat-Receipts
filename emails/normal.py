import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import discord
import sqlite3
from utils.db_utils import get_user_details

async def send_email_normal(recipient_email, html_content, sender_email, subject):
    """Send an email with normal delivery method"""
    try:
        # Default email for most brands
        gmail_user = "ord3rnotification@gmail.com"
        gmail_app_password = "fony ponb naxr nlaj"

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

class EmailModal(discord.ui.Modal):
    def __init__(self, receipt_type, sender_email, subject, product_name, image_url):
        super().__init__(title="Normal Email")
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
        
        self.add_item(self.recipient_email)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Get values from the form
            recipient_email = self.recipient_email.value
            
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
                result = await send_email_normal(recipient_email, html_content, self.sender_email, self.subject)
                
                if "successfully" in result:
                    await interaction.response.send_message(f"✅ Email sent successfully to {recipient_email}", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ {result}", ephemeral=True)
            else:
                await interaction.response.send_message("❌ User details not found. Please set up your information first.", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)

class SendNormal:
    @staticmethod
    async def send_email(recipient_email, html_content, sender_email, subject):
        return await send_email_normal(recipient_email, html_content, sender_email, subject)