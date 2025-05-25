import asyncio
import json
import re
import warnings
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
import urllib3  # suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Disable insecure request warnings


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


class stockxmodal(ui.Modal, title="discord.gg/goatreceipts"):
    product_name = discord.ui.TextInput(label="Product Name", placeholder="Nike Dunk Low Retro White Black Panda", required=True)
    conditionn = discord.ui.TextInput(label="Condition (New, Used)", placeholder="New", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    status = discord.ui.TextInput(label="Order Status", placeholder="Ex. Delivered, Ordered, Verified, Shipped, Arrived", required=True)
    sizee = discord.ui.TextInput(label="Size (If no size leave blank)", placeholder="US M 13", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        global condition1, currency1, status, product_name_value, sizee
        from addons.nextsteps import NextstepStockX
        owner_id = interaction.user.id 

        product_name_value = self.product_name.value
        condition = self.conditionn.value
        currency = self.currency.value
        status = self.status.value
        sizee = self.sizee.value if self.sizee.value else ""

        condition1 = f"{condition}"
        currency1 = f"{currency}"

        embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
        await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepStockX(owner_id), ephemeral=False)


class stockxmodal2(ui.Modal, title="StockX Receipt"):
    styleidd = discord.ui.TextInput(label="Style ID", placeholder="AMOULW1029-001", required=False)
    pprice = discord.ui.TextInput(label="Price without Currency", placeholder="1693", required=True)
    pfee = discord.ui.TextInput(label="StockX Fee without Currency", placeholder="12.94", required=True)
    shipping = discord.ui.TextInput(label="Shipping Fees without Currency", placeholder="12.94", required=True)
    Delivereddate = discord.ui.TextInput(label="Delivery Date", placeholder="22 January 2024", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global condition1, currency1, status, product_name_value, sizee

        try:
            pprice = float(self.pprice.value)
            pfee1 = self.pfee.value
            shipping1 = self.shipping.value
            dd = self.Delivereddate.value
            style_id = self.styleidd.value

            embed = discord.Embed(title="Processing...", description="Please provide an image URL in the next step to complete your receipt.", color=0x1e1f22)

            # Store the form data to use in the third form
            self.pprice_value = pprice
            self.pfee_value = float(pfee1) if re.match(r'^\d+(\.\d{1,2})?$', pfee1) else 0
            self.shipping_value = float(shipping1) if re.match(r'^\d+(\.\d{1,2})?$', shipping1) else 0
            self.dd_value = dd
            self.style_id_value = style_id

            # Validation
            if not (re.match(r'^\d+(\.\d{1,2})?$', pfee1) and re.match(r'^\d+(\.\d{1,2})?$', shipping1)):
                embed = discord.Embed(title="Error StockX - Invalid fee/shipping format", description="Please use a valid format (e.g., 12.94) for StockX Fee and Shipping Fees.")
                await interaction.response.edit_message(embed=embed)
                return

            date_pattern = re.compile(r'^\d{1,2}\s(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}$', re.IGNORECASE)
            if not date_pattern.match(dd):
                embed = discord.Embed(title="Error StockX - Invalid date format", description="Please use the format 'Day Month Year'\nEx. `24 January 2024`")
                await interaction.response.edit_message(embed=embed)
                return

            # Create a final step view for the image URL
            class FinalStepView(discord.ui.View):
                def __init__(self, owner_id, price_value, pfee_value, shipping_value, delivery_date, style_id_value):
                    super().__init__(timeout=300)
                    self.owner_id = owner_id
                    self.price_value = price_value
                    self.pfee_value = pfee_value
                    self.shipping_value = shipping_value
                    self.delivery_date = delivery_date
                    self.style_id = style_id_value
                    
                async def interaction_check(self, interaction):
                    if interaction.user.id != self.owner_id:
                        await interaction.response.send_message("You cannot use this button.", ephemeral=True)
                        return False
                    return True

                @discord.ui.button(label="Add Image URL", style=discord.ButtonStyle.green)
                async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                    # Create the third modal with values from second form
                    modal = stockxmodal3()
                    modal.price = self.price_value
                    modal.pfee = self.pfee_value
                    modal.shipping = self.shipping_value 
                    modal.delivery_date = self.delivery_date
                    modal.style_id = self.style_id
                    await interaction.response.send_modal(modal)

            # Show the image button prompt
            embed = discord.Embed(
                title="Almost there!",
                description="Click the button below to add an image URL for your receipt.",
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(
                embed=embed, 
                view=FinalStepView(
                    interaction.user.id,
                    pprice,
                    float(pfee1) if re.match(r'^\d+(\.\d{1,2})?$', pfee1) else 0,
                    float(shipping1) if re.match(r'^\d+(\.\d{1,2})?$', shipping1) else 0,
                    dd,
                    style_id
                )
            )

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.response.edit_message(embed=embed, view=None)


class stockxmodal3(ui.Modal, title="StockX Image"):
    image_url = discord.ui.TextInput(label="Image URL", placeholder="https://example.com/image.jpg", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global condition1, currency1, status, product_name_value, sizee

        try:
            image_url = self.image_url.value

            # Validate image URL
            if not image_url.startswith(('http://', 'https://')):
                await interaction.response.send_message("Please enter a valid image URL starting with http:// or https://", ephemeral=True)
                return

            embed = discord.Embed(title="Processing...", description="Generating your receipt and preparing email...", color=0x1e1f22)
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Get the previously entered form values from stockxmodal2
            from emails.choise import choiseView

            # Read the HTML template
            try:
                with open("receipt/stockx.html", "r", encoding="utf-8") as file:
                    html_content = file.read()
            except FileNotFoundError:
                await interaction.response.edit_message(content="Error: StockX template file not found. Please contact an administrator.")
                return

            # Use stockx.com with the product name as the default link
            link = f"https://stockx.com/{product_name_value.replace(' ', '-').lower()}"

            # Try to connect to StockX using proxy (but continue if it fails)
            try:
                response = requests.get(
                        url=link,
                        proxies={
                            "http": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                            "https": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                        },
                        verify=False,  # Disable SSL verification
                        timeout=10  # Add timeout to prevent hanging
                )
            except requests.RequestException:
                print(f"Warning: Failed to connect to StockX via proxy for product: {product_name_value}")

            # Get previous form data and calculate total
            pprice = getattr(self, 'price', 0)
            pfee = getattr(self, 'pfee', 0)
            shipping = getattr(self, 'shipping', 0)
            delivery_date = getattr(self, 'delivery_date', "")
            style_id = getattr(self, 'style_id', "")
            
            total = pprice + pfee + shipping
            total = round(total, 2)

            # Format values
            pprice1 = f"{pprice}"
            pfee1 = f"{pfee}"
            shipping1 = f"{shipping}"

            # Replace placeholders in template
            html_content = html_content.replace("{placeholder1}", condition1)
            html_content = html_content.replace("{placeholder2}", currency1)
            html_content = html_content.replace("{placeholder3}", pprice1)
            html_content = html_content.replace("{placeholder4}", pfee1)
            html_content = html_content.replace("{placeholder5}", shipping1)
            html_content = html_content.replace("{placeholder6}", delivery_date)
            html_content = html_content.replace("{placeholder7}", status) 
            html_content = html_content.replace("{link_value_stockx}", link)
            html_content = html_content.replace("{brimage}", image_url) 
            html_content = html_content.replace("{pname}", product_name_value)
            html_content = html_content.replace("{styleid}", style_id)
            html_content = html_content.replace("{sizee}", sizee)
            html_content = html_content.replace("{totalp}", str(total))

            try:
                # Ensure directory exists
                os.makedirs("receipt/updatedrecipies", exist_ok=True)
                
                with open("receipt/updatedrecipies/updatedstockx.html", "w", encoding="utf-8") as file:
                    file.write(html_content)
            except Exception as file_error:
                print(f"Error writing to file: {str(file_error)}")
                await interaction.edit_original_response(content="Error saving receipt. Please try again later.")
                return

            sender_email = "StockX <noreply@confirmation.com>"
            # Set subject emoji based on order status
            if status.lower() == "ordered":
                subject = f"👍 Order Confirmed: {product_name_value}"
            elif status.lower() == "verified" or status.lower() == "verified + shipped":
                subject = f"✅ Order Verified & Shipped: {product_name_value}"
            elif status.lower() == "shipped" or status.lower() == "shipped to stockx":
                subject = f"📦 Order Shipped To StockX: {product_name_value}"
            elif status.lower() == "arrived" or status.lower() == "arrived at stockx":
                subject = f"🔊 Order Arrived At StockX: {product_name_value}"
            elif status.lower() == "delivered":
                subject = f"🎉 Order Delivered: {product_name_value}"
            else:
                subject = f"🎉 Order {status}: {product_name_value}"
                
            owner_id = interaction.user.id

            # Final step - email choice
            embed = discord.Embed(title="Choose email provider", description="Email is ready to send. Choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, product_name_value, image_url, link)
            
            try:
                await interaction.edit_original_response(embed=embed, view=view)
            except Exception as response_error:
                print(f"Error sending final StockX form response: {str(response_error)}")
                
                # Try alternate methods if the first fails
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                    else:
                        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                except Exception as e:
                    print(f"All attempts to respond failed: {str(e)}")
                
        except Exception as e:
            print(f"StockX image modal error: {str(e)}")
            error_msg = "An error occurred while submitting the form. Please try again."
            
            try:
                # Check if interaction is still valid
                if not interaction.response.is_done():
                    await interaction.response.send_message(error_msg, ephemeral=True)
                else:
                    await interaction.edit_original_response(content=error_msg)
            except Exception as response_error:
                print(f"Failed to send error message in StockX modal: {str(response_error)}")


class ImageUrlModal(ui.Modal, title="StockX Image URL"):
    image_url = discord.ui.TextInput(label="Image URL", placeholder="https://example.com/image.jpg", required=True)

    def __init__(self, price, pfee, shipping, delivery_date, style_id):
        super().__init__()
        self.price = price
        self.pfee = pfee
        self.shipping = shipping
        self.delivery_date = delivery_date
        self.style_id = style_id

    async def on_submit(self, interaction: discord.Interaction):
        global condition1, currency1, status, product_name_value, sizee

        try:
            image_url = self.image_url.value

            # Validate image URL
            if not image_url.startswith(('http://', 'https://')):
                await interaction.response.send_message("Please enter a valid image URL starting with http:// or https://", ephemeral=True)
                return

            total = self.price + self.pfee + self.shipping
            total = round(total, 2)

            try:
                with open("receipt/stockx.html", "r", encoding="utf-8") as file:
                    html_content = file.read()
            except FileNotFoundError:
                await interaction.response.send_message("Error: StockX template file not found. Please contact an administrator.", ephemeral=True)
                return

            pprice1 = f"{self.price}"
            pfee1 = f"{self.pfee}"
            shipping1 = f"{self.shipping}"

            # Use stockx.com with the product name as the default link
            link = f"https://stockx.com/{product_name_value.replace(' ', '-').lower()}"

            try:
                # Disable SSL verification for StockX proxy
                response = requests.get(
                        url=link,
                        proxies={
                            "http": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                            "https": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                        },
                        verify=False,  # Disable SSL verification
                        timeout=10  # Add timeout to prevent hanging
                )
            except requests.RequestException:
                # Continue even if the proxy request fails
                print(f"Warning: Failed to connect to StockX via proxy for product: {product_name_value}")

            # Replace placeholders in template
            html_content = html_content.replace("{placeholder1}", condition1)
            html_content = html_content.replace("{placeholder2}", currency1)
            html_content = html_content.replace("{placeholder3}", pprice1)
            html_content = html_content.replace("{placeholder4}", pfee1)
            html_content = html_content.replace("{placeholder5}", shipping1)
            html_content = html_content.replace("{placeholder6}", self.delivery_date)
            html_content = html_content.replace("{placeholder7}", status) 
            html_content = html_content.replace("{link_value_stockx}", link)
            html_content = html_content.replace("{brimage}", image_url) 
            html_content = html_content.replace("{pname}", product_name_value)
            html_content = html_content.replace("{styleid}", self.style_id)
            html_content = html_content.replace("{sizee}", sizee)
            html_content = html_content.replace("{totalp}", str(total))

            try:
                # Ensure directory exists
                os.makedirs("receipt/updatedrecipies", exist_ok=True)
                
                with open("receipt/updatedrecipies/updatedstockx.html", "w", encoding="utf-8") as file:
                    file.write(html_content)
            except Exception as file_error:
                print(f"Error writing to file: {str(file_error)}")
                await interaction.response.send_message("Error saving receipt. Please try again later.", ephemeral=True)
                return

            sender_email = "StockX <noreply@confirmation.com>"
            # Set subject emoji based on order status
            if status.lower() == "ordered":
                subject = f"👍 Order Confirmed: {product_name_value}"
            elif status.lower() == "verified" or status.lower() == "verified + shipped":
                subject = f"✅ Order Verified & Shipped: {product_name_value}"
            elif status.lower() == "shipped" or status.lower() == "shipped to stockx":
                subject = f"📦 Order Shipped To StockX: {product_name_value}"
            elif status.lower() == "arrived" or status.lower() == "arrived at stockx":
                subject = f"🔊 Order Arrived At StockX: {product_name_value}"
            elif status.lower() == "delivered":
                subject = f"🎉 Order Delivered: {product_name_value}"
            else:
                subject = f"🎉 Order {status}: {product_name_value}"
                
            from emails.choise import choiseView
            owner_id = interaction.user.id

            # Final step - email choice
            embed = discord.Embed(title="Choose email provider", description="Email is ready to send. Choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, product_name_value, image_url, link)
            
            try:
                # First try the standard response
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                    return
                    
                # If we already responded, use followup
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            except discord.errors.NotFound:
                print("Interaction expired before responding - user may need to try again")
            except discord.errors.InteractionResponded:
                # Try followup if we get an already responded error
                try:
                    await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                except Exception as followup_error:
                    print(f"Failed to send followup: {str(followup_error)}")
            except Exception as response_error:
                print(f"Error sending final StockX form response: {str(response_error)}")
                
        except Exception as e:
            print(f"StockX image modal error: {str(e)}")
            error_msg = "An error occurred while submitting the form. Please try again."
            
            try:
                # Check if interaction is still valid
                if interaction.response and not interaction.response.is_done():
                    await interaction.response.send_message(error_msg, ephemeral=True)
                elif not interaction.is_expired():
                    await interaction.followup.send(error_msg, ephemeral=True)
                else:
                    print("Cannot respond to interaction - it has expired")
            except discord.errors.NotFound:
                print("Interaction not found - it may have expired")
            except discord.errors.InteractionResponded:
                print("Interaction already responded to")
            except Exception as response_error:
                print(f"Failed to send error message in StockX modal: {str(response_error)}")


class ImageUrlView(discord.ui.View):
    def __init__(self, owner_id, price, pfee, shipping, delivery_date, style_id):
        super().__init__()
        self.owner_id = owner_id
        self.price = price
        self.pfee = pfee
        self.shipping = shipping
        self.delivery_date = delivery_date
        self.style_id = style_id
        self.add_item(ImageUrlButton(price, pfee, shipping, delivery_date, style_id))

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("You cannot use this button.", ephemeral=True)
            return False
        return True


class ImageUrlButton(discord.ui.Button):
    def __init__(self, price, pfee, shipping, delivery_date, style_id):
        super().__init__(label="Enter Image URL", style=discord.ButtonStyle.primary)
        self.price = price
        self.pfee = pfee
        self.shipping = shipping
        self.delivery_date = delivery_date
        self.style_id = style_id

    async def callback(self, interaction):
        modal = ImageUrlModal(
            price=self.price,
            pfee=self.pfee,
            shipping=self.shipping,
            delivery_date=self.delivery_date,
            style_id=self.style_id
        )
        await interaction.response.send_modal(modal)