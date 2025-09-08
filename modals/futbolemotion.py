
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


class futbolemotionmodal(ui.Modal, title="discord.gg/goatreceipts"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="Chuteira F50 Elite LL FG Core Black", required=True)
    productprice = discord.ui.TextInput(label="Product Price", placeholder="159.99", required=True)
    currency = discord.ui.TextInput(label="Currency (€, $, £)", placeholder="€", required=True, min_length=1, max_length=2)
    productsize = discord.ui.TextInput(label="Product Size (UK)", placeholder="6.5 UK", required=True)
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
            currency = self.currency.value
            productsize = self.productsize.value
            imagelink = self.imagelink.value

            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=False)

            with open("receipt/Fútbol Emotion.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Generate random reference number
            def generate_ref_number():
                return f"WWW {random.randint(100000000000, 999999999999)}"

            ref_number = generate_ref_number()

            # Format price with 2 decimals
            formatted_price = f"{productprice:.2f}"
            
            # Replace placeholders
            html_content = html_content.replace("Gonçalo", name if name else "Customer")
            html_content = html_content.replace("WWW 202500216175", ref_number)
            
            # Replace product details
            html_content = re.sub(r'<img src="[^"]*" style="width:100%;font-family:&quot;Open Sans&quot;,Verdana,Arial" alt="[^"]*" class="CToWUd" data-bit="iit">', 
                                 f'<img src="{imagelink}" style="width:100%;font-family:&quot;Open Sans&quot;,Verdana,Arial" alt="{productname}" class="CToWUd" data-bit="iit">', html_content)
            
            # Replace price
            html_content = re.sub(r'<span style="font-family:&quot;Open Sans&quot;,Verdana,Arial">159</span><span style="font-family:&quot;Open Sans&quot;,Verdana,Arial">.</span><span style="font-family:&quot;Open Sans&quot;,Verdana,Arial">99</span><span style="font-family:&quot;Open Sans&quot;,Verdana,Arial">&nbsp;€</span>', 
                                 f'<span style="font-family:&quot;Open Sans&quot;,Verdana,Arial">{int(productprice)}</span><span style="font-family:&quot;Open Sans&quot;,Verdana,Arial">.</span><span style="font-family:&quot;Open Sans&quot;,Verdana,Arial">{str(productprice).split(".")[1].ljust(2, "0")}</span><span style="font-family:&quot;Open Sans&quot;,Verdana,Arial">&nbsp;{currency}</span>', html_content)
            
            # Replace product name
            html_content = re.sub(r'<b style="font-family:&quot;Open Sans&quot;,Verdana,Arial">Chuteira F50 Elite LL FG Core Black-Iron Met-Gold Met</b>', 
                                 f'<b style="font-family:&quot;Open Sans&quot;,Verdana,Arial">{productname}</b>', html_content)
            
            # Replace size
            html_content = re.sub(r'Tamanho: 6,5 UK', f'Tamanho: {productsize}', html_content)
            
            # Replace shipping currency
            html_content = re.sub(r'<span>0</span><span>&nbsp;€</span>', f'<span>0</span><span>&nbsp;{currency}</span>', html_content)
            
            # Replace total price
            html_content = re.sub(r'<span style="font-family:Arial,sans-serif">159.99</span><span style="font-family:Arial,sans-serif">&nbsp;€</span>', 
                                 f'<span style="font-family:Arial,sans-serif">{formatted_price}</span><span style="font-family:Arial,sans-serif">&nbsp;{currency}</span>', html_content)

            with open("receipt/updatedrecipies/updatedfutbolemotion.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            from emails.choise import choiseView
            sender_email = "Fútbol Emotion <web@futbolemotion.com>"
            subject = "Your Fútbol Emotion order has been shipped."
            link = "https://futbolemotion.com/"

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, productname, imagelink, link)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)
