import asyncio
import json
import random
import re
import webbrowser
import discord
import sqlite3
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



def is_apple_link(link):
    apple_pattern = re.compile(r'^https?://(www\.)?apple\.com/.+')

    return bool(apple_pattern.match(link))


class applemodal(ui.Modal, title="discord.gg/goatreceipt"):
    Price = discord.ui.TextInput(label="Price without currency", placeholder="790", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    orderdate = discord.ui.TextInput(label="Orderdate (DD/MM/YY)", placeholder="Ex. 9/10/2024", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global Price, currency, name, orderdate, street, city, zipp, country
        owner_id = str(interaction.user.id)

        # Get database connection only for email
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        # Get user email
        cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(owner_id),))
        email_result = cursor.fetchone()
        conn.close()

        if not email_result:
            embed = discord.Embed(
                title="Email Not Set",
                description="Please use the 'Set Email' button to configure your email first.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Generate random user details
        # Function to generate random data
        def generate_random_details():
            first_names = ["John", "Jane", "Michael", "Emma", "David", "Sarah", "Robert", "Lisa"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson"]
            streets = ["Oak Street", "Maple Avenue", "Pine Road", "Cedar Lane", "Elm Boulevard", "Willow Drive", "Birch Court", "Cypress Way"]
            cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", "San Antonio", "San Diego"]
            zips = ["10001", "90001", "60601", "77001", "85001", "19101", "78201", "92101"]
            countries = ["United States", "Canada", "United Kingdom", "Australia", "Germany", "France", "Spain", "Italy"]

            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            street = f"{random.randint(1, 999)} {random.choice(streets)}"
            city = random.choice(cities)
            zipp = random.choice(zips)
            country = random.choice(countries)

            return name, street, city, zipp, country

        # Generate random details instead of using database
        name, street, city, zipp, country = generate_random_details()

        # Add a class to handle the second form
        class NextstepApple(ui.View):
            def __init__(self, owner_id):
                super().__init__(timeout=300)
                self.owner_id = owner_id

            @ui.button(label="Continue", style=discord.ButtonStyle.green)
            async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
                await interaction.response.send_modal(applemodal2())

        currency = self.currency.value
        Price = float(self.Price.value)
        orderdate = self.orderdate.value

        embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
        await interaction.response.send_message(embed=embed, view=NextstepApple(owner_id), ephemeral=True)









class applemodal2(ui.Modal, title="Apple Receipt"):
    Pname = discord.ui.TextInput(label="Product Name", placeholder="Apple Macbook Pro", required=True)
    imgurl = discord.ui.TextInput(label="Image URL (Discord Image)", placeholder="https://cdn.discordapp.com/attachments/10869879156.....", required=True)
    Shipping = discord.ui.TextInput(label="Shipping without currency", placeholder="13.96", required=True)
    # Street = discord.ui.TextInput(label="Street", placeholder="Musterstraße 12", required=True)
    # Citywzip = discord.ui.TextInput(label="City with Zip", placeholder="Berlin 10115", required=True)
    # Country = discord.ui.TextInput(label="Country", placeholder="Germany", required=True)


    async def on_submit(self, interaction: discord.Interaction):
        global Price, currency, name, orderdate, street, city, zipp, country
        owner_id = str(interaction.user.id)

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(embed=embed, view=None)

            if not (re.match(r'^\d+(\.\d{1,2})?$', self.Shipping.value)):
                embed = discord.Embed(title="Error Apple - Invalid shipping format", description="Please use a valid format (e.g., 12.94) for Apple Shipping Fee.")
                await interaction.response.edit_message(embed=embed, ephemeral=True)
                return

            shipping = float(self.Shipping.value)

            with open("receipt/apple.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            product_name = self.Pname.value
            image_url = self.imgurl.value

            print()
            print(f"[{Colors.green}START Scraping{lg}] APPLE -> {interaction.user.id} ({interaction.user})" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {product_name}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {image_url}" + lg)
            print(f"[{Colors.green}Scraping DONE{lg}] APPLE -> {interaction.user.id} ({interaction.user})" + lg)
            print()

            Citywzip = f"{city} {zipp}"

            fulltotal = shipping + Price
            fulltotal = round(fulltotal, 2)

            def generate_order_number():
                return str(random.randint(1000000000, 9999999999))

            # Generate order number
            order_number = generate_order_number()

            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{ordernumber}", order_number)
            html_content = html_content.replace("{citywzip}", Citywzip)
            html_content = html_content.replace("{country}", country)
            html_content = html_content.replace("{orderdate}", orderdate)
            html_content = html_content.replace("{shipping}", str(shipping))
            html_content = html_content.replace("{fulltotal}", str(fulltotal))
            html_content = html_content.replace("{pimg}", str(image_url))
            html_content = html_content.replace("{pname}", str(product_name))
            html_content = html_content.replace("{currency}", currency) 
            html_content = html_content.replace("{total}", str(Price))

            with open("receipt/updatedrecipies/updatedapple.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            # Validate image URL
            from emails.sender import is_valid_image_url, send_email
            if not is_valid_image_url(image_url):
                embed = discord.Embed(
                    title="Invalid Image URL",
                    description="Please provide a valid image URL (must end with .jpg, .png, .gif, etc. or be from Discord CDN)",
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(embed=embed)
                return

            # Credit check functionality completely removed

            # Get user email from database
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (owner_id,))
            email_result = cursor.fetchone()
            conn.close()

            if not email_result:
                embed = discord.Embed(
                    title="Error",
                    description="Your email is not set. Please use the 'Set Email' button.",
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(embed=embed)
                return

            recipient_email = email_result[0]
            sender_email = "Apple <noreply@apple.com>"
            subject = f"We're processing your order W{order_number}"

            # Show loading message
            loading_embed = discord.Embed(
                title="<a:Loading:1366852189263499455> Sending your email receipt",
                description="Please allow a few seconds to send an **email**",
                color=discord.Color.blue()
            )
            await interaction.edit_original_response(embed=loading_embed, view=None)

            # Send email
            await send_email(
                interaction, 
                recipient_email, 
                html_content, 
                sender_email, 
                subject, 
                product_name, 
                image_url,
                brand="Apple"
            )

            # Credit deduction code completely removed

            # No need to store product_name on interaction object as we already pass it to send_email function

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)