
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

            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=discord.Color.from_str("#826bc2"))
            await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=False)

            with open("receipt/Fútbol Emotion.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Generate random reference number
            def generate_ref_number():
                return f"WWW {random.randint(100000000000, 999999999999)}"

            ref_number = generate_ref_number()

            # Format price with 2 decimals
            formatted_price = f"{productprice:.2f}"
            price_parts = formatted_price.split('.')
            price_whole = price_parts[0]
            price_decimal = price_parts[1]
            
            # Replace all placeholders
            html_content = html_content.replace("{name}", name if name else "Customer")
            html_content = html_content.replace("{ref_number}", ref_number)
            html_content = html_content.replace("{imagelink}", imagelink)
            html_content = html_content.replace("{productname}", productname)
            html_content = html_content.replace("{price_whole}", price_whole)
            html_content = html_content.replace("{price_decimal}", price_decimal)
            html_content = html_content.replace("{currency}", currency)
            html_content = html_content.replace("{productsize}", productsize)
            html_content = html_content.replace("{total_price}", formatted_price)

            with open("receipt/updatedrecipies/updatedfutbolemotion.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            from emails.choise import choiseView
            sender_email = "Fútbol Emotion"
            subject = "Your Fútbol Emotion order has been shipped."
            link = "https://futbolemotion.com/"

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=discord.Color.from_str("#826bc2"))
            view = choiseView(owner_id, html_content, sender_email, subject, productname, imagelink, link)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)
