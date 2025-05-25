import random
import re
import discord
from discord import ui



import requests  # gen random guid





from bs4 import BeautifulSoup

from pystyle import Colors



r = Colors.red
lg = Colors.light_gray



def is_adidas_link(link):
    adidas_pattern = re.compile(r'^https?://(www\.)?adidas\.com/.+')

    return bool(adidas_pattern.match(link))


class adidasmodal(ui.Modal, title="Adidas Receipt"):
    image_url = discord.ui.TextInput(label="Product Image URL", placeholder="https://example.com/image.jpg", required=True)
    pname = discord.ui.TextInput(label="Product Name", placeholder="Adidas Roadstar", required=True)
    Price = discord.ui.TextInput(label="Price without currency", placeholder="190.00", required=True)
    tax = discord.ui.TextInput(label="Tax Costs", placeholder="10.00", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)



    async def on_submit(self, interaction: discord.Interaction):
        global Price, currency, name, street, city, zipp, country, tax, image_url, pname
        from addons.nextsteps import NextstepAdidas
        owner_id = interaction.user.id 

        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, street, city, zipp, country FROM licenses WHERE owner_id = ?", (str(owner_id),))
        user_details = cursor.fetchone()

        if user_details:
            name, street, city, zipp, country = user_details

            currency = self.currency.value
            Price = float(self.Price.value)
            tax = float(self.tax.value)
            image_url = self.image_url.value
            pname = self.pname.value



            embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
            await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepAdidas(owner_id), ephemeral=False)
        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=False)




class adidasmodal2(ui.Modal, title="Adidas Receipt"):
    pcode = discord.ui.TextInput(label="Product Code", placeholder="JQ5111", required=True)
    size = discord.ui.TextInput(label="Size", placeholder="M", required=True)




    async def on_submit(self, interaction: discord.Interaction):
        global Price, currency, name, street, city, zipp, country, tax, image_url
        owner_id = interaction.user.id
        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                name, street, city, zipp, country, email = user_details

                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
                await interaction.response.edit_message(embed=embed, view=None)

                with open("receipt/adidas.html", "r", encoding="utf-8") as file:
                    html_content = file.read()

                pcode = self.pcode.value
                size = self.size.value

                # Default color
                colorr = "Black"

                print()
                print(f"[{Colors.green}Receipt Generation{lg}] Adidas-> {interaction.user.id} ({interaction.user})" + lg)
                print(f"    [{Colors.cyan}Details{lg}] Product Name: {pname}" + lg)
                print(f"    [{Colors.cyan}Details{lg}] Product Size: {size}" + lg)
                print(f"    [{Colors.cyan}Details{lg}] Product Price: {currency}{Price}" + lg)
                print(f"    [{Colors.cyan}Details{lg}] Image URL: {image_url}" + lg)
                print(f"[{Colors.green}Generation DONE{lg}] Adidas -> {interaction.user.id}" + lg)
                print()

                # Calculate total
                fulltotal = tax + Price
                fulltotal = round(fulltotal, 2)

                def generate_order_number():
                    return str(random.randint(1000000000, 9999999999))  # Generates a number between 1000000000 and 9999999999

                # Generate order number
                order_number = generate_order_number()

                # Replace all placeholders in HTML
                html_content = html_content.replace("{ordernumber}", order_number)
                html_content = html_content.replace("{pname}", pname)
                html_content = html_content.replace("{price}", str(Price))
                html_content = html_content.replace("{tax}", str(tax))
                html_content = html_content.replace("{total}", str(fulltotal))
                html_content = html_content.replace("{currency}", currency)
                html_content = html_content.replace("{color}", colorr)
                html_content = html_content.replace("{size}", size)
                html_content = html_content.replace("{articelno}", pcode)
                html_content = html_content.replace("{imageurl}", image_url)
                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{country}", country)



                with open("receipt/updatedrecipies/updatedadidas.html", "w", encoding="utf-8") as file:
                    file.write(html_content)

                from emails.choise import choiseView
                sender_email = "adidas CONFIRMED <noreply@adidas.com>"
                subject = "Order: CONFIRMED"


                # Create link from the product name and image URL for reference
                link = is_adidas_link(image_url) and image_url or f"https://adidas.com/search?q={pname.replace(' ', '+')}"

                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(owner_id, html_content, sender_email, subject, pname, image_url, link)
                await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)