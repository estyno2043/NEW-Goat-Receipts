import logging
import sqlite3
import os
import json
import discord
from discord.ext import commands
from discord import app_commands

# This is a template file for guild bots
# It will be used to generate bot files for guild users

# Load configuration
config = {}
try:
    with open("config.json", "r") as f:
        config = json.load(f)
except Exception as e:
    logging.error(f"Failed to load config: {e}")
    config = {}