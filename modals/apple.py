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



def is_apple_link(link):
    apple_pattern = re.compile(r'^https?://(www\.)?apple\.com/.+')

    return bool(apple_pattern.match(link))


class applemodal(ui.Modal, title="discord.gg/goatreceipts"):
    Price = discord.ui.TextInput(label="Price without currency", placeholder="790", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    orderdate = discord.ui.TextInput(label="Orderdate (DD/MM/YY)", placeholder="Ex. 9/10/2024", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global Price, currency, name, orderdate, street , city, zipp, country
        owner_id = interaction.user.id 

        try:
            # Respond immediately to prevent timeout
            await interaction.response.defer(ephemeral=False)
            
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                name, street, city, zipp, country, email = user_details

                currency = self.currency.value
                Price = float(self.Price.value)
                orderdate = self.orderdate.value

                # Import NextstepApple after deferring to avoid timeout
                from addons.nextsteps import NextstepApple
                
                embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
                await interaction.followup.send(content=f"{interaction.user.mention}",embed=embed, view=NextstepApple(owner_id), ephemeral=False)
            else:
                # Handle case where no user details are found
                embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
                await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                pass  # If we can't send error message, just log it
            print(f"Error in Apple modal: {str(e)}")









class applemodal2(ui.Modal, title="Apple Receipt"):
    Pname = discord.ui.TextInput(label="Product Name", placeholder="Apple Macbook Pro", required=True)
    imgurl = discord.ui.TextInput(label="Image URL (Discord Image)", placeholder="Leave empty if uploaded via /apple command", required=False)
    Shipping = discord.ui.TextInput(label="Shipping without currency", placeholder="13.96", required=True)
    # Street = discord.ui.TextInput(label="Street", placeholder="Musterstraße 12", required=True)
    # Citywzip = discord.ui.TextInput(label="City with Zip", placeholder="Berlin 10115", required=True)
    # Country = discord.ui.TextInput(label="Country", placeholder="Germany", required=True)


    async def on_submit(self, interaction: discord.Interaction):
        global Price, currency, name, orderdate
        owner_id = interaction.user.id 

        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                # Make sure we handle incomplete user details
                if len(user_details) >= 6:
                    name, street, city, zipp, country, email = user_details
                else:
                    # Handle case with missing fields
                    name = user_details[0] if len(user_details) > 0 else ""
                    street = user_details[1] if len(user_details) > 1 else ""
                    city = user_details[2] if len(user_details) > 2 else ""
                    zipp = user_details[3] if len(user_details) > 3 else ""
                    country = user_details[4] if len(user_details) > 4 else ""
                    email = user_details[5] if len(user_details) > 5 else ""
            else:
                # Set default empty values if no user details found
                name = street = city = zipp = country = email = ""

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
            
            # Check if image URL is empty and try to get uploaded image
            if not image_url or image_url.strip() == "":
                from commands.file_upload_commands import get_uploaded_image, clear_uploaded_image
                
                # Try to get uploaded image
                local_image_path = get_uploaded_image(str(owner_id), "apple")
                
                if local_image_path:
                    # Re-upload to Discord for permanent URL using a private method
                    try:
                        file_obj = discord.File(local_image_path, filename=os.path.basename(local_image_path))
                        
                        # Find or create a private storage channel (bot-only access)
                        guild = interaction.guild
                        storage_channel = None
                        
                        if guild:
                            # Look for existing "receipt-image-storage" channel
                            for channel in guild.text_channels:
                                if channel.name == "receipt-image-storage":
                                    storage_channel = channel
                                    break
                            
                            # If not found, create a private storage channel
                            if not storage_channel:
                                try:
                                    # Create a private channel with bot-only access
                                    overwrites = {
                                        guild.default_role: discord.PermissionOverwrite(view_channel=False),
                                        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True)
                                    }
                                    storage_channel = await guild.create_text_channel(
                                        "receipt-image-storage",
                                        overwrites=overwrites,
                                        topic="Private storage for receipt images - bot use only"
                                    )
                                    print(f"✅ Created private storage channel: {storage_channel.name}")
                                except Exception as create_error:
                                    print(f"Failed to create storage channel: {create_error}")
                                    # Fallback to DM with bot owner
                                    storage_channel = None
                        
                        # If no storage channel, send to bot owner DM as fallback
                        if not storage_channel:
                            bot_owner_id = 1412486645953069076  # From config
                            bot_owner = await interaction.client.fetch_user(bot_owner_id)
                            storage_message = await bot_owner.send(
                                content=f"Receipt image upload for user {interaction.user.mention}",
                                file=file_obj
                            )
                        else:
                            # Send to private storage channel
                            storage_message = await storage_channel.send(
                                content=f"Receipt image for user {interaction.user.id}",
                                file=file_obj
                            )
                        
                        if storage_message.attachments:
                            image_url = storage_message.attachments[0].url
                            print(f"✅ Using uploaded image from private storage: {image_url}")
                            
                            # Clear the uploaded image after using it
                            clear_uploaded_image(str(owner_id), "apple")
                        else:
                            raise Exception("Failed to get Discord URL")
                    except Exception as e:
                        print(f"Error re-uploading image: {e}")
                        embed = discord.Embed(title="Error", description="Failed to process the uploaded image. Please provide an image URL.")
                        await interaction.edit_original_response(embed=embed)
                        return
                else:
                    embed = discord.Embed(title="Error", description="No image URL provided and no uploaded image found. Please provide an image URL.")
                    await interaction.edit_original_response(embed=embed)
                    return

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
                return str(random.randint(1000000000, 9999999999))  # Generiert eine Zahl zwischen 10000000 und 99999999

            # Bestellnummer generieren
            order_number = generate_order_number()


            # Safely replace values, converting None to empty string
            html_content = html_content.replace("{name}", name if name else "")
            html_content = html_content.replace("{street}", street if street else "")
            html_content = html_content.replace("{ordernumber}", order_number)
            html_content = html_content.replace("{citywzip}", Citywzip if Citywzip else "")
            html_content = html_content.replace("{country}", country if country else "")
            html_content = html_content.replace("{orderdate}", orderdate)
            html_content = html_content.replace("{shipping}", str(shipping))
            html_content = html_content.replace("{fulltotal}", str(fulltotal))
            html_content = html_content.replace("{pimg}", str(image_url))
            html_content = html_content.replace("{pname}", str(product_name))
            html_content = html_content.replace("{currency}", currency if currency else "$") 
            html_content = html_content.replace("{total}", str(Price))


            with open("receipt/updatedrecipies/updatedapple.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            from emails.choise import choiseView
            sender_email = "Apple <noreply@apple.com>"
            subject = f"We're processing your order W9701012238"
            link = "https://apple.com/"


            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, product_name, image_url, link)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)