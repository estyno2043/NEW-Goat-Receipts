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





def is_arcteryx_link(link):
    arcteryx_link_pattern = re.compile(r'^https?://(www\.)?arcteryx\.com/.*$')
    return bool(arcteryx_link_pattern.match(link))


class arcteryxmodal(ui.Modal, title="discord.gg/goatreceipts"):
    Link = discord.ui.TextInput(label="Link", placeholder="https://arcteryx.com/...", required=True)
    price = discord.ui.TextInput(label="Price without Currency", placeholder="199.99", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    sizee = discord.ui.TextInput(label="Size", placeholder="US M", required=True)
    orderdate = discord.ui.TextInput(label="Orderdate (DD/MM/YYYY)", placeholder="06/06/2024", required=True)


    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id


        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

        if user_details:
            name, street, city, zipp, country, email = user_details


            link = self.Link.value
            price = self.price.value
            currency = self.currency.value
            sizee = self.sizee.value
            ordedate = self.orderdate.value


            if not is_arcteryx_link(link):
                embed = discord.Embed(title="Error - Invalid Arcteryx link", description="Please provide a valid Arcteryx link.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return



            try:


                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=discord.Color.from_str("#826bc2"))
                await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=False)


                with open("receipt/arcteryx.html", "r", encoding="utf-8") as file:
                    html_content = file.read()


                # Zyte API setup
                url = link

                response = requests.get(
                    url=url,
                    proxies={
                        "http": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                        "https": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                    },
                    verify=False  # Disable SSL verification to fix certificate errors
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    print()
                    print(f"[{Colors.green}START Scraping{lg}] Arcteryx -> {interaction.user.id} ({interaction.user})" + lg)

                    # Safely extract product name
                    pname_meta = soup.find('meta', {'property': 'og:title'})
                    pname = pname_meta.get('content', 'Unknown Product') if pname_meta else 'Unknown Product'
                    print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {pname}" + lg)

                    # Safely extract image URL
                    image_meta = soup.find('meta', {'property': 'og:image'})
                    image_url = image_meta.get('content', '') if image_meta else ''
                    print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {image_url}" + lg)


                    colorp = soup.find('span', class_='sc-93825a4d-1 jFqkUy qa--selected-option-colour')
                    if colorp:
                        color = colorp.text.strip()
                        print(f"    [{Colors.cyan}Scraping{lg}] Color: {color}" + lg)
                    else:
                        color = "None"



                    print(f"[{Colors.green}Scraping DONE{lg}] Arcteryx -> {interaction.user.id}" + lg)
                    print()



                def generate_order_number():
                    return str(random.randint(1000000000, 9999999999))  # Generiert eine Zahl zwischen 10000000 und 99999999

                # Bestellnummer generieren
                order_number = generate_order_number()

                # Store data for next modal
                import addons.nextsteps as nextsteps
                
                nextsteps.store[owner_id] = {
                    'link': link,
                    'price': price,
                    'currency': currency,
                    'sizee': sizee,
                    'ordedate': ordedate,
                    'pname': pname,
                    'image_url': image_url,
                    'color': color,
                    'order_number': order_number,
                    'name': name,
                    'street': street,
                    'city': city,
                    'zipp': zipp,
                    'country': country,
                    'email': email
                }

                from addons.nextsteps import NextstepArcteryx
                embed = discord.Embed(title="Continue to next step", description="Please continue to add shipping and tax information.", color=discord.Color.from_str("#826bc2"))
                view = NextstepArcteryx(owner_id)
                await interaction.edit_original_response(embed=embed, view=view)

            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.edit_original_response(embed=embed)

        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)


class arcteryxmodal2(ui.Modal, title="Arc'teryx - Shipping & Tax"):
    shipping = discord.ui.TextInput(label="Shipping Cost", placeholder="0.00", required=True)
    tax = discord.ui.TextInput(label="Tax Cost (12.00%)", placeholder="14.76", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id

        try:
            import addons.nextsteps as nextsteps

            if owner_id not in nextsteps.store:
                await interaction.response.send_message("Session expired. Please start over.", ephemeral=True)
                return

            # Get stored data
            data = nextsteps.store[owner_id]

            # Get new inputs with proper decimal formatting
            shipping = f"{float(self.shipping.value):.2f}"
            tax = f"{float(self.tax.value):.2f}"
            price = f"{float(data['price']):.2f}"

            # Calculate total
            total = float(price) + float(shipping) + float(tax)
            total_formatted = f"{total:.2f}"

            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=discord.Color.from_str("#826bc2"))
            await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=False)

            with open("receipt/arcteryx.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Replace all placeholders in the HTML template
            html_content = html_content.replace("{ordernumber}", data['order_number'])
            html_content = html_content.replace("{orderdate}", data['ordedate'])
            html_content = html_content.replace("{pname}", data['pname'])
            html_content = html_content.replace("{imageurl}", data['image_url'])
            html_content = html_content.replace("{color}", data['color'])
            html_content = html_content.replace("{size}", data['sizee'])
            html_content = html_content.replace("{currency}", data['currency'])
            html_content = html_content.replace("{price}", price)
            html_content = html_content.replace("{shipping_price}", shipping)
            html_content = html_content.replace("{tax_price}", tax)
            html_content = html_content.replace("{total}", total_formatted)

            # Replace user details
            html_content = html_content.replace("{name}", data['name'])
            html_content = html_content.replace("John Brown", data['name'])
            html_content = html_content.replace("{street}", data['street'])
            html_content = html_content.replace("651 Cedar Lane Los Angeles", data['street'])
            html_content = html_content.replace("{city}", data['city'])
            html_content = html_content.replace("Los Angeles", data['city'])
            html_content = html_content.replace("{zip}", data['zipp'])
            html_content = html_content.replace("78201", data['zipp'])
            html_content = html_content.replace("{country}", data['country'])

            with open("receipt/updatedrecipies/updatedarcteryx.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            sender_email = "Arc'teryx <noreply@arcteryx.org>"
            subject = f"Your Arc'teryx Order Is On Its Way"
            from emails.choise import choiseView

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=discord.Color.from_str("#826bc2"))
            view = choiseView(owner_id, html_content, sender_email, subject, data['pname'], data['image_url'], data['link'])
            await interaction.edit_original_response(embed=embed, view=view)

            # Clean up stored data
            if owner_id in nextsteps.store:
                del nextsteps.store[owner_id]

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)