import discord
from discord import ui
import re
import random
from pystyle import Colors
from datetime import datetime

lg = '\033[0m'  # Reset color

class argosmodal(ui.Modal, title="discord.gg/goatreceipt"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="Russell Hobbs Bronte 2 Slice Toaster", required=True)
    productimage = discord.ui.TextInput(label="Product Image URL (Discord Image)", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
    productprice = discord.ui.TextInput(label="Price without currency", placeholder="50.00", required=True)
    productcurrency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)
    productsku = discord.ui.TextInput(label="Product SKU", placeholder="7413016", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, productimage, productprice, productcurrency, productsku, name, street, city, zipp, country
        from addons.nextsteps import NextstepArgos
        owner_id = interaction.user.id 

        import sqlite3
        conn = sqlite3.connect('data.db') # Database connection established here
        cursor = conn.cursor()
        cursor.execute("SELECT name, street, city, zipp, country FROM licenses WHERE owner_id = ?", (str(owner_id),))
        user_details = cursor.fetchone()

        if user_details:
            name, street, city, zipp, country = user_details

            productname = self.productname.value
            productimage = self.productimage.value
            productprice = float(self.productprice.value)
            productcurrency = self.productcurrency.value
            productsku = self.productsku.value

            embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
            await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepArgos(owner_id), ephemeral=True)
            conn.close() # Close the connection after use
        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)


class argosmodal2(ui.Modal, title="Argos Receipt - Details"):
    productshippingcost = discord.ui.TextInput(label="Shipping Costs", placeholder="10.00", required=True)
    productpurchasedate = discord.ui.TextInput(label="Purchase Date (D/M/YYYY)", placeholder="6/5/2025", required=True)
    productarrivaldate = discord.ui.TextInput(label="Arrival Date (D/M/YYYY)", placeholder="7/5/2025", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, productimage, productprice, productcurrency, productsku, name, street, city, zipp, country
        owner_id = interaction.user.id 

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(content=None, embed=embed, view=None)

            with open("receipt/argos.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Calculate total
            price = productprice  # Use the global variable
            shipping = float(self.productshippingcost.value)
            total = price + shipping

            # Generate random order number
            ordernumber = ''.join(random.choices('0123456789', k=10))

            # Replace placeholders in HTML
            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{city}", city)
            html_content = html_content.replace("{zip}", zipp)
            html_content = html_content.replace("{country}", country)
            html_content = html_content.replace("{productname}", productname)
            html_content = html_content.replace("{imageurl}", productimage)
            html_content = html_content.replace("{productsku}", productsku)
            html_content = html_content.replace("{productprice}", str(price))
            html_content = html_content.replace("{productshippingcost}", str(shipping))
            html_content = html_content.replace("{total}", str(total))
            html_content = html_content.replace("{currency}", productcurrency)
            html_content = html_content.replace("{ordernumber}", ordernumber)
            html_content = html_content.replace("{productpurchasedate}", str(self.productpurchasedate.value))
            html_content = html_content.replace("{productarrivaldate}", str(self.productarrivaldate.value))

            # Save the updated HTML
            with open("receipt/updatedrecipies/updatedargos.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            productshippingcost = shipping
            productpurchasedate = self.productpurchasedate.value
            productarrivaldate = self.productarrivaldate.value

            # Total already calculated above

            # Replace placeholders in the HTML
            replacements = {
                "{productname}": productname,
                "{productimage}": productimage,
                "{productprice}": f"{productcurrency}{productprice:.2f}",
                "{productcurrency}": productcurrency,
                "{productsku}": productsku,
                "{productshippingcost}": f"{productcurrency}{productshippingcost:.2f}",
                "{productpurchasedate}": productpurchasedate,
                "{productarrivaldate}": productarrivaldate,
                "{name}": name,
                "{street}": street,
                "{city}": city,
                "{zip}": zipp,
                "{country}": country,
                "{total}": f"{productcurrency}{total:.2f}"
            }

            for placeholder, value in replacements.items():
                html_content = html_content.replace(placeholder, str(value))

            from emails.choise import choiseView
            from emails.normal import SendNormal
            from emails.spoofed import SendSpoofed

            # Log the data
            print()
            print(f"[{Colors.green}START Scraping{lg}] ARGOS -> {interaction.user.id} ({interaction.user})" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {productname}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Product Price: {productprice}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Arrival Date: {productarrivaldate}" + lg)
            print(f"[{Colors.green}Scraping DONE{lg}] ARGOS -> {interaction.user.id}" + lg)
            print()

            # Display email provider selection menu
            sender_email = "Argos <order-confirmation@argos.co.uk>"
            subject = "Your Argos order confirmation"
            
            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, productname, productimage, "https://www.argos.co.uk")
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}", color=0xff0000)
            await interaction.edit_original_response(embed=embed)
            print(f"Error in argosmodal2: {e}")