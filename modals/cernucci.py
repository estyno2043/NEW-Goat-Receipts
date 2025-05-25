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

def is_cernucci_link(link):
    cernucci_pattern = re.compile(r'^https?://((www\.|eu\.)?cernucci\.com|cernucci\.(eu|co\.uk|de|fr|it|es))/.+')
    return bool(cernucci_pattern.match(link))

class cernuccimodal(ui.Modal, title="discord.gg/goatreceipts"):
    Link = discord.ui.TextInput(label="Product link *", placeholder="https://cernucci.com/...", required=True)
    Price = discord.ui.TextInput(label="Price without currency *", placeholder="143", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £) *", placeholder="€", required=True, min_length=1, max_length=2)
    purchasedate = discord.ui.TextInput(label="Purchase date *", placeholder="5/4/2025", required=True)
    size = discord.ui.TextInput(label="Size *", placeholder="M", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)
            
            if user_details:
                name, street, city, zipp, country, email = user_details

                Link = self.Link.value
                Price = self.Price.value
                currency = self.currency.value
                purchasedate = self.purchasedate.value
                size = self.size.value

                if not is_cernucci_link(Link):
                    embed = discord.Embed(title="Error - Invalid Cernucci link", description="Please provide a valid Cernucci link.")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                # Store data in global variables for next step
                global link, price, curr, purchase_date, size_value
                link = Link
                price = Price
                curr = currency
                purchase_date = purchasedate
                size_value = size

                from addons.nextsteps import NextstepCernucci
                embed = discord.Embed(title="Next Page", description="Click 'Next Page' to continue to the next set of inputs.")
                await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepCernucci(owner_id), ephemeral=False)
            else:
                # Handle case where no user details are found
                embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class cernuccimodal2(ui.Modal, title="Cernucci Receipt"):
    taxcost = discord.ui.TextInput(label="Tax cost *", placeholder="10.00", required=True)
    shippingcost = discord.ui.TextInput(label="Shipping cost *", placeholder="10.00", required=True)
    deliverydate = discord.ui.TextInput(label="Delivery date *", placeholder="10/4/2025", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global link, price, curr, purchase_date, size_value
        owner_id = interaction.user.id 

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(embed=embed, view=None)

            with open("receipt/cernucci.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            tax = float(self.taxcost.value)
            shipping = float(self.shippingcost.value)
            delivery_date = self.deliverydate.value

            # Zyte API setup for scraping
            url = link

            # Zyte API request
            api_response = requests.post(
                "https://api.zyte.com/v1/extract",
                auth=("a9abed72c425496584d422cfdba283d2", ""),
                json={
                    "url": url,
                    "browserHtml": True,
                    "product": True,
                    "productOptions": {"extractFrom": "browserHtml"},
                },
            )

            # Decode HTML data and parse it
            browser_html = api_response.json().get("browserHtml")
            soup = BeautifulSoup(browser_html, 'html.parser')
            print()
            print(f"[{Colors.green}START Scraping{lg}] Cernucci -> {interaction.user.id} ({interaction.user})" + lg)

            # Extract product data
            product_data = api_response.json().get("product")
            product_name = "Product Name not found"
            image_url = "Image URL not found"

            if product_data:
                product_name = product_data.get("name", product_name)
                image_url = product_data.get("mainImage", {}).get("url", image_url)

            # If product name not found in product data, try to extract from HTML
            if product_name == "Product Name not found":
                # Try to find product name in the page
                product_name_element = soup.find('h1', class_='product-title')
                if product_name_element:
                    product_name = product_name_element.text.strip()

            # If image URL not found in product data, try to extract from HTML
            if image_url == "Image URL not found":
                # Try to find image in the page
                image_element = soup.find('img', class_='product-image')
                if image_element and 'src' in image_element.attrs:
                    image_url = image_element['src']
                else:
                    # Try meta og:image as fallback
                    og_image = soup.find('meta', {'property': 'og:image'})
                    if og_image and 'content' in og_image.attrs:
                        image_url = og_image['content']

            print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {product_name}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {image_url}" + lg)
            print(f"[{Colors.green}Scraping DONE{lg}] Cernucci -> {interaction.user.id}" + lg)
            print()

            # Calculate total
            price_float = float(price)
            total = price_float + shipping + tax
            total = round(total, 2)

            # Generate order number
            order_number = f"CER{random.randint(10000, 99999)}"

            import sqlite3
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name, street, city, zipp, country FROM licenses WHERE owner_id = ?", (str(owner_id),))
            user_details = cursor.fetchone()
            name, street, city, zipp, country = user_details

            # Replace all placeholders in the HTML template
            html_content = html_content.replace("{productname}", product_name)

            # Handle product image
            fallback_image = "https://eu.cernucci.com/cdn/shop/products/MK077-BLK_MODEL_F_7e6e0bac-4c22-4b73-bb3c-da9bf8fd20d5_1000x.jpg"

            # If scraped image exists and is valid, use it; otherwise use fallback
            if image_url and image_url != "Image URL not found" and (image_url.startswith("http") or image_url.startswith("//")):
                html_content = html_content.replace("{imageurl}", image_url)
            else:
                html_content = html_content.replace("{imageurl}", fallback_image)

            # Replace customer data
            html_content = html_content.replace("{price}", price)
            html_content = html_content.replace("{size}", size_value)
            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{city}", city)
            html_content = html_content.replace("{zip}", zipp)
            html_content = html_content.replace("{country}", country)

            # Replace pricing data
            html_content = html_content.replace("{currency}", curr)
            html_content = html_content.replace("{total}", str(total))
            html_content = html_content.replace("{shippingcost}", str(shipping))
            html_content = html_content.replace("{taxcost}", str(tax))

            # Replace dates and order info
            html_content = html_content.replace("{purchasedate}", purchase_date)
            html_content = html_content.replace("{deliverydate}", delivery_date)
            html_content = html_content.replace("{ordernumber}", order_number)

            with open("receipt/updatedrecipies/updatedcernucci.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            from emails.choise import choiseView
            sender_email = "Cernucci <support@cernucci.com>"
            subject = f"Order #{order_number} confirmed"

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, product_name, image_url, link)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)