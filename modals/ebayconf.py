
import asyncio
import discord
from discord.ui import Select
from discord import SelectOption, ui, app_commands, Interaction
import random
import os
import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

class EbayConfModal(ui.Modal, title="eBay Receipt - Step 1"):
    
    # Create alias for compatibility
    # ebayconfmodal = EbayConfModal  # This creates a circular reference, commented out
    productname = discord.ui.TextInput(label="Product Name", placeholder="Apple Earbuds Pro", required=True)
    productimagelink = discord.ui.TextInput(label="Product Image Link", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
    productprice = discord.ui.TextInput(label="Price without currency", placeholder="200.00", required=True)
    productcurrency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    productsku = discord.ui.TextInput(label="Item ID/SKU", placeholder="827384", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        productname = self.productname.value
        productimagelink = self.productimagelink.value
        productprice = self.productprice.value
        productcurrency = self.productcurrency.value
        productsku = self.productsku.value
        
        # Instead of sending another modal, store data and respond with a message/button
        embed = discord.Embed(title="Product Details", description="First part completed successfully!", color=0x1e1f22)
        embed.add_field(name="Product Name", value=productname, inline=False)
        embed.add_field(name="Price", value=f"{productcurrency}{productprice}", inline=True)
        embed.add_field(name="SKU", value=productsku, inline=True)
        
        # Create a button to continue to the next step
        class ContinueButton(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=300)
                
            @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary)
            async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                second_modal = EbayConfSecondModal(productname, productimagelink, productprice, productcurrency, productsku)
                await interaction.response.send_modal(second_modal)
        
        await interaction.response.send_message(embed=embed, view=ContinueButton(), ephemeral=True)

class EbayConfSecondModal(ui.Modal, title="eBay Receipt - Step 2"):
    def __init__(self, productname, productimagelink, productprice, productcurrency, productsku):
        super().__init__()
        self.productname = productname
        self.productimagelink = productimagelink
        self.productprice = productprice
        self.productcurrency = productcurrency
        self.productsku = productsku
        
        self.add_item(discord.ui.TextInput(label="Shipping Cost", placeholder="10.00", required=True))
        self.add_item(discord.ui.TextInput(label="Delivery Date (DD/MM/YYYY)", placeholder="6/5/2025", required=True))
        self.add_item(discord.ui.TextInput(label="Seller Name", placeholder="John Lewis", required=True))

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        # Get user details from database
        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

        if user_details:
            name, street, city, zipp, country, email = user_details
            
            # Get form values
            productshippingcost = self.children[0].value
            productdeliverydate = self.children[1].value
            productseller = self.children[2].value
            
            # Calculate total
            try:
                total = float(self.productprice) + float(productshippingcost)
                total_formatted = f"{total:.2f}"
            except ValueError:
                total_formatted = "Error calculating total"

            try:
                # Process the HTML template
                embed = discord.Embed(title="Processing...", description="Processing your receipt, please wait.", color=0x1e1f22)
                await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed)

                with open("receipt/ebayconf.html", "r", encoding="utf-8") as file:
                    html_content = file.read()

                # Replace placeholders with actual values
                html_content = html_content.replace("Thanks for your purchase, Laura Vincent.", f"Thanks for your purchase, {name}.")
                
                # Replace address information
                address_replacement = f"{name}<br>{street}<br>{city}, {zipp}<br>{country}"
                html_content = html_content.replace("Laura Vincent<br>2456 Miller Dale\nPort Sarahfurt, OK 06684<br>2456 Miller Dale\nPort Sarahfurt, OK 06684, 56370 <br>Guadeloupe", address_replacement)
                
                # Replace delivery date
                html_content = html_content.replace("6/5/2025", productdeliverydate)
                
                # Replace product details
                html_content = html_content.replace("Apple Earbuds Pro 1st Generation Wireless Headphones And Built In Microphone", self.productname)
                # Find and replace the image tag with the new product image
                import re
                # First look for the image in the HTML content
                img_pattern = re.compile(r'<img[^>]*?src="([^"]*?ebayimg\.com[^"]*?)"')
                img_match = img_pattern.search(html_content)
                if img_match:
                    old_img_src = img_match.group(1)
                    # Replace the old image source with the new one
                    html_content = html_content.replace(old_img_src, self.productimagelink)
                else:
                    # Fallback to direct replacement if pattern not found
                    html_content = html_content.replace("https://ci3.googleusercontent.com/meips/ADKq_NZ1ah4ngQLsz-9pI2EpOreZDtdHFo88218-LXqPJM9gozh7IUvr4LyivMVD9VbeTbugU_zecFewYn-SFAfaHigSJWq-UaMxaLXjy8tnqyNS9Q=s0-d-e1-ft#https://i.ebayimg.com/images/g/PiYAAOSwU3ZnxNik/s-l960.webp", self.productimagelink)
                
                # Replace pricing
                html_content = html_content.replace("<span><b>€200.00</b></span>", f"<span><b>{self.productcurrency}{self.productprice}</b></span>")
                html_content = html_content.replace("<span>827384</span>", f"<span>{self.productsku}</span>")
                html_content = html_content.replace("John Lewis", productseller)
                
                # Replace order totals
                html_content = html_content.replace("€200.00", f"{self.productcurrency}{self.productprice}")
                html_content = html_content.replace("€10.00", f"{self.productcurrency}{productshippingcost}")
                html_content = html_content.replace("€220.00", f"{self.productcurrency}{total_formatted}")

                # Generate a random order number
                order_number = f"{random.randint(10, 99)}-{random.randint(10000, 99999)}-{random.randint(10000, 99999)}"
                html_content = html_content.replace("79-91285-66371", order_number)

                # Save the updated HTML
                with open("receipt/updatedrecipies/updatedebayconf.html", "w", encoding="utf-8") as file:
                    file.write(html_content)

                # Set up email information
                sender_email = "eBay <noreply@ebay.shop>"
                subject = "Your purchase is confirmed"
                link = "https://ebay.com"

                from emails.choise import choiseView
                
                embed = discord.Embed(title="Choose email provider", description="Email is ready to send. Choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(owner_id, html_content, sender_email, subject, self.productname, self.productimagelink, link)
                await interaction.edit_original_response(embed=embed, view=view)
                
            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.edit_original_response(embed=embed)
        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
