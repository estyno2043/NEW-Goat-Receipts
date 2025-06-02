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





def is_end_link(link):
    cooblue_link_pattern = re.compile(r'^https?://(www\.)?endclothing\.com/.*$')
    return bool(cooblue_link_pattern.match(link))


class endmodal(ui.Modal, title="discord.gg/goatreceipts"):
    Link = discord.ui.TextInput(label="Link", placeholder="https://endclothing.com/...", required=True)
    imageurl = discord.ui.TextInput(label="Image URL (Discord Image)", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
    price = discord.ui.TextInput(label="Price", placeholder="120.00", required=True)
    size = discord.ui.TextInput(label="Size", placeholder="M", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)



    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)
            
            if user_details:
                name, street, city, zipp, country, email = user_details
            else:
                embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            link = self.Link.value
            price = self.price.value
            currency = self.currency.value
            size = self.size.value
            imageurl = self.imageurl.value





            

            if not is_end_link(link):
                embed = discord.Embed(title="Error - Invalid END link", description="Please provide a valid END link.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return


            
            try:


                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
                await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=False)


                with open("receipt/end.html", "r", encoding="utf-8") as file:
                    html_content = file.read()


                # Zyte API setup
                url = link

                response = requests.get(
                    url=url,
                    proxies={
                        "http": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                        "https": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                    },
                    verify=False 
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    print()
                    print(f"[{Colors.green}START Scraping{lg}] END -> {interaction.user.id} ({interaction.user})" + lg)

                    # More robust way to find product name using various possible class patterns
                    product_elem = soup.find('span', {'class': 'ProductDetails__ProductTitleSC-sc-1fqzeck-2 fpohwF'})
                    if not product_elem:
                        # Try alternative selectors if the original one doesn't work
                        product_elem = soup.find('h1', {'class': lambda c: c and 'ProductTitle' in c})
                        if not product_elem:
                            product_elem = soup.find('h1', {'data-test': 'product-title'})
                            if not product_elem:
                                # Fallback to link title if we can't find any product title
                                productname = link.split('/')[-1].replace('-', ' ').title()
                                print(f"    [{Colors.cyan}Scraping{lg}] Product Name (fallback): {productname}" + lg)
                            else:
                                productname = product_elem.text.strip()
                                print(f"    [{Colors.cyan}Scraping{lg}] Product Name (data-test): {productname}" + lg)
                        else:
                            productname = product_elem.text.strip()
                            print(f"    [{Colors.cyan}Scraping{lg}] Product Name (class contains ProductTitle): {productname}" + lg)
                    else:
                        productname = product_elem.text.strip()
                        print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {productname}" + lg)

                    print(f"[{Colors.green}Scraping DONE{lg}] END -> {interaction.user.id}" + lg)
                    print()



                def generate_order_number():
                    return str(random.randint(1000000000, 9999999999))  # Generiert eine Zahl zwischen 10000000 und 99999999

                # Bestellnummer generieren
                order_number = generate_order_number()


                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{country}", country)



                html_content = html_content.replace("{ordernumber}", order_number)
                html_content = html_content.replace("{pname}", productname)
                html_content = html_content.replace("{imageurl}", imageurl)
                html_content = html_content.replace("{price}", price)
                html_content = html_content.replace("{size}", size)
                html_content = html_content.replace("{currency}", currency)








                with open("receipt/updatedrecipies/updatedend.html", "w", encoding="utf-8") as file:
                    file.write(html_content)



                sender_email = "END <noreply@endclothing.com>"
                subject = f"Your END. order confirmation"

                from emails.choise import choiseView
                owner_id = interaction.user.id

                    
                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(owner_id, html_content, sender_email, subject, productname, imageurl, link)
                await interaction.edit_original_response(embed=embed, view=view)
            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.edit_original_response(embed=embed)

        except Exception as e:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)