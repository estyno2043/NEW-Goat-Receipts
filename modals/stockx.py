import asyncio
import json
import re
import warnings
import webbrowser
import discord
from discord.ui import Select
from discord import SelectOption, ui, app_commands
from datetime import datetime
import sqlite3  # Add import for sqlite3

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





class stockxmodal(ui.Modal, title="discord.gg/goatreceipts"):
    product_name = discord.ui.TextInput(label="Product Name", placeholder="Air Jordan 4 Retro", required=True)
    conditionn = discord.ui.TextInput(label="Condition (New, Used)", placeholder="New", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    status = discord.ui.TextInput(label="Order Status", placeholder="Ex. Delivered, Ordered, Verified", required=True)
    sizee = discord.ui.TextInput(label="Size (If no size leave blank)", placeholder="US M 13", required=False)

    async def has_left_vouch(self, interaction: discord.Interaction):
        # Owner ID exemption
        if interaction.user.id == 1339295766828552365:
            return True

        # Check database for vouch from this user
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT vouch_content FROM vouches WHERE user_id = ?", (str(interaction.user.id),))
        result = cursor.fetchone()
        conn.close()

        return result is not None

    async def on_submit(self, interaction: discord.Interaction):
        global condition1, currency1, status, product_name, sizee
        owner_id = interaction.user.id

        # Exempt the owner from the client role check
        if interaction.user.id == 1339295766828552365:
            pass  # Owner is exempt

        # Check for vouch
        if not await self.has_left_vouch(interaction):
            embed = discord.Embed(
                title="⚠️ Vouch To Continue",
                description="- Leave a **Vouch** message in <#1371111858114658314> To continue",
                color=discord.Color.yellow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return 

        product_name = self.product_name.value
        condition = self.conditionn.value
        currency = self.currency.value
        status = self.status.value
        sizee = self.sizee.value if self.sizee.value else ""

        condition1 = f"{condition}"
        currency1 = f"{currency}"

        # Create NextstepStockX class inline, similar to apple.py
        class NextstepStockX(ui.View):
            def __init__(self, owner_id):
                super().__init__(timeout=300)
                self.owner_id = owner_id

            @ui.button(label="Continue", style=discord.ButtonStyle.green)
            async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
                await interaction.response.send_modal(stockxmodal2())

        embed = discord.Embed(title="You are almost done...", description="Complete the next modal to continue with the receipt generation.")
        await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepStockX(owner_id), ephemeral=True)







class stockxmodal2(ui.Modal, title="StockX Receipt"):
    styleidd = discord.ui.TextInput(label="Style ID", placeholder="AMOULW1029-001", required=False)
    pprice = discord.ui.TextInput(label="Price without Currency", placeholder="1693", required=True)
    pfee = discord.ui.TextInput(label="StockX Fee without Currency", placeholder="12.94", required=True)
    shipping = discord.ui.TextInput(label="Shipping Fees without Currency", placeholder="12.94", required=True)
    Delivereddate = discord.ui.TextInput(label="Delivery Date", placeholder="22 January 2024", required=True)
    
    async def on_submit(self, interaction: discord.Interaction):
        global condition1, currency1, status, product_name, sizee
        global pprice, pfee, shipping, dd, style_id
        
        try:
            pprice = float(self.pprice.value)
            pfee1 = self.pfee.value
            shipping1 = self.shipping.value
            dd = self.Delivereddate.value
            style_id = self.styleidd.value

            if not (re.match(r'^\d+(\.\d{1,2})?$', pfee1) and re.match(r'^\d+(\.\d{1,2})?$', shipping1)):
                embed = discord.Embed(title="Error StockX - Invalid fee/shipping format", description="Please use a valid format (e.g., 12.94) for StockX Fee and Shipping Fees.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            pfee = float(self.pfee.value)
            shipping = float(self.shipping.value)

            date_pattern = re.compile(r'^\d{1,2}\s(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}$', re.IGNORECASE)

            if not date_pattern.match(dd):
                embed = discord.Embed(title="Error StockX - Invalid date format", description="Please use the format 'Day Month Year'\nEx. `24 January 2024`")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Create a class for the third step
            class FinalStepView(ui.View):
                def __init__(self, owner_id):
                    super().__init__(timeout=300)
                    self.owner_id = owner_id

                @ui.button(label="Add Image URL", style=discord.ButtonStyle.green)
                async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
                    await interaction.response.send_modal(stockxmodal3())

            # Show the third step button
            embed = discord.Embed(
                title="Almost there!",
                description="Click the button below to add an image URL for your receipt.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, view=FinalStepView(interaction.user.id), ephemeral=True)
        
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class stockxmodal3(ui.Modal, title="StockX Image"):
    image_url = discord.ui.TextInput(label="Image URL", placeholder="https://example.com/image.jpg", required=True)


    async def on_submit(self, interaction: discord.Interaction):
        global condition1, currency1, status, product_name, sizee
        global pprice, pfee, shipping, dd, style_id  # Store these for the third form

        # Credit check functionality completely removed

        try:
            pprice = float(self.pprice.value)
            pfee1 = self.pfee.value
            shipping1 = self.shipping.value
            dd = self.Delivereddate.value
            style_id = self.styleidd.value

            if not (re.match(r'^\d+(\.\d{1,2})?$', pfee1) and re.match(r'^\d+(\.\d{1,2})?$', shipping1)):
                embed = discord.Embed(title="Error StockX - Invalid fee/shipping format", description="Please use a valid format (e.g., 12.94) for StockX Fee and Shipping Fees.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            pfee = float(self.pfee.value)
            shipping = float(self.shipping.value)

            date_pattern = re.compile(r'^\d{1,2}\s(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}$', re.IGNORECASE)

            if not date_pattern.match(dd):
                embed = discord.Embed(title="Error StockX - Invalid date format", description="Please use the format 'Day Month Year'\nEx. `24 January 2024`")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Create a class for the third step
            class FinalStepView(ui.View):
                def __init__(self, owner_id):
                    super().__init__(timeout=300)
                    self.owner_id = owner_id

                @ui.button(label="Add Image URL", style=discord.ButtonStyle.green)
                async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
                    await interaction.response.send_modal(stockxmodal3())

            # Show the third step button
            embed = discord.Embed(
                title="Almost there!",
                description="Click the button below to add an image URL for your receipt.",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed, view=FinalStepView(interaction.user.id), ephemeral=True)
        
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)

    async def on_submit(self, interaction: discord.Interaction):
        global condition1, currency1, status, product_name, sizee
        global pprice, pfee, shipping, dd, style_id

        try:
            image_url = self.image_url.value
            
            # Calculate the total
            total = pprice + pfee + shipping
            total = round(total, 2)

            embed = discord.Embed(title="Processing...", description="Generating your receipt and sending email...", color=0x1e1f22)
            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Read the HTML template
            with open("receipt/stockx.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Format the price values
            pprice1 = f"{pprice:.2f}"
            pfee1 = f"{pfee:.2f}"
            shipping1 = f"{shipping:.2f}"

            # Replace placeholders with the provided values
            html_content = html_content.replace("{placeholder1}", condition1)
            html_content = html_content.replace("{placeholder2}", currency1)
            html_content = html_content.replace("{placeholder3}", pprice1)
            html_content = html_content.replace("{placeholder4}", pfee1)
            html_content = html_content.replace("{placeholder5}", shipping1)
            html_content = html_content.replace("{placeholder6}", dd)
            html_content = html_content.replace("{placeholder7}", status)
            html_content = html_content.replace("{link_value_stockx}", "https://stockx.com/")  # Default link
            html_content = html_content.replace("{brimage}", image_url)
            html_content = html_content.replace("{pname}", product_name)
            html_content = html_content.replace("{styleid}", style_id)
            html_content = html_content.replace("{sizee}", sizee)
            html_content = html_content.replace("{totalp}", f"{total:.2f}")

            # Save the updated HTML
            with open("receipt/updatedrecipies/updatedstockx.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            # Setup email variables
            sender_email = "StockX <noreply@stockx.com>"
            subject = f"🎉Order {status}: {product_name}"
            owner_id = interaction.user.id

            # Get user's email from database
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(owner_id),))
            result = cursor.fetchone()
            conn.close()

            if not result:
                embed = discord.Embed(title="Error", description="Email not found. Please set your email first.", color=discord.Color.red())
                await interaction.edit_original_response(embed=embed, view=None)
                return

            recipient_email = result[0]

            # Update loading message
            loading_embed = discord.Embed(
                title="<a:Loading:1366852189263499455> Sending your email receipt",
                description="**Please allow a few seconds to send an email**",
                color=discord.Color.blue()
            )
            await interaction.edit_original_response(embed=loading_embed, view=None)

            # Send email
            from emails.sender import send_email
            success = await send_email(
                interaction,
                recipient_email,
                html_content,
                sender_email,
                subject,
                product_name,
                image_url,
                brand="StockX"
            )

            if not success:
                embed = discord.Embed(title="Error", description="Failed to send email.", color=discord.Color.red())
                await interaction.edit_original_response(embed=embed, view=None)
            else:
                # Credit deduction code completely removed

                # Success message
                success_embed = discord.Embed(
                    title="✅ Receipt Generated Successfully",
                    description=f"Your StockX receipt for **{product_name}** has been sent to **{recipient_email}**.",
                    color=discord.Color.green()
                )
                await interaction.edit_original_response(embed=success_embed, view=None)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed, view=None)
