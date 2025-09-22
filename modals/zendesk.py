import discord
from discord import ui
from emails.choise import choiseView

class zendeskmodal(ui.Modal, title="Zendesk Support - Send Email"):
    # Optional form fields that can be empty
    ticket_number = ui.TextInput(
        label="Ticket Number (Optional)",
        placeholder="e.g., 233499",
        required=False,
        max_length=100
    )
    
    customer_name = ui.TextInput(
        label="Customer Name (Optional)", 
        placeholder="e.g., John Doe",
        required=False,
        max_length=100
    )
    
    issue_description = ui.TextInput(
        label="Issue Description (Optional)",
        placeholder="Brief description of the support request",
        required=False,
        max_length=200,
        style=discord.TextStyle.paragraph
    )
    
    priority_level = ui.TextInput(
        label="Priority Level (Optional)",
        placeholder="e.g., High, Normal, Low", 
        required=False,
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id
        
        # Get form values (they can be empty)
        ticket_num = self.ticket_number.value.strip() if self.ticket_number.value else "233499"
        customer = self.customer_name.value.strip() if self.customer_name.value else "Customer"
        issue_desc = self.issue_description.value.strip() if self.issue_description.value else "Support request"
        priority = self.priority_level.value.strip() if self.priority_level.value else "Normal"
        
        try:
            # Load the finished zendesk.html file
            with open("receipt/zendesk.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Customize email parameters based on form input
            sender_email = "G. Segarra (Support) <support@ticketera.zendesk.com>"
            subject = f"Solicitar información"
            item_desc = f"Zendesk Support Email - {issue_desc[:50]}{'...' if len(issue_desc) > 50 else ''}"
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

            # Create embed for the choice panel with form data
            embed = discord.Embed(
                title="📧 Zendesk Support Email - Choose Delivery Method",
                description="Your Zendesk support email is ready to send. Choose how you'd like to receive it:",
                color=0x03363D  # Zendesk brand color
            )
            
            # Add form data to embed if provided
            form_data_parts = []
            if self.ticket_number.value:
                form_data_parts.append(f"**Ticket:** #{ticket_num}")
            if self.customer_name.value:
                form_data_parts.append(f"**Customer:** {customer}")
            if self.issue_description.value:
                form_data_parts.append(f"**Issue:** {issue_desc[:100]}{'...' if len(issue_desc) > 100 else ''}")
            if self.priority_level.value:
                form_data_parts.append(f"**Priority:** {priority}")
            
            if form_data_parts:
                embed.add_field(
                    name="📋 Request Details",
                    value="\n".join(form_data_parts),
                    inline=False
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
            embed.set_footer(text=f"Zendesk Support | Request #{ticket_num}")
            
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