
import asyncio
import discord
from discord.ui import Select
from discord import SelectOption, ui, app_commands, Interaction
import random
import time
from datetime import datetime

# Import the existing EbayConfModal from ebayconf.py
from modals.ebayconf import EbayConfModal as EbayConfOriginal

# Create an alias to make it work with the dynamic import system
class EbayConfModal(EbayConfOriginal):
    pass

# Ensure the class is directly accessible
ebaymodal = EbayConfModal
