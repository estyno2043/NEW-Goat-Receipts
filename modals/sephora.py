import asyncio
import json
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





def is_sephora_link(link):
    rl_pattern = re.compile(r'^https?://(www\.)?sephora\.(com|de)(/.*)?$')

    return bool(rl_pattern.match(link))


class sephoranmodal(ui.Modal, title="discord.gg/goatreceipts"):

    # Define the inputs first
    Priceff = discord.ui.TextInput(label="Price without currency", placeholder="Ex. 790", required=True)
    currencyff = discord.ui.TextInput(label="Currency ($, £‚ €)", placeholder="€", required=True, min_length=1, max_length=1)
    delivery = discord.ui.TextInput(label="Order Date", placeholder="Ex. 24/04/2024", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global Priceff, currencyff, name, delivery, street, city, zipp, country
        from addons.nextsteps import Nextstepsephora
        owner_id = interaction.user.id 

        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                name, street, city, zipp, country, email = user_details

                currencyff = self.currencyff.value
                Priceff = float(self.Priceff.value)
                delivery = self.delivery.value


                embed = discord.Embed(title="You are almost done...", description="Complete the next steps to receive the receipt.")
                await interaction.response.send_message(content=f"{interaction.user.mention}",embed=embed, view=Nextstepsephora(owner_id), ephemeral=False)
            else:
                # Handle case where no user details are found
                embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)

# Create alias for compatibility after class is fully defined
sephoramodal = sephoranmodal





class sephoramodal2(ui.Modal, title="Sephora Receipt"):
    taxx = discord.ui.TextInput(label="Taxes without Currency", placeholder="14.99", required=True)
    image = discord.ui.TextInput(label="Image URL (Discord Image)", placeholder="https://cdn.discordapp.com/attachments/10869879156.....", required=True)
    pname = discord.ui.TextInput(label="Product Name", placeholder="Dior Sauvage", required=True)


    async def on_submit(self, interaction: discord.Interaction):
        global Priceff, currencyff, name, delivery, street, city, zipp, country
        owner_id = interaction.user.id 

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(content=None,embed=embed, view=None)

            image = self.image.value

            with open("receipt/sephora.html", "r", encoding="utf-8") as file:
                html_content = file.read()





            pname = self.pname.value



            print()
            print(f"[{Colors.green}START Scraping{lg}] SEPHORA -> {interaction.user.id} ({interaction.user})" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {image}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {pname}" + lg)
            print(f"[{Colors.green}Scraping DONE{lg}] SEPHORA -> {interaction.user.id}" + lg)
            print()



            cityzip = f"{city} {zipp}"
            taxx = float(self.taxx.value)


            total = Priceff + taxx
            total = round(total, 2)

            # Format numbers to always show 2 decimal places
            price_formatted = f"{Priceff:.2f}"
            tax_formatted = f"{taxx:.2f}"
            total_formatted = f"{total:.2f}"

            # Use a placeholder image if Discord CDN link is provided
            # Discord CDN links often don't work in email clients
            if "discord" in image.lower():
                # Use a generic Sephora product image that works in emails
                image_url = "https://via.placeholder.com/150x150/000000/FFFFFF?text=Product+Image"
            else:
                image_url = image

            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{orderdate}", delivery)
            html_content = html_content.replace("{productname}", pname or "Unknown Product")
            html_content = html_content.replace("{price}", price_formatted)
            html_content = html_content.replace("{currency}", currencyff)
            # html_content = html_content.replace("{imageurl}", image_url) # This line is removed to avoid duplicate image replacement
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{cityzip}", cityzip)
            html_content = html_content.replace("{country}", country)
            html_content = html_content.replace("{tax}", tax_formatted)
            html_content = html_content.replace("{total}", total_formatted)

            # Fix image display - ensure proper image tag formatting
            import re
            # Find and replace image tags that contain the productimage placeholder
            img_pattern = r'<img[^>]*src="{productimage}"[^>]*>'
            if re.search(img_pattern, html_content):
                # Create a properly formatted image tag
                image_tag = f'<img src="{image_url}" alt="{pname}" style="max-width:150px;height:auto;" class="CToWUd" data-bit="iit">'
                html_content = re.sub(img_pattern, image_tag, html_content)

            # Also handle direct replacement as fallback
            html_content = html_content.replace("{productimage}", image_url)


            with open("receipt/updatedrecipies/updatedsephora.html", "w", encoding="utf-8") as file:
                file.write(html_content)


            sender_email = "Sephora <noreply@sephora.org>"
            subject = "Your receipt from Sephora"
            from emails.choise import choiseView
            owner_id = interaction.user.id
            link = "https://sephora.com"


            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, pname, image, link)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)