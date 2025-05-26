import discord
from discord import ui
import sqlite3
import random
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# For colored console output
class Colors:
    red = '\033[91m'
    green = '\033[92m'
    yellow = '\033[93m'
    blue = '\033[94m'
    magenta = '\033[95m'
    cyan = '\033[96m'
    white = '\033[97m'
    end = '\033[0m'

# Reset color code
lg = Colors.end

# Validate if the provided URL is from guapi.ch
def is_guapi_link(link):
    pattern = r'https?://(?:www\.)?guapi\.ch'
    return bool(re.match(pattern, link))

class guapimodal(ui.Modal, title="Guapi Order - Step 1"):
    productlink = ui.TextInput(label="Product Link", placeholder="https://www.guapi.ch/collections/...", required=True)
    productsize = ui.TextInput(label="Size", placeholder="XL", required=True)
    productprice = ui.TextInput(label="Price without currency", placeholder="138.00", required=True)
    currency = ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=1)
    shippingcost = ui.TextInput(label="Shipping Cost", placeholder="0.00", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        # Get user details from database
        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)
        
        if user_details:
            name, street, city, zipp, country, email = user_details

            # Validate the product link
            productlink = self.productlink.value
            if not is_guapi_link(productlink):
                embed = discord.Embed(title="Error - Invalid Guapi link", description="Please provide a valid Guapi.ch link.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Store initial form data
            productsize = self.productsize.value
            productprice = self.productprice.value
            currency = self.currency.value
            shippingcost = self.shippingcost.value

            # Scrape product information
            try:
                embed = discord.Embed(title="Processing...", description="Scraping product details...Please wait !", color=0x1e1f22)
                await interaction.response.send_message(embed=embed, ephemeral=False)

                # Configure proxies for scraping using Zyte API (as used in other modals)
                proxies = {
                    "http": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                    "https": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/"
                }

                print(f"[{Colors.green}START Scraping{lg}] Guapi -> {interaction.user.id} ({interaction.user})" + lg)
                print(f"    [{Colors.cyan}Scraping{lg}] Product URL: {productlink}" + lg)

                # Make the request with proxies
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }

                response = requests.get(productlink, headers=headers, proxies=proxies, verify=False)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract product details
                product_name = None
                product_image = None

                # Find product name - adapt selectors based on guapi.ch's structure
                title_element = soup.find('h1', class_='product-single__title')
                if title_element:
                    product_name = title_element.text.strip()
                    print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {product_name}" + lg)

                # Find product image
                image_element = soup.find('img', class_='product__image')
                if image_element and 'src' in image_element.attrs:
                    product_image = image_element['src']
                    if product_image.startswith('//'):
                        product_image = 'https:' + product_image
                    print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {product_image}" + lg)

                # If scraping fails, fall back to user input
                if not product_name:
                    product_name = "Guapi Product"  # Default fallback name

                if not product_image:
                    product_image = "https://cdn.shopify.com/s/files/1/1800/4445/files/GUAP_FONT_BLACK_3.shopifz_ec7510ec-0d1e-4615-ad1d-2b612978fce4.png"  # Default logo

                print(f"[{Colors.green}Scraping DONE{lg}] Guapi -> {interaction.user.id} ({interaction.user})" + lg)

                # Store form data in global dictionary
                if 'guapi_form_data' not in globals():
                    global guapi_form_data
                    guapi_form_data = {}

                guapi_form_data[str(owner_id)] = {
                    'product_name': product_name,
                    'product_image': product_image,
                    'product_size': productsize,
                    'product_price': productprice,
                    'currency': currency,
                    'shipping_cost': shippingcost,
                    'name': name,
                    'street': street,
                    'city': city,
                    'zipp': zipp,
                    'country': country
                }

                # Create "Next Page" button view
                view = GuapiNextButton(owner_id)

                # Update the message
                await interaction.edit_original_response(
                    content="Click 'Next Page' to continue to the next set of inputs.",
                    embed=None,
                    view=view, ephemeral=False
                )

            except Exception as e:
                print(f"[{Colors.red}ERROR{lg}] Scraping failed: {str(e)}")
                await interaction.edit_original_response(content=f"An error occurred while scraping: {str(e)}", embed=None, ephemeral=True)

        else:
            embed = discord.Embed(title="Error", description="User details not found. Please set up your credentials in settings.")
            await interaction.response.send_message(embed=embed, ephemeral=True)


class GuapiNextButton(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=300)  # 5 minute timeout
        self.owner_id = owner_id

    @discord.ui.button(label="Next Page", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your form.", ephemeral=True)
            return

        # Complete the order process
        if str(self.owner_id) not in guapi_form_data:
            await interaction.response.send_message("Your session has expired. Please start over.", ephemeral=True)
            return

        data = guapi_form_data[str(self.owner_id)]

        # Generate a random order number
        order_number = ''.join(random.choices('0123456789', k=6))

        # Generate receipt
        with open('receipt/guapi.html', 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Replace placeholders with actual values
        html_content = html_content.replace('{name}', data['name'])
        html_content = html_content.replace('{street}', data['street'])
        html_content = html_content.replace('{city}', data['city'])
        html_content = html_content.replace('{zip}', data['zipp'])
        html_content = html_content.replace('{country}', data['country'])
        html_content = html_content.replace('{productname}', data['product_name'])
        html_content = html_content.replace('{productsize}', data['product_size'])
        html_content = html_content.replace('{productprice}', data['product_price'])
        html_content = html_content.replace('{productcurrency}', data['currency'])
        html_content = html_content.replace('{shippingcost}', data['shipping_cost'])
        html_content = html_content.replace('€138.00', f"{data['currency']}{data['product_price']}")

        # Save the modified HTML to a file without sending it directly
        file_name = f"guapi_receipt_{interaction.user.id}.html"
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Set up email sending options
        try:
            from emails.choise import choiseView

            # Use the specified email for Guapi
            sender_email = "Guapi <no-reply@guapi.com>"
            subject = "Thank you for your purchase!"
            link = "https://www.guapi.ch"

            # Create embed for email provider choice
            embed = discord.Embed(title="Choose email provider", description="Email is ready to send. Choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(interaction.user.id, html_content, sender_email, subject, data['product_name'], data['product_image'], link)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

        except Exception as e:
            await interaction.followup.send(f"Failed to prepare email options: {str(e)}", ephemeral=True)

        # Clean up temporary data
        if str(self.owner_id) in guapi_form_data:
            del guapi_form_data[str(self.owner_id)]

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your form.", ephemeral=True)
            return

        await interaction.response.edit_message(content="Form cancelled.", view=None, ephemeral=True)

# Initialize global dictionary to store form data between steps
guapi_form_data = {}