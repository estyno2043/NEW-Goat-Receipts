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



def is_apple_link(link):
    apple_pattern = re.compile(r'^https?://(www\.)?apple\.com/.+')

    return bool(apple_pattern.match(link))


class applemodal(ui.Modal, title="discord.gg/goatreceipts"):
    Price = discord.ui.TextInput(label="Price without currency", placeholder="790", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    orderdate = discord.ui.TextInput(label="Orderdate (DD/MM/YY)", placeholder="Ex. 9/10/2024", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global Price, currency, name, orderdate, street , city, zipp, country
        owner_id = interaction.user.id 

        try:
            # Respond immediately to prevent timeout
            await interaction.response.defer(ephemeral=False)
            
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                name, street, city, zipp, country, email = user_details

                currency = self.currency.value
                Price = float(self.Price.value)
                orderdate = self.orderdate.value

                # Import NextstepApple after deferring to avoid timeout
                from addons.nextsteps import NextstepApple
                
                embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
                await interaction.followup.send(content=f"{interaction.user.mention}",embed=embed, view=NextstepApple(owner_id), ephemeral=False)
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
            print(f"Error in Apple modal: {str(e)}")









class applemodal2(ui.Modal, title="Apple Receipt"):
    Pname = discord.ui.TextInput(label="Product Name", placeholder="Apple Macbook Pro", required=True)
    imgurl = discord.ui.TextInput(label="Image URL (Discord Image)", placeholder="https://cdn.discordapp.com/attachments/10869879156.....", required=True)
    Shipping = discord.ui.TextInput(label="Shipping without currency", placeholder="13.96", required=True)
    # Street = discord.ui.TextInput(label="Street", placeholder="Musterstraße 12", required=True)
    # Citywzip = discord.ui.TextInput(label="City with Zip", placeholder="Berlin 10115", required=True)
    # Country = discord.ui.TextInput(label="Country", placeholder="Germany", required=True)


    async def on_submit(self, interaction: discord.Interaction):
        global Price, currency, name, orderdate
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


            if not (re.match(r'^\d+(\.\d{1,2})?$', self.Shipping.value)):
                embed = discord.Embed(title="Error Apple - Invalid shipping format", description="Please use a valid format (e.g., 12.94) for Apple Shipping Fee.")
                await interaction.response.edit_message(embed=embed, ephemeral=True)
                return

            shipping = float(self.Shipping.value)




            with open("receipt/apple.html", "r", encoding="utf-8") as file:
                html_content = file.read()



            product_name = self.Pname.value
            image_url = self.imgurl.value

            print()
            print(f"[{Colors.green}START Scraping{lg}] APPLE -> {interaction.user.id} ({interaction.user})" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {product_name}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {image_url}" + lg)

            print(f"[{Colors.green}Scraping DONE{lg}] APPLE -> {interaction.user.id} ({interaction.user})" + lg)
            print()








            Citywzip = f"{city} {zipp}"

            fulltotal = shipping + Price
            fulltotal = round(fulltotal, 2)

            def generate_order_number():
                return str(random.randint(1000000000, 9999999999))  # Generiert eine Zahl zwischen 10000000 und 99999999

            # Bestellnummer generieren
            order_number = generate_order_number()


            # Safely replace values, converting None to empty string
            html_content = html_content.replace("{name}", name if name else "")
            html_content = html_content.replace("{street}", street if street else "")
            html_content = html_content.replace("{ordernumber}", order_number)
            html_content = html_content.replace("{citywzip}", Citywzip if Citywzip else "")
            html_content = html_content.replace("{country}", country if country else "")
            html_content = html_content.replace("{orderdate}", orderdate)
            html_content = html_content.replace("{shipping}", str(shipping))
            html_content = html_content.replace("{fulltotal}", str(fulltotal))
            html_content = html_content.replace("{pimg}", str(image_url))
            html_content = html_content.replace("{pname}", str(product_name))
            html_content = html_content.replace("{currency}", currency if currency else "$") 
            html_content = html_content.replace("{total}", str(Price))


            with open("receipt/updatedrecipies/updatedapple.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            from emails.choise import choiseView
            sender_email = "Apple <noreply@apple.com>"
            subject = f"We're processing your order W9701012238"
            link = "https://apple.com/"


            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, product_name, image_url, link)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)