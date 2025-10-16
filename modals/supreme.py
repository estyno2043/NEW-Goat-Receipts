import asyncio
import json
import random
import re
import discord
from discord.ui import TextInput, Modal, Select
from discord import SelectOption, ui
import os
import json as jsond
import time
import binascii
from uuid import uuid4
import requests
import sys
import platform
import os
import hashlib
from datetime import datetime

class suprememodal(ui.Modal, title="discord.gg/goatreceipts"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="Supreme Box Logo Hoodie", required=True)
    productsku = discord.ui.TextInput(label="Product SKU", placeholder="4033592", required=True)
    productsize = discord.ui.TextInput(label="Product Size", placeholder="M", required=True)
    productcurrency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    productprice = discord.ui.TextInput(label="Price without currency", placeholder="138.00", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, productsku, productsize, productcurrency, productprice, name, street, city, zipp, country
        from addons.nextsteps import NextstepSupreme
        owner_id = interaction.user.id 

        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

        if user_details:
            name, street, city, zipp, country, email = user_details

            productname = self.productname.value
            productsku = self.productsku.value
            productsize = self.productsize.value
            productcurrency = self.productcurrency.value
            productprice = self.productprice.value

            embed = discord.Embed(title="Next Page", description="Click 'Next Page' to continue to the next set of inputs.")
            await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepSupreme(owner_id), ephemeral=False)
        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class suprememodal2(ui.Modal, title="Supreme Receipt"):
    orderdate = discord.ui.TextInput(label="Order Date", placeholder="5/4/2025", required=True)
    shippingprice = discord.ui.TextInput(label="Shipping Price", placeholder="10.00", required=True)
    taxcost = discord.ui.TextInput(label="Tax Cost", placeholder="10.00", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, productsku, productsize, productcurrency, productprice, orderdate, shippingprice, taxcost
        owner_id = interaction.user.id 

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=discord.Color.from_str("#826bc2"))
            await interaction.response.edit_message(embed=embed, view=None)

            with open("receipt/supreme.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            orderdate = self.orderdate.value
            shippingprice = float(self.shippingprice.value)
            taxcost = float(self.taxcost.value)

            # Generate random order number
            order_number = str(random.randint(100000, 999999))

            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)
            
            if user_details:
                name, street, city, zipp, country, email = user_details

            # Calculate total
            product_price_float = float(productprice)
            total = product_price_float + shippingprice + taxcost
            total = round(total, 2)

            # Replace all placeholders in the HTML template
            # Replace all placeholders with actual values
            html_content = html_content.replace("{orderdate}", orderdate)
            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{ordernumber}", order_number)
            html_content = html_content.replace("{productname}", productname)
            html_content = html_content.replace("{productsku}", productsku)
            html_content = html_content.replace("{productsize}", productsize)
            html_content = html_content.replace("{currency}", productcurrency)
            html_content = html_content.replace("{productprice}", productprice)
            html_content = html_content.replace("{shippingprice}", str(shippingprice))
            html_content = html_content.replace("{taxcost}", str(taxcost))
            html_content = html_content.replace("{total}", str(total))

            with open("receipt/updatedrecipies/updatedsupreme.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            from emails.choise import choiseView
            sender_email = "Supreme <supreme@info.org>"
            subject = f"Supreme Order Confirmation - {order_number}"

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=discord.Color.from_str("#826bc2"))
            view = choiseView(owner_id, html_content, sender_email, subject, productname, "", "")
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)