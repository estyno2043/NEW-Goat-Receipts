
import discord
from discord import ui
from datetime import datetime

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

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


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

            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
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

                # Email choice view
                from emails.choise import EmailChoiceView
                email_view = EmailChoiceView(
                    brand="6pm",
                    product_name=first_data['productname'],
                    product_image=first_data['productimage'],
                    product_price=first_data['productprice'],
                    shipping_cost=first_data['productshippingcost'],
                    taxes_cost=first_data['producttaxescost'],
                    currency=self.productcurrency.value,
                    total=f"{total:.2f}",
                    customer_name=name,
                    customer_email=email,
                    customer_street=street,
                    customer_city=city,
                    customer_zip=zipp,
                    customer_country=country,
                    spoofed_sender="admin@vegasstrongbirdsupply.com",
                    sender_name="6PM",
                    subject="Your order has been processed!"
                )

                embed = discord.Embed(
                    title="Choose Email Type",
                    description="Select whether to send from a normal or spoofed email domain.",
                    color=discord.Color.from_str("#c2ccf8")
                )
                await interaction.edit_original_response(embed=embed, view=email_view)

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
