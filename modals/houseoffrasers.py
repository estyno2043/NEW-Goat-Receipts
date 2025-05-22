
import discord
from discord import ui
from discord.ui import TextInput
import random
from utils.db_utils import get_user_details
from utils.utils import send_html
from emails.choise import choiseView
import datetime

class houseoffrasermodal(ui.Modal, title="House of Fraser Receipt Generator (1/2)"):
    productname = discord.ui.TextInput(label="Product Name", placeholder="Oxford Short Sleeve Tailored Shirt", required=True)
    imagelink = discord.ui.TextInput(label="Image URL", placeholder="https://example.com/image.jpg", required=True)
    productprice = discord.ui.TextInput(label="Price without currency", placeholder="50.00", required=True)
    currency = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=1)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, imagelink, productprice, currency
        from addons.nextsteps import NextstepHouseOfFraser
        owner_id = interaction.user.id 

        productname = self.productname.value
        imagelink = self.imagelink.value
        productprice = self.productprice.value
        currency = self.currency.value

        embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receipt.")
        await interaction.response.send_message(content=f"{interaction.user.mention}", embed=embed, view=NextstepHouseOfFraser(owner_id), ephemeral=True)


class houseofffrasersmodal2(ui.Modal, title="House of Fraser Receipt Generator (2/2)"):
    productcode = discord.ui.TextInput(label="Product Code", placeholder="55792622350", required=True)
    shippingcost = discord.ui.TextInput(label="Shipping Cost", placeholder="10.00", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global productname, imagelink, productprice, currency
        owner_id = interaction.user.id

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=0x1e1f22)
            await interaction.response.edit_message(content=None, embed=embed, view=None)

            productcode = self.productcode.value
            shippingcost = self.shippingcost.value

            # Get user details from database
            user_details = get_user_details(owner_id)
            
            if user_details:
                name, street, city, zipp, country, email = user_details
                
                # Calculate total
                try:
                    total = float(productprice) + float(shippingcost)
                    total_formatted = f"{total:.2f}"
                except ValueError:
                    embed = discord.Embed(title="Error", description="Invalid price format. Please use numerical values.")
                    await interaction.edit_original_response(embed=embed)
                    return

                # Get HTML template
                with open("receipt/houseoffrasers.html", "r", encoding="utf-8") as file:
                    html_content = file.read()
                
                # Replace placeholders with user details from database
                html_content = html_content.replace("{name}", name)
                html_content = html_content.replace("Theodore Jones", name)
                html_content = html_content.replace("874 Beard Garden Suite 760\nBrandonfort, CO 89234", street)
                html_content = html_content.replace("East Nicolefort Oneillchester", city)
                html_content = html_content.replace("{street}", street)
                html_content = html_content.replace("{city}", city)
                html_content = html_content.replace("{zip}", zipp)
                html_content = html_content.replace("{country}", country)
                html_content = html_content.replace("Germany", country)
                html_content = html_content.replace("53877", zipp)
                
                # Replace product details
                html_content = html_content.replace("Oxford Short Sleeve Tailored Shirt", productname)
                html_content = html_content.replace("{productname}", productname)
                html_content = html_content.replace("55792622350", productcode)
                html_content = html_content.replace("{productcode}", productcode)
                html_content = html_content.replace("€50.00", f"{currency}{productprice}")
                html_content = html_content.replace("{currency}", currency)
                html_content = html_content.replace("{productprice}", productprice)
                html_content = html_content.replace("€10.00", f"{currency}{shippingcost}")
                html_content = html_content.replace("{shippingcost}", shippingcost)
                html_content = html_content.replace("€60.00", f"{currency}{total_formatted}")
                html_content = html_content.replace("{total}", total_formatted)
                
                # Replace image - both original pattern and placeholder format
                html_content = html_content.replace("https://ci3.googleusercontent.com/meips/ADKq_NaoQm0MVfJnpQqWzUS2S0RqVAaMH0OI8dHjVonuPwg_Cy4Kr6k9sYLcJ__imocCUfd22eGA0iEaLULvtxdsyvcGjmR16-iNghGLldoZhN3gwcn2BeY=s0-d-e1-ft#https://www.houseoffraser.co.uk/images/products/55792601_zt.jpg", imagelink)
                
                # Also replace the img src directly
                import re
                img_pattern = re.compile(r'<img src="[^"]+" alt="Long Length Bench Jacket Anorak Mens"')
                html_content = re.sub(img_pattern, f'<img src="{imagelink}" alt="Long Length Bench Jacket Anorak Mens"', html_content)
                
                # Set up email variables
                sender_email = "HOUSE OF FRASER <noreply@houseoffrasers.com>"
                subject = f"Your order HOF97109960348759"
                
                # Update order date to current date
                current_date = datetime.datetime.now().strftime("%d/%m/%Y")
                html_content = html_content.replace("<h3 style=\"font-family:Helvetica,Arial,sans-serif;margin:0 0 15px;font-weight:700;font-size:26px;line-height:24px;text-align:center;text-transform:uppercase;color:#000\"></h3>", f"<h3 style=\"font-family:Helvetica,Arial,sans-serif;margin:0 0 15px;font-weight:700;font-size:26px;line-height:24px;text-align:center;text-transform:uppercase;color:#000\">{current_date}</h3>")
                
                embed = discord.Embed(title="House of Fraser Receipt Generated", description="Choose how to receive your receipt:")
                view = choiseView(owner_id, html_content, sender_email, subject, productname, "houseoffrasers image.png", "https://www.houseoffraser.co.uk")
                
                await interaction.edit_original_response(embed=embed, view=view)
            else:
                embed = discord.Embed(title="Error", description="No user details found. Please run /settings to set up your information.")
                await interaction.edit_original_response(embed=embed)
                
        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)
