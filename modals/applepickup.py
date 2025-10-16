import asyncio
import json
import random
import re
import discord
from discord.ui import Modal, TextInput
from discord import ui, app_commands
from datetime import datetime

import os
import time
from uuid import uuid4

import requests

import sys
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

class applepickupmodal(ui.Modal, title="Apple Pickup Receipt - Step 1"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="AirPods Pro", required=True)
    productimagelink = discord.ui.TextInput(label="Product Image Link", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
    orderdate = discord.ui.TextInput(label="Order Date", placeholder="9/9/2025", required=True)
    productprice = discord.ui.TextInput(label="Product Price", placeholder="133", required=True)
    taxcost = discord.ui.TextInput(label="Tax Cost", placeholder="12", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        from addons.nextsteps import NextstepApplepickup
        owner_id = interaction.user.id 

        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)
        
        if user_details:
            name, street, city, zipp, country, email = user_details

            # Store data in global variables for next step
            global productname, productimagelink, orderdate, productprice, taxcost
            productname = self.productname.value
            productimagelink = self.productimagelink.value
            orderdate = self.orderdate.value
            productprice = self.productprice.value
            taxcost = self.taxcost.value

            embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
            await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepApplepickup(owner_id), ephemeral=False)
        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class applepickupmodal2(ui.Modal, title="Apple Pickup Receipt - Step 2"):
    productcurrency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="$", required=True, min_length=1, max_length=1)
    taxpercent = discord.ui.TextInput(label="Tax Percent", placeholder="10", required=True)
    storestreet = discord.ui.TextInput(label="Store Street", placeholder="Orange Blossom", required=True)
    storephone = discord.ui.TextInput(label="Store Phone", placeholder="0977893123", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, productimagelink, orderdate, productprice, taxcost
        owner_id = interaction.user.id
        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                name, street, city, zipp, country, email = user_details

                # Display processing message
                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=discord.Color.from_str("#826bc2"))
                await interaction.response.edit_message(embed=embed, view=None)

                # Load HTML template
                with open("receipt/applepickup.html", "r", encoding="utf-8") as file:
                    html_content = file.read()

                # Get values from form
                productcurrency = self.productcurrency.value
                taxpercent = self.taxpercent.value
                storestreet = self.storestreet.value
                storephone = self.storephone.value #Fixed typo here

                # Print scraping info for debugging
                print()
                print(f"[{Colors.green}START Processing{lg}] Apple Pickup -> {interaction.user.id} ({interaction.user})" + lg)
                print(f"    [{Colors.cyan}Processing{lg}] Product Name: {productname}" + lg)
                print(f"    [{Colors.cyan}Processing{lg}] Image URL: {productimagelink}" + lg)
                print(f"[{Colors.green}Processing DONE{lg}] Apple Pickup -> {interaction.user.id}" + lg)
                print()

                # Calculate total
                price_float = float(productprice)
                tax_float = float(taxcost)
                total = price_float + tax_float
                total = round(total, 2)

                # Replace all placeholders in the HTML template
                html_content = html_content.replace("{orderdate}", orderdate)
                html_content = html_content.replace("{productname}", productname)
                html_content = html_content.replace("{productcurrency}", productcurrency)
                html_content = html_content.replace("{productprice}", productprice)
                html_content = html_content.replace("{storestreet}", storestreet)
                html_content = html_content.replace("{storephone}", storephone)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{country}", country)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{email}", email if email else "")
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{taxpercent}", taxpercent)
                html_content = html_content.replace("{taxcost}", taxcost)
                html_content = html_content.replace("{ordertotal}", str(total))

                # Calculate total cost
                tax_amount = float(productprice) * (float(taxpercent) / 100)
                taxcost = round(tax_amount, 2)
                total = float(productprice) + tax_amount
                total = round(total, 2)

                # Replace all placeholders in the HTML
                html_content = html_content.replace("{orderdate}", orderdate)
                html_content = html_content.replace("{productimagelink}", productimagelink)
                html_content = html_content.replace("{productname}", productname)
                html_content = html_content.replace("{productcurrency}", productcurrency)
                html_content = html_content.replace("{productprice}", productprice)
                html_content = html_content.replace("{storestreet}", storestreet)
                html_content = html_content.replace("{storephone}", storephone)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{country}", country)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{email}", email)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{taxpercent}", taxpercent)
                html_content = html_content.replace("{taxcost}", str(taxcost))
                html_content = html_content.replace("{total}", str(total))

                # Save updated HTML
                with open("receipt/updatedrecipies/updatedapplepickup.html", "w", encoding="utf-8") as file:
                    file.write(html_content)

                # Prepare email
                from emails.choise import choiseView
                sender_email = "Apple <noreply@apple.com>"
                subject = f"We're processing your order W886012551"
                link = "https://apple.com/"

                # Display email options
                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=discord.Color.from_str("#826bc2"))
                view = choiseView(owner_id, html_content, sender_email, subject, productname, productimagelink, link)
                await interaction.edit_original_response(embed=embed, view=view)
            else:
                embed = discord.Embed(title="Error", description=f"Could not retrieve user details.")
                await interaction.edit_original_response(embed=embed)


        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)