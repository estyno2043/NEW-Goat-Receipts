"""
File Upload Commands for GOAT Receipts
Creates a slash command for each brand that accepts image file uploads
"""

import discord
from discord import app_commands
from typing import Optional

# Dictionary to store uploaded images per user and brand
uploaded_images = {}

def get_uploaded_image(user_id: str, brand: str) -> Optional[str]:
    """Get the uploaded image URL for a user and brand"""
    key = f"{user_id}_{brand}"
    return uploaded_images.get(key)

def set_uploaded_image(user_id: str, brand: str, image_url: str):
    """Store the uploaded image URL for a user and brand"""
    key = f"{user_id}_{brand}"
    uploaded_images[key] = image_url

def clear_uploaded_image(user_id: str, brand: str):
    """Clear the uploaded image for a user and brand"""
    key = f"{user_id}_{brand}"
    if key in uploaded_images:
        del uploaded_images[key]

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
            
            # Store the uploaded image URL
            set_uploaded_image(user_id, brand_name, product_image.url)
            
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
                    # Show the modal (without image URL field)
                    await interaction.response.send_modal(modal_class())
                else:
                    # Fallback: show error if modal not found
                    embed = discord.Embed(
                        title="Modal Not Found",
                        description=f"The modal for {display} is not available yet. Please use the regular /generate command.",
                        color=discord.Color.red()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
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
