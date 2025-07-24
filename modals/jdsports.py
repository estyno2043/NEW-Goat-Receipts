import asyncio
import json
import re
import webbrowser
import discord
from discord.ui import Select
from discord import SelectOption, ui, app_commands

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





def is_jd_link(link):
    # Accept all valid URLs
    return True


class jdsportsmodal(ui.Modal, title="discord.gg/goatreceipt"):
    Linkff = discord.ui.TextInput(label="Link", placeholder="JD Sports Link (any country)", required=True)
    Priceff = discord.ui.TextInput(label="Price without currency", placeholder="Ex. 790", required=True)
    currencyff = discord.ui.TextInput(label="Currency ($, £‚ €)", placeholder="€", required=True, min_length=1, max_length=2)
    delivery = discord.ui.TextInput(label="Order Date", placeholder="Ex. 24/04/2024", required=True)
    Size = discord.ui.TextInput(label="Size", placeholder="Ex. M", required=True)


    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)
        
        if user_details:
            name, street, city, zipp, country, email = user_details

            Linkff = self.Linkff.value
            currencyff = self.currencyff.value
            Priceff = self.Priceff.value
            delivery = self.delivery.value



            if not is_jd_link(Linkff):
                embed = discord.Embed(title="Error - Invalid JD Sports link", description="Please provide a valid JD Sports link from any supported country domain.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            try:
                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
                await interaction.response.send_message(content=f"{interaction.user.mention}",embed=embed, ephemeral=True)



                with open("receipt/jdsports.html", "r", encoding="utf-8") as file:
                    html_content = file.read()



                url = Linkff

                response = requests.get(
                    url=url,
                    proxies={
                        "http": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                        "https": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                    },
                    verify=False  # Disable SSL verification for now
                )


                product_name = None
                first_img_link = None

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    print()
                    print(f"[{Colors.green}START Scraping{lg}] JD SPORTS -> {interaction.user.id} ({interaction.user})" + lg)


                    try:
                        product_name_element = soup.find('h1', {'itemprop': 'name'})
                        if product_name_element:
                            product_name = product_name_element.text.strip()
                            print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {product_name}" + lg)
                        else:
                            product_name = "JD Sports Product"
                            print(f"    [{Colors.yellow}Warning{lg}] Could not find product name, using default" + lg)
                    except Exception as name_error:
                        product_name = "JD Sports Product"
                        print(f"    [{Colors.yellow}Warning{lg}] Product name scraping failed: {str(name_error)}, using default" + lg)



                    try:
                        first_img_element = soup.find('li', {'class': 'tap-zoom'})
                        if first_img_element:
                            img_tag = first_img_element.find('img')
                            if img_tag and 'src' in img_tag.attrs:
                                first_img_link = img_tag['src']
                                print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {first_img_link}" + lg)
                            else:
                                first_img_link = "https://via.placeholder.com/300x300?text=JD+Sports"
                                print(f"    [{Colors.yellow}Warning{lg}] Could not find image src, using placeholder" + lg)
                        else:
                            first_img_link = "https://via.placeholder.com/300x300?text=JD+Sports"
                            print(f"    [{Colors.yellow}Warning{lg}] Could not find tap-zoom element, using placeholder" + lg)
                    except Exception as img_error:
                        first_img_link = "https://via.placeholder.com/300x300?text=JD+Sports"
                        print(f"    [{Colors.yellow}Warning{lg}] Image scraping failed: {str(img_error)}, using placeholder" + lg)

                    print(f"[{Colors.green}Scraping DONE{lg}] JD SPORTS -> {interaction.user.id}" + lg)
                    print()


                size = self.Size.value




                delivery_date = datetime.strptime(delivery, '%d/%m/%Y')
                adjusted_delivery_date = delivery_date + datetime.timedelta(days=3)

                formatted_delivery_date = adjusted_delivery_date.strftime('%d/%m/%Y')

                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{orderdate}", delivery)
                html_content = html_content.replace("{orderdate3d}", formatted_delivery_date)
                html_content = html_content.replace("{price}", str(Priceff))
                html_content = html_content.replace("{productlink}", str(first_img_link))
                html_content = html_content.replace("{productname}", str(product_name))
                html_content = html_content.replace("{size}", size)
                html_content = html_content.replace("{link}", str(Linkff))
                html_content = html_content.replace("{currency}", str(currencyff))


                with open("receipt/updatedrecipies/updatedjdsports.html", "w", encoding="utf-8") as file:
                    file.write(html_content)

                sender_email = "JD Sports <sales@jdsports.co.uk>"
                subject = "Thanks for your order"
                from emails.choise import choiseView
                owner_id = interaction.user.id
                link = "https://jdsports.co.uk/"


                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(owner_id, html_content, sender_email, subject, product_name, first_img_link, link)
                await interaction.edit_original_response(embed=embed, view=view)

            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.edit_original_response(embed=embed)


        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)