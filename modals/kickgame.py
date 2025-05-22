import discord
import random
import requests
from bs4 import BeautifulSoup
from discord import ui
from discord.ui import TextInput
import sqlite3
from datetime import datetime

class kickgamemodal(discord.ui.Modal, title="Kick Game Receipt Generator (1/2)"):
    def __init__(self):
        super().__init__()
        self.productlink = TextInput(
            label="Product Link",
            placeholder="https://kickgame.co.uk/products/...",
            required=True
        )
        self.productsize = TextInput(
            label="Product Size",
            placeholder="M, L, UK9, etc.",
            required=True
        )
        self.productprice = TextInput(
            label="Product Price",
            placeholder="Price without currency symbol (e.g. 113.99)",
            required=True
        )
        self.productcurrency = TextInput(
            label="Currency Symbol",
            placeholder="€, £, $, etc.",
            required=True,
            min_length=1,
            max_length=2
        )
        self.productarrivaldate = TextInput(
            label="Product Arrival Date",
            placeholder="DD/MM/YYYY",
            required=True
        )

        self.add_item(self.productlink)
        self.add_item(self.productsize)
        self.add_item(self.productprice)
        self.add_item(self.productcurrency)
        self.add_item(self.productarrivaldate)

    async def on_submit(self, interaction: discord.Interaction):
        from addons.nextsteps import NextstepKickgame
        await interaction.response.send_message(content=f"Processing your Kick Game receipt...", ephemeral=True)

        # Attempt to scrape product details
        product_name = "Product Name"
        product_image = "https://example.com/product-image.jpg"

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.productlink.value, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                product_name_elem = soup.select_one('h1.product-title') or soup.select_one('h1')
                if product_name_elem:
                    product_name = product_name_elem.text.strip()

                # Try multiple selectors to find the product image
                img_elem = (soup.select_one('img.product-featured-image') or 
                           soup.select_one('.product-single__photos img') or
                           soup.select_one('img[itemprop="image"]') or
                           soup.select_one('.product-image img') or
                           soup.select_one('.product__media img'))

                if img_elem and img_elem.get('src'):
                    product_image = img_elem['src']
                    if product_image.startswith('//'):
                        product_image = 'https:' + product_image
                    # Make sure we have the full URL
                    elif product_image.startswith('/'):
                        base_url = '/'.join(self.productlink.value.split('/')[:3])
                        product_image = base_url + product_image
        except Exception as e:
            print(f"Error scraping product details: {e}")

        view = NextstepKickgame(interaction.user.id)

        # Store values for the next step
        view.productlink = self.productlink.value
        view.productname = product_name
        view.productimage = product_image
        view.productsize = self.productsize.value
        view.productprice = self.productprice.value
        view.productcurrency = self.productcurrency.value
        view.productarrivaldate = self.productarrivaldate.value

        await interaction.followup.send(view=view, ephemeral=True)

class kickgamemodal2(discord.ui.Modal, title="Kick Game Receipt Generator (2/2)"):
    def __init__(self):
        super().__init__()
        self.productpurchasedate = TextInput(
            label="Purchase Date",
            placeholder="DD/MM/YYYY",
            required=True
        )
        self.productshippingcost = TextInput(
            label="Shipping Cost",
            placeholder="10.00",
            required=True
        )
        self.producttaxcost = TextInput(
            label="Tax Cost",
            placeholder="10.00",
            required=True
        )
        self.productimagelink = TextInput(
            label="Product Image Link",
            placeholder="https://example.com/image.jpg",
            required=False
        )

        self.add_item(self.productpurchasedate)
        self.add_item(self.productshippingcost)
        self.add_item(self.producttaxcost)
        self.add_item(self.productimagelink)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(content="Generating your Kick Game receipt...", ephemeral=True)

        # Retrieve user data
        member = interaction.user

        # Get values from the previous form stored in nextsteps.py
        from addons.nextsteps import store
        user_id = interaction.user.id
        if user_id in store:
            productlink = store[user_id].get('productlink', 'https://kickgame.co.uk')
            productname = store[user_id].get('productname', 'Product Name')
            productimage = store[user_id].get('productimage', '')
            productsize = store[user_id].get('productsize', 'M')
            productprice = store[user_id].get('productprice', '113.99')
            productcurrency = store[user_id].get('productcurrency', '€')
            productarrivaldate = store[user_id].get('productarrivaldate', '01/01/2025')
        else:
            await interaction.followup.send("Session expired. Please start again.", ephemeral=True)
            return

        # Get shipping details from interaction user's profile
        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, street, city, zipp, country FROM licenses WHERE owner_id = ?", (str(interaction.user.id),))
        user_details = cursor.fetchone()

        if user_details:
            name, street, city, zipp, country = user_details
        else:
            # Fallback to default values if no user details found
            name = "Laura Vincent"
            street = "123 Example Street"
            city = "London"
            zipp = "SW1A 1AA"
            country = "United Kingdom"

        try:
            # Generate random order number
            order_number = f"0{random.randint(10000000, 99999999)}"

            # Open and read the HTML template
            with open("receipt/kickgame.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Generate random last 4 digits for credit card
            card_last4 = str(random.randint(1000, 9999))

            # Replace all placeholders in the HTML template
            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{city}", city)
            html_content = html_content.replace("{zip}", zipp)
            html_content = html_content.replace("{country}", country)
            html_content = html_content.replace("{phone}", "001-364-564-2274x31090") # Add default phone if not available
            html_content = html_content.replace("{productname}", productname)
            html_content = html_content.replace("{productsize}", productsize)
            # Find image tag in HTML and replace src attribute entirely
            import re

            # Use the user-provided image link if available
            if self.productimagelink.value and self.productimagelink.value.startswith("http"):
                product_img_url = self.productimagelink.value
            # Fall back to scraped image if available
            elif productimage and productimage.startswith("http"):
                product_img_url = productimage
            # Default fallback image if neither is available
            else:
                product_img_url = "https://ci3.googleusercontent.com/meips/ADKq_NYux2c5tHAOhiTvExPzg58IAKKUIJHlvKMl54PycffsCEusD02IkYxOGmAiYTEkHysE1KzTncM70r8kyDSKSCTNdE3zwclhZMFCwoxxMbhKTqrM_Va819Kp6uORmijM97yo66k9IJwH3ixE2Ci3Xjk8qejCW3EOQfi5tNHgUdsDH-uN=s0-d-e1-ft"

            # Replace the image source in the HTML
            img_pattern = r'<img width="160" src="[^"]*" alt="Product Image"'
            replacement = f'<img width="160" src="{product_img_url}" alt="Product Image"'
            html_content = re.sub(img_pattern, replacement, html_content)
            html_content = html_content.replace("{productprice}", productprice)
            html_content = html_content.replace("{productcurrency}", productcurrency)
            html_content = html_content.replace("{ordernumber}", order_number)
            html_content = html_content.replace("{productpurchasedate}", self.productpurchasedate.value)
            html_content = html_content.replace("{productshippingcost}", self.productshippingcost.value)
            html_content = html_content.replace("{producttaxcost}", self.producttaxcost.value)
            html_content = html_content.replace("{cardlast4}", card_last4)

            # Calculate total
            try:
                price = float(productprice)
                shipping = float(self.productshippingcost.value)
                tax = float(self.producttaxcost.value)
                total = price + shipping + tax
                html_content = html_content.replace("{total}", f"{total:.2f}")
            except Exception as e:
                print(f"Error calculating total: {e}")
                html_content = html_content.replace("{total}", "0.00")

            # Save the updated HTML
            with open("receipt/updatedrecipies/updatedkickgame.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            # Set up email information
            sender_email = "Kick Game <orders@kickgame.co.uk>"
            subject = f"Order #{order_number} confirmed"

            # Send the generated receipt
            from emails.choise import choiseView
            owner_id = interaction.user.id
            link = "https://kickgame.co.uk"

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send. Choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, productname, productimage, link)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.followup.send(embed=embed, ephemeral=True)