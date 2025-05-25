import discord
from discord import ui, SelectOption
import sqlite3
import random
import os
import json

class istoresmodal(ui.Modal, title="iStores Order - Step 1"):
    productname = ui.TextInput(label="Product Name", placeholder="Epico Cleaning Kit for AirPods", required=True)
    productcode = ui.TextInput(label="Product Code", placeholder="135091", required=True)
    productprice = ui.TextInput(label="Price with DPH", placeholder="4.90", required=True)
    pricewithouttax = ui.TextInput(label="Price without DPH", placeholder="3.98", required=True)
    shippingcost = ui.TextInput(label="Shipping Cost with DPH", placeholder="2.98", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        # Get user details from database
        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)
        
        if user_details:
            name, street, city, zipp, country, email = user_details

            # Save the values as class attributes for later access
            istoresmodal.productname_value = self.productname.value
            istoresmodal.productcode_value = self.productcode.value
            istoresmodal.productprice_value = self.productprice.value
            istoresmodal.pricewithouttax_value = self.pricewithouttax.value
            istoresmodal.shippingcost_value = self.shippingcost.value

            # Instead of sending another modal, create a button that will trigger the second modal
            view = discord.ui.View()
            button = discord.ui.Button(label="Continue to Step 2", style=discord.ButtonStyle.primary)

            async def button_callback(btn_interaction):
                second_modal = iStoresSecondModal()
                await btn_interaction.response.send_modal(second_modal)

            button.callback = button_callback
            view.add_item(button)

            await interaction.response.send_message("Please click the button below to continue:", view=view, ephemeral=True)
        else:
            await interaction.response.send_message("Please set up your credentials in settings first.", ephemeral=True)


class iStoresSecondModal(ui.Modal, title="iStores Order - Step 2"):
    shippingwithouttax = ui.TextInput(label="Shipping without DPH", placeholder="2.42", required=True)
    yourname = ui.TextInput(label="Your Name", placeholder="Your Name", required=True)
    youremail = ui.TextInput(label="Your Email", placeholder="Your Email", required=True)
    yourphone = ui.TextInput(label="Your Phone", placeholder="Your Phone Number", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id

        # First retrieve user credentials from database
        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, street, city, zipp, country FROM licenses WHERE owner_id = ?", (str(owner_id),))
        user_details = cursor.fetchone()
        conn.close()

        # Check if user credentials exist
        if not user_details:
            await interaction.response.send_message("Please set up your credentials in settings first.", ephemeral=True)
            return

        # Unpack user details
        name, street, city, zipp, country = user_details

        # Get values from the first modal using class attributes
        productname = istoresmodal.productname_value if hasattr(istoresmodal, 'productname_value') else "Epico Cleaning Kit for AirPods"
        productcode = istoresmodal.productcode_value if hasattr(istoresmodal, 'productcode_value') else "135091"
        productprice = istoresmodal.productprice_value if hasattr(istoresmodal, 'productprice_value') else "4.90"
        pricewithouttax = istoresmodal.pricewithouttax_value if hasattr(istoresmodal, 'pricewithouttax_value') else "3.98"
        shippingcost = istoresmodal.shippingcost_value if hasattr(istoresmodal, 'shippingcost_value') else "2.98"

        # Get values from the second modal
        shippingwithouttax = self.shippingwithouttax.value
        yourname = self.yourname.value
        youremail = self.youremail.value
        yourphone = self.yourphone.value

        # Generate random order number
        order_number = ''.join(random.choices('0123456789', k=7))

        # Show loading message
        await interaction.response.defer(ephemeral=True)

        try:
            # Calculate totals
            try:
                total_without_vat = float(pricewithouttax) + float(shippingwithouttax)
                total_with_vat = float(productprice) + float(shippingcost)
            except ValueError:
                # Handle any conversion errors
                total_without_vat = 6.40
                total_with_vat = 7.88

            # Read HTML template
            with open("receipt/istores.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Calculate totals for display
            try:
                total_without_vat = float(pricewithouttax) + float(shippingwithouttax)
                total_with_vat = float(productprice) + float(shippingcost)
            except ValueError:
                # Handle any conversion errors
                total_without_vat = 6.40
                total_with_vat = 7.88

            # Replace placeholders
            html_content = html_content.replace("2522011469", order_number)
            html_content = html_content.replace("{productname}", productname)
            html_content = html_content.replace("{productsku}", productcode)
            html_content = html_content.replace("{productprice}", str(productprice))
            html_content = html_content.replace("{pricewithoutdph}", str(pricewithouttax))
            html_content = html_content.replace("{shippingwithdph}", str(shippingcost))
            html_content = html_content.replace("{shippingwithoutdph}", str(shippingwithouttax))
            html_content = html_content.replace("{totalwithoutdph}", str(total_without_vat))
            html_content = html_content.replace("{totalwithdph}", str(total_with_vat))

            # Make sure all user credentials are properly replaced
            html_content = html_content.replace("{name}", yourname)
            html_content = html_content.replace("{street}", street if street else "")
            html_content = html_content.replace("{city}", city if city else "")
            html_content = html_content.replace("{zip}", zipp if zipp else "")
            html_content = html_content.replace("{country}", country if country else "")
            html_content = html_content.replace("{youremail}", youremail)
            html_content = html_content.replace("{yourphone}", yourphone)

            # Setup email parameters
            from emails.choise import choiseView
            sender_email = "iStores <obchod@istores.sk>"
            subject = f"iStores.sk- Prijatie objednávky č. {order_number}"
            image_url = "https://www.istores.sk/brands/istores-partner.png"

            # Send the email selection view
            embed = discord.Embed(title="Choose email provider", description="Email is ready to send. Choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, productname, image_url, "https://www.istores.sk")
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)
            # Log the error for debugging
            print(f"Error in iStores modal: {str(e)}")