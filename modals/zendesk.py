# Zendesk brand placeholder - handled directly in brand selection callback
# This file exists only so Zendesk appears in the brand discovery list

import discord
from discord import ui

class zendeskmodal(ui.Modal, title="Zendesk"):
    # This modal is never actually used - Zendesk is handled directly in BrandSelectMenu callback
    pass