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



class cartiermodal(ui.Modal, title="discord.gg/goatreceipts"):
    Price = discord.ui.TextInput(label="Price without currency", placeholder="790.00", required=True)
    shipping = discord.ui.TextInput(label="Shipping Costs", placeholder="10.00", required=True)
    tax = discord.ui.TextInput(label="Tax Costs", placeholder="10.00", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    delivery = discord.ui.TextInput(label="Delivery (DD/MM/YY)", placeholder="9/10/2024", required=True)



    async def on_submit(self, interaction: discord.Interaction):
        global Price, currency, name, delivery, street , city, zipp, country, tax, shipping
        from addons.nextsteps import Nextstepcartier
        owner_id = interaction.user.id 

        owner_id = interaction.user.id 

        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)
            
            if user_details:
                name, street, city, zipp, country, email = user_details

                currency = self.currency.value
                Price = float(self.Price.value)
                delivery = self.delivery.value
                tax = float(self.tax.value)
                shipping = float(self.shipping.value)



                embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
                await interaction.response.send_message(content=f"{interaction.user.mention}",embed=embed, view=Nextstepcartier(owner_id))
            else:
                # Handle case where no user details are found
                embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)






class cartiermodal2(ui.Modal, title="Cartier Receipt"):
    pname = discord.ui.TextInput(label="Product Name", placeholder="Trinity Ring", required=True)
    imageurl = discord.ui.TextInput(label="Image URL (Discord Image)", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
    size = discord.ui.TextInput(label="Size", placeholder="52", required=True)
    color = discord.ui.TextInput(label="Color (If none leave blank)", placeholder="Gold/Silver", required=False)




    async def on_submit(self, interaction: discord.Interaction):
        global Price, currency, name, delivery, street , city, zipp, country, tax, shipping
        owner_id = interaction.user.id 

        try:

            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(content=f"{interaction.user.mention}",embed=embed, view=None)





            with open("receipt/cartier.html", "r", encoding="utf-8") as file:
                html_content = file.read()



            product_name = self.pname.value
            size = self.size.value
            image_url = self.imageurl.value
            color = self.color.value




            print()
            print(f"[{Colors.green}START Scraping{lg}] cartier -> {interaction.user.id} ({interaction.user})" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {product_name}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {image_url}" + lg)
            print(f"[{Colors.green}Scraping DONE{lg}] cartier -> {interaction.user.id} ({interaction.user})" + lg)
            print()






            # Calculate total and ensure all values have 2 decimal places
            fulltotal = shipping + tax + Price
            fulltotal = round(fulltotal, 2)

            # Format all price values to show 2 decimal places
            price_formatted = f"{Price:.2f}"
            tax_formatted = f"{tax:.2f}"
            shipping_formatted = f"{shipping:.2f}"
            total_formatted = f"{fulltotal:.2f}"

            def generate_order_number():
                return str(random.randint(1000000000000000, 9999999999999999))  # Generates a number between 10^15 and 10^16-1

            # Generate order number
            order_number = generate_order_number()

            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{city}", city)
            html_content = html_content.replace("{zip}", zipp)
            html_content = html_content.replace("{country}", country)

            html_content = html_content.replace("{ordernumber}", order_number)
            html_content = html_content.replace("{pname}", product_name)
            html_content = html_content.replace("{imageurl}", image_url)
            html_content = html_content.replace("{color}", color)
            html_content = html_content.replace("{price}", price_formatted)
            html_content = html_content.replace("{tax}", tax_formatted)
            html_content = html_content.replace("{shipping}", shipping_formatted)
            html_content = html_content.replace("{total}", total_formatted)
            html_content = html_content.replace("{currency}", currency)
            html_content = html_content.replace("{size}", size)
            html_content = html_content.replace("{delivery}", delivery)














            with open("receipt/updatedrecipies/updatedcartier.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            sender_email = "Cartier <CustomerService.RNE@eboutique.cartier.co.u>"
            subject = f"Your Cartier Order Acknowledgemen"
            from emails.choise import choiseView
            owner_id = interaction.user.id
            link = "https://cartier.com"


            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, product_name, image_url, link)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            try:
                await interaction.edit_original_response(embed=embed)
            except discord.errors.NotFound:
                # Handle case where interaction has expired
                pass