
import asyncio
import json
import random
import re
import discord
from discord.ui import Select
from discord import SelectOption, ui, app_commands

import datetime
from datetime import datetime, timedelta

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from pystyle import Colors

r = Colors.red
lg = Colors.light_gray

def is_bijenkorf_link(link):
    bijenkorf_pattern = re.compile(r'^https?://(www\.)?(debijenkorf\.(nl|be))(/.+)?')
    return bool(bijenkorf_pattern.match(link))

class bijenkorfmodal(ui.Modal, title="discord.gg/goatreceipts"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="Filippa K", required=True)
    imageurl = discord.ui.TextInput(label="Product Image URL", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
    productcategory = discord.ui.TextInput(label="Product Category", placeholder="Filippa K", required=True)
    orderdate = discord.ui.TextInput(label="Order Date", placeholder="10/2/2025", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, imageurl, productcategory, orderdate, name, street, city, zipp, country
        from addons.nextsteps import Nextstepbijenkorf
        owner_id = interaction.user.id 

        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)
        
        if user_details:
            name, street, city, zipp, country, email = user_details

            productname = self.productname.value
            imageurl = self.imageurl.value
            productcategory = self.productcategory.value
            orderdate = self.orderdate.value

            print(f"[{Colors.green}START Scraping{lg}] Bijenkorf -> {interaction.user.id} ({interaction.user})" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {productname}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Product Category: {productcategory}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {imageurl}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Order Date: {orderdate}" + lg)
            print(f"[{Colors.green}Scraping DONE{lg}] Bijenkorf -> {interaction.user.id}" + lg)
            print()

            embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
            await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=Nextstepbijenkorf(owner_id), ephemeral=False)

        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class bijenkorfmodal2(ui.Modal, title="discord.gg/goatreceipt"):
    productsize = discord.ui.TextInput(label="Product Size", placeholder="L", required=True)
    productprice = discord.ui.TextInput(label="Product Price", placeholder="690.00", required=True)
    shippingcost = discord.ui.TextInput(label="Shipping Cost", placeholder="10.00", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        global productsize, productprice, shippingcost, currency

        productsize = self.productsize.value
        productprice = self.productprice.value
        shippingcost = self.shippingcost.value
        currency = self.currency.value

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, ephemeral=True)

            with open("receipt/bijenkorf.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Calculate total
            try:
                total_price = float(productprice) + float(shippingcost)
                total_formatted = f"{total_price:.2f}"
            except ValueError:
                total_formatted = f"{productprice}"

            # Format the address for display
            zipcity = f"{city} {zipp}"

            # Replace placeholders in HTML
            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{zipcity}", zipcity)
            html_content = html_content.replace("{country}", country)
            html_content = html_content.replace("{orderdate}", orderdate)
            html_content = html_content.replace("{imageurl}", imageurl)
            html_content = html_content.replace("{productname}", productname)
            html_content = html_content.replace("{productcategory}", productcategory)
            html_content = html_content.replace("{productsize}", productsize)
            html_content = html_content.replace("{currency}", currency)
            html_content = html_content.replace("{productprice}", productprice)
            html_content = html_content.replace("{shippingcost}", shippingcost)
            html_content = html_content.replace("{total}", total_formatted)

            with open("receipt/updatedrecipies/updatedbijenkorf.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            sender_email = "De Bijenkorf <noreply@bijenkorf.shop>"
            subject = f"Hartelijk bedankt voor je bestelling"
            from emails.choise import choiseView
            owner_id = interaction.user.id

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, productname, imageurl, "https://www.debijenkorf.nl")
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)
