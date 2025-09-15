
import asyncio
import json
import random
import re
import webbrowser
import discord
from discord.ui import Select
from discord import SelectOption, ui, app_commands
from datetime import datetime

import hashlib
import sys

import os
import json as jsond  # json
import time  # sleep before exit
import binascii  # hex encoding
from uuid import uuid4

import requests  # gen random guid

import sys
import time
import platform
import os
import hashlib
from time import sleep
from datetime import datetime

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from bs4 import BeautifulSoup

from pystyle import Colors

r = Colors.red
lg = Colors.light_gray

class vwmodal(ui.Modal, title="Vivienne Westwood - Step 1"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="Pourpoint Jacket", required=True)
    productprice = discord.ui.TextInput(label="Product Price", placeholder="995.00", required=True)
    imagelink = discord.ui.TextInput(label="Image Link", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
    orderdate = discord.ui.TextInput(label="Order Date (DD/MM/YY)", placeholder="Ex. 9/10/2024", required=True)
    deliverydate = discord.ui.TextInput(label="Delivery Date (DD/MM/YY)", placeholder="Ex. 15/10/2024", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, productprice, imagelink, orderdate, deliverydate
        owner_id = interaction.user.id 

        try:
            # Respond immediately to prevent timeout
            await interaction.response.defer(ephemeral=False)
            
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                name, street, city, zipp, country, email = user_details

                productname = self.productname.value
                productprice = self.productprice.value
                imagelink = self.imagelink.value
                orderdate = self.orderdate.value
                deliverydate = self.deliverydate.value

                # Import NextstepVW after deferring to avoid timeout
                from addons.nextsteps import NextstepVW
                
                embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
                await interaction.followup.send(content=f"{interaction.user.mention}",embed=embed, view=NextstepVW(owner_id), ephemeral=False)
            else:
                # Handle case where no user details are found
                embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                pass  # If we can't send error message, just log it
            print(f"Error in VW modal: {str(e)}")

class vwmodal2(ui.Modal, title="Vivienne Westwood - Step 2"):
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    shippingprice = discord.ui.TextInput(label="Shipping Price", placeholder="10.00", required=True)
    productcolor = discord.ui.TextInput(label="Product Color", placeholder="Sage Green", required=True)
    productsize = discord.ui.TextInput(label="Product Size", placeholder="S", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, productprice, imagelink, orderdate, deliverydate
        owner_id = interaction.user.id 

        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                # Make sure we handle incomplete user details
                if len(user_details) >= 6:
                    name, street, city, zipp, country, email = user_details
                else:
                    # Handle case with missing fields
                    name = user_details[0] if len(user_details) > 0 else ""
                    street = user_details[1] if len(user_details) > 1 else ""
                    city = user_details[2] if len(user_details) > 2 else ""
                    zipp = user_details[3] if len(user_details) > 3 else ""
                    country = user_details[4] if len(user_details) > 4 else ""
                    email = user_details[5] if len(user_details) > 5 else ""
            else:
                # Set default empty values if no user details found
                name = street = city = zipp = country = email = ""

            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(embed=embed, view=None)

            if not (re.match(r'^\d+(\.\d{1,2})?$', self.shippingprice.value)):
                embed = discord.Embed(title="Error VW - Invalid shipping format", description="Please use a valid format (e.g., 12.94) for Vivienne Westwood Shipping Fee.")
                await interaction.response.edit_message(embed=embed, ephemeral=True)
                return

            currency = self.currency.value
            shippingprice = float(self.shippingprice.value)
            productcolor = self.productcolor.value
            productsize = self.productsize.value
            productprice_float = float(productprice)

            with open("receipt/vw.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            print()
            print(f"[{Colors.green}START Processing{lg}] VIVIENNE WESTWOOD -> {interaction.user.id} ({interaction.user})" + lg)
            print(f"    [{Colors.cyan}Processing{lg}] Product Name: {productname}" + lg)
            print(f"    [{Colors.cyan}Processing{lg}] Product Color: {productcolor}" + lg)
            print(f"    [{Colors.cyan}Processing{lg}] Product Size: {productsize}" + lg)
            print(f"    [{Colors.cyan}Processing{lg}] Image URL: {imagelink}" + lg)

            print(f"[{Colors.green}Processing DONE{lg}] VIVIENNE WESTWOOD -> {interaction.user.id} ({interaction.user})" + lg)
            print()

            # Calculate total
            total_price = productprice_float + shippingprice
            total_price = round(total_price, 2)

            def generate_order_number():
                return f"VW-VW{random.randint(100000000, 999999999)}"

            # Generate order number
            order_number = generate_order_number()

            # Safely replace values, converting None to empty string
            html_content = html_content.replace("{name}", name if name else "")
            html_content = html_content.replace("{street}", street if street else "")
            html_content = html_content.replace("{city}", city if city else "")
            html_content = html_content.replace("{zip}", zipp if zipp else "")
            html_content = html_content.replace("{state}", country if country else "")
            html_content = html_content.replace("{user_email}", email if email else "")
            html_content = html_content.replace("{order_number}", order_number)
            html_content = html_content.replace("{order_date}", orderdate)
            html_content = html_content.replace("{delivery_date}", deliverydate)
            html_content = html_content.replace("{product_name}", productname)
            html_content = html_content.replace("{product_price}", f"{productprice_float:.2f}")
            html_content = html_content.replace("{currency}", currency)
            html_content = html_content.replace("{shipping_price}", f"{shippingprice:.2f}")
            html_content = html_content.replace("{shipping}", f"{shippingprice:.2f}")
            html_content = html_content.replace("{total_price}", f"{total_price:.2f}")
            html_content = html_content.replace("{imagelink}", imagelink)
            html_content = html_content.replace("{productcolor}", productcolor)
            html_content = html_content.replace("{product_size}", productsize)

            with open("receipt/updatedrecipies/updatedvw.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            from emails.choise import choiseView
            sender_email = "Vivienne Westwood <noreply@viviennewestwood.com>"
            subject = "Thank you for your order"
            link = "https://www.viviennewestwood.com/"

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, productname, imagelink, link)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)
