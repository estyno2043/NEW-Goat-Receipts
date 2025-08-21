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

def is_goat_link(link):
    goat_link_pattern = re.compile(r'^https?://(www\.)?goat\.com/.*$')
    return bool(goat_link_pattern.match(link))

class goat(ui.Modal, title="GOAT Receipt - Step 1"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="Air Jordan 1 Retro High OG", required=True)
    productsize = discord.ui.TextInput(label="Product Size", placeholder="US 10.5", required=True)
    sku = discord.ui.TextInput(label="SKU", placeholder="555088-134", required=True)
    productprice = discord.ui.TextInput(label="Product Price (without currency)", placeholder="250.00", required=True)
    shippingfee = discord.ui.TextInput(label="Shipping Fee (without currency)", placeholder="14.75", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
        view = GoatSecondModal(
            self.productname.value,
            self.productsize.value, 
            self.sku.value,
            self.productprice.value,
            self.shippingfee.value
        )
        await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=view, ephemeral=False)

class GoatSecondModal(ui.View):
    def __init__(self, productname, productsize, sku, productprice, shippingfee):
        super().__init__(timeout=300)
        self.productname = productname
        self.productsize = productsize
        self.sku = sku
        self.productprice = productprice
        self.shippingfee = shippingfee

    @ui.button(label="Continue", style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
        modal = GoatSecondModalForm(
            self.productname,
            self.productsize,
            self.sku,
            self.productprice,
            self.shippingfee
        )
        await interaction.response.send_modal(modal)

class GoatSecondModalForm(ui.Modal, title="GOAT Receipt - Step 2"):
    def __init__(self, productname, productsize, sku, productprice, shippingfee):
        super().__init__()
        self.productname = productname
        self.productsize = productsize
        self.sku = sku
        self.productprice = productprice
        self.shippingfee = shippingfee

        self.currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="$", required=True, min_length=1, max_length=2)
        self.applepay_ending = discord.ui.TextInput(label="Apple Pay ending 4 digits (optional)", placeholder="7369", required=False, max_length=4)
        self.imagelink = discord.ui.TextInput(label="Product Image Link", placeholder="https://cdn.discordapp.com/attachments/...", required=True)

        self.add_item(self.currency)
        self.add_item(self.applepay_ending)
        self.add_item(self.imagelink)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id

        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

        if user_details:
            name, street, city, zipp, country, email = user_details

            try:
                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
                await interaction.response.edit_message(content=f"{interaction.user.mention}", embed=embed, view=None)

                with open("receipt/goat.html", "r", encoding="utf-8") as file:
                    html_content = file.read()

                # Generate random 9-digit order number
                random_order_number = str(random.randint(100000000, 999999999))

                # Calculate total (product price + shipping fee + tax 3.24)
                try:
                    product_price_float = float(self.productprice)
                    shipping_fee_float = float(self.shippingfee)
                    tax = 3.24
                    total_paid = product_price_float + shipping_fee_float + tax
                    total_formatted = f"{total_paid:.2f}"
                except ValueError:
                    total_formatted = "0.00"

                # Use provided Apple Pay ending or default
                applepay_ending = self.applepay_ending.value if self.applepay_ending.value else "7369"

                # Replace placeholders in HTML
                html_content = html_content.replace("{randomnumbers}", random_order_number)
                html_content = html_content.replace("{productname}", self.productname)
                html_content = html_content.replace("{productsize}", self.productsize)
                html_content = html_content.replace("{SKU}", self.sku)
                html_content = html_content.replace("{currency}", self.currency.value)
                html_content = html_content.replace("{productprice}", self.productprice)
                html_content = html_content.replace("{shippingfee}", self.shippingfee)
                html_content = html_content.replace("{totalpaid}", total_formatted)
                html_content = html_content.replace("{applepayending}", applepay_ending)
                html_content = html_content.replace("{imagelink}", self.imagelink.value)
                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{country}", country)

                with open("receipt/updatedrecipies/updatedgoat.html", "w", encoding="utf-8") as file:
                    file.write(html_content)

                sender_email_spoofed = "GOAT <noreply@e.goat.com>"
                sender_email_normal = "GOAT <info@goat.com>"
                subject = f"Your GOAT order #{random_order_number}"

                from emails.choise import choiseView
                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(owner_id, html_content, sender_email_normal, subject, self.productname, self.imagelink.value, sender_email_spoofed)
                await interaction.edit_original_response(embed=embed, view=view)

            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.edit_original_response(embed=embed)

        else:
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.edit_original_response(embed=embed)

# Create a global variable to make the class accessible outside
goatmodal = goat