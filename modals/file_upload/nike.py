"""
Nike File Upload Modal - Without image URL field
The image is already uploaded via the command
"""

import discord
from discord import ui
from commands.file_upload_commands import get_uploaded_image, clear_uploaded_image

class NikeModalFileUpload(ui.Modal, title="Nike Receipt"):
    Priceff = discord.ui.TextInput(label="Price without currency", placeholder="120", required=True)
    currencyff = discord.ui.TextInput(label="Currency ($, £, €)", placeholder="€", required=True, min_length=1, max_length=2)
    delivery = discord.ui.TextInput(label="Order Date", placeholder="Ex. 24/04/2024", required=True)
    size = discord.ui.TextInput(label="Size", placeholder="M / 44", required=True)
    product_name = discord.ui.TextInput(label="Product Name", placeholder="Air Jordan 1", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id
        user_id = str(owner_id)

        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)

            if user_details:
                name, street, city, zipp, country, email = user_details

                # Get the uploaded image URL
                image_url = get_uploaded_image(user_id, "nike")
                
                if not image_url:
                    embed = discord.Embed(
                        title="Error",
                        description="Image upload not found. Please try the command again.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                currencyff = self.currencyff.value
                Priceff = self.Priceff.value
                delivery = self.delivery.value
                size = self.size.value
                product_name = self.product_name.value

                try:
                    embed = discord.Embed(
                        title="Under Process...",
                        description="Processing your email will be sent soon!",
                        color=discord.Color.from_str("#826bc2")
                    )
                    await interaction.response.send_message(
                        content=f"{interaction.user.mention}",
                        embed=embed,
                        ephemeral=False
                    )

                    with open("receipt/nike.html", "r", encoding="utf-8") as file:
                        html_content = file.read()

                    cityzip = f"{city} {zipp}"

                    import datetime
                    delivery_date = datetime.datetime.strptime(delivery, '%d/%m/%Y')
                    adjusted_delivery_date = delivery_date + datetime.timedelta(days=3)
                    formatted_delivery_date = adjusted_delivery_date.strftime('%d/%m/%Y')

                    html_content = html_content.replace("{name}", name)
                    html_content = html_content.replace("{street}", street)
                    html_content = html_content.replace("{cityzip}", cityzip)
                    html_content = html_content.replace("{size}", size)
                    html_content = html_content.replace("{orderdate}", delivery)
                    html_content = html_content.replace("{orderdate3d}", formatted_delivery_date)
                    html_content = html_content.replace("{currency}", str(currencyff))
                    html_content = html_content.replace("{price}", str(Priceff))
                    html_content = html_content.replace("{productlink}", str(image_url))
                    html_content = html_content.replace("{productname}", str(product_name))

                    with open("receipt/updatedrecipies/updatednike.html", "w", encoding="utf-8") as file:
                        file.write(html_content)

                    sender_email = "Nike.com <noreply@nike.com>"
                    subject = "Order Received (Nike.com #4124888905)"
                    from emails.choise import choiseView

                    embed = discord.Embed(
                        title="Choose email provider",
                        description="Email is ready to send choose Spoofed or Normal domain.",
                        color=discord.Color.from_str("#826bc2")
                    )
                    view = choiseView(owner_id, html_content, sender_email, subject, product_name, image_url, image_url)
                    await interaction.edit_original_response(embed=embed, view=view)
                    
                    # Clear the uploaded image after processing
                    clear_uploaded_image(user_id, "nike")

                except Exception as e:
                    embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
                    await interaction.edit_original_response(embed=embed)
                    clear_uploaded_image(user_id, "nike")

        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description="No user details found. Please ensure your information is set up."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            clear_uploaded_image(user_id, "nike")
