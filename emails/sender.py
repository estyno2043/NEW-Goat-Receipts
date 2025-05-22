import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import discord
import sqlite3

async def send_email(interaction, recipient_email, html_content, sender_email, subject, product_name, image_url, brand="Apple"):
    """Send an email with the receipt"""
    try:
        # Email credentials
        if brand.lower() == "stockx":
            gmail_user = "noreply.stockxconfirm@gmail.com"
            gmail_app_password = "eoou kqqv asws ptrz"
        elif brand.lower() == "vinted":
            gmail_user = "teamvinteed@gmail.com"
            gmail_app_password = "sycj rilo rkys fzsj"
        else:
            gmail_user = "noreply.appleconfirm@gmail.com"
            gmail_app_password = "zfxz okdo qpsd jqsa"

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

        # Create success embed
        embed = discord.Embed(
            title="Email was sent successfully",
            description=f"**Kindly check your Inbox/Spam folder**\n\nReceipt for: {product_name or 'your purchase'}",
            color=discord.Color.green()
        )

        # If we have an image URL, add it to the embed
        if image_url:
            embed.set_thumbnail(url=image_url)

        # Update interaction message to show closed panel
        await interaction.edit_original_response(embed=embed, view=None)

        # Send confirmation message to the confirmation channel
        confirmation_channel_id = 1371073235969638461
        confirmation_channel = interaction.client.get_channel(confirmation_channel_id)

        if confirmation_channel:
            confirmation_embed = discord.Embed(
                title=f"<a:Confirmation:1366854650401128528> {brand} Receipt Generated",
                description=f"Receipt for {product_name or 'your purchase'} sent successfully",
                color=discord.Color.green()
            )

            if image_url:
                confirmation_embed.set_thumbnail(url=image_url)

            # Send message with user mention and embed
            await confirmation_channel.send(
                content=f"<@{interaction.user.id}> has generated free **{brand}** receipt",
                embed=confirmation_embed
            )

        # Create a closed panel embed for the original panel
        closed_panel_embed = discord.Embed(
            title="Panel Closed",
            description="Receipt has been sent successfully. Panel is now closed.",
            color=discord.Color.greyple()
        )

        # Try to close the original panel message
        try:
            # Access panel data in a more robust way
            panel_data = getattr(interaction, '_panel_data', {}) or {}
            if not panel_data:
                print(f"No panel data found on interaction for user {interaction.user.id}")

            # Log what we found to help debug
            if panel_data:
                print(f"Found panel data keys: {', '.join(panel_data.keys())}")

            # Check for panel_message
            panel_message = panel_data.get('panel_message')
            if panel_message:
                print(f"Found panel message for user {interaction.user.id}")
            if panel_message:
                try:
                    await panel_message.edit(embed=closed_panel_embed, view=None)
                    print("Panel closed using stored message reference")
                    return True
                except Exception as e:
                    print(f"Failed to close panel using message reference: {e}")

            # Check for panel_interaction
            panel_interaction = panel_data.get('panel_interaction')
            if panel_interaction:
                try:
                    await panel_interaction.edit_original_response(embed=closed_panel_embed, view=None)
                    print("Panel closed using panel interaction")
                    return True
                except Exception as e:
                    print(f"Failed to close panel using panel interaction: {e}")

            # Check for original_interaction
            original_interaction = panel_data.get('original_interaction')
            if original_interaction:
                try:
                    await original_interaction.edit_original_response(embed=closed_panel_embed, view=None)
                    print("Panel closed using original interaction")
                    return True
                except Exception as e:
                    print(f"Failed to close panel using original interaction: {e}")

        except Exception as e:
            print(f"Error while trying to close panel: {e}")

        return True
    except Exception as e:
        # Create error embed
        embed = discord.Embed(
            title="Error",
            description=f"Failed to send email: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.edit_original_response(embed=embed, view=None)
        return False

def is_valid_image_url(url):
    """Check if URL is likely a valid image URL"""
    # Basic pattern to match common image extensions
    image_pattern = re.compile(r'^https?://.*\.(jpg|jpeg|png|gif|webp|bmp)(\?.*)?$', re.IGNORECASE)

    # More comprehensive check including Discord CDN links
    discord_cdn_pattern = re.compile(r'^https?://(?:cdn\.discordapp\.com|media\.discordapp\.net|i\.imgur\.com)/.*', re.IGNORECASE)

    return bool(image_pattern.match(url)) or bool(discord_cdn_pattern.match(url))