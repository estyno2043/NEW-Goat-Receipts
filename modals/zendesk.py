import discord
from emails.choise import choiseView

class zendeskmodal(discord.ui.Modal, title="Zendesk Support Ticket"):
    # Add a dummy field that doesn't actually do anything but satisfies Discord's requirement
    ticket_number = discord.ui.TextInput(
        label="Ticket Reference (Optional)",
        placeholder="Enter ticket # or leave blank",
        required=False,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Defer the response to avoid timeout
        await interaction.response.defer(ephemeral=False)
        
        owner_id = interaction.user.id
        
        # Load the finished zendesk.html file
        with open("receipt/zendesk.html", "r", encoding="utf-8") as file:
            html_content = file.read()
        
        # Set up Zendesk email parameters
        sender_email = "G. Segarra (Support) <support@ticketera.zendesk.com>"
        subject = "Your request has been updated - Request #233499"
        item_desc = "Zendesk Support Email"
        image_url = ""  # Empty to avoid Discord length issues
        link = "https://ticketera.zendesk.com"
        
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
        
        # Send the choice panel
        await interaction.followup.send(
            content=f"{interaction.user.mention}",
            embed=embed, 
            view=view, 
            ephemeral=False
        )