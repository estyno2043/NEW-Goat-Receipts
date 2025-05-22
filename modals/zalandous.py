import asyncio
import json
import random
import re
import webbrowser
import discord
from discord.ui import Select
from discord import SelectOption, ui, app_commands

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

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from datetime import datetime, timedelta



from bs4 import BeautifulSoup

from pystyle import Colors


r = Colors.red
lg = Colors.light_gray



def is_zalando_link(link):
    # More permissive pattern to catch different variations of Zalando URLs
    zalando_pattern = re.compile(r'^https?://(www\.|m\.)?(zalando\.(com|co\.uk|de|at|fr|it|nl|es|se|dk|fi|no|ch|pl|be|ie|sk)|en\.zalando\.(com|de)|m\.zalando\.(com|co\.uk|de))(/.+)?', re.IGNORECASE)

    return bool(zalando_pattern.match(link))


class zalandomodal(ui.Modal, title="discord.gg/goatreceipt"):
    Link = discord.ui.TextInput(label="Link", placeholder="zalando.com link", required=True)
    Price = discord.ui.TextInput(label="Price without currency", placeholder="790,00", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    orderdate2 = discord.ui.TextInput(label="Orderdate", placeholder="24/07/2024", required=True)
    sizee = discord.ui.TextInput(label="Size", placeholder="US M")


    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, street, city, zipp, country FROM licenses WHERE owner_id = ?", (str(owner_id),))
        user_details = cursor.fetchone()

        if user_details:
            name, street, city, zipp, country = user_details

            Link = self.Link.value
            orderdate2 = self.orderdate2.value
            Price = self.Price.value
            currency = str(self.currency.value)
            

            if not is_zalando_link(Link):
                embed = discord.Embed(title="Error - Invalid Zalando link", description="Please provide a valid Zalando link.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return


            try:

                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
                await interaction.response.send_message(embed=embed) # Removed ephemeral=True to allow for edits later

                



                with open("receipt/zalandous.html", "r", encoding="utf-8") as file:
                    html_content = file.read()


                url = Link

                response = requests.get(
                    url=url,
                    proxies={
                        "http": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                        "https": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                    },
                    verify=False  # Disable SSL verification
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    print()
                    print(f"[{Colors.green}START Scraping{lg}] ZALANDO US -> {interaction.user.id} ({interaction.user})" + lg)

                    product_name = None
                    image_url = None


                    product_name_element = soup.find('h1', class_='voFjEy _2kjxJ6 m3OCL3 HlZ_Tf')
                    if product_name_element:
                        product_name = product_name_element.text.strip()
                    else:
                        product_name_element = soup.find('span', class_='EKabf7 R_QwOV')
                        if product_name_element:
                            product_name = product_name_element.text.strip()


                    image_url = soup.find('meta', {'property': 'og:image'})['content']
                    print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {image_url}" + lg)
                    print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {product_name}" + lg)

                    print(f"[{Colors.green}Scraping DONE{lg}] ZALANDO US -> {interaction.user.id}" + lg)
                    print()

                        

                    



                sizee = str(self.sizee.value)


                order_date = datetime.strptime(orderdate2, "%d/%m/%Y")
                delivery_date = order_date + timedelta(days=1)
                td_delivery_date = order_date + timedelta(days=4)



                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{orderdate}", orderdate2)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{size}", sizee)
                html_content = html_content.replace("{imageurl}", image_url)
                html_content = html_content.replace("{pname}", product_name)
                html_content = html_content.replace("{currency}", currency)
                html_content = html_content.replace("{price}", Price)
                html_content = html_content.replace("{deliverydate}", delivery_date.strftime("%d/%m/%Y"))
                html_content = html_content.replace("{tddeliverydate}", td_delivery_date.strftime("%d/%m/%Y"))


                

                with open("receipt/updatedrecipies/updatedzalandous.html", "w", encoding="utf-8") as file:
                    file.write(html_content)


                sender_email = "Zalando Team <noreply@zalando.com>"
                subject = f"Thank you for your order"
                from emails.choise import choiseView
                owner_id = interaction.user.id

                    
                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(owner_id, html_content, sender_email, subject, product_name, image_url, Link)
                await interaction.edit_original_response(embed=embed, view=view) # Changed from send_message to edit_original_response

            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.edit_original_response(embed=embed) # Changed from send_message to edit_original_response

        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)