import discord
from discord import ui
from emails.choise import choiseView

class zendeskmodal(ui.Modal, title="Zendesk Support - Send Email"):
    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id
        
        try:
            # Load the finished zendesk.html file
            with open("receipt/zendesk.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Set up Zendesk email parameters
            sender_email = "G. Segarra (Support) <support@ticketera.zendesk.com>"
            subject = "Your request has been updated - Request #233499"
            item_desc = "Zendesk Support Email"
            image_url = "https://ci3.googleusercontent.com/meips/ADKq_Naffa1qvXrm4dqCkt52iCtLy4BtCnUkh6Zl78BANOoWIDHMNDRZXrUeijJmc_FObCfabHV926z23QSh1kkzJleEKUGC9L1IM9W5CRKxZm12xe7P-wRY8XEG_V7uXziEh7Rsm_igv_WPyjhnNKQ1_nNaXNERxGzsS0YZhnV9Cc6N7VL_bCo0yxFd4w=s0-d-e1-ft#https://ticketera.zendesk.com/system/photos/23822070395540/Black___White_Minimalist_Aesthetic_Initials_Font_Logo.png"
            link = ""

            # Create the choice view for domain selection
            view = choiseView(
                owner_id=owner_id,
                receipt_html=html_content,
                sender_email=sender_email,
                subject=subject,
                item_desc=item_desc,
                image_url=image_url,
                link=link
            )

            # Create embed for the choice panel
            embed = discord.Embed(
                title="📧 Zendesk Support Email - Choose Delivery Method",
                description="Your Zendesk support email is ready to send. Choose how you'd like to receive it:",
                color=0x03363D  # Zendesk brand color
            )
            embed.add_field(
                name="🔄 Spoofed Email", 
                value="Sends from the actual Zendesk domain (may go to spam)", 
                inline=True
            )
            embed.add_field(
                name="📧 Normal Email", 
                value="Sends through our secure servers (recommended)", 
                inline=True
            )
            embed.set_footer(text="Zendesk Support | Request #233499")
            
            if image_url:
                embed.set_thumbnail(url=image_url)

            # Send the choice panel
            await interaction.response.send_message(
                content=f"{interaction.user.mention}",
                embed=embed, 
                view=view, 
                ephemeral=False
            )

        except FileNotFoundError:
            embed = discord.Embed(
                title="❌ File Error",
                description="The Zendesk email template could not be found. Please contact an administrator.",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred while preparing your Zendesk email: {str(e)}",
                color=0xe74c3c
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)