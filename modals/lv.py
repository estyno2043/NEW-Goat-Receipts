import asyncio
import json
import queue
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



class lvmodal(ui.Modal, title="Louis Vuitton Receipt Generator"):
    Linklv = discord.ui.TextInput(label="Link", placeholder="Louis Vuitton EU link", required=True)
    ProductName = discord.ui.TextInput(label="Product Name", placeholder="Enter Product Name", required=True)
    Reference = discord.ui.TextInput(label="Reference Number", placeholder="Enter Reference Number", required=True)
    imglink = discord.ui.TextInput(label="Image Link (Discord Img)", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
    Price = discord.ui.TextInput(label="Price", placeholder="Enter price with currency (e.g. €1600)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)
        
        if user_details:
            name, street, city, zipp, country, email = user_details

            try:
                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
                await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=False)

                with open("receipt/lv.html", "r", encoding="utf-8") as file:
                    html_content = file.read()

                firstname = name
                cityzip = f"{city} {zipp}"

                html_content = html_content.replace("{fname}", firstname)
                html_content = html_content.replace("{fullname}", name)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{city}", cityzip)
                html_content = html_content.replace("{country}", country)

                # Get just the currency symbol from the price
                price_str = self.Price.value
                currency_symbol = ''.join(c for c in price_str if not (c.isdigit() or c == '.' or c == ','))
                # Get just the number from the price
                price_value = ''.join(c for c in price_str if c.isdigit() or c == '.' or c == ',')

                html_content = html_content.replace("{pname}", self.ProductName.value)
                html_content = html_content.replace("{pimage}", self.imglink.value)
                html_content = html_content.replace("{reference}", self.Reference.value)
                html_content = html_content.replace("{currency}", currency_symbol)
                html_content = html_content.replace("{total}", price_value)
                html_content = html_content.replace("{price}", price_value)

                with open("receipt/updatedrecipies/updatedlv.html", "w", encoding="utf-8") as file:
                    file.write(html_content)

                sender_email = "Louis Vuitton <customer.service@louisvuitton.com>"
                subject = "Your Louis Vuitton Order Has been Shipped"

                from emails.choise import choiseView
                view = choiseView(owner_id, html_content, sender_email, subject, self.ProductName.value, self.imglink.value, self.Linklv.value)
                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
                await interaction.edit_original_response(embed=embed, view=view)

            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.edit_original_response(embed=embed)

        else:
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)