import asyncio
from base64 import b64decode
import json
import random
import re
import webbrowser
import discord
from discord.ui import Select
from discord import SelectOption, ui, app_commands, Interaction

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





class ebayauthmodal(ui.Modal, title="discord.gg/goatreceipts"):
    pname = discord.ui.TextInput(label="Product Name", placeholder="Product Name", required=True)
    imageurl = discord.ui.TextInput(label="Image URL (Discord Image)", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
    price = discord.ui.TextInput(label="Price without currency", placeholder="100.00", required=True)
    tax = discord.ui.TextInput(label="Shipping without currency", placeholder="10.00", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)





    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)
            
            if user_details:
                name, street, city, zipp, country, email = user_details

            pname = self.pname.value
            imageurl = self.imageurl.value
            price = self.price.value
            tax = self.tax.value
            currency = self.currency.value



            try:


                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
                await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed)


                with open("receipt/ebayauth.html", "r", encoding="utf-8") as file:
                    html_content = file.read()



                html_content = html_content.replace("{imageurl}", imageurl)
                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{pname}", pname)
                html_content = html_content.replace("{currency}", currency)
                html_content = html_content.replace("{price}", price)
                html_content = html_content.replace("{shipping}", tax)













                with open("receipt/updatedrecipies/updatedebayauth.html", "w", encoding="utf-8") as file:
                    file.write(html_content)



                sender_email = "eBay <authentication@ebay.shop>"
                subject = f"Your item has been authenticated!"

                from emails.choise import choiseView
                owner_id = interaction.user.id
                link = "https://ebay.com"
                pname = "AUTHENTICATED"



                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(owner_id, html_content, sender_email, subject, pname, imageurl, link)
                await interaction.edit_original_response(embed=embed, view=view)
            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.edit_original_response(embed=embed)


        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)