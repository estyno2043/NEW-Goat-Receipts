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





def is_cooblue_link(link):
    cooblue_link_pattern = re.compile(r'^https?://(www\.)?coolblue\.de/.*$')
    return bool(cooblue_link_pattern.match(link))


class coolbluemodal(ui.Modal, title="discord.gg/goatreceipt"):
    Link = discord.ui.TextInput(label="Link", placeholder="https://cooblue.de/...", required=True)
    deliverydate = discord.ui.TextInput(label="Delivery Date (DD/MM/YYYY)", placeholder="06/03/2024", required=True)


    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 


        owner_id = interaction.user.id 

        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, street, city, zipp, country FROM licenses WHERE owner_id = ?", (str(owner_id),))
        user_details = cursor.fetchone()

        if user_details:
            name, street, city, zipp, country = user_details

            link = self.Link.value
            deliverydate = self.deliverydate.value



            

            if not is_cooblue_link(link):
                embed = discord.Embed(title="Error - Invalid Coolblue link", description="Please provide a valid Coolblue link.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return


            
            try:


                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
                await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=True)


                with open("receipt/coolblue.html", "r", encoding="utf-8") as file:
                    html_content = file.read()


                # Zyte API setup
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
                    print()
                    print(f"[{Colors.green}START Scraping{lg}] Coolblue -> {interaction.user.id} ({interaction.user})" + lg)

                    product_name = soup.find('meta', {'property': 'og:title'})['content']
                    print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {product_name}" + lg)

                    img_src = soup.find('meta', {'property': 'og:image'})['content']
                    print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {img_src}" + lg)


                    print(f"[{Colors.green}Scraping DONE{lg}] Coolblue -> {interaction.user.id}" + lg)
                    print()



                def generate_order_number():
                    return str(random.randint(1000000000, 9999999999))  # Generiert eine Zahl zwischen 10000000 und 99999999

                # Bestellnummer generieren
                order_number = generate_order_number()


                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{zip}", zipp)


                html_content = html_content.replace("{deliverydate}", deliverydate)
                html_content = html_content.replace("{ordernumber}", order_number)
                html_content = html_content.replace("{pname}", product_name)
                html_content = html_content.replace("{imageurl}", img_src)





                with open("receipt/updatedrecipies/updatedcoolblue.html", "w", encoding="utf-8") as file:
                    file.write(html_content)



                sender_email = "CoolBlue <noreply@coolblue.org>"
                subject = f"Order Confirmation {order_number} "

                from emails.choise import choiseView
                owner_id = interaction.user.id

                    
                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(owner_id, html_content, sender_email, subject, product_name, img_src, link)
                await interaction.edit_original_response(embed=embed, view=view)
            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.edit_original_response(embed=embed)

        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)