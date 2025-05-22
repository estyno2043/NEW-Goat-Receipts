
import re
import discord
from discord import ui
from discord.ui import Select, Button, Modal, TextInput
import asyncio
from emails.choise import choiseView

class SamsungSecondModal(ui.Modal, title="Samsung Order - Step 2"):
    def __init__(self, productname, imagelink, productprice, currency, productsku):
        super().__init__(timeout=None)
        
        # Store first form values
        self.productname = productname
        self.imagelink = imagelink
        self.productprice = productprice
        self.currency = currency
        self.productsku = productsku
        
        # Second form fields
        self.ordernumber = ui.TextInput(
            label='Order Number',
            placeholder='SO12345678',
            required=True
        )
        self.orderdate = ui.TextInput(
            label='Order Date (DD/MM/YYYY)',
            placeholder='01/05/2023',
            required=True
        )
        self.deliverydate = ui.TextInput(
            label='Delivery Date (DD/MM/YYYY)',
            placeholder='05/05/2023',
            required=True
        )
        self.serialnumber = ui.TextInput(
            label='Serial Number',
            placeholder='SN12345678',
            required=True
        )
        self.taxcost = ui.TextInput(
            label='Tax Cost',
            placeholder='10.00',
            required=True
        )
        
        # Add items to the modal
        self.add_item(self.ordernumber)
        self.add_item(self.orderdate)
        self.add_item(self.deliverydate)
        self.add_item(self.serialnumber)
        self.add_item(self.taxcost)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        # Get user details from database
        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

        if user_details:
            # Handle both 6 and 7 value formats for backward compatibility
            if len(user_details) == 7:
                name, street, city, zip_code, country, phone_number, email = user_details
            elif len(user_details) == 6:
                name, street, city, zip_code, country, email = user_details
                phone_number = ""  # Default empty phone number if not provided
            
            # Create receipt
            with open("receipt/samsung.html", "r", encoding="utf-8") as file:
                html_content = file.read()
                
            # Replace placeholders
            html_content = html_content.replace("{productname}", self.productname)
            html_content = html_content.replace("{imagelink}", self.imagelink)
            html_content = html_content.replace("{productprice}", self.productprice)
            html_content = html_content.replace("{currency}", self.currency)
            html_content = html_content.replace("{productsku}", self.productsku)
            html_content = html_content.replace("{ordernumber}", self.ordernumber.value)
            html_content = html_content.replace("{orderdate}", self.orderdate.value)
            html_content = html_content.replace("{deliverydate}", self.deliverydate.value)
            html_content = html_content.replace("{serialnumber}", self.serialnumber.value)
            html_content = html_content.replace("{taxcost}", self.taxcost.value)
            
            # Replace user details
            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{city}", city)
            html_content = html_content.replace("{zip}", zip_code)
            html_content = html_content.replace("{country}", country)
            # Only replace phone number if it exists in the template
            if "{phonenumber}" in html_content:
                html_content = html_content.replace("{phonenumber}", phone_number)
            html_content = html_content.replace("ogucetdano@gmail.com", email)
            
            # Create receipt file
            receipt_filename = f"samsung_receipt_{owner_id}.html"
            with open(receipt_filename, "w", encoding="utf-8") as file:
                file.write(html_content)
                
            # Create email selection view
            view = discord.ui.View()
            
            # Create a select menu for email options
            email_select = Select(
                placeholder="Choose email type",
                options=[
                    discord.SelectOption(label="Normal Email", value="normal"),
                    discord.SelectOption(label="Spoofed Email", value="spoofed")
                ]
            )

            # Instead of using the Select menu and callback, use the choiseView directly
            sender_email = "SAMSUNG <noreply@samsung.com>"
            subject = "Samsung - Order Confirmed"
            link = "https://samsung.com/"
            
            # Create embed for final screen
            receipt_embed = discord.Embed(
                title="Samsung Receipt Generated",
                description="Your Samsung receipt has been generated successfully. You can now choose to send it via email.",
                color=0x0080FF
            )
            receipt_embed.add_field(name="Product", value=self.productname, inline=False)
            receipt_embed.add_field(name="Price", value=f"{self.currency} {self.productprice}", inline=True)
            receipt_embed.add_field(name="Tax", value=f"{self.currency} {self.taxcost}", inline=True)
            receipt_embed.add_field(name="Order Number", value=self.ordernumber.value, inline=False)
            
            # Create email provider selection view
            sender_email = "SAMSUNG <noreply@samsung.com>"
            subject = "Samsung - Order Confirmed"
            link = "https://samsung.com/"
            
            view = choiseView(owner_id, html_content, sender_email, subject, self.productname, self.imagelink, link)
            
            # Handle interaction response with better error management
            # Use a single response with all information instead of multiple attempts
            try:
                # First try to defer if not already deferred/responded
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                    await interaction.followup.send(embed=receipt_embed, view=view, ephemeral=True)
                else:
                    # If already responded to, use followup
                    await interaction.followup.send(embed=receipt_embed, view=view, ephemeral=True)
            except discord.errors.NotFound:
                # If interaction is completely expired, we can't do anything further
                print(f"Interaction expired for user {owner_id} in Samsung modal")
            except Exception as e:
                # Log any other errors for debugging
                print(f"Error sending Samsung receipt to user {owner_id}: {str(e)}")
                
            # No need to add these if already using choiseView
            # email_select.callback = email_callback 
            # view.add_item(email_select)
        else:
            try:
                # First try to defer if not already deferred/responded
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                    await interaction.followup.send("Please set up your credentials in settings first.", ephemeral=True)
                else:
                    # If already responded to, use followup
                    await interaction.followup.send("Please set up your credentials in settings first.", ephemeral=True)
            except discord.errors.NotFound:
                # If interaction is completely expired, we can't do anything further
                print(f"Interaction expired for user {owner_id} in Samsung modal")
            except Exception as e:
                # Log any other errors for debugging
                print(f"Error in Samsung modal credential check for user {owner_id}: {str(e)}")


class SamsungModal(ui.Modal, title="Samsung Order - Step 1"):
    def __init__(self):
        super().__init__(timeout=None)
        
        # First form fields
        self.productname = ui.TextInput(
            label='Product Name',
            placeholder='Samsung Galaxy S23 Ultra',
            required=True
        )
        self.imagelink = ui.TextInput(
            label='Product Image Link',
            placeholder='https://example.com/image.jpg',
            required=True,
            style=discord.TextStyle.paragraph
        )
        self.productprice = ui.TextInput(
            label='Product Price',
            placeholder='1199.99',
            required=True
        )
        self.currency = ui.TextInput(
            label='Currency',
            placeholder='$',
            required=True
        )
        self.productsku = ui.TextInput(
            label='Product SKU',
            placeholder='SM-S918BZKGEUB',
            required=True
        )
        
        # Add items to the modal
        self.add_item(self.productname)
        self.add_item(self.imagelink)
        self.add_item(self.productprice)
        self.add_item(self.currency)
        self.add_item(self.productsku)

    async def on_submit(self, interaction: discord.Interaction):
        # Get values from first form
        productname = self.productname.value
        imagelink = self.imagelink.value
        productprice = self.productprice.value
        currency = self.currency.value
        productsku = self.productsku.value
        
        # Store the data for later use
        await interaction.response.defer(ephemeral=True)
        
        # Create a button to show the second modal
        view = discord.ui.View()
        button = discord.ui.Button(label="Continue to Step 2", style=discord.ButtonStyle.primary)
        
        async def button_callback(button_interaction):
            # Create the second modal
            second_modal = SamsungSecondModal(productname, imagelink, productprice, currency, productsku)
            # Send the second modal when the button is clicked
            await button_interaction.response.send_modal(second_modal)
            
        button.callback = button_callback
        view.add_item(button)
        
        # Send a response with a button to continue
        embed = discord.Embed(
            title="Samsung Order - Step 1 Complete",
            description="Click the button below to continue to step 2.",
            color=0x0080FF
        )
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
