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
    
    # Module name mapping for brands with different file names
    module_name_mapping = {
        "chrono": "chrono24",
        "corteiz": "crtz",
        "tnf": "tnf",
        "lv": "lv",
        "houseoffrasers": "houseoffrasers",
        "vw": "vw"
    }
    
    # Create a command for each brand
    for brand in brands:
        display_name = brand_display_names.get(brand, brand.title())
        
        # Create command function with brand captured in closure via default parameters
        def make_brand_command(brand_name: str, display: str):
            async def brand_command(interaction: discord.Interaction, product_image: discord.Attachment):
                """File upload command for a specific brand"""
                user_id = str(interaction.user.id)
                guild_id = str(interaction.guild.id if interaction.guild else "0")
                
                # Check subscription/license before allowing access
                try:
                    from utils.mongodb_manager import mongo_manager
                    from utils.license_manager import LicenseManager
                    import json
                
                # Load config to get main guild ID
                try:
                    with open("config.json", "r") as f:
                                config = json.load(f)
                                main_guild_id = config.get("guild_id", "1412488621293961226")
                        except Exception as e:
                            print(f"Error loading config: {e}")
                            main_guild_id = "1412488621293961226"
                        
                        # Check if this is a guild-specific or main guild request
                        is_main_guild = (guild_id == main_guild_id)
                        
                        if not is_main_guild:
                            # Check guild configuration and access
                            db = mongo_manager.get_database()
                            if db is None:
                                embed = discord.Embed(
                                    title="Database Error",
                                    description="Unable to connect to database. Please try again later.",
                                    color=discord.Color.red()
                                )
                                await interaction.response.send_message(embed=embed, ephemeral=True)
                                return
                            
                            guild_config = db.guild_configs.find_one({"guild_id": guild_id})
                            
                            if not guild_config:
                                embed = discord.Embed(
                                    title="Server Not Configured",
                                    description="This server has not been configured to use GOAT Receipts. Please ask the server admin to use `/configure_guild`.",
                                    color=discord.Color.red()
                                )
                                await interaction.response.send_message(embed=embed, ephemeral=True)
                                return
                            
                            # Get the guild configuration including roles
                            client_role_id = guild_config.get("client_role_id")
                            admin_role_id = guild_config.get("admin_role_id")
                            
                            # Check if user has admin role
                            has_admin_role = False
                            if admin_role_id and interaction.guild:
                                admin_role = discord.utils.get(interaction.guild.roles, id=int(admin_role_id))
                                if admin_role and admin_role in interaction.user.roles:
                                    has_admin_role = True
                            
                            # Check if user has client role
                            has_client_role = False
                            if client_role_id and interaction.guild:
                                client_role = discord.utils.get(interaction.guild.roles, id=int(client_role_id))
                                if client_role and client_role in interaction.user.roles:
                                    has_client_role = True
                            
                            # Check database access using GuildLicenseChecker
                            from utils.guild_license_checker import GuildLicenseChecker
                            has_access, access_info = await GuildLicenseChecker.check_guild_access(user_id, guild_id, guild_config)
                            
                            # Grant access if user has admin or client role
                            if not (has_admin_role or has_client_role or has_access):
                                embed = discord.Embed(
                                    title="Access Denied",
                                    description="You don't have a valid subscription to use this command. Please purchase a subscription or contact a server admin.",
                                    color=discord.Color.red()
                                )
                                await interaction.response.send_message(embed=embed, ephemeral=True)
                                return
                        else:
                            # In main guild, check license normally
                            license_status = await LicenseManager.is_subscription_active(user_id)
                            
                            if not license_status:
                                # Check if it's a lite subscription that's exhausted
                                license_doc = mongo_manager.get_license(user_id)
                                
                                if license_doc and license_doc.get("subscription_type") == "lite":
                                    receipt_count = license_doc.get("receipt_count", 0)
                                    max_receipts = license_doc.get("max_receipts", 7)
                                    
                                    if receipt_count >= max_receipts:
                                        embed = discord.Embed(
                                            title="Lite Subscription Limit Reached",
                                            description=f"You've used all {max_receipts} receipts in your Lite subscription.\n\n"
                                                       f"Please upgrade to continue generating receipts.",
                                            color=discord.Color.red()
                                        )
                                    else:
                                        embed = discord.Embed(
                                            title="Subscription Expired",
                                            description="Your subscription has expired. Please renew to continue using this command.",
                                            color=discord.Color.red()
                                        )
                                else:
                                    embed = discord.Embed(
                                        title="No Active Subscription",
                                        description="You need an active subscription to use this command.\n\n"
                                                   "Please purchase a subscription to get started.",
                                        color=discord.Color.red()
                                    )
                                
                                await interaction.response.send_message(embed=embed, ephemeral=True)
                                return
                                
            except Exception as check_error:
                        print(f"Error checking subscription for {brand_name}: {check_error}")
                        import traceback
                        traceback.print_exc()
                        embed = discord.Embed(
                            title="Verification Error",
                            description="There was an error verifying your subscription. Please try again or contact support.",
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
            
            # Validate that the attachment is an image
            if not product_image.content_type or not product_image.content_type.startswith('image/'):
                        embed = discord.Embed(
                            title="Invalid File Type",
                            description="Please upload an image file (PNG, JPG, JPEG, GIF, or WEBP).",
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
            
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
                        
                        embed = discord.Embed(
                            title="Upload Failed",
                            description=f"Failed to save your image: {str(upload_error)}\n\nPlease try again or use the /generate command with an image link.",
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        clear_uploaded_image(user_id, brand_name)
                        return
            
            # Import the modal for this brand and show it directly
            try:
                        # Map brand name to module name
                        modal_module_name = module_name_mapping.get(brand_name, brand_name)
                        
                        # Import the existing brand modal (not the file upload modal)
                        module = __import__(f"modals.{modal_module_name}", fromlist=[""])
                        
                        # Get the modal class - try common naming patterns
                        modal_class = None
                        for attr_name in dir(module):
                            if attr_name.lower().endswith("modal") and not attr_name.startswith("_"):
                                attr = getattr(module, attr_name)
                                if isinstance(attr, type) and issubclass(attr, discord.ui.Modal):
                                    modal_class = attr
                                    break
                        
                        if modal_class:
                            # Directly show the modal to the user (no image display, no message)
                            await interaction.response.send_modal(modal_class())
                        else:
                            # Fallback: show error if modal not found
                            embed = discord.Embed(
                                title="Modal Not Found",
                                description=f"The modal for {display} is not available yet. Please use the regular /generate command.",
                                color=discord.Color.red()
                            )
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                            clear_uploaded_image(user_id, brand_name)
                            
            except Exception as e:
                        print(f"Error loading modal for {brand_name}: {e}")
                        import traceback
                        traceback.print_exc()
                        embed = discord.Embed(
                            title="Error",
                            description=f"An error occurred loading the {display} form. Please try again or use the /generate command.",
                            color=discord.Color.red()
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        clear_uploaded_image(user_id, brand_name)
            
            return brand_command
        
        # Call factory to create command with proper closure
        brand_command = make_brand_command(brand, display_name)
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
        
        # Store command for ID logging after sync
        if not hasattr(bot, '_file_upload_commands'):
            bot._file_upload_commands = []
        bot._file_upload_commands.append((brand, display_name, cmd))
    
    print(f"✅ Registered {len(brands)} file upload commands")
    return len(brands)
