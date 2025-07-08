import re
import random
import discord
import requests
from discord import ui
from discord.ui import Modal, TextInput
from bs4 import BeautifulSoup
from emails.choise import choiseView
from pystyle import Colors

lg = "\033[0m"  # Text reset to default color

class synaworldmodal(ui.Modal, title="Synaworld Order - Step 1"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="Synaworld Syna Logo Twinset Black", required=True)
    productsize = discord.ui.TextInput(label="Product Size", placeholder="L", required=True)
    productprice = discord.ui.TextInput(label="Product Price", placeholder="100.00", required=True)
    taxcost = discord.ui.TextInput(label="Tax Cost", placeholder="0.00", required=True)
    productcurrency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, productsize, productprice, taxcost, productcurrency
        owner_id = interaction.user.id 

        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

        if user_details:
            name, street, city, zipp, country, email = user_details

            # Store user inputs
            productname = self.productname.value
            productsize = self.productsize.value
            productprice = self.productprice.value
            taxcost = self.taxcost.value
            productcurrency = self.productcurrency.value

            # Continue to next step with button
            embed = discord.Embed(
                title="Product Information Provided",
                description=f"Product: {productname}\nSize: {productsize}\nPrice: {productcurrency}{productprice}",
                color=0x2F3136
            )

            # Create button to proceed to second form
            class NextStepButton(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=300)

                @discord.ui.button(label="Continue to Step 2", style=discord.ButtonStyle.primary)
                async def continue_button(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    if button_interaction.user.id == owner_id:
                        second_modal = synaworldmodal2()
                        await button_interaction.response.send_modal(second_modal)
                    else:
                        await button_interaction.response.send_message("This button is not for you!", ephemeral=True)

            await interaction.response.send_message(embed=embed, view=NextStepButton(), ephemeral=False)

            print()
            print(f"[{Colors.green}Product Info{lg}] Synaworld -> {interaction.user.id} ({interaction.user})" + lg)
            print(f"    [{Colors.cyan}Details{lg}] Product Name: {productname}" + lg)
            print(f"    [{Colors.cyan}Details{lg}] Product Size: {productsize}" + lg)
            print(f"    [{Colors.cyan}Details{lg}] Product Price: {productcurrency}{productprice}" + lg)
        else:
            embed = discord.Embed(
                title="No License Found",
                description="You don't have a saved license. Please run `/settings` first.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=False)


class synaworldmodal2(ui.Modal, title="Synaworld Order - Step 2"):
    shippingcost = discord.ui.TextInput(label="Shipping Cost", placeholder="10.00", required=True)
    productimagelink = discord.ui.TextInput(label="Product Image URL", placeholder="https://example.com/image.jpg", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, productsize, productprice, taxcost, productcurrency
        owner_id = interaction.user.id

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your receipt...", color=0x1e1f22)
            await interaction.response.send_message(embed=embed, ephemeral=False)

            # Store shipping cost and image link
            shippingcost = self.shippingcost.value
            imageurl = self.productimagelink.value

            # Generate random order number
            random_number = random.randint(100000, 999999)

            # Calculate total
            try:
                total = float(productprice) + float(shippingcost) + float(taxcost)
                total_str = f"{total:.2f}"
            except ValueError:
                total_str = "138.00"  # Default fallback

            # Read HTML template
            with open("receipt/synaworld.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Prepare receipt
            html_content = html_content.replace("ORDER 551512", f"ORDER {random_number}")
            html_content = html_content.replace("Synaworld Syna Logo Twinset Black - Syna World", productname)

            # Replace only the product image in the order summary section
            # First identify the Order Summary section
            order_summary_section = html_content.find('<h3 style="font-weight:normal;font-size:20px;margin:0px 0px 25px;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Oxygen,Ubuntu,Cantarell,\'Fira Sans\',\'Droid Sans\',\'Helvetica Neue\',sans-serif">Order summary</h3>')
            if order_summary_section != -1:
                # Find the first image after the Order Summary heading
                order_img_pattern = r'<img style="margin-right:15px;border-radius:8px;border:1px solid #e5e5e5;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Oxygen,Ubuntu,Cantarell,\'Fira Sans\',\'Droid Sans\',\'Helvetica Neue\',sans-serif"[^>]*?class="CToWUd"'
                # Replace only this specific product image
                html_content = re.sub(order_img_pattern, f'<img style="margin-right:15px;border-radius:8px;border:1px solid #e5e5e5;font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,Oxygen,Ubuntu,Cantarell,\'Fira Sans\',\'Droid Sans\',\'Helvetica Neue\',sans-serif" src="{imageurl}" width="50" height="50" class="CToWUd"', html_content, count=1)

            # Replace all placeholders
            html_content = html_content.replace("{randomnumber}", str(random_number))
            html_content = html_content.replace("{productname}", productname)
            html_content = html_content.replace("{productsize}", productsize)
            html_content = html_content.replace("{productprice}", productprice)
            html_content = html_content.replace("{productcurrency}", productcurrency)
            html_content = html_content.replace("{shippingcost}", shippingcost)
            html_content = html_content.replace("{taxcost}", taxcost)
            html_content = html_content.replace("{total_str}", total_str)

            # Replace customer information
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                name, street, city, zipp, country, email = user_details
                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{country}", country)

            # Save the modified HTML to a temporary file
            receipt_path = f"synaworld_receipt_{interaction.user.id}.html"
            with open(receipt_path, "w", encoding="utf-8") as file:
                file.write(html_content)

            # Prompt user to choose email type
            from emails.choise import choiseView
            sender_email = "Syna World <noreply@synaworld.com>"
            subject = f"Order {random_number} confirmed"
            link = "https://synaworlds.com/"

            embed = discord.Embed(
                title="Choose email provider",
                description="Email is ready to send. Choose Spoofed or Normal domain.",
                color=0x1e1f22
            )
            view = choiseView(owner_id, html_content, sender_email, subject, productname, imageurl, link)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred while generating the receipt: {str(e)}",
                color=0xFF0000
            )
            await interaction.edit_original_response(embed=embed)