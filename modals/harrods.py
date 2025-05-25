
import random
import re
import discord
from discord import ui
import requests
from bs4 import BeautifulSoup
from pystyle import Colors

r = Colors.red
lg = Colors.light_gray

def is_harrods_link(link):
    harrods_pattern = re.compile(r'^https?://(www\.)?harrods\.com/.+')
    return bool(harrods_pattern.match(link))

class harrodsmodal(ui.Modal, title="discord.gg/goatreceipt"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="Bottega Veneta Sunglasses", required=True)
    imagelink = discord.ui.TextInput(label="Image URL", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
    productsku = discord.ui.TextInput(label="Product SKU", placeholder="2600d1", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, imagelink, productsku, currency
        from addons.nextsteps import NextstepHarrods
        owner_id = interaction.user.id 

        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

        if user_details:
            name, street, city, zipp, country = user_details

            productname = self.productname.value
            imagelink = self.imagelink.value
            productsku = self.productsku.value
            currency = self.currency.value

            embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
            await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepHarrods(owner_id))
        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class harrodsmodal2(ui.Modal, title="discord.gg/goatreceipt"):
    productprice = discord.ui.TextInput(label="Product Price", placeholder="520.00", required=True)
    shippingcost = discord.ui.TextInput(label="Shipping Cost", placeholder="10.00", required=True)
    deliverydate = discord.ui.TextInput(label="Delivery Date", placeholder="DD/MM/YYYY", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, imagelink, productsku, currency
        owner_id = interaction.user.id 

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(embed=embed, view=None)

            with open("receipt/harrods.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            print()
            print(f"[{Colors.green}START Scraping{lg}] Harrods -> {interaction.user.id} ({interaction.user})" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {productname}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {imagelink}" + lg)
            print(f"[{Colors.green}Scraping DONE{lg}] Harrods -> {interaction.user.id}" + lg)
            print()

            # Get user details from database
            from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

            if not user_details:
                raise Exception("User details not found")

            name, street, city, zipp, country = user_details
            
            # Get values from form
            productprice = self.productprice.value
            shippingcost = self.shippingcost.value
            deliverydate = self.deliverydate.value

            # Calculate total
            try:
                total_price = float(productprice) + float(shippingcost)
                total_formatted = f"{total_price:.2f}"
            except ValueError:
                total_formatted = f"{productprice}"

            # Generate random order number
            def generate_order_number():
                return ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(6))

            order_number = generate_order_number()

            # Replace placeholders in HTML
            html_content = html_content.replace("0FSGQ8", order_number)
            html_content = html_content.replace("{orderNumber}", order_number)
            html_content = html_content.replace("2456 Miller Dale\nPort Sarahfurt, OK 06684 \n                  <br>Obrienberg Stevensville  \n                  <br>56370\n                  <br>Guadeloupe", f"{street}\n{city} \n                  <br>{zipp}  \n                  <br>{country}")
            html_content = html_content.replace("BOTTEGA VENETA", productname)
            html_content = html_content.replace("2600d1", productsku)
            html_content = html_content.replace("5/4/2025", deliverydate)
            html_content = html_content.replace("€520.00", f"{currency}{productprice}")
            html_content = html_content.replace("€10.00", f"{currency}{shippingcost}")
            html_content = html_content.replace("€530.00", f"{currency}{total_formatted}")
            
            # Replace placeholder variables with curly braces
            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{city}", city)
            html_content = html_content.replace("{zip}", zipp)
            html_content = html_content.replace("{country}", country)
            html_content = html_content.replace("{productname}", productname)
            html_content = html_content.replace("{productsku}", productsku)
            html_content = html_content.replace("{currency}", currency)
            html_content = html_content.replace("{productprice}", productprice)
            html_content = html_content.replace("{shippingcost}", shippingcost)
            html_content = html_content.replace("{deliverydate}", deliverydate)
            html_content = html_content.replace("{total}", total_formatted)
            html_content = html_content.replace("{imagelink}", imagelink)
            
            # Replace product image
            html_content = html_content.replace("https://ci3.googleusercontent.com/meips/ADKq_NZ-Ihr4s8RWhpn3qNkit4hfupI62vUZEt_YbfBMXwAicFVPJB-Bad6ApchfHpV_7pIfZgp3_A08hXmFO77mzzKbkfuWpAymWxkaZ2yW1a-5mCESG64DyLnPOiMvGOIyDwQGVH0RpBN1nzUyV9Pq1yo1D_ZrIX5iHoqn2JuG_NkSjCcp2UBbRzWmeb3f_XLcsgYaJs4gMwSd01JUwQ=s0-d-e1-ft#https://hrd-live.cdn.scayle.cloud/images/4c98024e9217ede09d3dd27f7055e63c.jpg?brightness=1&amp;width=922&amp;height=1230&amp;quality=75&amp;bg=ffffff", imagelink)

            with open("receipt/updatedrecipies/updatedharrods.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            from emails.choise import choiseView
            sender_email = "Harrods <no-reply@orders.mail.harrods.com>"
            subject = "Thank you for your order"
            link = "https://harrods.com/"

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, productname, imagelink, link)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)
