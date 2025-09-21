import discord

class NextstepHarrods(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="Next Step", style=discord.ButtonStyle.green)
    async def next_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)
            return

        from modals.harrods import harrodsmodal2
        await interaction.response.send_modal(harrodsmodal2())

import discord
from modals.acnestudios import acnemodal2
from modals.adidas import adidasmodal2
from modals.apple import  applemodal2
from modals.bape import bapemodal2
from modals.brokenplanet import brokenmodal2
from modals.canadagoose import canadagoose2
from modals.cartier import cartiermodal2
from modals.chromehearts import chromemodal2
from modals.cernucci import cernuccimodal2
from modals.bijenkorf import bijenkorfmodal2
from modals.flannels import flannelsmodal2
from modals.gallerydept import gallerydeptmodal2
from modals.grailed import grailedmodal2
from modals.loropiana import loromodal2
from modals.maisonmargiela import maisonmodal, maisonmodal2
from modals.pandora import pandoramodal2
from modals.sephora import sephoramodal2
from modals.stockx import stockxmodal2
from modals.tnf import tnfmodal2
from modals.adwysd import adwysdmodal2
from modals.hermes import HermesSecondModal
from modals.houseoffrasers import houseofffrasersmodal2
from modals.ugg import uggmodal2
from modals.vinted import vintedmodal2
from modals.zalandode import zalandodemodal2


class NextstepStockX(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__()
        self.owner_id = owner_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction, button):
        from modals.stockx import stockxmodal2
        modal = stockxmodal2()
        await interaction.response.send_modal(modal)

class NextstepSynaworld(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            from modals.synaworld import synaworldmodal2
            await interaction.response.send_modal(synaworldmodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)



class Nextstepbape(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(bapemodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)

class NextstepApple(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(applemodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)


class Nextsteptnf(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(tnfmodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)

class Nextstepcg(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(canadagoose2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)


class NextstepArgos(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            from modals.argos import argosmodal2
            await interaction.response.send_modal(argosmodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)


class Nextstepsephora(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(sephoramodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)


class Nextstepzara(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="Next Step", style=discord.ButtonStyle.green)
    async def next_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)
            return

        from modals.zara import zaramodal2
        await interaction.response.send_modal(zaramodal2())

class NextstepUgg(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="Next Step", style=discord.ButtonStyle.green)
    async def next_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)
            return

        from modals.ugg import uggmodal2
        await interaction.response.send_modal(uggmodal2())

class NextstepAcne(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(acnemodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)


class NextstepAdidas(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(adidasmodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)


class Nextstepbroken(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(brokenmodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)


class Nextstepcartier(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(cartiermodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)


class NextstepChrome(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(chromemodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)


class NextstepFlannels(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(flannelsmodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)


class NextstepGallerydept(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(gallerydeptmodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)


class NextstepLoro(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(loromodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)

class NextstepMaison(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            try:
                from modals.maisonmargiela import maisonmodal2
                await interaction.response.send_modal(maisonmodal2())
            except Exception as e:
                await interaction.response.send_message(content=f"Error: {str(e)}", ephemeral=True)
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)

class NextstepPandora(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(pandoramodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)

class Nextstepbijenkorf(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(bijenkorfmodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)

class NextstepGrailed(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id


    @discord.ui.button(label="Next Modal")
    async def nextmodal(self, interaction: discord.Interaction, Button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            await interaction.response.send_modal(grailedmodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)

class NextstepTrapstar(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__()
        self.owner_id = owner_id

    @discord.ui.button(label="Next Page", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("That is not your button.", ephemeral=True)
            return

        from modals.trapstar import trapstarmodal2
        await interaction.response.send_modal(trapstarmodal2())

class NextstepAdwysd(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Next Step", style=discord.ButtonStyle.green)
    async def next_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        from modals.adwysd import adwysdmodal2
        await interaction.response.send_modal(adwysdmodal2())

class NextstepCernucci(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label='Next Page', style=discord.ButtonStyle.primary, custom_id='nextpage_cernucci')
    async def button_callback(self, interaction, button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(content="This is not your panel!", ephemeral=True)
            return

        from modals.cernucci import cernuccimodal2
        await interaction.response.send_modal(cernuccimodal2())

class NextstepArcteryx(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="Next Step", style=discord.ButtonStyle.green)
    async def next_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)
            return

        from modals.arcteryx import arcteryxmodal2
        await interaction.response.send_modal(arcteryxmodal2())

# Store for temporarily holding form data between steps
store = {}

class NextstepGucci(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.productname = None
        self.productimage = None
        self.productsku = None
        self.productsize = None
        self.productprice = None

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            # Store the data from the first form
            global store
            store[self.owner_id] = {
                'productname': self.productname,
                'productimage': self.productimage,
                'productsku': self.productsku,
                'productsize': self.productsize,
                'productprice': self.productprice
            }

            from modals.gucci import guccimodal2
            await interaction.response.send_modal(guccimodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)
class NextstepKickgame(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id
        self.productlink = None
        self.productname = None
        self.productimage = None
        self.productsize = None
        self.productprice = None
        self.productcurrency = None
        self.productarrivaldate = None

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.primary)
    async def continue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            # Store the data from the first form
            if 'store' not in globals():
                global store
                store = {}

            store[self.owner_id] = {
                'productlink': self.productlink,
                'productname': self.productname,
                'productimage': self.productimage,
                'productsize': self.productsize,
                'productprice': self.productprice,
                'productcurrency': self.productcurrency,
                'productarrivaldate': self.productarrivaldate
            }

            from modals.kickgame import kickgamemodal2
            await interaction.response.send_modal(kickgamemodal2())
        else:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)

from discord.ext import commands, tasks
import discord
from discord.ui import View, Button, Modal, Select, select
from discord import Embed, File, Interaction, ui
import os
import asyncio
import random

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class NextstepApplepickup(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=180)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your menu!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label='Next Step', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        from modals.applepickup import applepickupmodal2
        await interaction.response.send_modal(applepickupmodal2())

class NextstepSupreme(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__()
        self.owner_id = owner_id

    @discord.ui.button(label='Next Page', style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction, button):
        if interaction.user.id == self.owner_id:
            from modals.supreme import suprememodal2
            await interaction.response.send_modal(suprememodal2())
        else:
            await interaction.response.send_message("This is not for you!", ephemeral=True)

class NextstepVinted(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__()
        self.owner_id = owner_id

    @discord.ui.button(label='Next Step', style=discord.ButtonStyle.primary)
    async def button_callback(self, interaction, button):
        if interaction.user.id == self.owner_id:
            from modals.vinted import vintedmodal2
            await interaction.response.send_modal(vintedmodal2())
        else:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
import discord
from modals.vinted import vintedmodal2

class NextstepVinted(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="Next Step", style=discord.ButtonStyle.green)
    async def next_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(content="That is not your panel", ephemeral=True)
            return

        await interaction.response.send_modal(vintedmodal2())

class NextstepZalando(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) == str(self.owner_id):
            await interaction.response.send_modal(zalandodemodal2())
        else:
            await interaction.response.send_message(content="This button is not for you.", ephemeral=True)

class NextstepHouseOfFraser(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="Continue", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) == str(self.owner_id):
            from modals.houseoffrasers import houseofffrasersmodal2
            await interaction.response.send_modal(houseofffrasersmodal2())
        else:
            await interaction.response.send_message(content="This button is not for you.", ephemeral=True)

class NextstepSneakerStoreCZ(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=300)
        self.owner_id = owner_id

    @discord.ui.button(label="Next Step", style=discord.ButtonStyle.green, emoji="✅")
    async def nextstep(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            # Assuming SneakerStoreCZModal2 is defined in modals.sneakerstorecz
            from modals.sneakerstorecz import SneakerStoreCZModal2 
            await interaction.response.send_modal(SneakerStoreCZModal2())
        else:
            await interaction.response.send_message("This is not your receipt generation session.", ephemeral=True)

class NextstepVW(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=180)
        self.owner_id = owner_id

    @discord.ui.button(label='Next Step', style=discord.ButtonStyle.green, emoji='✅')
    async def nextstep(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel", ephemeral=True)
            return

        from modals.vw import vwmodal2
        modal = vwmodal2()
        await interaction.response.send_modal(modal)

