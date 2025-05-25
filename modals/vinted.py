import asyncio
import json
import re
import webbrowser
import discord
from discord.ui import Select
from discord import SelectOption, ui, app_commands
from datetime import datetime

import sys
import os
import time
from time import sleep
from uuid import uuid4

import requests

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from bs4 import BeautifulSoup
from pystyle import Colors

r = Colors.red
lg = Colors.light_gray

class vintedmodal(ui.Modal, title="discord.gg/goatreceipts"):
    yourvintedname = ui.TextInput(label="Your Vinted Name", placeholder="Enter your Vinted username", required=True)
    sellername = ui.TextInput(label="Seller Name", placeholder="Enter seller's username", required=True)
    productname = ui.TextInput(label="Product Name", placeholder="Enter product name", required=True)
    currency = ui.TextInput(label="Currency", placeholder="€", required=True, min_length=1, max_length=1)
    shippingcost = ui.TextInput(label="Shipping Cost", placeholder="1.45", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global yourvintedname, sellername, productname, currency, shippingcost
        from addons.nextsteps import NextstepVinted
        owner_id = interaction.user.id 

        yourvintedname = self.yourvintedname.value
        sellername = self.sellername.value
        productname = self.productname.value
        currency = self.currency.value
        shippingcost = self.shippingcost.value

        embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
        await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepVinted(owner_id), ephemeral=False)

class vintedmodal2(ui.Modal, title="Vinted Receipt"):
    productprice = ui.TextInput(label="Product Price", placeholder="2.00", required=True)
    buyerfeecost = ui.TextInput(label="Buyer Fee Cost", placeholder="0.80", required=True)
    paymentmethod = ui.TextInput(label="Payment Method", placeholder="Apple Pay", required=True)
    orderdate = ui.TextInput(label="Order Date (DD/MM/YYYY)", placeholder="05/05/2025", required=True)
    transactionid = ui.TextInput(label="Transaction ID", placeholder="13656997548", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global yourvintedname, sellername, productname, currency, shippingcost

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(content=None, embed=embed, view=None)

            productprice = self.productprice.value
            buyerfeecost = self.buyerfeecost.value
            paymentmethod = self.paymentmethod.value
            orderdate = self.orderdate.value
            transactionid = self.transactionid.value

            # Get current time
            now = datetime.now()
            current_time = now.strftime("%I:%M %p")

            # Calculate the total
            try:
                product_price_float = float(productprice)
                buyer_fee_float = float(buyerfeecost)
                shipping_cost_float = float(shippingcost)
                total = product_price_float + buyer_fee_float
                total_formatted = round(total, 2)
            except ValueError:
                embed = discord.Embed(title="Error", description="Invalid price format. Please use numerical values.")
                await interaction.edit_original_response(embed=embed)
                return

            with open("receipt/vinted.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Replace all placeholders with their actual values
            # Convert string values to float for proper formatting
            try:
                product_price_float = float(productprice)
                buyer_fee_float = float(buyerfeecost)
                shipping_cost_float = float(shippingcost)

                # Format all numeric values with two decimal places
                formatted_product_price = f"{product_price_float:.2f}"
                formatted_buyer_fee = f"{buyer_fee_float:.2f}"
                formatted_shipping = f"{shipping_cost_float:.2f}"
                formatted_total = f"{total_formatted:.2f}"

                replacements = {
                    "{yourvintedname}": yourvintedname,
                    "{sellername}": sellername,
                    "{productname}": productname,
                    "{currency}": currency,
                    "{shippingcost}": formatted_shipping,
                    "{productprice}": formatted_product_price,
                    "{buyerfeecost}": formatted_buyer_fee,
                    "{paymentmethod}": paymentmethod,
                    "{orderdate}": orderdate,
                    "{current_time}": current_time,
                    "{transactionid}": transactionid,
                    "{total}": formatted_total
                }
            except ValueError:
                # Fallback to non-formatted strings if conversion fails
                replacements = {
                    "{yourvintedname}": yourvintedname,
                    "{sellername}": sellername,
                    "{productname}": productname,
                    "{currency}": currency,
                    "{shippingcost}": shippingcost,
                    "{productprice}": productprice,
                    "{buyerfeecost}": buyerfeecost,
                    "{paymentmethod}": paymentmethod,
                    "{orderdate}": orderdate,
                    "{current_time}": current_time,
                    "{transactionid}": transactionid,
                    "{total}": str(total_formatted)
                }

            for placeholder, value in replacements.items():
                html_content = html_content.replace(placeholder, str(value))

            with open("receipt/updatedrecipies/updatedvinted.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            sender_email = "Team Vinted <noreply@vinted.com>"
            subject = f"Your receipt for \"{productname}\""
            from emails.choise import choiseView
            owner_id = interaction.user.id

            # Using the Vinted image for the receipt
            image_url = "vinted image.png"
            vinted_url = "https://vinted.com"

            # Prepare embed with vinted image
            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            # Create the view with the file path to the local image
            view = choiseView(owner_id, html_content, sender_email, subject, productname, "vinted image.png", vinted_url)

            # Since we can't attach files to edit_original_response, we'll just use the embed and view
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)