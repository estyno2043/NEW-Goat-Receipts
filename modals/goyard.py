
import discord
from discord import ui
import random
from datetime import datetime

# Global variable to store form data between modals
goyard_form_data = {}

class GoyardModal(ui.Modal, title="Goyard Receipt - Step 1"):
    product_name = discord.ui.TextInput(label="Product Name", placeholder="Saint-Louis GM", required=True)
    product_color = discord.ui.TextInput(label="Product Color", placeholder="Black", required=True)
    product_size = discord.ui.TextInput(label="Product Size", placeholder="GM", required=True)
    sku = discord.ui.TextInput(label="SKU", placeholder="SLGM001", required=True)
    product_price = discord.ui.TextInput(label="Product Price (without currency)", placeholder="1790.00", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global goyard_form_data
        owner_id = str(interaction.user.id)
        
        # Store first form data
        goyard_form_data[owner_id] = {
            'product_name': self.product_name.value,
            'product_color': self.product_color.value,
            'product_size': self.product_size.value,
            'sku': self.sku.value,
            'product_price': self.product_price.value
        }

        embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
        view = GoyardSecondModal(interaction.user.id)
        await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=view, ephemeral=False)

class GoyardSecondModal(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(GoyardSecondModalForm())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)

class GoyardSecondModalForm(ui.Modal, title="Goyard Receipt - Step 2"):
    def __init__(self):
        super().__init__()
        
        self.imagelink = discord.ui.TextInput(label="Product Image Link", placeholder="https://cdn.discordapp.com/attachments/...", required=True)
        self.tax = discord.ui.TextInput(label="Tax Amount (without currency)", placeholder="179.00", required=True)
        self.shipping = discord.ui.TextInput(label="Shipping Amount (without currency)", placeholder="25.00", required=True)
        self.currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)

        self.add_item(self.imagelink)
        self.add_item(self.tax)
        self.add_item(self.shipping)
        self.add_item(self.currency)

    async def on_submit(self, interaction: discord.Interaction):
        global goyard_form_data
        owner_id = str(interaction.user.id)

        from utils.db_utils import get_user_details
        user_details = get_user_details(interaction.user.id)

        if user_details and owner_id in goyard_form_data:
            name, street, city, zipp, country, email = user_details
            first_data = goyard_form_data[owner_id]

            try:
                embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
                await interaction.response.edit_message(content=f"{interaction.user.mention}", embed=embed, view=None)

                with open("receipt/goyard.html", "r", encoding="utf-8") as file:
                    html_content = file.read()

                # Generate random order number
                random_order_number = f"GY{random.randint(100000, 999999)}"
                
                # Get current date
                current_date = datetime.now().strftime("%B %d, %Y")
                
                # Calculate totals
                product_price = float(first_data['product_price'])
                tax_amount = float(self.tax.value)
                shipping_amount = float(self.shipping.value)
                subtotal = product_price
                grand_total = product_price + tax_amount + shipping_amount
                
                # Replace all placeholders in HTML
                html_content = html_content.replace("{{customer_first_name}}", name.split()[0])
                html_content = html_content.replace("{{order_number}}", random_order_number)
                html_content = html_content.replace("{{order_date}}", current_date)
                html_content = html_content.replace("{{product_name}}", first_data['product_name'])
                html_content = html_content.replace("{{product_color}}", first_data['product_color'])
                html_content = html_content.replace("{{product_size}}", first_data['product_size'])
                html_content = html_content.replace("{{sku}}", first_data['sku'])
                html_content = html_content.replace("{{line_total}}", f"{self.currency.value}{product_price:.2f}")
                html_content = html_content.replace("{{subtotal}}", f"{self.currency.value}{subtotal:.2f}")
                html_content = html_content.replace("{{shipping}}", f"{self.currency.value}{shipping_amount:.2f}")
                html_content = html_content.replace("{{tax}}", f"{self.currency.value}{tax_amount:.2f}")
                html_content = html_content.replace("{{grand_total}}", f"{self.currency.value}{grand_total:.2f}")
                
                # Replace shipping and billing details
                html_content = html_content.replace("{{shipping_name}}", name)
                html_content = html_content.replace("{{shipping_address_1}}", street)
                html_content = html_content.replace("{{shipping_address_2}}", f"{city}, {zipp}")
                html_content = html_content.replace("{{shipping_country}}", country)
                html_content = html_content.replace("{{billing_name}}", name)
                html_content = html_content.replace("{{billing_address_1}}", street)
                html_content = html_content.replace("{{billing_address_2}}", f"{city}, {zipp}")
                html_content = html_content.replace("{{billing_country}}", country)
                
                # Replace product image placeholder
                html_content = html_content.replace("https://via.placeholder.com/96", self.imagelink.value)
                
                # Replace order status URL (you can customize this)
                html_content = html_content.replace("{{order_status_url}}", "https://www.goyard.com/en/order-status")

                # Email configuration
                sender_email_normal = "Maison Goyard <clientservice@goyard.com>"
                sender_email_spoofed = "Maison Goyard <no-reply@goyard.com>"
                subject = "Purchase Confirmation"

                from emails.choise import choiseView
                embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(interaction.user.id, html_content, sender_email_normal, subject, first_data['product_name'], self.imagelink.value, sender_email_spoofed)
                await interaction.edit_original_response(embed=embed, view=view)

                # Clean up stored data
                if owner_id in goyard_form_data:
                    del goyard_form_data[owner_id]

            except Exception as e:
                embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                await interaction.edit_original_response(embed=embed)

        else:
            embed = discord.Embed(title="Error", description="No user details found or session expired. Please ensure your information is set up and try again.")
            await interaction.edit_original_response(embed=embed)

# Create a global variable to make the class accessible outside
goyardmodal = GoyardModal
