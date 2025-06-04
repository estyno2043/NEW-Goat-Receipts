import os
import discord
import json
import sqlite3
import random
from datetime import datetime, timedelta
from discord.ui import View, Select, Button, Modal
from discord import SelectOption, ui, Embed
from utils.db_utils import get_db_connection
from addons.settings import SettingsView
from modals.acnestudios import acnemodal
from modals.adidas import adidasmodal
from modals.adwysd import adwysdmodal # ADWYSD added here
from modals.amazon import amazonmodal
from modals.amazonuk import AmazonUKModal
from modals.arcteryx import arcteryxmodal
from modals.brokenplanet import brokenmodal
from modals.ebayconf import EbayConfModal
from modals.burberry import burberrymodal
from modals.cartier import cartiermodal
from modals.chanel import chanelmodal
from modals.chewforever import Chewforevermodal
from modals.chromehearts import chromemodal
from modals.chrono import chronomodal
from modals.coolblue import coolbluemodal
from modals.culturekings import ckmodal
from modals.denimtears import denimtearsmodal
from modals.dior import diormodal
from modals.dyson import dyson
from modals.apple import applemodal
from modals.balenciaga import balenciagamodal
from modals.bape import bapemodal
from modals.canadagoose import canadagoose
from modals.ebayauth import ebayauthmodal
from modals.end import endmodal
from modals.flannels import flannelsmodal
from modals.gallerydept import gallerydeptmodal
from modals.goat import goat
from modals.grailed import grailedmodal
from modals.jdsports import jdsportsmodal
from modals.legitapp import legitappmodal
from modals.loropiana import loromodal
from modals.maisonmargiela import maisonmodal
from modals.moncler import monclermodal
from modals.nike import nikemodal
from modals.nosauce import nosaucemodal
from modals.pandora import pandoramodal
from modals.prada import Pradamodal
from modals.ralphlauren import ralphlaurenmodal
from modals.sephora import sephoranmodal
from modals.snkrs import snkrsmodal
from modals.spider import spidermodal
from modals.stockx import stockxmodal
from modals.lv import lvmodal
from modals.crtz import crtzmodal
from modals.farfetch import farfetchmodal
from modals.breuninger import breuningermodal
from modals.stussy import stussymodal
from modals.tnf import tnfmodal
from modals.trapstar import trapstarmodal
from modals.zalandode import zalandodemodal
from modals.zalandous import zalandomodal
from modals.zara import zaramodal
from modals.fightclub import fightclubmodal
from modals.adwysd import adwysdmodal # Added adwysdmodal import
from modals.cernucci import cernuccimodal # Added cernuccimodal import
from modals.bijenkorf import bijenkorfmodal # Added bijenkorfmodal import
from modals.argos import argosmodal # Added argosmodal import
from modals.gucci import guccimodal1 # Added guccimodal1 import
from modals.kickgame import kickgamemodal # Added kickgamemodal import
from modals.hermes import HermesModal # Added HermesModal import
from modals.guapi import guapimodal # Added guapimodal import
from modals.istores import istoresmodal # Added istoresmodal import
from modals.harrods import harrodsmodal # Added harrodsmodal import
from modals.offwhite import offwhitemodal
from modals.zalandous import zalandomodal
from modals.ugg import uggmodal #Import for UGG modal
from modals.applepickup import applepickupmodal #Import for Apple Pickup modal
from modals.supreme import suprememodal #Import for Supreme modal
from modals.synaworld import synaworldmodal #Import for Synaworld modal
from modals.vinted import vintedmodal #Import for Vinted modal
from modals.houseoffrasers import houseoffrasermodal #Import for House of Fraser modal
from addons.nextsteps import NextstepHouseOfFraser
from modals.samsung import SamsungModal as samsungmodal
from modals.xerjoff import xerjoffmodal

conn = sqlite3.connect('data.db')
cursor = conn.cursor()

def get_bot_name():
    import os
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            return config.get("bot_name", "GOAT Receipts")
    except FileNotFoundError:
        return "GOAT Receipts"

def get_client_id(guild_id=None):
    import os
    # First try to get server-specific client ID if guild_id is provided
    if guild_id:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT client_id FROM server_configs WHERE guild_id = ?", (str(guild_id),))
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            try:
                return int(result[0])
            except (ValueError, TypeError):
                pass  # Fall back to global config if conversion fails

    # Fall back to global config
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    with open(config_path, "r") as f:
        config = json.load(f)
        return int(config.get("Client_ID"))

# Initialize with global config, will be updated per interaction
clientid = get_client_id()


# All brands combined in alphabetical order across all regions
all_brands = {
    'Acne Studios': acnemodal,
    'Adidas': adidasmodal,
    'ADWYSD': adwysdmodal,
    'Amazon': amazonmodal,
    'Amazon UK': AmazonUKModal,
    'Apple': applemodal,
    'Apple Pickup': applepickupmodal,
    'Arc\'teryx': arcteryxmodal,
    'Argos': argosmodal,
    'Balenciaga': balenciagamodal,
    'Bape': bapemodal,
    'Bijenkorf': bijenkorfmodal,
    'Breuninger': breuningermodal,
    'Broken Planet': brokenmodal,
    'Burberry': burberrymodal,
    'Canada Goose': canadagoose,
    'Cartier': cartiermodal,
    'Cernucci': cernuccimodal,
    'Chanel': chanelmodal,
    'Chew Forever': Chewforevermodal,
    'Chrome Hearts': chromemodal,
    'Chrono24': chronomodal,
    'Coolblue': coolbluemodal,
    'Corteiz': crtzmodal,
    'Culture Kings': ckmodal,
    'Denim Tears': denimtearsmodal,
    'Dior': diormodal,
    'Dyson': dyson,
    'Ebay': EbayConfModal,
    'END.': endmodal,
    'Farfetch': farfetchmodal,
    'Fight Club': fightclubmodal,
    'Flannels': flannelsmodal,
    'Gallery Dept': gallerydeptmodal,
    'Goat': goat,
    'Grailed': grailedmodal,
    'Guapi': guapimodal,
    'Gucci': guccimodal1,
    'Harrods': harrodsmodal,
    'Hermès': HermesModal,
    'House of Fraser': houseoffrasermodal,
    'iStores': istoresmodal,
    'JD Sports': jdsportsmodal,
    'Kick Game': kickgamemodal,
    'Legit App': legitappmodal,
    'Loro Piana': loromodal,
    'Louis Vuitton': lvmodal,
    'Maison Margiela': maisonmodal,
    'Moncler': monclermodal,
    'Nike': nikemodal,
    'No Sauce The Plug': nosaucemodal,
    'Off-White': offwhitemodal,
    'Pandora': pandoramodal,
    'Prada': Pradamodal,
    'Ralph Lauren': ralphlaurenmodal,
    'Samsung': samsungmodal,
    'Sephora': sephoranmodal,
    'SNKRS': snkrsmodal,
    'Spider': spidermodal,
    'StockX': stockxmodal,
    'Stüssy': stussymodal,
    'Supreme': suprememodal,
    'Syna World': synaworldmodal,
    'The North Face': tnfmodal,
    'Trapstar': trapstarmodal,
    'UGG': uggmodal,
    'Vinted': vintedmodal,
    'Xerjoff': xerjoffmodal,
    'Zalando DE': zalandodemodal,
    'Zalando US': zalandomodal,
    'Zara': zaramodal,
    'eBay Auth': ebayauthmodal,
}

# Define German brands to exclude from US regions
de_brands = ['Bijenkorf', 'Breuninger', 'Zalando DE', 'Zara']

# Distribute brands across regions, filtering out DE brands from US regions
all_keys = [k for k in all_brands.keys() if k not in de_brands]
us_brands_count = len(all_keys)
brands_per_region = (us_brands_count + 4) // 5  # Distribute US brands evenly across 5 regions

brands = {
    'USA': {k: all_brands[k] for k in all_keys[:brands_per_region]},
    'USA2': {k: all_brands[k] for k in all_keys[brands_per_region:brands_per_region*2]},
    'USA3': {k: all_brands[k] for k in all_keys[brands_per_region*2:brands_per_region*3]},
    'USA4': {k: all_brands[k] for k in all_keys[brands_per_region*3:brands_per_region*4]},
    'USA5': {k: all_brands[k] for k in all_keys[brands_per_region*4:]},
    'DE': {
        'Breuninger': breuningermodal,
        'Zalando DE': zalandodemodal,
        'Zara': zaramodal,
        'Bijenkorf': bijenkorfmodal
    },

}


def load_brands(region='USA'):
    return sorted(brands[region].items(), key=lambda x: x[0])

brands_usa = load_brands('USA')
brands_usa2 = load_brands('USA2') # Added brands_usa2
brands_usa3 = load_brands('USA3') #Added brands_usa3
brands_usa4 = load_brands('USA4') #Added brands_usa4
brands_usa5 = load_brands('USA5') #Added brands_usa5
brands_de = load_brands('DE')


class PaginatedDropdown(discord.ui.Select):
    def __init__(self, owner_id, options, per_page=25):
        super().__init__(placeholder='Select a brand to proceed', min_values=1, max_values=1)
        self.owner_id = owner_id
        self.all_options = sorted(options, key=lambda x: x[0])  # Sort alphabetically
        self.per_page = per_page
        self.page = 0
        self.update_options(self.page)

    def update_options(self, page):
        """Update the options in the dropdown based on current page"""
        self.page = page
        start_idx = page * self.per_page
        end_idx = min(start_idx + self.per_page, len(self.all_options))

        # Clear existing options
        self.options.clear()

        # Add options for current page
        for brand_name, _ in self.all_options[start_idx:end_idx]:
            self.options.append(discord.SelectOption(label=brand_name, value=brand_name))

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)
            return

        selected_brand = self.values[0]
        modal_function = dict(self.all_options).get(selected_brand)
        if callable(modal_function):
            await interaction.response.send_modal(modal_function())
        else:
            await interaction.response.send_message("Error: Modal function not available.", ephemeral=True)


class DropdownView(discord.ui.View):
    def __init__(self, owner_id, brand_options):
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.dropdown = PaginatedDropdown(owner_id, brand_options, per_page=13)
        self.add_item(self.dropdown)
        self.region = "US"  # Default region

        if brand_options == brands_de:
            self.region = "DE"
            # Remove navigation buttons for German view
            for child in list(self.children):
                if isinstance(child, discord.ui.Button) and child.label in ["Previous", "Next Brands"]:
                    self.remove_item(child)
        elif brand_options == brands_usa:
            self.region = "US"
        elif brand_options == brands_usa2:
            self.region = "US2"
        elif brand_options == brands_usa3:
            self.region = "US3"
        elif brand_options == brands_usa4:
            self.region = "US4"
        elif brand_options == brands_usa5:
            self.region = "US5"
        elif brand_options == brands_usa6:
            self.region = "US6"

    def calculate_total_pages(self):
        """Calculate total pages for the current dropdown"""
        total_items = len(self.dropdown.all_options)
        return (total_items + self.dropdown.per_page - 1) // self.dropdown.per_page

    def calculate_total_brands(self):
        """Calculate total brands across all regions"""
        # Use the actual length of all_brands dictionary which contains all brands
        return len(all_brands)

    def get_page_indicator(self):
        """Return page indicator text"""
        current_page = self.dropdown.page + 1
        total_pages = self.calculate_total_pages()
        return f"Page {current_page} of {total_pages}"

    def get_region_name(self):
        """Get human-readable region name"""
        if self.region.startswith("US"):
            return "US" + (self.region[2:] if len(self.region) > 2 else "")
        return self.region

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, disabled=True, row=1)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return

        try:
            # Get current page and calculate previous page
            current_page = self.dropdown.page
            if current_page > 0:
                self.dropdown.update_options(current_page - 1)

                # Enable/disable buttons based on current page
                if self.dropdown.page == 0:
                    button.disabled = True
                self.next_button.disabled = False  # Enable next button

                # Update the embed
                await self.update_embed_appearance(interaction)
            else:
                # Handle region transitions for previous button
                try:
                    if self.region == "US2":
                        await self.transition_to_region(interaction, "US", brands_usa)
                    elif self.region == "US3":
                        await self.transition_to_region(interaction, "US2", brands_usa2)
                    elif self.region == "US4":
                        await self.transition_to_region(interaction, "US3", brands_usa3)
                    elif self.region == "US5":
                        await self.transition_to_region(interaction, "US4", brands_usa4)
                    elif self.region == "US6":
                        await self.transition_to_region(interaction, "US5", brands_usa5)
                    else:
                        await interaction.response.send_message(content="You are already on the first page.", ephemeral=True)
                except Exception as e:
                    print(f"Error transitioning region: {e}")
                    import traceback
                    traceback.print_exc()
                    await interaction.response.send_message(
                        "There was an error loading the previous page. Please try again or use the command again.",
                        ephemeral=True
                    )
        except Exception as e:
            print(f"Error in previous button: {e}")
            await interaction.followup.send("There was an error processing your request. Please try again.", ephemeral=True)

    @discord.ui.button(label="Next Brands", style=discord.ButtonStyle.primary, row=1)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return

        try:
            # Get current page and calculate next page
            current_page = self.dropdown.page
            last_page = self.calculate_total_pages() - 1

            if current_page < last_page:
                # Still have pages in current region
                self.dropdown.update_options(current_page + 1)

                # Enable/disable buttons based on current page
                if self.dropdown.page == last_page:
                    button.disabled = True
                self.previous_button.disabled = False  # Enable previous button

                # Update the embed
                await self.update_embed_appearance(interaction)
            else:
                # Handle region transitions
                try:
                    if self.region == "US" and self.dropdown.page == last_page:
                        await self.transition_to_region(interaction, "US2", brands_usa2)
                    elif self.region == "US2" and self.dropdown.page == last_page:
                        await self.transition_to_region(interaction, "US3", brands_usa3)
                    elif self.region == "US3" and self.dropdown.page == last_page:
                        await self.transition_to_region(interaction, "US4", brands_usa4)
                    elif self.region == "US4" and self.dropdown.page == last_page:
                        await self.transition_to_region(interaction, "US5", brands_usa5)
                    elif self.region == "US5" and self.dropdown.page == last_page:
                        await self.transition_to_region(interaction, "US6", brands_usa6)
                    else:
                        # If there are no more regions to transition to
                        await interaction.response.send_message(
                            "You've reached the last page of brands.",
                            ephemeral=True
                        )
                except Exception as e:
                    print(f"Error transitioning region: {e}")
                    import traceback
                    traceback.print_exc()
                    # Gracefully handle error
                    await interaction.response.send_message(
                        "There was an error loading the next page. Please try again or use the command again.",
                        ephemeral=True
                    )
        except Exception as e:
            print(f"Error in next button: {e}")
            import traceback
            traceback.print_exc()
            await interaction.followup.send("There was an error processing your request. Please try again.", ephemeral=True)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, row=1)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return

        try:
            # Create a closed interaction embed
            embed = discord.Embed(
                title="Interaction Closed",
                description="The interaction has been closed and is no longer active.",
                color=0x2b2d31
            )

            # Remove user from active_menus in GenerateCog
            from commands.generate import GenerateCog
            for cog in interaction.client.cogs.values():
                if isinstance(cog, GenerateCog):
                    cog.active_menus.pop(self.owner_id, None)
                    break

            # Update the message instead of deleting it
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            print(f"Error closing interaction: {e}")
            try:
                await interaction.response.send_message("There was an error closing the panel.", ephemeral=True)
            except:
                pass

    async def transition_to_region(self, interaction, new_region, brand_options):
        """Handle transition between regions"""
        try:
            # Safety check to ensure brand_options is not empty
            if not brand_options:
                print(f"Warning: Empty brand options for region {new_region}")
                await interaction.followup.send("No brands available for this region. Please try a different region.", ephemeral=True)
                return

            view = DropdownView(self.owner_id, brand_options)
            view.region = new_region

            # Create updated embed with modern design
            now = datetime.now()
            date_str = now.strftime("%d/%m/%YYYY %H:%M")

            # Get total brands count
            total_brands = self.calculate_total_brands()

            # Calculate total pages based on actual brand distribution
            total_pages = 6  # USA1-USA6 pages

            # Determine current page based on the new region
            current_page = 1
            if new_region == "US":
                current_page = 1
            elif new_region == "US2":
                current_page = 2
            elif new_region == "US3":
                current_page = 3
            elif new_region == "US4":
                current_page = 4
            elif new_region == "US5":
                current_page = 5
            elif new_region == "US6":
                current_page = 6

            # For DE region, remove Previous and Next buttons
            if new_region == "DE":
                # Remove navigation buttons for German view
                for child in list(view.children):
                    if isinstance(child, discord.ui.Button) and child.label in ["Previous", "Next"]:
                        view.remove_item(child)


            # Create the embed with user's name in the title
            embed = discord.Embed(title=f"{interaction.user.display_name}'s Panel", color=0x2b2d31)
            embed.description = f"Choose the type of receipt from the dropdown menu below. `(Total: {total_brands})`\nPage {current_page} of {total_pages}"

            # Add bot info at the bottom without timestamp
            bot_name = get_bot_name()
            embed.set_footer(text=f"{bot_name}", icon_url=interaction.guild.me.avatar.url if interaction.guild and interaction.guild.me.avatar else None)

            # For transitions from next button, go to page 0
            # For transitions from previous button, go to last page of the region
            if new_region in ["US", "US2", "US3", "US4", "US5"]:
                # If coming from a higher-numbered region (going backward)
                if (self.region == "US2" and new_region == "US") or \
                   (self.region == "US3" and new_region == "US2") or \
                   (self.region == "US4" and new_region == "US3") or \
                   (self.region == "US5" and new_region == "US4"):
                    # Calculate the last page for this region's dropdown
                    last_page = (len(brand_options) + view.dropdown.per_page - 1) // view.dropdown.per_page - 1
                    if last_page >= 0:
                        view.dropdown.update_options(last_page)
                else:
                    # Reset page counter for forward transitions
                    view.dropdown.page = 0

            # Set previous button state based on current page and region
            view.previous_button.disabled = (current_page <= 1 and view.dropdown.page == 0)

            # Set next button state based on current page and region
            view.next_button.disabled = (current_page >= total_pages and 
                                        view.dropdown.page >= (len(brand_options) + view.dropdown.per_page - 1) // view.dropdown.per_page - 1)

            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            print(f"Error in region transition: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.followup.send("There was an error updating the view. Please try the command again.", ephemeral=True)
            except:
                pass

    async def update_embed_appearance(self, interaction):
        """Update the embed with modern appearance"""
        try:
            # Create a modern looking embed
            now = datetime.now()
            date_str = now.strftime("%d/%m/%YYYY %H:%M")

            # Get total brands and page info
            total_brands = self.calculate_total_brands()

            # Set total pages to fixed value of 6 pages across all regions
            total_pages = 6  # Use consistent value for total pages

            # Determine current page based on region
            current_page = 1
            if self.region == "US":
                current_page = 1
            elif self.region == "US2":
                current_page = 2
            elif self.region == "US3":
                current_page = 3
            elif self.region == "US4":
                current_page = 4
            elif self.region == "US5":
                current_page = 5
            elif self.region == "US6":
                current_page = 6

            # Create page info string
            page_info = f"Page {current_page} of {total_pages}"

            # Create embed with user's display name in title
            embed = discord.Embed(title=f"{interaction.user.display_name}'s Panel", color=0x2b2d31)
            embed.description = f"Choose the type of receipt from the dropdown menu below. `(Total: {total_brands})`\n{page_info}"

            # Add bot info at the bottom without timestamp
            bot_name = get_bot_name()
            embed.set_footer(text=f"{bot_name}", icon_url=interaction.guild.me.avatar.url if interaction.guild and interaction.guild.me.avatar else None)

            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            print(f"Error updating embed: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.followup.send("There was an error updating the view. Please try the command again.", ephemeral=True)
            except:
                pass


class RegionSelectionView(discord.ui.View):
    def __init__(self, owner_id, user_roles):
        super().__init__(timeout=180)  # 3 minute timeout
        self.owner_id = owner_id
        self.user_roles = user_roles
        self.value = None

        # Add region selection dropdown
        self.add_item(self.RegionSelect(self))

    # Get total number of brands across all regions
    def get_total_brands(self):
        # Return the actual number of brands from the all_brands dictionary
        return len(all_brands)

    # Create a Select menu for region selection
    class RegionSelect(discord.ui.Select):
        def __init__(self, view):
            self.parent_view = view
            options = [
                discord.SelectOption(label="English", description="US receipts", emoji="🇺🇸", value="USA"),
                discord.SelectOption(label="German", description="DE receipts", emoji="🇩🇪", value="DE"),
            ]
            super().__init__(placeholder="Select Receipt Language", options=options, row=0)

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.parent_view.owner_id:
                await interaction.response.send_message("This is not your panel.", ephemeral=True)
                return

            selected_region = self.values[0]

            cursor.execute("SELECT key, expiry, emailtf, credentialstf FROM licenses WHERE owner_id = ?", (str(interaction.user.id),))
            license_data = cursor.fetchone()

            if license_data:
                key, expiry_str, emailtf, credentialstf = license_data
                extime = datetime.strptime(expiry_str, "%d/%m/%Y %H:%M:%S")
                now = datetime.now()

                if emailtf == "True" and credentialstf == "True":
                    if extime >= now:  # Allow usage on the exact expiry day/time
                        if key and key.startswith("LifetimeKey"):
                            await self.parent_view.show_brand_selection(interaction, selected_region)
                        else:
                            delta = extime - now
                            total_seconds = delta.total_seconds()
                            # Allow access even if it's just hours left on the last day
                            if total_seconds > 0:
                                await self.parent_view.show_brand_selection(interaction, selected_region)
                            else:
                                embed = discord.Embed(title="Dashboard", description="Your subscription has expired. Please renew to continue accessing.")
                                await interaction.response.edit_message(embed=embed)
                    else:
                        embed = discord.Embed(title="Dashboard", description="Your subscription has expired. Please renew to continue accessing.")
                        await interaction.response.edit_message(embed=embed)
                else:
                    message = ""
                    if emailtf == "False":
                        message = "You did not select an email, go to settings and select your mail."
                    if credentialstf == "False":
                        message = "You did not select your credentials, go to settings and set up your credentials."

                    embed = discord.Embed(title="Dashboard", description=message)
                    embed.set_footer(text=f"{interaction.user}'s Panel", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
                    await interaction.response.edit_message(embed=embed)
            else:
                embed = discord.Embed(title="Error", description="No valid license found.")
                await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Settings", style=discord.ButtonStyle.secondary, row=1)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return

        cursor.execute("SELECT key, expiry, emailtf, credentialstf FROM licenses WHERE owner_id = ?", (str(interaction.user.id),))
        license_data = cursor.fetchone()

        if license_data:
            key, expiry_str, emailtf, credentialstf = license_data
            extime = datetime.strptime(expiry_str, "%d/%m/%Y %H:%M:%S")
            now = datetime.now()

            if extime < now:
                embed = discord.Embed(title="Dashboard", description="You have currently no access for Settings")
                view = None
            else:
                description = f"Please make sure you fill in the options below. (Data will save)\n\nEmail = **{emailtf}**\nCredentials = **{credentialstf}**"
                embed = discord.Embed(title="Dashboard", description=description)
                view = SettingsView(self.owner_id, interaction.user.roles)
                embed.set_footer(text=f"{interaction.user}'s Panel", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

            await interaction.response.edit_message(embed=embed, view=view)
        else:
            embed = discord.Embed(title="Error", description="No valid license found.")
            await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, row=1)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return

        # Create a closed interaction embed
        embed = discord.Embed(
            title="Interaction Closed",
            description="The interaction has been closed and is no longer active.",
            color=0x2b2d31
        )

        # Remove user from active_menus in GenerateCog
        from commands.generate import GenerateCog
        for cog in interaction.client.cogs.values():
            if isinstance(cog, GenerateCog):
                cog.active_menus.pop(self.owner_id, None)
                break

        # Update the message instead of deleting it
        await interaction.response.edit_message(embed=embed, view=None)


    async def show_brand_selection(self, interaction, region):
        try:
            owner_id = interaction.user.id
            user_roles = interaction.user.roles

            # Get server-specific client ID/role ID
            VIP_ROLE_ID = get_client_id(interaction.guild.id if interaction.guild else None)
            user_roles_ids = [role.id for role in interaction.user.roles]

            embed = None
            view = None

            # Create a modern dropdown view
            from utils.utils import Utils
            is_whitelisted = await Utils.is_whitelisted(owner_id)
            is_vip = VIP_ROLE_ID in user_roles_ids

            # Check access based on region
            has_access = is_whitelisted or is_vip

            if has_access:
                # Modern UI design
                now = datetime.now()
                date_str = now.strftime("%d/%m/%YYYY %H:%M")
                bot_name = get_bot_name()

                # Get the brands for the selected region
                if region == "DE":
                    brand_options = brands_de
                    region_code = "DE"
                elif region == "USA":
                    brand_options = brands_usa
                    region_code = "US"
                elif region == "USA2":
                    brand_options = brands_usa2
                    region_code = "US2"
                elif region == "USA3":
                    brand_options = brands_usa3
                    region_code = "US3"
                elif region == "USA4":
                    brand_options= brands_usa4
                    region_code = "US4"
                elif region == "USA5":
                    brand_options = brands_usa5
                    region_code = "US5"
                else:
                    # Default to US brands if region is unknown
                    brand_options = brands_usa
                    region_code = "US"

                # Create the view with dropdown
                view = DropdownView(owner_id, brand_options)
                view.region = region_code

                # Calculate total brands - use the actual length of all_brands dictionary
                total_brands = len(all_brands)

                # Create modern embed with user's name in title
                embed = discord.Embed(title=f"{interaction.user.display_name}'s Panel", color=0x2b2d31)

                # Set total pages based on region
                if region_code == "DE":
                    total_pages = 1
                    current_page = 1
                else:
                    # Set fixed total pages to 6 for US regions
                    total_pages = 6

                    # Determine current page based on region
                    current_page = 1
                    if region_code == "US":
                        current_page = 1
                    elif region_code == "US2":
                        current_page = 2
                    elif region_code == "US3":
                        current_page = 3
                    elif region_code == "US4":
                        current_page = 4
                    elif region_code == "US5":
                        current_page = 5
                    elif region_code == "US6":
                        current_page = 6



                # Create page indicator string
                page_indicator = f"Page {current_page} of {total_pages}"

                # Add description with total brands count and page info
                embed.description = f"Choose the type of receipt from the dropdown menu below. `(Total: {total_brands})`\nPage {current_page} of {total_pages}"

                # Add bot info at the bottom without timestamp
                bot_name = get_bot_name()
                embed.set_footer(text=f"{bot_name}", icon_url=interaction.guild.me.avatar.url if interaction.guild and interaction.guild.me.avatar else None)
            else:
                # No access
                embed = discord.Embed(
                    title=f"{interaction.user.display_name}'s Panel",
                    description=f"You currently don't have access for {region} receipts. <:false:1307050325160497273>",
                    color=0x1e1f22
                )
                view = RegionSelectionView(owner_id, user_roles)
                embed.set_footer(
                    text=f"{interaction.user}'s Panel",
                    icon_url=interaction.user.avatar.url if interaction.user.avatar else None
                )

            # Handle errors
            if embed is None:
                now = datetime.now()
                date_str = now.strftime("%d/%m/%YYYY %H:%M")
                bot_name = get_bot_name()

                embed = discord.Embed(
                    title=f"{interaction.user.display_name}'s Panel",
                    description=f"An unexpected error occurred. Please try again later.",
                    color=0xff0000
                )
                view = None
                embed.set_footer(text=f"{bot_name}", icon_url=interaction.guild.me.avatar.url if interaction.guild and interaction.guild.me.avatar else None)

            # Send the response
            try:
                await interaction.response.edit_message(embed=embed, view=view)
            except discord.errors.NotFound:
                try:
                    await interaction.followup.send("Menu timed out. Please use the command again.", ephemeral=True)
                except:
                    pass
            except discord.errors.InteractionResponded:
                try:
                    await interaction.edit_original_response(embed=embed, view=view)
                except:
                    pass
        except Exception as e:
            print(f"Error in show_brand_selection: {e}")
            import traceback
            traceback.print_exc()
            try:
                await interaction.response.send_message(f"An error occurred. Please try again.", ephemeral=True)
            except discord.errors.InteractionResponded:
                await interaction.followup.send(f"An error occurred. Please try again.", ephemeral=True)
            except:
                pass

async def check_access(self, user_id, user_roles, region):
    # First check if user is whitelisted
    from utils.utils import Utils
    if await Utils.is_whitelisted(user_id):
        return True

    # Check basic access
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT expiry FROM licenses WHERE owner_id = ?", (str(user_id),))
    license_data = cursor.fetchone()
    conn.close()

    if not license_data:
        return False

class AmazonUKModal(Modal):
    def __init__(self):
        super().__init__(title="Amazon UK Order - Step 1")
        self.add_item(discord.ui.TextInput(label="Product Name", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Condition", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Product Price", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Product Currency", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Product Arrival Date (YYYY-MM-DD)", style=discord.TextStyle.short, required=True))

    async def callback(self, interaction: discord.Interaction):
        product_name = self.children[0].value
        condition = self.children[1].value
        product_price = self.children[2].value
        product_currency = self.children[3].value
        product_arrival_date = self.children[4].value

        next_modal = AmazonUKSecondModal(product_name, condition, product_price, product_currency, product_arrival_date)
        await interaction.response.send_modal(next_modal)

class AmazonUKSecondModal(Modal):
    def __init__(self, product_name, condition, product_price, product_currency, product_arrival_date):
        super().__init__(title="Amazon UK Order - Step 2")
        self.product_name = product_name
        self.condition = condition
        self.product_price = product_price
        self.product_currency = product_currency
        self.product_arrival_date = product_arrival_date
        self.add_item(discord.ui.TextInput(label="Product Image Link", style=discord.TextStyle.long, required=True))

    async def callback(self, interaction: discord.Interaction):
        product_image_link = self.children[0].value

        # Placeholder for getting user address - replace with your actual address retrieval logic
        name = "John Doe"
        city = "London"
        zip_code = "SW1A 2AA"
        country = "UK"


        embed = discord.Embed(title="Amazon.co.uk Order Summary", color=discord.Color.green())
        embed.add_field(name="Product Name", value=self.product_name, inline=False)
        embed.set_image(url=product_image_link)
        embed.add_field(name="Condition", value=self.condition, inline=False)
        embed.add_field(name="Price", value=f"{self.product_currency} {self.product_price}", inline=False)
        embed.add_field(name="Arriving:", value=self.product_arrival_date, inline=False)
        embed.add_field(name="Shipping Address", value=f"{name}\n{city}, {zip_code}\n{country}", inline=False)
        embed.add_field(name="Order Total:", value=f"{self.product_currency} {self.product_price}", inline=False)

        # Placeholder for email sending - replace with your actual email sending logic
        # ... send email to user with embed content ...
        await interaction.response.send_message(embed=embed)

#Add kickgamemodal Function here.  This is a placeholder and needs to be implemented based on your requirements.
class kickgamemodal(Modal):
    def __init__(self):
        super().__init__(title="KickGame Order")
        self.add_item(discord.ui.TextInput(label="Product Link", placeholder="Paste product link here", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Product Size", placeholder="Enter product size", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Product Price", placeholder="Enter product price", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Product Currency", placeholder="Enter product currency (e.g., USD, EUR)", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Product Arrival Date", placeholder="Enter product arrival date (YYYY-MM-DD)", style=discord.TextStyle.short, required=True))


    async def callback(self, interaction: discord.Interaction):
        #Implementation for scraping product name and image using proxies should be added here.
        product_link = self.children[0].value
        product_size = self.children[1].value
        product_price = self.children[2].value
        product_currency = self.children[3].value
        product_arrival_date = self.children[4].value

        # Placeholder for scraping -  replace with your actual scraping logic
        product_name = "Example Product Name"  
        product_image_url = "https://example.com/image.jpg"

        # Create second modal for remaining details
        second_modal = SecondKickGameModal(product_link, product_size, product_price, product_currency, product_arrival_date, product_name, product_image_url)
        await interaction.response.send_modal(second_modal)


class SecondKickGameModal(Modal):
    def __init__(self, product_link, product_size, product_price, product_currency, product_arrival_date, product_name, product_image_url):
        super().__init__(title="Kick Game Order - Step 2")
        self.product_link = product_link
        self.product_size = product_size
        self.product_price = product_price
        self.product_currency = product_currency
        self.product_arrival_date = product_arrival_date
        self.product_name = product_name
        self.product_image_url = product_image_url
        self.add_item(discord.ui.TextInput(label="Product Purchase Date", placeholder="Enter purchase date (YYYY-MM-DD)", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Shipping Cost", placeholder="Enter shipping cost", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Tax Cost", placeholder="Enter tax cost", style=discord.TextStyle.short, required=True))



    async def callback(self, interaction: discord.Interaction):
        purchase_date = self.children[0].value
        shipping_cost = self.children[1].value
        tax_cost = self.children[2].value

        # Generate random order number
        order_number = ''.join(random.choices('0123456789', k=9))


        # Construct the embed
        embed = discord.Embed(title="Kick Game Order Confirmed", color=discord.Color.green())
        embed.add_field(name="Order No.", value=order_number, inline=False)
        embed.add_field(name="Customer", value=f"{interaction.user.name}  ...", inline=False) #Incomplete address - needs to be added later
        embed.add_field(name="Product", value=f"{self.product_name} ({self.product_size})", inline=False)
        embed.set_thumbnail(url=self.product_image_url)
        embed.add_field(name=f"{self.product_currency} {self.product_price}", value=f"Subtotal: {self.product_price}", inline=False)
        embed.add_field(name=shipping_cost, value=f"Delivery: {shipping_cost}", inline=False)
        embed.add_field(name=tax_cost, value=f"Tax: {tax_cost}", inline=False)

        embed.set_footer(text=f"Order placed on {purchase_date}")

        # Send the email
        #Email Sending Logic should be added here


        await interaction.response.send_message(embed=embed)

class EbayConfModal(Modal):
    def __init__(self):
        super().__init__(title="eBay Order - Step 1")
        self.add_item(discord.ui.TextInput(label="Product Name", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Product Image Link", style=discord.TextStyle.long, required=True))
        self.add_item(discord.ui.TextInput(label="Product Price", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Product Currency", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Product SKU", style=discord.TextStyle.short, required=True))

    async def callback(self, interaction: discord.Interaction):
        product_name = self.children[0].value
        product_image_link = self.children[1].value
        product_price = self.children[2].value
        product_currency = self.children[3].value
        product_sku = self.children[4].value

        next_modal = EbayConfSecondModal(product_name, product_image_link, product_price, product_currency, product_sku)
        await interaction.response.send_modal(next_modal)


class EbayConfSecondModal(Modal):
    def __init__(self, product_name, product_image_link, product_price, product_currency, product_sku):
        super().__init__(title="eBay Order - Step 2")
        self.product_name = product_name
        self.product_image_link = product_image_link
        self.product_price = product_price
        self.product_currency = product_currency
        self.product_sku = product_sku
        self.add_item(discord.ui.TextInput(label="Shipping Cost", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Delivery Date (YYYY-MM-DD)", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Seller Name", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Street", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="City", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Zip", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Country", style=discord.TextStyle.short, required=True))
        self.add_item(discord.ui.TextInput(label="Name", style=discord.TextStyle.short, required=True))

    async def callback(self, interaction: discord.Interaction):
        product_shipping_cost = self.children[0].value
        product_delivery_date = self.children[1].value
        product_seller = self.children[2].value
        street = self.children[3].value
        city = self.children[4].value
        zip_code = self.children[5].value
        country = self.children[6].value
        name = self.children[7].value

        embed = discord.Embed(title="eBay Purchase Confirmed", color=discord.Color.green())
        embed.add_field(name="Product Name", value=self.product_name, inline=False)
        embed.set_image(url=self.product_image_link)
        embed.add_field(name="Price", value=f"{self.product_currency} {self.product_price}", inline=False)
        embed.add_field(name="Item ID", value=self.product_sku, inline=False)
        embed.add_field(name="Seller", value=product_seller, inline=False)
        embed.add_field(name="Shipping Address", value=f"{name}\n{street}\n{city} {zip_code}\n{country}", inline=False)
        embed.add_field(name="Estimated delivery", value=product_delivery_date, inline=False)
        embed.add_field(name="Subtotal", value=f"{self.product_currency} {self.product_price}", inline=True)
        embed.add_field(name="Postage", value=f"{self.product_currency} {product_shipping_cost}", inline=True)
        embed.add_field(name="Total charged to", value=f"{self.product_currency} {float(self.product_price) + float(product_shipping_cost)}", inline=False)
        embed.set_footer(text=f"Order confirmed by eBay")

        #Email Sending Logic should be added here


        await interaction.response.send_message(embed=embed)

# Guapi Modal Implementation
class guapimodal(Modal):
    def __init__(self):
        super().__init__(title="Guapi Order - Step 1")
        self.add_item(discord.ui.TextInput(label="Product Link (guapi.ch)", style=discord.TextStyle.long, required=True, placeholder="Paste product link here"))

    async def callback(self, interaction: discord.Interaction):
        product_link = self.children[0].value

        # Basic validation (replace with more robust check if needed)
        if not product_link.startswith("https://guapi.ch/"):
            await interaction.response.send_message("Invalid Guapi product link.", ephemeral=True)
            return


        # Placeholder for scraping product details (replace with your scraping logic)
        product_name = "Guapi Product Name"  # Replace with scraped data
        product_image = "https://guapi.ch/product_image.jpg" # Replace with scraped data
        product_size = "M" #Replace with scraped data
        product_price = "138.00" #Replace with scraped data
        product_currency = "EUR" #Replace with scraped data
        shipping_cost = "10.00" #Replace with scraped data

        # Proceed to the second step
        await interaction.response.send_modal(GuapiSecondModal(product_link, product_name, product_image, product_size, product_price, product_currency, shipping_cost))

class GuapiSecondModal(Modal):
    def __init__(self, product_link, product_name, product_image, product_size, product_price, product_currency, shipping_cost):
        super().__init__(title="Guapi Order - Step 2")
        self.product_link = product_link
        self.product_name = product_name
        self.product_image = product_image
        self.product_size = product_size
        self.product_price = product_price
        self.product_currency = product_currency
        self.shipping_cost = shipping_cost
        self.add_item(discord.ui.TextInput(label="Name", style=discord.TextStyle.short, required=True, placeholder="Your Full Name"))
        self.add_item(discord.ui.TextInput(label="Street", style=discord.TextStyle.short, required=True, placeholder="Street Address"))
        self.add_item(discord.ui.TextInput(label="City", style=discord.TextStyle.short, required=True, placeholder="City"))
        self.add_item(discord.ui.TextInput(label="Zip Code", style=discord.TextStyle.short, required=True, placeholder="Zip Code"))
        self.add_item(discord.ui.TextInput(label="Country", style=discord.TextStyle.short, required=True, placeholder="Country"))
        self.add_item(Select(placeholder="Choose email type", options=[SelectOption(label="Normal Email", value="normal"), SelectOption(label="Spoofed Email", value="spoofed")]))

    async def callback(self, interaction: discord.Interaction):
        name = self.children[0].value
        street = self.children[1].value
        city = self.children[2].value
        zip_code = self.children[3].value
        country = self.children[4].value
        email_type = self.children[5].values[0]

        #Construct Embed
        embed = discord.Embed(title=f"Guapi Order Summary for {self.product_name}", color=discord.Color.green())
        embed.set_thumbnail(url=self.product_image)
        embed.add_field(name="Product Name", value=self.product_name, inline=False)
        embed.add_field(name="Size", value=self.product_size, inline=True)
        embed.add_field(name="Price", value=f"{self.product_currency} {self.product_price}", inline=True)
        embed.add_field(name="Subtotal", value=f"{self.product_currency} {self.product_price}", inline=True)
        embed.add_field(name="Shipping", value=f"{self.product_currency} {self.shipping_cost}", inline=True)
        embed.add_field(name="Shipping Address", value=f"{name}\n{street}\n{city} {zip_code}\n{country}", inline=False)

        # Email sending logic (replace with actual implementation)
        email = "user@example.com" # Replace with user's email (retrieve from interaction or database)
        if email_type == "spoofed":
            email = "no-reply@guapi.com"

        # Placeholder for email sending - replace with your actual email sending logic
        # ... send email to user with embed content ...
        await interaction.response.send_message(embed=embed)
# iStores Modal Implementation
class istoresmodal(Modal):
    def __init__(self):
        super().__init__(title="iStores Order - Step 1")
        self.add_item(discord.ui.TextInput(label="Product Name", style=discord.TextStyle.short, required=True, placeholder="Epico Cleaning Kit for AirPods"))
        self.add_item(discord.ui.TextInput(label="Product Price (with VAT)", style=discord.TextStyle.short, required=True, placeholder="4,90"))
        self.add_item(discord.ui.TextInput(label="Shipping Cost (with VAT)", style=discord.TextStyle.short, required=True, placeholder="2,98"))
        self.add_item(discord.ui.TextInput(label="Product Code", style=discord.TextStyle.short, required=True, placeholder="135091"))

    async def callback(self, interaction: discord.Interaction):
        product_name = self.children[0].value
        product_price_vat = self.children[1].value
        shipping_cost_vat = self.children[2].value
        product_code = self.children[3].value

        await interaction.response.send_modal(iStoresSecondModal(product_name, product_price_vat, shipping_cost_vat, product_code))

class iStoresSecondModal(Modal):
    def __init__(self, product_name, product_price_vat, shipping_cost_vat, product_code):
        super().__init__(title="iStores Order - Step 2")
        self.product_name = product_name
        self.product_price_vat = product_price_vat
        self.shipping_cost_vat = shipping_cost_vat
        self.product_code = product_code
        self.add_item(discord.ui.TextInput(label="Product Price (without VAT)", style=discord.TextStyle.short, required=True, placeholder="3,98"))
        self.add_item(discord.ui.TextInput(label="Shipping Cost (without VAT)", style=discord.TextStyle.short, required=True, placeholder="2,42"))
        self.add_item(discord.ui.TextInput(label="Your Name", style=discord.TextStyle.short, required=True, placeholder="Your Name"))
        self.add_item(discord.ui.TextInput(label="Your Email", style=discord.TextStyle.short, required=True, placeholder="kuboestok@gmail.com"))
        self.add_item(discord.ui.TextInput(label="Your Phone Number", style=discord.TextStyle.short, required=True, placeholder="Your Phone Number"))

    async def callback(self, interaction: discord.Interaction):
        product_price_no_vat = self.children[0].value
        shipping_cost_no_vat = self.children[1].value
        your_name = self.children[2].value
        your_email = self.children[3].value
        your_phone = self.children[4].value

        # Add email selection modal
        email_modal = discord.ui.Select(
            placeholder="Choose Email Type",
            options=[
                discord.SelectOption(label="Normal Email", value="normal"),
                discord.SelectOption(label="Spoofed Email", value="spoofed")
            ]
        )

        # Generate random order number
        order_number = ''.join(random.choices('0123456789', k=9))

        # Construct the embed
        embed = discord.Embed(title="iStores Order Confirmed", color=discord.Color.green())
        embed.add_field(name="Order Number", value=order_number, inline=False)
        embed.add_field(name="Product Name", value=self.product_name, inline=False)
        embed.add_field(name="Product Code", value=self.product_code, inline=False)
        embed.add_field(name="Jednotková cena s DPH", value=self.product_price_vat, inline=True)
        embed.add_field(name="Celkom bez DPH", value=str(float(product_price_no_vat) + float(shipping_cost_no_vat)), inline=True)
        embed.add_field(name="Celkom s DPH", value=str(float(self.product_price_vat) + float(self.shipping_cost_vat)), inline=True)
        embed.add_field(name="Doručovacie údaje", value=f"{your_name}\n{your_email}\n{your_phone}", inline=False)
        embed.add_field(name="Login", value=f"{your_email}\nTelefón: {your_phone}", inline=False)

        # Create view for email selection
        view = discord.ui.View()

        # Add email selection callback
        async def email_callback(email_interaction):
            email_type = email_modal.values[0]

            # Email sending logic
            from emails.choise import send_email_with_type

            # Generate HTML receipt from template
            with open('receipt/istores.html', 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Replace placeholders
            receipt_html = html_content

            # Save the receipt
            receipt_filename = f"istores_receipt_{interaction.user.id}.html"
            with open(receipt_filename, 'w', encoding='utf-8') as f:
                f.write(receipt_html)

            # Send the email
            try:
                sender_email = "youremail@example.com"
                sender_name = "Your Name"
                subject = f"iStores.sk- Prijatie objednávky č. {order_number}"

                if email_type == "spoofed":
                    sender_email = "obchod@istores.sk"
                    sender_name = "obchod"

                # Get user's email from database
                cursor.execute("SELECT email FROM licenses WHERE owner_id = ?", (str(interaction.user.id),))
                result = cursor.fetchone()
                user_email = result[0] if result else your_email

                await send_email_with_type(email_type, user_email, sender_email, sender_name, subject, receipt_html, receipt_filename)
                await email_interaction.response.send_message(content=f"Receipt sent to {user_email} successfully!", ephemeral=True)
            except Exception as e:
                await email_interaction.response.send_message(content=f"Failed to send email: {str(e)}", ephemeral=True)

        email_modal.callback = email_callback
        view.add_item(email_modal)

        await interaction.response.send_message(embed=embed, view=view)

# Define brand lists
brands_usa = [
    ('Acne Studios', lambda: acnemodal()),
    ('Adidas', lambda: adidasmodal()),
    ('ADWYSD', lambda: adwysdmodal()),
    ('Amazon', lambda: amazonmodal()),
    ('Amazon UK', lambda: AmazonUKModal()),
    ('Apple', lambda: applemodal()),
    ("Arc'teryx", lambda: arcteryxmodal()),
    ('Argos', lambda: argosmodal()),
    ('Balenciaga', lambda: balenciagamodal()),
    ('Bape', lambda: bapemodal()),
    ('eBay Auth', lambda: ebayauthmodal())
]

brands_usa2 = [
    ('Broken Planet', lambda: brokenmodal()),
    ('Burberry', lambda: burberrymodal()),
    ('Canada Goose', lambda: canadagoose()),
    ('Cartier', lambda: cartiermodal()),
    ('Cernucci', lambda: cernuccimodal()),
    ('Chanel', lambda: chanelmodal()),
    ('Chew Forever', lambda: Chewforevermodal()),
    ('Chrome Hearts', lambda: chromemodal()),
    ('Chrono24', lambda: chronomodal())
]

brands_usa3 = [
    ('Coolblue', lambda: coolbluemodal()),
    ('Corteiz', lambda: crtzmodal()),
    ('Culture Kings', lambda: ckmodal()),
    ('Denim Tears', lambda: denimtearsmodal()),
    ('Dior', lambda: diormodal()),
    ('Dyson', lambda: dyson()),
    ('Ebay', lambda: EbayConfModal()),
    ('END.', lambda: endmodal()),
    ('Farfetch', lambda: farfetchmodal()),
    ('Flight Club', lambda: fightclubmodal()),
    ('Flannels', lambda: flannelsmodal())
]

brands_usa4 = [
    ('Gallery Dept', lambda: gallerydeptmodal()),
    ('Goat', lambda: goat()),
    ('Grailed', lambda: grailedmodal()),
    ('Guapi', lambda: guapimodal()),
    ('Gucci', lambda: guccimodal1()),
    ('Harrods', lambda: harrodsmodal()),
    ('Hermès', lambda: HermesModal()),
    ('iStores', lambda: istoresmodal()),
    ('JD Sports', lambda: jdsportsmodal()),
    ('Kick Game', lambda: kickgamemodal()),
    ('Legit App', lambda: legitappmodal())
]

brands_usa5 = [
    ('Loro Piana', lambda: loromodal()),
    ('Louis Vuitton', lambda: lvmodal()),
    ('Maison Margiela', lambda: maisonmodal()),
    ('Moncler', lambda: monclermodal()),
    ('Nike', lambda: nikemodal()),
    ('No Sauce The Plug', lambda: nosaucemodal()),
    ('Off-White', lambda: offwhitemodal()),
    ('Pandora', lambda: pandoramodal()),
    ('Prada', lambda: Pradamodal()),
    ('Ralph Lauren', lambda: ralphlaurenmodal()),
    ('Samsung', lambda: samsungmodal()),
    ('Sephora', lambda: sephoranmodal()),
    ('Stüssy', lambda: stussymodal()),
    ('Supreme', lambda: suprememodal()),
    ('Syna World', lambda: synaworldmodal()),
    ('The North Face', lambda: tnfmodal()),
    ('Trapstar', lambda: trapstarmodal()),
    ('UGG', lambda: uggmodal()),
    ('Vinted', lambda: vintedmodal()),
    ('Zalando US', lambda: zalandomodal()),
    ('Zara', lambda: zaramodal()),
]

# Ensure UGG, Vinted and Zalando US are included in the programmatic list creation
# This helps make sure they appear in the dropdown regardless of sorting
brands_usa5 = sorted(brands_usa5 + [
    ('UGG', lambda: uggmodal()),
    ('Vinted', lambda: vintedmodal()),
    ('Zalando US', lambda: zalandomodal())
], key=lambda x: x[0])

# Remove any duplicates while preserving order
seen = set()
brands_usa5 = [x for x in brands_usa5 if x[0] not in seen and not seen.add(x[0])]

# Define authentication brands
brands_auth = [
    ('eBay Auth', lambda: ebayauthmodal()),
    ('Legit App', lambda: legitappmodal())
]
# Define brand lists programmatically
def create_brand_lambda(brand_name):
    """Create a lambda function for a brand modal"""
    modal_func = all_brands.get(brand_name)
    if callable(modal_func):
        return (brand_name, lambda: modal_func())
    return None

# Create brand lists for each page
all_brand_keys = list(all_brands.keys())
brands_usa = [create_brand_lambda(brand) for brand in all_brand_keys[:13] if create_brand_lambda(brand)]
brands_usa2 = [create_brand_lambda(brand) for brand in all_brand_keys[13:26] if create_brand_lambda(brand)]
brands_usa3 = [create_brand_lambda(brand) for brand in all_brand_keys[26:39] if create_brand_lambda(brand)]
brands_usa4 = [create_brand_lambda(brand) for brand in all_brand_keys[39:52] if create_brand_lambda(brand)]
brands_usa5 = [create_brand_lambda(brand) for brand in all_brand_keys[52:65] if create_brand_lambda(brand)]

# Create a 6th page specifically for missing brands
brands_usa6 = [
    ('UGG', lambda: uggmodal()),
    ('Vinted', lambda: vintedmodal()),
    ('Zalando US', lambda: zalandomodal())
]

brands_auth = [create_brand_lambda(brand) for brand in all_brand_keys[65:] if create_brand_lambda(brand)]


# Filter out any None values that might be causing issues
brands_auth = [brand for brand in brands_auth if brand is not None]
class USView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        # Add buttons alphabetically
        self.add_item(discord.ui.Button(label="Adidas", custom_id="adidas", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="ADWYSD", custom_id="adwysd", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Amazon", custom_id="amazon", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Apple", custom_id="apple", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Apple Pickup", custom_id="applepickup", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Arc'teryx", custom_id="arcteryx", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Argos", custom_id="argos", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Balenciaga", custom_id="balenciaga", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Bape", custom_id="bape", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Bijenkorf", custom_id="bijenkorf", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Breuninger", custom_id="breuninger", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Broken Planet", custom_id="brokenplanet", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Burberry", custom_id="burberry", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Canada Goose", custom_id="canadagoose", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Cartier", custom_id="cartier", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Cernucci", custom_id="cernucci", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Chanel", custom_id="chanel", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Chew Forever", custom_id="chewforever", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Chrome Hearts", custom_id="chromehearts", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Chrono24", custom_id="chrono", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Coolblue", custom_id="coolblue", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Corteiz", custom_id="crtz", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Culture Kings", custom_id="culturekings", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Denim Tears", custom_id="denimtears", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Dior", custom_id="dior", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Dyson", custom_id="dyson", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="eBay", custom_id="ebayconf", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="END.", custom_id="end", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Farfetch", custom_id="farfetch", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Flight Club", custom_id="fightclub", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Flannels", custom_id="flannels", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Gallery Dept", custom_id="gallerydept", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Goat", custom_id="goat", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Grailed", custom_id="grailed", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Gucci", custom_id="gucci", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Guapi", custom_id="guapi", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Harrods", custom_id="harrods", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Hermès", custom_id="hermes", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="House of Fraser", custom_id="houseoffraser", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="iStores", custom_id="istores", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="JD Sports", custom_id="jdsports", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Kick Game", custom_id="kickgame", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Legit App", custom_id="legitapp", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Loro Piana", custom_id="loropiana", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Louis Vuitton", custom_id="lv", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Maison Margiela", custom_id="maisonmargiela", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Moncler", custom_id="moncler", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Nike", custom_id="nike", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="No Sauce The Plug", custom_id="nosauce", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Off-White", custom_id="offwhite", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Pandora", custom_id="pandora", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Prada", custom_id="prada", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Ralph Lauren", custom_id="ralphlauren", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Samsung", custom_id="samsung", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Sephora", custom_id="sephora", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="SNKRS", custom_id="snkrs", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Spider", custom_id="spider", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Stockx", custom_id="stockx", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Stussy", custom_id="stussy", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Supreme", custom_id="supreme", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Syna World", custom_id="synaworld", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="TNF", custom_id="tnf", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Trapstar", custom_id="trapstar", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="UGG", custom_id="ugg", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Vinted", custom_id="vinted", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Zalando US", custom_id="zalandous", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Zara", custom_id="zara", style=discord.ButtonStyle.primary))

class DEView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)
        # Add buttons alphabetically
        self.add_item(discord.ui.Button(label="Bijenkorf", custom_id="bijenkorf", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Breuninger", custom_id="breuninger", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Zalando DE", custom_id="zalandode", style=discord.ButtonStyle.primary))
        self.add_item(discord.ui.Button(label="Zara", custom_id="zara", style=discord.ButtonStyle.primary))

async def handle_button_click(interaction: discord.Interaction, custom_id: str):
    if interaction.user.id != interaction.client.user.id:
        if custom_id == "adidas":
            from modals.adidas import adidasmodal
            await interaction.response.send_modal(adidasmodal())
        elif custom_id == "adwysd":
            from modals.adwysd import adwysdmodal
            await interaction.response.send_modal(adwysdmodal())
        elif custom_id == "amazon":
            from modals.amazon import amazonmodal
            await interaction.response.send_modal(amazonmodal())
        elif custom_id == "apple":
            from modals.apple import applemodal
            await interaction.response.send_modal(applemodal())
        elif custom_id == "applepickup":
            from modals.applepickup import applepickupmodal
            await interaction.response.send_modal(applepickupmodal())
        elif custom_id == "arcteryx":
            from modals.arcteryx import arcteryxmodal
            await interaction.response.send_modal(arcteryxmodal())
        elif custom_id == "argos":
            from modals.argos import argosmodal
            await interaction.response.send_modal(argosmodal())
        elif custom_id == "balenciaga":
            from modals.balenciaga import balenciagamodal
            await interaction.response.send_modal(balenciagamodal())
        elif custom_id == "bape":
            from modals.bape import bapemodal
            await interaction.response.send_modal(bapemodal())
        elif custom_id == "bijenkorf":
            from modals.bijenkorf import bijenkorfmodal
            await interaction.response.send_modal(bijenkorfmodal())
        elif custom_id == "breuninger":
            from modals.breuninger import breuningermodal
            await interaction.response.send_modal(breuningermodal())
        elif custom_id == "brokenplanet":
            from modals.brokenplanet import brokenmodal
            await interaction.response.send_modal(brokenmodal())
        elif custom_id == "burberry":
            from modals.burberry import burberrymodal
            await interaction.response.send_modal(burberrymodal())
        elif custom_id == "canadagoose":
            from modals.canadagoose import canadagoose
            await interaction.response.send_modal(canadagoose())
        elif custom_id == "cartier":
            from modals.cartier import cartiermodal
            await interaction.response.send_modal(cartiermodal())
        elif custom_id == "cernucci":
            from modals.cernucci import cernuccimodal
            await interaction.response.send_modal(cernuccimodal())
        elif custom_id == "chanel":
            from modals.chanel import chanelmodal
            await interaction.response.send_modal(chanelmodal())
        elif custom_id == "chewforever":
            from modals.chewforever import Chewforevermodal
            await interaction.response.send_modal(Chewforevermodal())
        elif custom_id == "chromehearts":
            from modals.chromehearts import chromemodal
            await interaction.response.send_modal(chromemodal())
        elif custom_id == "chrono":
            from modals.chrono import chronomodal
            await interaction.response.send_modal(chronomodal())
        elif custom_id == "coolblue":
            from modals.coolblue import coolbluemodal
            await interaction.response.send_modal(coolbluemodal())
        elif custom_id == "culturekings":
            from modals.culturekings import ckmodal
            await interaction.response.send_modal(ckmodal())
        elif custom_id == "denimtears":
            from modals.denimtears import denimtearsmodal
            await interaction.response.send_modal(denimtearsmodal())
        elif custom_id == "dior":
            from modals.dior import diormodal
            await interaction.response.send_modal(diormodal())
        elif custom_id == "dyson":
            from modals.dyson import dyson
            await interaction.response.send_modal(dyson())
        elif custom_id == "ebayconf":
            from modals.ebayconf import EbayConfModal
            await interaction.response.send_modal(EbayConfModal())
        elif custom_id == "end":
            from modals.end import endmodal
            await interaction.response.send_modal(endmodal())
        elif custom_id == "farfetch":
            from modals.farfetch import farfetchmodal
            await interaction.response.send_modal(farfetchmodal())
        elif custom_id == "fightclub":
            from modals.fightclub import fightclubmodal
            await interaction.response.send_modal(fightclubmodal())
        elif custom_id == "flannels":
            from modals.flannels import flannelsmodal
            await interaction.response.send_modal(flannelsmodal())
        elif custom_id == "gallerydept":
            from modals.gallerydept import gallerydeptmodal
            await interaction.response.send_modal(gallerydeptmodal())
        elif custom_id == "goat":
            from modals.goat import goat
            await interaction.response.send_modal(goat())
        elif custom_id == "grailed":
            from modals.grailed import grailedmodal
            await interaction.response.send_modal(grailedmodal())
        elif custom_id == "gucci":
            from modals.gucci import guccimodal1
            await interaction.response.send_modal(guccimodal1())
        elif custom_id == "guapi":
            from modals.guapi import guapimodal
            await interaction.response.send_modal(guapimodal())
        elif custom_id == "harrods":
            from modals.harrods import harrodsmodal
            await interaction.response.send_modal(harrodsmodal())
        elif custom_id == "hermes":
            from modals.hermes import HermesModal
            await interaction.response.send_modal(HermesModal())
        elif custom_id == "istores":
            from modals.istores import istoresmodal
            await interaction.response.send_modal(istoresmodal())
        elif custom_id == "jdsports":
            from modals.jdsports import jdsportsmodal
            await interaction.response.send_modal(jdsportsmodal())
        elif custom_id == "kickgame":
            from modals.kickgame import kickgamemodal
            await interaction.response.send_modal(kickgamemodal())
        elif custom_id == "legitapp":
            from modals.legitapp import legitappmodal
            await interaction.response.send_modal(legitappmodal())
        elif custom_id == "loropiana":
            from modals.loropiana import loromodal
            await interaction.response.send_modal(loromodal())
        elif custom_id == "lv":
            from modals.lv import lvmodal
            await interaction.response.send_modal(lvmodal())
        elif custom_id == "maisonmargiela":
            from modals.maisonmargiela import maisonmodal
            await interaction.response.send_modal(maisonmodal())
        elif custom_id == "moncler":
            from modals.moncler import monclermodal
            await interaction.response.send_modal(monclermodal())
        elif custom_id == "nike":
            from modals.nike import nikemodal
            await interaction.response.send_modal(nikemodal())
        elif custom_id == "nosauce":
            from modals.nosauce import nosaucemodal
            await interaction.response.send_modal(nosaucemodal())
        elif custom_id == "offwhite":
            from modals.offwhite import offwhitemodal
            await interaction.response.send_modal(offwhitemodal())
        elif custom_id == "pandora":
            from modals.pandora import pandoramodal
            await interaction.response.send_modal(pandoramodal())
        elif custom_id == "prada":
            from modals.prada import Pradamodal
            await interaction.response.send_modal(Pradamodal())
        elif custom_id == "ralphlauren":
            from modals.ralphlauren import ralphlaurenmodal
            await interaction.response.send_modal(ralphlaurenmodal())
        elif custom_id == "samsung":
            from modals.samsung import SamsungModal as samsungmodal
            await interaction.response.send_modal(samsungmodal())
        elif custom_id == "sephora":
            from modals.sephora import sephoranmodal
            await interaction.response.send_modal(sephoranmodal())
        elif custom_id == "snkrs":
            from modals.snkrs import snkrsmodal
            await interaction.response.send_modal(snkrsmodal())
        elif custom_id == "spider":
            from modals.spider import spidermodal
            await interaction.response.send_modal(spidermodal())
        elif custom_id == "stockx":
            from modals.stockx import stockxmodal
            await interaction.response.send_modal(stockxmodal())
        elif custom_id == "stussy":
            from modals.stussy import stussymodal
            await interaction.response.send_modal(stussymodal())
        elif custom_id == "supreme":
            from modals.supreme import suprememodal
            await interaction.response.send_modal(suprememodal())
        elif custom_id == "synaworld":
            from modals.synaworld import synaworldmodal
            await interaction.response.send_modal(synaworldmodal())
        elif custom_id == "tnf":
            from modals.tnf import tnfmodal
            await interaction.response.send_modal(tnfmodal())
        elif custom_id == "trapstar":
            from modals.trapstar import trapstarmodal
            await interaction.response.send_modal(trapstarmodal())
        elif custom_id == "ugg":
            from modals.ugg import uggmodal
            await interaction.response.send_modal(uggmodal())
        elif custom_id == "vinted":
            from modals.vinted import vintedmodal
            await interaction.response.send_modal(vintedmodal())
        elif custom_id == "zalandode":
            from modals.zalandode import zalandodemodal
            await interaction.response.send_modal(zalandodemodal())
        elif custom_id == "zalandous":
            from modals.zalandous import zalandomodal
            await interaction.response.send_modal(zalandomodal())
        elif custom_id == "zara":
            from modals.zara import zaramodal
            await interaction.response.send_modal(zaramodal())
        elif custom_id == "ebayauth":
            from modals.ebayauth import ebayauthmodal
            await interaction.response.send_modal(ebayauthmodal())
        elif custom_id == "houseoffraser":
            from modals.houseoffrasers import houseoffrasermodal
            await interaction.response.send_modal(houseoffrasermodal())
        elif custom_id == "xerjoff":
            from modals.xerjoff import xerjoffmodal
            await interaction.response.send_modal(xerjoffmodal(interaction.user.id))
        else:
            await interaction.response.send_message("Invalid button ID.", ephemeral=True)
    else:
        await interaction.response.send_message("You can't use this panel.", ephemeral=True)



# Define brand lists programmatically
def create_brand_lambda(brand_name):
    """Create a lambda function for a brand modal"""
    modal_func = all_brands.get(brand_name)
    if callable(modal_func):
        return (brand_name, lambda: modal_func())
    return None

# Create brand lists for each page
all_brand_keys = list(all_brands.keys())
brands_usa = [create_brand_lambda(brand) for brand in all_brand_keys[:13] if create_brand_lambda(brand)]
brands_usa2 = [create_brand_lambda(brand) for brand in all_brand_keys[13:26] if create_brand_lambda(brand)]
brands_usa3 = [create_brand_lambda(brand) for brand in all_brand_keys[26:39] if create_brand_lambda(brand)]
brands_usa4 = [create_brand_lambda(brand) for brand in all_brand_keys[39:52] if create_brand_lambda(brand)]
brands_usa5 = [create_brand_lambda(brand) for brand in all_brand_keys[52:65] if create_brand_lambda(brand)]

# Create a 6th page specifically for missing brands
brands_usa6 = [
    ('UGG', lambda: uggmodal()),
    ('Vinted', lambda: vintedmodal()),
    ('Zalando US', lambda: zalandomodal())
]

brands_auth = [create_brand_lambda(brand) for brand in all_brand_keys[65:] if create_brand_lambda(brand)]


# Filter out any None values that might be causing issues
brands_auth = [brand for brand in brands_auth if brand is not None]