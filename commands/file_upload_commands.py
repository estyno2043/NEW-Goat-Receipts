"""
File Upload Commands for GOAT Receipts
Creates a slash command for each brand that accepts image file uploads
"""

import discord
from discord import app_commands
from typing import Optional

# Dictionary to store uploaded images per user and brand with timestamps
uploaded_images = {}

def get_uploaded_image(user_id: str, brand: str) -> Optional[str]:
    """Get the uploaded image URL for a user and brand"""
    import time
    key = f"{user_id}_{brand}"
    data = uploaded_images.get(key)
    
    if data:
        # Check if image hasn't expired (15 minute timeout)
        timestamp, url = data
        if time.time() - timestamp < 900:  # 15 minutes
            return url
        else:
            # Clean up expired entry
            del uploaded_images[key]
            return None
    return None

def set_uploaded_image(user_id: str, brand: str, image_url: str):
    """Store the uploaded image URL for a user and brand with timestamp"""
    import time
    key = f"{user_id}_{brand}"
    uploaded_images[key] = (time.time(), image_url)

def clear_uploaded_image(user_id: str, brand: str):
    """Clear the uploaded image for a user and brand"""
    key = f"{user_id}_{brand}"
    if key in uploaded_images:
        del uploaded_images[key]

def cleanup_expired_uploads():
    """Clean up expired upload entries (called periodically)"""
    import time
    current_time = time.time()
    expired_keys = [
        key for key, (timestamp, _) in uploaded_images.items()
        if current_time - timestamp > 900  # 15 minutes
    ]
    for key in expired_keys:
        del uploaded_images[key]
    if expired_keys:
        print(f"Cleaned up {len(expired_keys)} expired image uploads")

def register_file_upload_commands(bot):
    """Register all file upload commands for each brand"""
    
    brands = [
        "6pm", "acnestudios", "adidas", "adwysd", "amazon", "amazonuk", "apple", "applepickup",
        "arcteryx", "argos", "balenciaga", "bape", "bijenkorf", "breuninger", "brokenplanet", 
        "burberry", "canadagoose", "cartier", "cernucci", "chanel", "chewforever", "chromehearts",
        "chrono", "coolblue", "corteiz", "crtz", "culturekings", "denimtears", "dior", "dyson",
        "ebayauth", "ebayconf", "end", "farfetch", "fightclub", "flannels", "futbolemotion",
        "gallerydept", "goat", "goyard", "grailed", "guapi", "gucci", "harrods", "hermes",
        "houseoffrasers", "istores", "jdsports", "jomashop", "kickgame", "legitapp", "loropiana",
        "lv", "maisonmargiela", "moncler", "nike", "nosauce", "offwhite", "pandora", "prada",
        "ralphlauren", "samsung", "sephora", "sneakerstorecz", "snkrs", "spider", "stockx",
        "stussy", "supreme", "synaworld", "tnf", "trapstar", "ugg", "vinted", "vw", "xerjoff",
        "zalandode", "zalandous", "zara", "zendesk"
    ]
    
    # Brand display names (some need special formatting)
    brand_display_names = {
        "6pm": "6pm",
        "acnestudios": "Acne Studios",
        "adidas": "Adidas",
        "adwysd": "Adwysd",
        "amazon": "Amazon",
        "amazonuk": "Amazon UK",
        "apple": "Apple",
        "applepickup": "Apple Pickup",
        "arcteryx": "Arc'teryx",
        "argos": "Argos",
        "balenciaga": "Balenciaga",
        "bape": "BAPE",
        "bijenkorf": "Bijenkorf",
        "breuninger": "Breuninger",
        "brokenplanet": "Broken Planet",
        "burberry": "Burberry",
        "canadagoose": "Canada Goose",
        "cartier": "Cartier",
        "cernucci": "Cernucci",
        "chanel": "Chanel",
        "chewforever": "Chew Forever",
        "chromehearts": "Chrome Hearts",
        "chrono": "Chrono24",
        "coolblue": "Coolblue",
        "corteiz": "Corteiz",
        "crtz": "CRTZ",
        "culturekings": "Culture Kings",
        "denimtears": "Denim Tears",
        "dior": "Dior",
        "dyson": "Dyson",
        "ebayauth": "eBay Auth",
        "ebayconf": "eBay Conf",
        "end": "END.",
        "farfetch": "Farfetch",
        "fightclub": "Fight Club",
        "flannels": "Flannels",
        "futbolemotion": "Fútbol Emotion",
        "gallerydept": "Gallery Dept",
        "goat": "GOAT",
        "goyard": "Goyard",
        "grailed": "Grailed",
        "guapi": "Guapi",
        "gucci": "Gucci",
        "harrods": "Harrods",
        "hermes": "Hermès",
        "houseoffrasers": "House of Fraser",
        "istores": "iStores",
        "jdsports": "JD Sports",
        "jomashop": "Jomashop",
        "kickgame": "KickGame",
        "legitapp": "Legit App",
        "loropiana": "Loro Piana",
        "lv": "Louis Vuitton",
        "maisonmargiela": "Maison Margiela",
        "moncler": "Moncler",
        "nike": "Nike",
        "nosauce": "No Sauce",
        "offwhite": "Off-White",
        "pandora": "Pandora",
        "prada": "Prada",
        "ralphlauren": "Ralph Lauren",
        "samsung": "Samsung",
        "sephora": "Sephora",
        "sneakerstorecz": "Sneaker Store CZ",
        "snkrs": "SNKRS",
        "spider": "Spider",
        "stockx": "StockX",
        "stussy": "Stüssy",
        "supreme": "Supreme",
        "synaworld": "Syna World",
        "tnf": "The North Face",
        "trapstar": "Trapstar",
        "ugg": "UGG",
        "vinted": "Vinted",
        "vw": "VW",
        "xerjoff": "Xerjoff",
        "zalandode": "Zalando DE",
        "zalandous": "Zalando US",
        "zara": "Zara",
        "zendesk": "Zendesk"
    }
    
    # Create a command for each brand
    for brand in brands:
        display_name = brand_display_names.get(brand, brand.title())
        
        # Create command function with brand captured in closure
        async def brand_command(interaction: discord.Interaction, product_image: discord.Attachment, brand_name=brand, display=display_name):
            """File upload command for a specific brand"""
            user_id = str(interaction.user.id)
            
            # Validate that the attachment is an image
            if not product_image.content_type or not product_image.content_type.startswith('image/'):
                embed = discord.Embed(
                    title="Invalid File Type",
                    description="Please upload an image file (PNG, JPG, JPEG, GIF, or WEBP).",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Defer response as download/re-upload might take time
            await interaction.response.defer(ephemeral=False)
            
            try:
                # Download the image to persist it locally (Discord attachment URLs expire)
                import aiohttp
                import io
                import os
                from datetime import datetime
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(product_image.url) as resp:
                        if resp.status != 200:
                            raise Exception("Failed to download image")
                        image_data = await resp.read()
                
                # Save to local storage in attached_assets/uploaded_images/
                storage_dir = "attached_assets/uploaded_images"
                os.makedirs(storage_dir, exist_ok=True)
                
                # Create unique filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename_parts = os.path.splitext(product_image.filename)
                unique_filename = f"{user_id}_{brand_name}_{timestamp}{filename_parts[1]}"
                local_path = os.path.join(storage_dir, unique_filename)
                
                # Save image locally
                with open(local_path, 'wb') as f:
                    f.write(image_data)
                
                print(f"✅ Saved uploaded image to: {local_path}")
                
                # Store the local file path
                set_uploaded_image(user_id, brand_name, local_path)
                    
            except Exception as upload_error:
                print(f"❌ Error persisting image: {upload_error}")
                import traceback
                traceback.print_exc()
                
                # DON'T fallback to expiring URL - notify user of failure
                embed = discord.Embed(
                    title="Upload Failed",
                    description=f"Failed to save your image: {str(upload_error)}\n\nPlease try again or use the /generate command with an image link.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                clear_uploaded_image(user_id, brand_name)
                return
            
            # Import the modal for this brand
            try:
                # Dynamic import of the modal based on brand name
                if brand_name == "chrono":
                    modal_module_name = "chrono24"
                elif brand_name == "corteiz":
                    modal_module_name = "crtz"
                elif brand_name == "futbolemotion":
                    modal_module_name = "futbolemotion"
                else:
                    modal_module_name = brand_name
                
                # Import the file upload modal
                from modals.file_upload import get_file_upload_modal
                modal_class = get_file_upload_modal(brand_name)
                
                if modal_class:
                    # Show success message and send modal
                    embed = discord.Embed(
                        title="✅ Image Uploaded",
                        description=f"Product image uploaded successfully for {display}.\nPlease fill out the form below to generate your receipt.",
                        color=discord.Color.green()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    
                    # Show the modal (without image URL field)
                    # Note: We need to use interaction.response since modals require it
                    # Since we already deferred, we'll need to handle this differently
                    # Actually, after defer we can't send a modal. Let me use a button instead.
                    
                    # Create a button to trigger the modal
                    from discord import ui as discord_ui
                    
                    class OpenModalButton(discord_ui.View):
                        def __init__(self):
                            super().__init__(timeout=900)  # 15 minute timeout
                        
                        @discord_ui.button(label=f"Fill {display} Receipt Form", style=discord.ButtonStyle.primary)
                        async def open_modal(self, button_interaction: discord.Interaction, button: discord_ui.Button):
                            # Show the modal when button is clicked
                            await button_interaction.response.send_modal(modal_class())
                    
                    view = OpenModalButton()
                    await interaction.followup.send(
                        content=f"Click the button below to fill out the {display} receipt details:",
                        view=view,
                        ephemeral=False
                    )
                else:
                    # Fallback: show error if modal not found
                    embed = discord.Embed(
                        title="Modal Not Found",
                        description=f"The modal for {display} is not available yet. Please use the regular /generate command.",
                        color=discord.Color.red()
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    clear_uploaded_image(user_id, brand_name)
                    
            except Exception as e:
                print(f"Error loading modal for {brand_name}: {e}")
                embed = discord.Embed(
                    title="Error",
                    description=f"An error occurred loading the {display} form. Please try again or use the /generate command.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Set command name and description
        brand_command.__name__ = f"{brand}_upload"
        
        # Create the app command with proper parameters
        cmd = app_commands.Command(
            name=brand,
            description=f"Upload product image for {display_name} receipt",
            callback=brand_command
        )
        
        # Add parameter annotation for the image
        cmd._params[list(cmd._params.keys())[0]].required = True
        
        # Register the command
        bot.tree.add_command(cmd)
    
    print(f"✅ Registered {len(brands)} file upload commands")
    return len(brands)
