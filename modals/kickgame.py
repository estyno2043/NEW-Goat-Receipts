import discord
import random
import requests
from bs4 import BeautifulSoup
from discord import ui
from discord.ui import TextInput
from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

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
            view = choiseView(owner_id, html_content, sender_email, subject, productname, productimage, link, proxies={
        "http": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
        "https": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
    },
    verify=False)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.followup.send(embed=embed, ephemeral=True)