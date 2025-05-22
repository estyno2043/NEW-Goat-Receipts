import asyncio
import json
import re
import discord
from discord.ui import Select
from discord import SelectOption, ui, app_commands
from datetime import datetime
import sqlite3

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

# Global variables to store first modal data
yourvintedname = ""
sellername = ""
productname = ""
currency = ""
shippingcost = ""

class vintedmodal(ui.Modal, title="discord.gg/goatreceipts"):
    yourvintedname = ui.TextInput(label="Your Vinted Name", placeholder="Enter your Vinted username", required=True)
    sellername = ui.TextInput(label="Seller Name", placeholder="Enter seller's username", required=True)
    productname = ui.TextInput(label="Product Name", placeholder="Enter product name", required=True)
    currency = ui.TextInput(label="Currency", placeholder="€", required=True, min_length=1, max_length=1)
    shippingcost = ui.TextInput(label="Shipping Cost", placeholder="1.45", required=True)

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
        global yourvintedname, sellername, productname, currency, shippingcost
        owner_id = interaction.user.id 

        # Check for vouch
        if not await self.has_left_vouch(interaction):
            embed = discord.Embed(
                title="⚠️ Vouch To Continue",
                description="- Leave a **Vouch** message in <#1371111858114658314> To continue",
                color=discord.Color.yellow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        yourvintedname = self.yourvintedname.value
        sellername = self.sellername.value
        productname = self.productname.value
        currency = self.currency.value
        shippingcost = self.shippingcost.value

        # Create NextstepVinted class inline, similar to stockx.py
        class NextstepVinted(ui.View):
            def __init__(self, owner_id):
                super().__init__(timeout=300)
                self.owner_id = owner_id

            @ui.button(label="Continue", style=discord.ButtonStyle.green)
            async def continue_button(self, interaction: discord.Interaction, button: ui.Button):
                await interaction.response.send_modal(vintedmodal2())

        embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
        await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepVinted(owner_id), ephemeral=True)

class vintedmodal2(ui.Modal, title="Vinted Receipt"):
    productprice = ui.TextInput(label="Product Price", placeholder="2.00", required=True)
    buyerfeecost = ui.TextInput(label="Buyer Fee Cost", placeholder="0.80", required=True)
    paymentmethod = ui.TextInput(label="Payment Method", placeholder="Apple Pay", required=True)
    orderdate = ui.TextInput(label="Order Date (DD/MM/YYYY)", placeholder="05/05/2025", required=True)
    transactionid = ui.TextInput(label="Transaction ID", placeholder="13656997548", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global yourvintedname, sellername, productname, currency, shippingcost

        try:
            loading_embed = discord.Embed(
                title="<a:Loading:1366852189263499455> Sending your email receipt",
                description="**Please allow a few seconds to send an email**",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=loading_embed, ephemeral=True)

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

            # Check if user has credits (skip for owner)
            if interaction.user.id != 1339295766828552365:  # Owner ID exemption
                user_id = str(interaction.user.id)
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()

                # Check if user exists in credits table
                cursor.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()

                if not result:
                    # Add user with default 3 credits
                    cursor.execute("INSERT INTO user_credits (user_id, credits) VALUES (?, 3)", (user_id,))
                    conn.commit()
                    credits = 3
                else:
                    credits = result[0]

                conn.close()

                # Check if user has enough credits
                if credits <= 0:
                    embed = discord.Embed(
                        title="Limit Reached",
                        description="Oops... you have used all of your remaining **credits**. You will need to buy a **[premium plan](https://goatreceipts.xyz)** to continue generating receipts for over **80** available brands.",
                        color=discord.Color.red()
                    )
                    await interaction.edit_original_response(embed=embed, view=None)
                    return

            # Get user's email from database
            owner_id = interaction.user.id
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

            # Prepare email data
            sender_email = "Team Vinted <noreply@vinted.com>"
            subject = f"Your receipt for \"{productname}\""
            image_url = "https://media.discordapp.net/attachments/1339298010169086075/1371113448867631244/vinted_logo.png?ex=6821f468&is=6820a2e8&hm=cc122088f870e7ab0431c8c7f3963283e26e685eeb7e1b130e9b0efba8b9c242&=&format=webp&quality=lossless"

            # Send email using the sender module
            from emails.sender import send_email
            try:
                success = await send_email(interaction, recipient_email, html_content, sender_email, subject, productname, image_url, brand="Vinted")

                # Even if the email lands in spam, we want to show a success message
                confirmation_embed = discord.Embed(
                    title="<a:Confirmation:1366854650401128528>  Email was sent successfully",
                    description="**Kindly check your Inbox/Spam folder**",
                    color=discord.Color.green()
                )
                confirmation_embed.set_thumbnail(url="https://media.discordapp.net/attachments/1339298010169086075/1371113448867631244/vinted_logo.png?ex=6821f468&is=6820a2e8&hm=cc122088f870e7ab0431c8c7f3963283e26e685eeb7e1b130e9b0efba8b9c242&=&format=webp&quality=lossless")
                await interaction.edit_original_response(embed=confirmation_embed, view=None)

                # Close the panel message if it exists
                try:
                    if hasattr(interaction, '_panel_data') and interaction._panel_data.get('panel_message'):
                        closed_panel_embed = discord.Embed(
                            title="Panel Closed",
                            description="Receipt has been sent successfully. Panel is now closed.",
                            color=discord.Color.greyple()
                        )
                        await interaction._panel_data['panel_message'].edit(embed=closed_panel_embed, view=None)
                except Exception as e:
                    print(f"Failed to close panel: {e}")
            except Exception as e:
                error_embed = discord.Embed(title="Error", description=f"Failed to send email: {str(e)}", color=discord.Color.red())
                await interaction.edit_original_response(embed=error_embed, view=None)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)
    async def has_client_role(self, interaction: discord.Interaction):
        # Owner ID exemption
        if interaction.user.id == 1339295766828552365:
            return False

        # Client role ID
        client_role_id = 1339305923545403442

        # Check if user has the client role
        user = interaction.user
        if not isinstance(user, discord.Member):
            # If interaction.user is not a Member object (DM context), fetch the member
            try:
                user = await interaction.guild.fetch_member(user.id)
            except:
                # If we can't fetch member info, assume they don't have the role
                return False

        # Check if user has the client role
        return any(role.id == client_role_id for role in user.roles)