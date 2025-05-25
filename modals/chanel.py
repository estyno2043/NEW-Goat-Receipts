import asyncio
from base64 import b64decode
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
import time
import platform
import hashlib
from time import sleep
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from bs4 import BeautifulSoup
from pystyle import Colors
import requests

r = Colors.red
lg = Colors.light_gray

def is_chanel_link(link):
    chanel_link_pattern = re.compile(r'^https?://(www\.)?chanel\.com/.*$')
    return bool(chanel_link_pattern.match(link))

class chanelmodal(ui.Modal, title="discord.gg/goatreceipts"):
    Link = discord.ui.TextInput(label="Link", placeholder="https://chanel.com/...", required=True)
    price = discord.ui.TextInput(label="Price without Currency", placeholder="199.99", required=True)
    tax = discord.ui.TextInput(label="Tax", placeholder="19.99", required=True)
    shipping = discord.ui.TextInput(label="Shipping", placeholder="19.99", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)
            
            if user_details:
                name, street, city, zipp, country, email = user_details

            link = self.Link.value
            price = float(self.price.value)
            currency = self.currency.value
            tax = float(self.tax.value)
            shipping = float(self.shipping.value)

            if not is_chanel_link(link):
                embed = discord.Embed(title="Error - Invalid Chanel link", description="Please provide a valid Chanel link.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            try:
                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
                await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=False)

                with open("receipt/chanel.html", "r", encoding="utf-8") as file:
                    html_content = file.read()

                url = link
                response = requests.get(
                    url=url,
                    proxies={
                        "http": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                        "https": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                    },
                    verify='zyte-ca.crt' 
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    print(f"[{Colors.green}START Scraping{lg}] chanel -> {interaction.user.id} ({interaction.user})" + lg)

                    script_tag = soup.find('script', {'type': 'application/ld+json'})
                    if script_tag:
                        data = json.loads(script_tag.string)
                        pname = data.get('name', 'No product name')
                        image_url = data.get('image', 'No image URL')
                        print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {pname}" + lg)
                        print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {image_url}" + lg)
                    else:
                        pname = "None"
                        image_url = "None"

                    print(f"[{Colors.green}Scraping DONE{lg}] chanel -> {interaction.user.id}" + lg)

                def generate_order_number():
                    return str(random.randint(1000000000, 9999999999))

                order_number = generate_order_number()
                fulltotal = shipping + tax + price
                fulltotal = round(fulltotal, 2)

                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{country}", country)
                html_content = html_content.replace("{price}", str(price))
                html_content = html_content.replace("{tax}", str(tax))
                html_content = html_content.replace("{shipping}", str(shipping))
                html_content = html_content.replace("{currency}", currency)
                html_content = html_content.replace("{ordernumber}", order_number)
                html_content = html_content.replace("{total}", str(fulltotal))
                html_content = html_content.replace("{pname}", pname)
                html_content = html_content.replace("{imageurl}", image_url)

                with open("receipt/updatedrecipies/updatedchanel.html", "w", encoding="utf-8") as file:
                    file.write(html_content)

                sender_email = "CHANEL <orders@e-us.chanel.co.uk>"
                subject = f"Your CHANEL Order MP{order_number} confirmation"

                from emails.choise import choiseView
                owner_id = interaction.user.id
                link = "https://chanel.com"

                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(owner_id, html_content, sender_email, subject, pname, image_url, link)
                await interaction.edit_original_response(embed=embed, view=view)
            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.edit_original_response(embed=embed)
        else:
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)