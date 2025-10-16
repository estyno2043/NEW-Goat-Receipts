import discord
from discord import ui
from datetime import datetime
import random

# Global variable to store first form data
sixpm_form_data = {}

class SixPMModal(ui.Modal, title="6PM Order - Step 1"):
    productname = ui.TextInput(label="Product Name", placeholder="Enter the product name", required=True)
    productimage = ui.TextInput(label="Product Image", placeholder="Enter the product image link", required=True)
    productshippingcost = ui.TextInput(label="Product Shipping Cost", placeholder="Enter the product shipping cost (e.g, 10.00)", required=True)
    producttaxescost = ui.TextInput(label="Product Taxes Cost", placeholder="Enter the product taxes cost (e.g, 10.00)", required=True)
    productprice = ui.TextInput(label="Product Price", placeholder="Enter the product price (e.g, 100.00)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # Store form data globally for the second modal
        global sixpm_form_data
        sixpm_form_data[str(interaction.user.id)] = {
            'productname': self.productname.value,
            'productimage': self.productimage.value,
            'productshippingcost': self.productshippingcost.value,
            'producttaxescost': self.producttaxescost.value,
            'productprice': self.productprice.value
        }

        embed = discord.Embed(
            title="You are almost done...",
            description="Complete the next modal to receive the receipt.",
            color=discord.Color.from_str("#c2ccf8")
        )

        view = ui.View()
        continue_button = ui.Button(label="Continue to Step 2", style=discord.ButtonStyle.green)

        async def continue_callback(btn_interaction):
            second_modal = SixPMSecondModal()
            await btn_interaction.response.send_modal(second_modal)

        continue_button.callback = continue_callback
        view.add_item(continue_button)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)


class SixPMSecondModal(ui.Modal, title="6PM Order - Step 2"):
    productcurrency = ui.TextInput(label="Product Currency", placeholder="Enter the product currency (e.g, £)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global sixpm_form_data
        owner_id = str(interaction.user.id)

        try:
            # Check if first form data exists
            if owner_id not in sixpm_form_data:
                await interaction.response.send_message("Session expired. Please start over.", ephemeral=True)
                return

            first_data = sixpm_form_data[owner_id]

            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=discord.Color.from_str("#826bc2"))
            await interaction.response.edit_message(embed=embed, view=None)

            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                name, street, city, zipp, country, email = user_details

                # Calculate total
                product_price = float(first_data['productprice'])
                shipping_cost = float(first_data['productshippingcost'])
                taxes_cost = float(first_data['producttaxescost'])
                total = product_price + shipping_cost + taxes_cost

                # Generate random order number
                import random
                order_number = f"{random.randint(1000000, 9999999)}-{random.randint(10000000, 99999999)}"

                # Read and process HTML template
                with open("receipt/6pm.html", "r", encoding="utf-8") as file:
                    html_content = file.read()

                # Replace all placeholders
                html_content = html_content.replace("{{order_number}}", order_number)
                html_content = html_content.replace("{{product_name}}", first_data['productname'])
                html_content = html_content.replace("{{product_image}}", first_data['productimage'])
                html_content = html_content.replace("{{product_price}}", first_data['productprice'])
                html_content = html_content.replace("{{shipping_cost}}", first_data['productshippingcost'])
                html_content = html_content.replace("{{taxes_cost}}", first_data['producttaxescost'])
                html_content = html_content.replace("{{currency}}", self.productcurrency.value)
                html_content = html_content.replace("{{total}}", f"{total:.2f}")
                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{country}", country)

                # Save updated HTML
                import os
                os.makedirs("receipt/updatedrecipies", exist_ok=True)
                with open("receipt/updatedrecipies/updated6pm.html", "w", encoding="utf-8") as file:
                    file.write(html_content)

                # Email choice view
                from emails.choise import choiseView
                sender_email = "6PM <no-reply@6pmseason.com>"
                subject = f"Thank You For Your Order #{order_number}"
                link = "https://6pmseason.com/"

                embed = discord.Embed(title="Choose Email Type", description="Select whether to send from a normal or spoofed email domain.", color=discord.Color.from_str("#c2ccf8"))
                view = choiseView(interaction.user.id, html_content, sender_email, subject, first_data['productname'], first_data['productimage'], link)
                await interaction.edit_original_response(embed=embed, view=view)

                # Clean up stored data
                if owner_id in sixpm_form_data:
                    del sixpm_form_data[owner_id]
            else:
                await interaction.edit_original_response(content="Please set up your credentials in settings first.", embed=None, view=None)

        except Exception as e:
            print(f"Error in 6PM second modal: {e}")
            await interaction.edit_original_response(content="An error occurred. Please try again.", embed=None, view=None)

# Create alias for compatibility
sixpmmodal = SixPMModal