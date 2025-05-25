import random
import discord
from discord import ui
import requests
from bs4 import BeautifulSoup
from pystyle import Colors

r = Colors.red
lg = Colors.light_gray

class uggmodal(ui.Modal, title="UGG Receipt Generator"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="TASMAN II", required=True)
    imagelink = discord.ui.TextInput(label="Image URL", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
    productsize = discord.ui.TextInput(label="Product Size", placeholder="46", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, imagelink, productsize, currency
        from addons.nextsteps import NextstepUgg
        owner_id = interaction.user.id 

        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

        if user_details:
            name, street, city, zipp, country = user_details

            productname = self.productname.value
            imagelink = self.imagelink.value
            productsize = self.productsize.value
            currency = self.currency.value

            embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
            await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepUgg(owner_id), ephemeral=False)
        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class uggmodal2(ui.Modal, title="UGG Receipt Generator (2/2)"):
    productprice = discord.ui.TextInput(label="Product Price", placeholder="138.00", required=True)
    shippingprice = discord.ui.TextInput(label="Shipping Price", placeholder="10.00", required=True)
    taxcost = discord.ui.TextInput(label="Tax Cost", placeholder="10.00", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, imagelink, productsize, currency
        owner_id = interaction.user.id 

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(embed=embed, view=None)

            with open("receipt/ugg.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            print()
            print(f"[{Colors.green}START Scraping{lg}] UGG -> {interaction.user.id} ({interaction.user})" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {productname}" + lg)
            print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {imagelink}" + lg)
            print(f"[{Colors.green}Scraping DONE{lg}] UGG -> {interaction.user.id}" + lg)
            print()

            # Get user details from database
            from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

            if not user_details:
                raise Exception("User details not found")

            name, street, city, zipp, country = user_details

            # Get form values
            productprice = self.productprice.value
            shippingprice = self.shippingprice.value
            taxcost = self.taxcost.value

            # Calculate total
            try:
                product_price_float = float(productprice)
                shipping_price_float = float(shippingprice)
                tax_cost_float = float(taxcost)
                total = product_price_float + shipping_price_float + tax_cost_float
                total_formatted = f"{total:.2f}"
            except ValueError:
                total_formatted = "Error calculating total"

            # Generate random order number
            def generate_order_number():
                prefix = "NA"
                number_part = ''.join(random.choice('0123456789') for _ in range(8))
                return f"{prefix}{number_part}"

            order_number = generate_order_number()

            # Replace content in HTML
            html_content = html_content.replace("NA03860822", order_number)
            html_content = html_content.replace("Order #NA03860822", f"Order #{order_number}")

            # Replace product image
            html_content = html_content.replace('https://ci3.googleusercontent.com/meips/ADKq_NZm1P-zGLLaaPu6sVruMXx-nKd8FGXKTTI4CO-XpohT-EoXrCfmqVkrSWXex-85w-mUUjGsQZZadrlW8uHIzWiR7cuXZj6zL0qTtJ0SBL6AD_IPvJIvC1A=s0-d-e1-ft#https://photos6.spartoo.sk/photos/278/27871229/27871229_1200_A.jpg', imagelink)

            # Update the UGG logo image
            html_content = html_content.replace('https://i.imgur.com/NsUCTYI.png', 'https://ci3.googleusercontent.com/meips/ADKq_NaO-9a5OvmqmOAhGs6uu_4TvhCJVvipN6Qz_HGaO0E6RlKlDN9FF4iS9ePs3P4PJqN992lsm__r46qiHGhmIlYn4Q2_R2vVH24Xkwlp_jU=s0-d-e1-ft#https://images.usw2.cordial.com/1663/204x100/ugg_logo.png')

            # Replace product details
            html_content = html_content.replace("TASMAN II", productname)
            html_content = html_content.replace("46", productsize)
            html_content = html_content.replace("€138.00", f"{currency}{productprice}")

            # Replace shipping address placeholders
            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{city}", city)
            html_content = html_content.replace("{zip}", zipp)
            html_content = html_content.replace("{country}", country)

            # Replace order summary values
            html_content = html_content.replace("Sales Subtotal: €138.00", f"Sales Subtotal: {currency}{productprice}")
            html_content = html_content.replace("Product Discount: €0.00", f"Product Discount: {currency}0.00")
            html_content = html_content.replace("Gift Wrap: €0.00", f"Gift Wrap: {currency}0.00")
            html_content = html_content.replace("Shipping: €10.00", f"Shipping: {currency}{shippingprice}")
            html_content = html_content.replace("Ship Discount: €0.00", f"Ship Discount: {currency}0.00")
            html_content = html_content.replace("Tax: €10.00", f"Tax: {currency}{taxcost}")
            html_content = html_content.replace("Total: €158.00", f"Total: {currency}{total_formatted}")

            with open("receipt/updatedrecipies/updatedugg.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            from emails.choise import choiseView
            sender_email = "UGG <no-reply@emails.ugg.com>"
            subject = "Thank you for your order"
            link = "https://www.ugg.com/"

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, productname, imagelink, link)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)