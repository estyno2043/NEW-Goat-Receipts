import asyncio
import json
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





def is_tnf_link(link):
    tnf_pattern = re.compile(r'^https?://(www\.)?thenorthface\.(com|co\.uk|de|fr|it|es|ca|com\.au|jp|kr|cn)/.+')

    return bool(tnf_pattern.match(link))


class tnfmodal(ui.Modal, title="discord.gg/goatreceipts"):
    Linkff = discord.ui.TextInput(label="Link", placeholder="thenorthface.co.uk link", required=True)
    Priceff = discord.ui.TextInput(label="Price without currency", placeholder="Ex. 790", required=True)
    deliverydate = discord.ui.TextInput(label="Delivery Date", placeholder="Ex. 14/07/2024", required=True)
    currencyff = discord.ui.TextInput(label="Currency ($, €‚ £)", placeholder="€", required=True, min_length=1, max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        global Linkff , Priceff, currencyff, name, deliverydate, street, city, zipp, country
        from addons.nextsteps import Nextsteptnf
        owner_id = interaction.user.id 

        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

        if user_details:
            name, street, city, zipp, country, email = user_details

            Linkff = self.Linkff.value
            currencyff = self.currencyff.value
            Priceff = self.Priceff.value
            deliverydate = self.deliverydate.value

            if not is_tnf_link(Linkff):
                embed = discord.Embed(title="Error - Invalid  link", description="Please provide a valid The North Face link.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return


            embed = discord.Embed(title="You are almost done...", description="Complete the next steps to receive the receipt.")
            await interaction.response.send_message(content=f"{interaction.user.mention}",embed=embed, view=Nextsteptnf(owner_id), ephemeral=False)

        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)








class tnfmodal2(ui.Modal, title="The North Face Receipt"):
    Size = discord.ui.TextInput(label="Size", placeholder="Ex. XL", required=True)
    Color = discord.ui.TextInput(label="Color", placeholder="Black", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global Linkff , Priceff, currencyff, name, deliverydate, street, city, zipp, country
        owner_id = interaction.user.id 

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(content=None,embed=embed, view=None)



            with open("receipt/tnf.html", "r", encoding="utf-8") as file:
                html_content = file.read()



            url = Linkff

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
                print(f"[{Colors.green}START Scraping{lg}] THE NORTH FACE -> {interaction.user.id} ({interaction.user})" + lg)


                product_name = None
                pname = soup.find('div', {'class': 'product-info product-info-js'})
                if pname:
                    product_name_element = pname.find('h1', {'class': 'product-content-info-name product-info-js'})
                    if product_name_element:
                        product_name = product_name_element.text.strip()
                        print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {product_name}" + lg)
                
                # If product name not found with first method, try alternative methods
                if not product_name:
                    # Try og:title meta tag
                    og_title = soup.find('meta', {'property': 'og:title'})
                    if og_title and og_title.get('content'):
                        product_name = og_title['content']
                        print(f"    [{Colors.cyan}Scraping{lg}] Product Name (from og:title): {product_name}" + lg)
                    else:
                        # Fallback to a generic name
                        product_name = "The North Face Product"
                        print(f"    [{Colors.cyan}Scraping{lg}] Product Name: Using fallback name" + lg)

                image_url = None
                og_image = soup.find('meta', {'property': 'og:image'})
                if og_image and og_image.get('content'):
                    image_url = og_image['content']
                    print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {image_url}" + lg)
                else:
                    # Fallback image URL
                    image_url = "https://via.placeholder.com/300x300?text=The+North+Face"
                    print(f"    [{Colors.cyan}Scraping{lg}] Image URL: Using fallback image" + lg)

                print(f"[{Colors.green}Scraping DONE{lg}] THE NORTH FACE -> {interaction.user.id}" + lg)
                print()





            cityzip = f"{city} {zipp}"

            size = self.Size.value
            color = self.Color.value


            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{cityzip}", cityzip)
            html_content = html_content.replace("{country}", country)
            html_content = html_content.replace("{deliverydate}", deliverydate)

            html_content = html_content.replace("{price}", str(Priceff)) 

            html_content = html_content.replace("{imageurl}", str(image_url))
            html_content = html_content.replace("{productname}", product_name)
            html_content = html_content.replace("{color}", color)
            html_content = html_content.replace("{size}", size)
            html_content = html_content.replace("{link}", Linkff)




            html_content = html_content.replace("{currency}", str(currencyff)) 



            with open("receipt/updatedrecipies/updatedtnf.html", "w", encoding="utf-8") as file:
                file.write(html_content)


            sender_email = "The North Face <noreply@thenorthface.com>"
            subject = "Great! Order 25953667 has been placed"
            from emails.choise import choiseView
            owner_id = interaction.user.id


            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, product_name, image_url, Linkff)
            await interaction.edit_original_response(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)