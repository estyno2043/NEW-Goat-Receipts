
import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
from datetime import datetime, timedelta
import json
import logging
import os

class SubscriptionOption(discord.ui.Select):
    def __init__(self, view, user):
        self.parent_view = view
        self.user = user
        options = [
            discord.SelectOption(label="1 Day", description="Add 1 day of access", value="1_day"),
            discord.SelectOption(label="3 Days", description="Add 3 days of access", value="3_days"),
            discord.SelectOption(label="14 Days", description="Add 14 days of access", value="14_days"),
            discord.SelectOption(label="1 Month", description="Add 30 days of access", value="1_month"),
            discord.SelectOption(label="Lifetime", description="Add lifetime access", value="lifetime")
        ]
        super().__init__(placeholder="Select subscription duration...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.owner_id:
            await interaction.response.send_message("You cannot use this panel.", ephemeral=True)
            return

        selected = self.values[0]
        
        # Define subscription types and durations
        subscription_data = {
            "1_day": ("1 Day", 1),
            "3_days": ("3 Days", 3),
            "14_days": ("14 Days", 14),
            "1_month": ("1 Month", 30),
            "lifetime": ("Lifetime", 0)  # 0 means lifetime
        }
        
        subscription_type, days = subscription_data[selected]
        
        # Connect to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Check if user already exists in database
        cursor.execute("SELECT expiry FROM licenses WHERE owner_id = ?", (str(self.user.id),))
        existing_license = cursor.fetchone()
        
        # Generate key based on subscription type
        key_prefix = "1Day"
        if selected == "3_days":
            key_prefix = "3Days"
        elif selected == "14_days":
            key_prefix = "14Days"
        elif selected == "1_month":
            key_prefix = "1Month"
        elif selected == "lifetime":
            key_prefix = "LifetimeKey"
        
        # Generate unique key
        license_key = f"{key_prefix}-{self.user.id}"
        
        # Calculate expiry date
        if days > 0:
            expiry_date = datetime.now() + timedelta(days=days)
            expiry_str = expiry_date.strftime('%d/%m/%Y %H:%M:%S')
        else:
            # For lifetime, set a far future date
            expiry_date = datetime.now() + timedelta(days=3650)  # ~10 years
            expiry_str = expiry_date.strftime('%d/%m/%Y %H:%M:%S')
        
        if existing_license:
            # Update existing license
            cursor.execute('''
            UPDATE licenses 
            SET key = ?, expiry = ? 
            WHERE owner_id = ?
            ''', (license_key, expiry_str, str(self.user.id)))
        else:
            # Create new license
            cursor.execute('''
            INSERT INTO licenses (owner_id, key, expiry, emailtf, credentialstf) 
            VALUES (?, ?, ?, 'False', 'False')
            ''', (str(self.user.id), license_key, expiry_str))
        
        conn.commit()
        conn.close()
        
        # Try to add client role to the user
        try:
            # Load role ID from config
            with open("config.json", "r") as f:
                config = json.load(f)
                client_role_id = int(config.get("Client_ID", 1339305923545403442))
            
            # Get the role
            client_role = discord.utils.get(interaction.guild.roles, id=client_role_id)
            
            if client_role:
                await self.user.add_roles(client_role)
            else:
                print(f"Client role with ID {client_role_id} not found.")
        except Exception as e:
            print(f"Error adding role to user: {e}")
        
        # Send confirmation message
        embed = discord.Embed(
            title="Thanks for choosing us!",
            description=f"Successfully added `{subscription_type}` access to {self.user.mention} subscription.\n\n"
                        f"» Go to <#1339520924596043878> and read the setup guide.\n"
                        f"» Please make a vouch in this format `+rep <10/10> <experience>` <#1339306483816337510>",
            color=discord.Color.green()
        )
        
        # Add warning about email change
        embed.add_field(name="", value="🔴 Email can be changed once a week.", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=False)

class AdminPanelView(discord.ui.View):
    def __init__(self, owner_id, user):
        super().__init__(timeout=None)
        self.owner_id = owner_id  # ID of admin who invoked the command
        self.user = user  # User being edited

    @discord.ui.button(label="Information", style=discord.ButtonStyle.gray)
    async def handle_information(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return

        embed = discord.Embed(title="User Information", color=discord.Color.blue())

        # Connect to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Get license information
        cursor.execute('''
        SELECT key, expiry, email, name, street, city, zipp, country
        FROM licenses WHERE owner_id = ?
        ''', (str(self.user.id),))
        
        license_info = cursor.fetchone()
        conn.close()
        
        if license_info:
            key, expiry_str, email, name, street, city, zip_code, country = license_info if len(license_info) >= 8 else (
                license_info[0], license_info[1], license_info[2] if len(license_info) > 2 else "Not set", 
                "Not set", "Not set", "Not set", "Not set", "Not set"
            )
            
            # Check if it's a lifetime key
            if key and "LifetimeKey" in key:
                subscription_status = "Lifetime"
                remaining_days = "∞"
            else:
                try:
                    expiry_date = datetime.strptime(expiry_str, "%d/%m/%Y %H:%M:%S")
                    current_date = datetime.now()
                    remaining_days = (expiry_date - current_date).days
                    subscription_status = f"Expires: {expiry_str} ({remaining_days} days remaining)"
                except:
                    subscription_status = "Unknown"
                    remaining_days = "?"
            
            embed.add_field(name="User", value=f"{self.user.mention} ({self.user.id})", inline=False)
            embed.add_field(name="Subscription", value=subscription_status, inline=False)
            embed.add_field(name="Email", value=email or "Not set", inline=False)
            
            # Add personal info if available
            if name and name != "Not set":
                personal_info = f"Name: {name}\nStreet: {street}\nCity: {city}\nZIP: {zip_code}\nCountry: {country}"
                embed.add_field(name="Personal Information", value=personal_info, inline=False)
            else:
                embed.add_field(name="Personal Information", value="Not set", inline=False)
        else:
            embed.add_field(name="Status", value="No license information found for this user.", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Add Access", style=discord.ButtonStyle.gray)
    async def handle_add_access(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return
        
        # Create the subscription dropdown view
        view = discord.ui.View(timeout=180)
        view.add_item(SubscriptionOption(self, self.user))
        
        # Send response with dropdown
        embed = discord.Embed(
            title="Add Access",
            description=f"Select the subscription type to add for {self.user.mention}",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(label="Remove Access", style=discord.ButtonStyle.gray)
    async def handle_remove_access(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return
        
        # Connect to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        try:
            # Properly mark the license as expired
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y %H:%M:%S')
            
            # First check if the user has a license
            cursor.execute("SELECT key FROM licenses WHERE owner_id = ?", (str(self.user.id),))
            license_result = cursor.fetchone()
            
            if license_result:
                # Update the expiry to yesterday and add "EXPIRED" to the key to ensure it's invalid
                original_key = license_result[0]
                expired_key = f"EXPIRED-{original_key}" if not original_key.startswith("EXPIRED-") else original_key
                
                cursor.execute("UPDATE licenses SET expiry = ?, key = ? WHERE owner_id = ?", 
                              (yesterday, expired_key, str(self.user.id)))
            else:
                # If no license exists, create an expired one
                cursor.execute("INSERT INTO licenses (owner_id, key, expiry, emailtf, credentialstf) VALUES (?, ?, ?, 'False', 'False')",
                              (str(self.user.id), f"EXPIRED-Removed-{self.user.id}", yesterday))
            
            # Also clear cache in LicenseManager if it exists
            from utils.license_manager import LicenseManager
            if hasattr(LicenseManager, "_license_cache") and str(self.user.id) in LicenseManager._license_cache:
                LicenseManager._license_cache.pop(str(self.user.id), None)
            
            # Also remove from old tables
            cursor.execute("DELETE FROM user_emails WHERE user_id = ?", (str(self.user.id),))
            cursor.execute("DELETE FROM user_credentials WHERE user_id = ?", (str(self.user.id),))
            cursor.execute("DELETE FROM user_subscriptions WHERE user_id = ?", (str(self.user.id),))
            
            conn.commit()
            
            # No longer removing client role - keeping it as requested
            logging.info(f"Access removed for {self.user.name} but client role was kept")
            
        except Exception as e:
            print(f"Error updating user access: {e}")
            logging.error(f"Error removing access: {e}")
        finally:
            conn.close()
        
        embed = discord.Embed(
            title="Access Removed",
            description=f"Successfully removed access for {self.user.mention}.\nAll user data has been cleared from the database.\nThe client role has been kept as requested.",
            color=discord.Color.red()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Remove Email", style=discord.ButtonStyle.gray)
    async def handle_remove_email(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return
        
        # Connect to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        
        # Remove email
        cursor.execute("UPDATE licenses SET email = NULL WHERE owner_id = ?", (str(self.user.id),))
        conn.commit()
        conn.close()
        
        # Also check old user_emails table
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_emails WHERE user_id = ?", (str(self.user.id),))
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Email Removed",
            description=f"Successfully removed email for {self.user.mention}.",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="edit", description="Admin panel to edit user subscription and details")
    async def edit(self, interaction: discord.Interaction, user: discord.Member):
        # Check if the command invoker is the bot owner
        with open("config.json", "r") as f:
            config = json.load(f)
            owner_id = int(config.get("owner_id", 1339295766828552365))
        
        if interaction.user.id != owner_id:
            embed = discord.Embed(
                title="Access Denied",
                description="Only the bot owner can use this command.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create the admin panel view
        view = AdminPanelView(interaction.user.id, user)
        
        # Send response with panel
        embed = discord.Embed(
            title=f"Admin Panel | User Connected: {user.display_name}",
            description="Select an option below to use the Panel",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
