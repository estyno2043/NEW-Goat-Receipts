"""
Universal File Upload Modal System for GOAT Receipts
Creates modals without image URL fields for all brands
"""

import discord
from discord import ui
from commands.file_upload_commands import get_uploaded_image, clear_uploaded_image

# Define common modal fields for different brand types
class UniversalFileUploadModal(ui.Modal):
    """Base file upload modal with common fields"""
    
    def __init__(self, brand: str, title: str = None):
        super().__init__(title=title or f"{brand.title()} Receipt")
        self.brand = brand
    
    product_name = discord.ui.TextInput(
        label="Product Name",
        placeholder="Product name",
        required=True
    )
    
    price = discord.ui.TextInput(
        label="Price (without currency)",
        placeholder="120.00",
        required=True
    )
    
    currency = discord.ui.TextInput(
        label="Currency",
        placeholder="$ or € or £",
        required=True,
        min_length=1,
        max_length=2
    )
    
    size = discord.ui.TextInput(
        label="Size",
        placeholder="M / 44",
        required=False
    )
    
    order_date = discord.ui.TextInput(
        label="Order Date",
        placeholder="24/04/2024",
        required=True
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id
        user_id = str(owner_id)
        
        try:
            from utils.db_utils import get_user_details
            user_details = get_user_details(owner_id)
            
            if not user_details:
                embed = discord.Embed(
                    title="Error",
                    description="No user details found. Please set up your credentials first.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                clear_uploaded_image(user_id, self.brand)
                return
            
            name, street, city, zipp, country, email = user_details
            
            # Get the uploaded image path
            image_path = get_uploaded_image(user_id, self.brand)
            
            if not image_path:
                embed = discord.Embed(
                    title="Error",
                    description="Image upload not found or expired. Please upload again.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Re-upload the local file to Discord for a persistent URL
            # This ensures the email can display the image properly
            import discord as discord_module
            import os
            
            try:
                # Get a channel to upload to (using interaction's guild or DM the bot owner)
                storage_channel = None
                
                if interaction.guild:
                    # Try to find a suitable channel in the guild
                    for channel in interaction.guild.text_channels:
                        if channel.permissions_for(interaction.guild.me).send_messages:
                            storage_channel = channel
                            break
                
                if not storage_channel:
                    # Fallback: use the interaction channel
                    storage_channel = interaction.channel
                
                if storage_channel:
                    # Re-upload the file to Discord for permanent URL
                    file = discord_module.File(image_path, filename=os.path.basename(image_path))
                    storage_message = await storage_channel.send(
                        content=f"📸 Receipt image for {interaction.user.mention}",
                        file=file
                    )
                    
                    if storage_message.attachments:
                        image_url = storage_message.attachments[0].url
                        print(f"✅ Uploaded image to Discord: {image_url}")
                    else:
                        raise Exception("Failed to get Discord URL after upload")
                else:
                    raise Exception("No suitable channel found for image upload")
                
            except Exception as e:
                print(f"Error re-uploading image to Discord: {e}")
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to prepare the image for email: {str(e)}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                clear_uploaded_image(user_id, self.brand)
                return
            
            # Send processing message
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
            
            # Process the receipt
            try:
                # Import receipt generation
                await self.generate_receipt(
                    interaction=interaction,
                    image_url=image_url,
                    product_name=self.product_name.value,
                    price=self.price.value,
                    currency=self.currency.value,
                    size=self.size.value,
                    order_date=self.order_date.value,
                    user_details=(name, street, city, zipp, country, email),
                    owner_id=owner_id
                )
                
                # Clear the uploaded image after successful processing
                clear_uploaded_image(user_id, self.brand)
                
            except Exception as e:
                print(f"Error generating receipt for {self.brand}: {e}")
                embed = discord.Embed(
                    title="Error",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(embed=embed)
                clear_uploaded_image(user_id, self.brand)
                
        except Exception as e:
            print(f"Error in file upload modal for {self.brand}: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.edit_original_response(embed=embed)
            clear_uploaded_image(user_id, self.brand)
    
    async def generate_receipt(self, interaction, image_url, product_name, price, currency, 
                               size, order_date, user_details, owner_id):
        """Generate the receipt HTML and send email"""
        name, street, city, zipp, country, email = user_details
        
        # Load the receipt template
        import os
        receipt_file = f"receipt/{self.brand}.html"
        
        if not os.path.exists(receipt_file):
            raise FileNotFoundError(f"Receipt template not found for {self.brand}")
        
        with open(receipt_file, "r", encoding="utf-8") as file:
            html_content = file.read()
        
        # Replace placeholders in the HTML
        import datetime
        
        cityzip = f"{city} {zipp}"
        
        # Parse and format dates
        try:
            delivery_date = datetime.datetime.strptime(order_date, '%d/%m/%Y')
            adjusted_delivery_date = delivery_date + datetime.timedelta(days=3)
            formatted_delivery_date = adjusted_delivery_date.strftime('%d/%m/%Y')
        except:
            formatted_delivery_date = order_date
        
        # Replace common placeholders
        replacements = {
            "{name}": name,
            "{street}": street,
            "{city}": city,
            "{cityzip}": cityzip,
            "{zipp}": zipp,
            "{country}": country,
            "{size}": size or "N/A",
            "{orderdate}": order_date,
            "{orderdate3d}": formatted_delivery_date,
            "{currency}": currency,
            "{price}": str(price),
            "{productlink}": image_url,
            "{productname}": product_name,
            "{image_url}": image_url,
        }
        
        for placeholder, value in replacements.items():
            html_content = html_content.replace(placeholder, value)
        
        # Save the updated receipt
        os.makedirs("receipt/updatedrecipies", exist_ok=True)
        output_file = f"receipt/updatedrecipies/updated{self.brand}.html"
        
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(html_content)
        
        # Send email
        sender_email = f"{self.brand.title()}.com <noreply@{self.brand.lower()}.com>"
        subject = f"Order Received ({self.brand.title()}.com #{owner_id})"
        
        from emails.choise import choiseView
        
        embed = discord.Embed(
            title="Choose email provider",
            description="Email is ready to send choose Spoofed or Normal domain.",
            color=discord.Color.from_str("#826bc2")
        )
        view = choiseView(owner_id, html_content, sender_email, subject, product_name, image_url, image_url)
        await interaction.edit_original_response(embed=embed, view=view)


def get_file_upload_modal(brand: str):
    """Get a file upload modal for the specified brand"""
    
    # Brand-specific display names
    brand_display_names = {
        "6pm": "6pm",
        "acnestudios": "Acne Studios",
        "chrono": "Chrono24",
        "futbolemotion": "Fútbol Emotion",
        "tnf": "The North Face",
        "lv": "Louis Vuitton",
    }
    
    display_name = brand_display_names.get(brand, brand.title())
    
    # Create a modal class for this brand
    class BrandFileUploadModal(UniversalFileUploadModal):
        def __init__(self):
            super().__init__(brand=brand, title=f"{display_name} Receipt")
    
    return BrandFileUploadModal


__all__ = ['get_file_upload_modal', 'UniversalFileUploadModal']
