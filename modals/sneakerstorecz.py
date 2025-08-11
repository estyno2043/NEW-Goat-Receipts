
import discord
from discord import ui
import random
from addons.nextsteps import NextstepSneakerStoreCZ

class SneakerStoreCZModal(ui.Modal, title="SneakerStore CZ - Step 1"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="Enter name of the product", required=True)
    productid = discord.ui.TextInput(label="Product ID", placeholder="ex. 2620/46", required=True)
    pricecost = discord.ui.TextInput(label="Price Cost", placeholder="00.00", required=True)
    currency = discord.ui.TextInput(label="Currency (€, $, £)", placeholder="(€, $, £)", required=True, min_length=1, max_length=2)
    shippingfee = discord.ui.TextInput(label="Shipping Fee", placeholder="0.00", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global sneakerstorecz_form_data
        owner_id = interaction.user.id

        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)
            
            if user_details:
                name, street, city, zipp, country, email = user_details

                # Store first form data globally
                if 'sneakerstorecz_form_data' not in globals():
                    global sneakerstorecz_form_data
                    sneakerstorecz_form_data = {}

                sneakerstorecz_form_data[str(owner_id)] = {
                    'productname': self.productname.value,
                    'productid': self.productid.value,
                    'pricecost': self.pricecost.value,
                    'currency': self.currency.value,
                    'shippingfee': self.shippingfee.value,
                    'name': name,
                    'street': street,
                    'city': city,
                    'zipp': zipp,
                    'country': country,
                    'email': email
                }

                embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
                await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepSneakerStoreCZ(owner_id))
            else:
                embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class SneakerStoreCZModal2(ui.Modal, title="SneakerStore CZ - Step 2"):
    productsize = discord.ui.TextInput(label="Product Size", placeholder="Velikost", required=True)
    deliveryplace = discord.ui.TextInput(label="Delivery Place (Z-BOX)", placeholder="Z-BOX", required=True)
    orderdate = discord.ui.TextInput(label="Order Date", placeholder="Date of your order", required=True)
    ordernumber = discord.ui.TextInput(label="Order Number", placeholder="ex. 2025005105", required=True)
    imagelink = discord.ui.TextInput(label="Product Image Link", placeholder="Link of the image", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global sneakerstorecz_form_data
        owner_id = str(interaction.user.id)

        try:
            # Check if first form data exists
            if 'sneakerstorecz_form_data' not in globals() or owner_id not in sneakerstorecz_form_data:
                await interaction.response.send_message("Session expired. Please start over.", ephemeral=True)
                return

            first_data = sneakerstorecz_form_data[owner_id]

            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(embed=embed, view=None)

            # Calculate total price
            try:
                total_price = float(first_data['pricecost']) + float(first_data['shippingfee'])
                total_price_str = f"{total_price:.2f}"
            except ValueError:
                total_price_str = "184.00"

            # Read HTML template
            with open("receipt/sneakerstorecz.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Replace placeholders with form data
            html_content = html_content.replace("{ordernumber}", self.ordernumber.value)
            html_content = html_content.replace("{orderdate}", self.orderdate.value)
            html_content = html_content.replace("{name}", first_data['name'])
            html_content = html_content.replace("{street}", first_data['street'])
            html_content = html_content.replace("{city}", first_data['city'])
            html_content = html_content.replace("{zipp}", first_data['zipp'])
            html_content = html_content.replace("{country}", first_data['country'])
            html_content = html_content.replace("{imagelink}", self.imagelink.value)
            html_content = html_content.replace("{productid}", first_data['productid'])
            html_content = html_content.replace("{productname}", first_data['productname'])
            html_content = html_content.replace("{productsize}", self.productsize.value)
            html_content = html_content.replace("{deliveryplace}", self.deliveryplace.value)
            html_content = html_content.replace("{currency}", first_data['currency'])
            html_content = html_content.replace("{pricecost}", first_data['pricecost'])
            html_content = html_content.replace("{shippingfee}", first_data['shippingfee'])
            html_content = html_content.replace("{totalprice}", total_price_str)

            # Save updated HTML
            with open("receipt/updatedrecipies/updatedsneakerstorecz.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            # Prepare email choice panel
            from emails.choise import choiseView
            sender_email = "info@sneakerstore.cz"
            subject = f"SneakerStore objednávka [{self.ordernumber.value}]"
            owner_id = interaction.user.id
            link = "https://www.sneakerstore.cz/"

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, first_data['productname'], self.imagelink.value, link)
            await interaction.edit_original_response(embed=embed, view=view)

            # Clean up stored data
            if owner_id in sneakerstorecz_form_data:
                del sneakerstorecz_form_data[owner_id]

        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.edit_original_response(embed=embed)

# Add alias for dynamic loading
sneakerstoreczmodal = SneakerStoreCZModal
