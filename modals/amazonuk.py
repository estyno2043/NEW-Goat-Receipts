
import asyncio
from base64 import b64decode
import json
import re
import webbrowser
import discord
from discord.ui import Select
from discord import SelectOption, ui, app_commands, Interaction
from datetime import datetime

import hashlib
import sys

import os
import json as jsond  # json
import time  # sleep before exit
import binascii  # hex encoding
from uuid import uuid4

import requests  # gen random guid

from bs4 import BeautifulSoup
from pystyle import Colors

r = Colors.red
lg = Colors.light_gray

class AmazonUKModal(ui.Modal, title="Amazon UK Order Generator"):
    
    # Create alias for compatibility
    amazonukmodal = AmazonUKModal
    def __init__(self):
        super().__init__(timeout=None)
        
        # First form fields
        self.productname = ui.TextInput(
            label='Product Name',
            placeholder='Smart Watches for Men Fitness Tracker',
            required=True
        )
        self.condition = ui.TextInput(
            label='Condition',
            placeholder='New',
            required=True
        )
        self.productprice = ui.TextInput(
            label='Product Price',
            placeholder='49.99',
            required=True
        )
        self.productcurrency = ui.TextInput(
            label='Product Currency',
            placeholder='€',
            required=True
        )
        self.productarrivaldate = ui.TextInput(
            label='Product Arrival Date',
            placeholder='6/5/2025',
            required=True
        )
        
        # Add items to the modal
        self.add_item(self.productname)
        self.add_item(self.condition)
        self.add_item(self.productprice)
        self.add_item(self.productcurrency)
        self.add_item(self.productarrivaldate)

    async def on_submit(self, interaction: discord.Interaction):
        # Get values from the first form
        productname = self.productname.value
        condition = self.condition.value
        productprice = self.productprice.value
        productcurrency = self.productcurrency.value
        productarrivaldate = self.productarrivaldate.value
        
        # Instead of opening a second modal directly, send an ephemeral message with a button
        embed = discord.Embed(
            title="Product Details Submitted",
            description="Please click the button below to enter the product image link",
            color=0x1e1f22
        )
        
        # Create a view with a button to open the second modal
        class ImageLinkButton(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=None)
            
            @discord.ui.button(label="Add Image Link", style=discord.ButtonStyle.primary)
            async def image_button(self, button_interaction: discord.Interaction, button):
                if button_interaction.user.id != interaction.user.id:
                    await button_interaction.response.send_message("This is not your form.", ephemeral=True)
                    return
                
                # Create and show the second form
                second_form = AmazonUKSecondModal(
                    productname=productname,
                    condition=condition,
                    productprice=productprice,
                    productcurrency=productcurrency,
                    productarrivaldate=productarrivaldate
                )
                await button_interaction.response.send_modal(second_form)
        
        # Send the message with the button
        await interaction.response.send_message(embed=embed, view=ImageLinkButton(), ephemeral=True)

class AmazonUKSecondModal(ui.Modal, title='Amazon UK Order - Part 2'):
    def __init__(self, productname, condition, productprice, productcurrency, productarrivaldate):
        super().__init__(timeout=None)
        
        # Store first form values
        self.productname = productname
        self.condition = condition
        self.productprice = productprice
        self.productcurrency = productcurrency
        self.productarrivaldate = productarrivaldate
        
        # Second form fields
        self.productimagelink = ui.TextInput(
            label='Product Image Link',
            placeholder='https://example.com/image.jpg',
            required=True
        )
        
        # Add items to the modal
        self.add_item(self.productimagelink)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)
        
        # Get user details from database
        owner_id = interaction.user.id
        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)
        
        if user_details:
            name, street, city, zipp, country, email = user_details
            
            try:
                # Open and read the HTML template
                with open("receipt/amazonuk.html", "r", encoding="utf-8") as file:
                    html_content = file.read()
                
                # Get values from the forms
                productname = self.productname
                condition = self.condition
                productprice = self.productprice
                productcurrency = self.productcurrency
                productarrivaldate = self.productarrivaldate
                productimagelink = self.productimagelink.value
                
                print()
                print(f"[{Colors.green}START Scraping{lg}] Amazon UK -> {interaction.user.id} ({interaction.user})" + lg)
                print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {productname}" + lg)
                print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {productimagelink}" + lg)
                print(f"[{Colors.green}Scraping DONE{lg}] Amazon UK -> {interaction.user.id}" + lg)
                print()
                
                # Replace placeholders in HTML
                html_content = html_content.replace("{productarrivaldate}", productarrivaldate)
                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{country}", country)
                html_content = html_content.replace("{productname}", productname)
                html_content = html_content.replace("{condition}", condition)
                html_content = html_content.replace("{productprice}", productprice)
                html_content = html_content.replace("{productcurrency}", productcurrency)
                html_content = html_content.replace("{imageurl}", productimagelink)
                html_content = html_content.replace("{pname}", productname)
                
                # Create directory for the updated receipt if not exists
                import os
                os.makedirs("receipt/updatedrecipies", exist_ok=True)
                
                # Save the updated HTML
                with open("receipt/updatedrecipies/updatedamazonuk.html", "w", encoding="utf-8") as file:
                    file.write(html_content)
                
                # Set up email information
                sender_email = "Amazon <auto-confirm@amazon.co.uk>"
                subject = "Your Amazon.co.uk order."
                link = "https://www.amazon.co.uk/"
                
                # Send the generated receipt
                from emails.choise import choiseView
                
                embed = discord.Embed(title="Choose email provider", description="Email is ready to send. Choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(owner_id, html_content, sender_email, subject, productname, productimagelink, link)
                await interaction.followup.send(embed=embed, view=view)
                
            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.followup.send(embed=embed)
                
        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.followup.send(embed=embed)
