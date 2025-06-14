
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

class jomashopmodal(ui.Modal, title="discord.gg/goatreceipts"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="Dandelion Embroidered Check Cashmere Scarf", required=True)
    productprice = discord.ui.TextInput(label="Product Price without currency", placeholder="198.00", required=True)
    shippingcost = discord.ui.TextInput(label="Shipping Cost without currency", placeholder="10.00", required=True)
    imagelink = discord.ui.TextInput(label="Image URL (Discord Image)", placeholder="https://cdn.discordapp.com/attachments/...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                name, street, city, zipp, country, email = user_details

                productname = self.productname.value
                productprice = float(self.productprice.value)
                shippingcost = float(self.shippingcost.value)
                imagelink = self.imagelink.value

                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
                await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=False)

                if not (re.match(r'^\d+(\.\d{1,2})?$', str(productprice))):
                    embed = discord.Embed(title="Error Jomashop - Invalid price format", description="Please use a valid format (e.g., 198.00) for product price.")
                    await interaction.edit_original_response(embed=embed)
                    return

                if not (re.match(r'^\d+(\.\d{1,2})?$', str(shippingcost))):
                    embed = discord.Embed(title="Error Jomashop - Invalid shipping format", description="Please use a valid format (e.g., 10.00) for shipping cost.")
                    await interaction.edit_original_response(embed=embed)
                    return

                with open("receipt/jomashop.html", "r", encoding="utf-8") as file:
                    html_content = file.read()

                print()
                print(f"[{Colors.green}START Scraping{lg}] JOMASHOP -> {interaction.user.id} ({interaction.user})" + lg)
                print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {productname}" + lg)
                print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {imagelink}" + lg)
                print(f"[{Colors.green}Scraping DONE{lg}] JOMASHOP -> {interaction.user.id} ({interaction.user})" + lg)
                print()

                address = f"{street}"
                citywzip = f"{city}, {zipp}"
                fulltotal = productprice + shippingcost
                fulltotal = round(fulltotal, 2)

                def generate_order_number():
                    return str(random.randint(10000000, 99999999))

                order_number = generate_order_number()

                # Safely replace values, converting None to empty string
                html_content = html_content.replace("{name}", name if name else "")
                html_content = html_content.replace("{address}", address if address else "")
                html_content = html_content.replace("{city}", city if city else "")
                html_content = html_content.replace("{zip}", zipp if zipp else "")
                html_content = html_content.replace("{country}", country if country else "")
                html_content = html_content.replace("{ordernumber}", order_number)
                html_content = html_content.replace("{productname}", productname)
                html_content = html_content.replace("{imagelink}", imagelink)
                html_content = html_content.replace("{productprice}", str(productprice))
                html_content = html_content.replace("{shippingcost}", str(shippingcost))
                html_content = html_content.replace("{fulltotal}", str(fulltotal))

                with open("receipt/updatedrecipies/updatedjomashop.html", "w", encoding="utf-8") as file:
                    file.write(html_content)

                from emails.choise import choiseView
                sender_email = "Jomashop <noreply@jomashop.com>"
                subject = f"We're processing your order W{order_number}"
                link = "https://jomashop.com/"

                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(owner_id, html_content, sender_email, subject, productname, imagelink, link)
                await interaction.edit_original_response(embed=embed, view=view)

            else:
                # Handle case where no user details are found
                embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)
