# Applying the provided changes to the original code, focusing on webhook notification and edit command functionality.
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
            discord.SelectOption(label="Lifetime", description="Add lifetime access", value="lifetime"),
            discord.SelectOption(label="Guild 30 Days", description="Add 30 days guild access", value="guild_30days"),
            discord.SelectOption(label="Guild Lifetime", description="Add lifetime guild access", value="guild_lifetime"),
            discord.SelectOption(label="Lite Subscription", description="Generate up to 7 receipts", value="lite") # Added Lite Subscription option
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
            "lifetime": ("Lifetime", 0),  # 0 means lifetime
            "guild_30days": ("Guild 30 Days", 30),
            "guild_lifetime": ("Guild Lifetime", 0),  # 0 means lifetime
            "lite": ("Lite Subscription", 0) # Lite subscription does not have a time limit, but a receipt limit
        }

        subscription_type, days = subscription_data[selected]

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
        elif selected == "guild_30days":
            key_prefix = "guild_30days"
        elif selected == "guild_lifetime":
            key_prefix = "guild_lifetime"
        elif selected == "lite":
            key_prefix = "LiteKey" # Prefix for Lite Subscription keys

        # Generate unique key
        license_key = f"{key_prefix}-{self.user.id}"

        # Calculate expiry date
        if days > 0:
            expiry_date = datetime.now() + timedelta(days=days)
            expiry_str = expiry_date.strftime('%d/%m/%Y %H:%M:%S')
        else:
            # For lifetime and Lite Subscription, set a far future date or handle differently
            if selected == "lifetime" or selected == "guild_lifetime":
                expiry_date = datetime.now() + timedelta(days=3650)  # ~10 years
                expiry_str = expiry_date.strftime('%d/%m/%Y %H:%M:%S')
            else: # For Lite Subscription, expiry is not the primary limiter
                expiry_str = "N/A" # Indicate no specific expiry date

        # Save to MongoDB
        from utils.mongodb_manager import mongo_manager
        license_data = {
            "subscription_type": subscription_type.replace(" ", "").lower(),
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": expiry_str,
            "is_active": True,
            "expiry": expiry_str,
            "key": license_key
        }

        # Add receipt tracking for lite subscription
        if selected == "lite":
            license_data["receipt_count"] = 0
            license_data["max_receipts"] = 7


        success = mongo_manager.create_or_update_license(self.user.id, license_data)

        if not success:
            await interaction.response.send_message("Failed to save license to database. Please try again.", ephemeral=True)
            return

        # Try to add client role to the user
        try:
            # Use the specific client role ID for manual access addition
            client_role_id = 1350410798899531778

            # Get the client role
            client_role = discord.utils.get(interaction.guild.roles, id=client_role_id)

            if client_role:
                await self.user.add_roles(client_role)
                print(f"Added client role to {self.user.display_name}")

            # Add new unified role for 1 month, lifetime, and guild subscriptions
            if selected in ["1_month", "lifetime", "guild_30days", "guild_lifetime"]:
                # Add the new role for all premium subscription types
                new_role = discord.utils.get(interaction.guild.roles, id=1402941054243831888)
                if new_role:
                    await self.user.add_roles(new_role)
                    print(f"Added new subscription role to {self.user.display_name}")

        except Exception as e:
            print(f"Error adding roles to user: {e}")

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

        # Send purchase notification to Purchases channel (like key redemption)
        try:
            purchases_channel = interaction.client.get_channel(1402938227962417222)
            if purchases_channel:
                # Create notification embed
                notification_embed = discord.Embed(
                    title="Thank you for purchasing",
                    description=f"{self.user.mention}, your subscription has been updated. Check below\n"
                              f"-# Run command /generate in <#1350413411455995904> to continue\n\n"
                              f"**Subscription Type**\n"
                              f"`{subscription_type}`\n\n"
                              f"- Please consider leaving a review at <#1350413086074474558>",
                    color=discord.Color.green()
                )

                await purchases_channel.send(content=self.user.mention, embed=notification_embed)

                # Send DM to user
                try:
                    await self.user.send(embed=notification_embed)
                except:
                    print(f"Could not send DM to {self.user.display_name}")
        except Exception as e:
            print(f"Error sending purchase notification: {e}")

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

        # Get license information from MongoDB
        from utils.mongodb_manager import mongo_manager
        license_doc = mongo_manager.get_license(self.user.id)
        user_credentials = mongo_manager.get_user_credentials(self.user.id)
        user_email = mongo_manager.get_user_email(self.user.id)

        if license_doc:
            key = license_doc.get("key", "")
            expiry_str = license_doc.get("expiry", "")
            email = user_email or "Not set"

            # Get user credentials
            name = "Not set"
            street = "Not set"
            city = "Not set"
            zip_code = "Not set"
            country = "Not set"

            if user_credentials:
                name = user_credentials.get("name", "Not set")
                street = user_credentials.get("street", "Not set")
                city = user_credentials.get("city", "Not set")
                zip_code = user_credentials.get("zip", "Not set")
                country = user_credentials.get("country", "Not set")

            # Check subscription type and guild access
            guild_access = "No Guild Access"
            subscription_status = "Unknown"
            remaining_days = "?"

            if key:
                # Check for guild subscriptions
                if "guild_lifetime" in key.lower():
                    guild_access = "Guild Lifetime"
                    subscription_status = "Guild Lifetime"
                    remaining_days = "∞"
                elif "guild_30days" in key.lower():
                    guild_access = "Guild 30 Days"
                    try:
                        expiry_date = datetime.strptime(expiry_str, "%d/%m/%Y %H:%M:%S")
                        current_date = datetime.now()
                        remaining_days = (expiry_date - current_date).days
                        subscription_status = f"Guild 30 Days - Expires: {expiry_str} ({remaining_days} days remaining)"
                    except:
                        subscription_status = "Guild 30 Days - Unknown expiry"
                        remaining_days = "?"
                # Check for regular lifetime key
                elif "LifetimeKey" in key or "lifetime" in key.lower():
                    subscription_status = "Lifetime"
                    remaining_days = "∞"
                # Lite subscription
                elif "LiteKey" in key or "lite" in key.lower():
                    receipt_count = license_doc.get("receipt_count", 0)
                    max_receipts = license_doc.get("max_receipts", 7)
                    subscription_status = f"Lite Subscription - Receipts used: {receipt_count}/{max_receipts}"
                    remaining_days = f"{max_receipts - receipt_count} remaining"
                # Regular subscription
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
            embed.add_field(name="Guild Access", value=guild_access, inline=False)
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

        try:
            # Get license information before deletion for notification
            from utils.mongodb_manager import mongo_manager
            original_license = mongo_manager.get_license(self.user.id)

            # Remove from MongoDB
            mongo_manager.delete_license(self.user.id)
            mongo_manager.delete_user_credentials(self.user.id)
            mongo_manager.delete_user_email(self.user.id)

            # Also clear cache in LicenseManager if it exists
            from utils.license_manager import LicenseManager
            if hasattr(LicenseManager, "_license_cache") and str(self.user.id) in LicenseManager._license_cache:
                LicenseManager._license_cache.pop(str(self.user.id), None)

            # Remove subscription-specific roles but keep client role
            try:
                # Remove new unified subscription role
                new_role = discord.utils.get(interaction.guild.roles, id=1402941054243831888)
                if new_role and new_role in self.user.roles:
                    await self.user.remove_roles(new_role)
                    logging.info(f"Removed subscription role from {self.user.name}")

                # Also remove old roles in case they still exist
                month_role = discord.utils.get(interaction.guild.roles, id=1372256426684317909)
                if month_role and month_role in self.user.roles:
                    await self.user.remove_roles(month_role)
                    logging.info(f"Removed old 1 month role from {self.user.name}")

                lifetime_role = discord.utils.get(interaction.guild.roles, id=1372256491729453168)
                if lifetime_role and lifetime_role in self.user.roles:
                    await self.user.remove_roles(lifetime_role)
                    logging.info(f"Removed old lifetime role from {self.user.name}")

            except Exception as role_error:
                logging.error(f"Error removing subscription roles: {role_error}")

            # No longer removing client role - keeping it as requested
            logging.info(f"Access removed for {self.user.name} but client role was kept")

        except Exception as e:
            print(f"Error updating user access: {e}")
            logging.error(f"Error removing access: {e}")

        embed = discord.Embed(
            title="Access Removed",
            description=f"Successfully removed access for {self.user.mention}.\nAll user data has been cleared from the database.\nThe client role has been kept as requested.",
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Send subscription expired notification to purchases channel
        try:
            # Determine subscription type for display using stored license info
            display_type = "Unknown"
            if original_license:
                original_key = original_license.get("key", "")
                if "LifetimeKey" in original_key:
                    display_type = "Lifetime"
                elif "1Month" in original_key:
                    display_type = "1 Month"
                elif "14Days" in original_key or "14day" in original_key:
                    display_type = "14 Days"
                elif "3Days" in original_key or "3day" in original_key:
                    display_type = "3 Days"
                elif "1Day" in original_key or "1day" in original_key:
                    display_type = "1 Day"
                elif "LiteKey" in original_key:
                    display_type = "Lite Subscription"

            # Create DM embed
            dm_embed = discord.Embed(
                title="Your Subscription Has Expired",
                description=f"Hello {self.user.mention},\n\nYour subscription has expired. We appreciate your support!\n\nIf you'd like to renew, click the button below.",
                color=discord.Color.default()
            )

            # Create purchases channel embed
            purchases_embed = discord.Embed(
                title="Subscription Expired",
                description=f"{self.user.mention}, your subscription has expired. Thank you for purchasing.\n-# Consider renewing below!\n\n**Subscription Type**\n`{display_type}`\n\nPlease consider leaving a review at <#1350413086074474558>",
                color=discord.Color.default()
            )

            # Create renewal buttons
            dm_view = discord.ui.View()
            dm_view.add_item(discord.ui.Button(label="Renew", style=discord.ButtonStyle.link, url="https://goatreceipts.com"))

            purchases_view = discord.ui.View()
            purchases_view.add_item(discord.ui.Button(label="Renew", style=discord.ButtonStyle.link, url="https://goatreceipts.com"))

            # Try to DM the user
            try:
                await self.user.send(embed=dm_embed, view=dm_view)
                logging.info(f"Sent expiration DM to {self.user.name}")
            except:
                logging.info(f"Could not DM {self.user.name} about access removal")

            # Send notification to Purchases channel
            try:
                purchases_channel = interaction.client.get_channel(1402938227962417222)
                if purchases_channel:
                    await purchases_channel.send(content=self.user.mention, embed=purchases_embed, view=purchases_view)
                    logging.info(f"Sent expiration notification to purchases channel for {self.user.name}")
            except Exception as channel_error:
                logging.error(f"Could not send access removal notification to Purchases channel: {channel_error}")

        except Exception as notification_error:
            logging.error(f"Error sending subscription expiration notifications: {notification_error}")

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

    @app_commands.command(name="limit", description="Apply 11-hour rate limit to a user (Owner only)")
    async def limit(self, interaction: discord.Interaction, user: discord.Member):
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

        # Apply 11-hour rate limit using MongoDB
        from utils.mongodb_manager import mongo_manager
        from datetime import datetime, timedelta

        # Set limit expiry to 11 hours from now
        limit_expiry = datetime.now() + timedelta(hours=11)

        # Save rate limit to MongoDB
        rate_limit_data = {
            "user_id": str(user.id),
            "limited_by": str(interaction.user.id),
            "limit_start": datetime.now().isoformat(),
            "limit_end": limit_expiry.isoformat(), # Changed to limit_end for clarity
            "reason": "Rate limited by owner"
        }

        success = mongo_manager.set_user_rate_limit(user.id, rate_limit_data)

        if success:
            embed = discord.Embed(
                title="Rate Limit Applied",
                description=f"Successfully applied 11-hour rate limit to {user.mention}.\nThey will be unable to use `/generate` or `/menu` until {limit_expiry.strftime('%d/%m/%Y %H:%M:%S')}",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="Error",
                description="Failed to apply rate limit. Please try again.",
                color=discord.Color.red()
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unlimit", description="Remove rate limit from a user (Owner only)")
    async def unlimit(self, interaction: discord.Interaction, user: discord.Member):
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

        # Remove rate limit using MongoDB
        from utils.mongodb_manager import mongo_manager

        rate_limit_success = mongo_manager.remove_user_rate_limit(user.id)

        # Also reset email change limitation
        email_limit_success = mongo_manager.reset_email_change_limit(user.id)

        if rate_limit_success:
            description = f"Successfully removed rate limit from {user.mention}.\nThey can now use `/generate` and `/menu` commands normally."
            if email_limit_success:
                description += "\nEmail change limitation has also been reset - they can change their email once."
            else:
                description += "\nNote: Email limitation reset failed or user had no email restrictions."

            embed = discord.Embed(
                title="Limits Removed",
                description=description,
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Error",
                description="Failed to remove rate limit or user was not rate limited.",
                color=discord.Color.red()
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

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

        # Create admin panel embed
        embed = discord.Embed(
            title="Admin Panel",
            description=f"Managing user: {user.mention} ({user.display_name})",
            color=discord.Color.blue()
        )

        # Create the admin panel view
        view = AdminPanelView(interaction.user.id, user)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def get_user_info(self, user_id):
        """Get comprehensive user information from all sources"""
        info = {
            'license': None,
            'credentials': None,
            'email': None,
            'subscription_active': False,
            'guild_access': {}
        }

        try:
            # Get license info
            from utils.mongodb_manager import mongo_manager
            license_doc = mongo_manager.get_license(user_id)
            if license_doc:
                info['license'] = license_doc

            # Get user details (credentials + email)
            user_details = mongo_manager.get_user_details(user_id)
            if user_details:
                name, street, city, zip_code, country, email = user_details
                info['credentials'] = {
                    'name': name,
                    'street': street,
                    'city': city,
                    'zip': zip_code,
                    'country': country
                }
                info['email'] = email

            # Check subscription status
            from utils.license_manager import LicenseManager
            info['subscription_active'] = await LicenseManager.is_subscription_active(user_id)

            # Get guild-specific access (including webhook-granted access)
            db = mongo_manager.get_database()
            if db:
                # Check all server access records
                server_access_records = list(db.server_access.find({"user_id": str(user_id)}))
                for record in server_access_records:
                    guild_id = record.get('guild_id')
                    if guild_id:
                        info['guild_access'][guild_id] = {
                            'access_type': record.get('access_type'),
                            'expiry': record.get('expiry'),
                            'added_by': record.get('added_by', 'system'),
                            'added_at': record.get('added_at'),
                            'source': 'webhook' if record.get('added_by') == 'system' else 'manual'
                        }

                # Also check guild-specific licenses
                guild_licenses = list(db.guild_user_licenses.find({"user_id": str(user_id)}))
                for record in guild_licenses:
                    guild_id = record.get('guild_id')
                    license_data = record.get('license_data', {})
                    if guild_id and license_data:
                        if guild_id not in info['guild_access']:
                            info['guild_access'][guild_id] = {}
                        info['guild_access'][guild_id].update({
                            'license_type': license_data.get('subscription_type'),
                            'license_expiry': license_data.get('expiry'),
                            'granted_by': license_data.get('granted_by'),
                            'source': 'license'
                        })

        except Exception as e:
            logging.error(f"Error getting user info for {user_id}: {e}")

        return info

    @app_commands.command(name="userinfo", description="Get comprehensive information for a user")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member):
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

        # Get user information
        user_id = str(user.id)
        user_info = await self.get_user_info(user_id)

        # Create embed
        embed = discord.Embed(
            title=f"User Information for {user.name}",
            color=discord.Color.blue()
        )

        # License Information
        if user_info['license']:
            license_data = user_info['license']
            embed.add_field(name="License Key", value=license_data.get('key', 'N/A'), inline=False)
            embed.add_field(name="Expiry", value=license_data.get('expiry', 'N/A'), inline=False)
            # Display Lite Subscription specific info
            if license_data.get('subscription_type') == 'litesubscription':
                receipt_count = license_data.get('receipt_count', 0)
                max_receipts = license_data.get('max_receipts', 7)
                embed.add_field(name="Receipts Used", value=f"{receipt_count}/{max_receipts}", inline=False)
        else:
            embed.add_field(name="License", value="No license found", inline=False)

        # Personal Information
        if user_info['credentials']:
            credentials = user_info['credentials']
            personal_info = (
                f"Name: {credentials.get('name', 'N/A')}\n"
                f"Street: {credentials.get('street', 'N/A')}\n"
                f"City: {credentials.get('city', 'N/A')}\n"
                f"ZIP: {credentials.get('zip', 'N/A')}\n"
                f"Country: {credentials.get('country', 'N/A')}"
            )
            embed.add_field(name="Personal Information", value=personal_info, inline=False)
        else:
            embed.add_field(name="Personal Information", value="No details found", inline=False)

        # Guild Access Information
        if user_info['guild_access']:
            guild_access_text = ""
            for guild_id, access_data in user_info['guild_access'].items():
                try:
                    guild = self.bot.get_guild(int(guild_id))
                    guild_name = guild.name if guild else f"Guild {guild_id}"
                    access_type = access_data.get('access_type', 'Unknown')
                    expiry = access_data.get('expiry', 'Unknown')
                    source = access_data.get('source', 'unknown')
                    added_by = access_data.get('added_by', 'Unknown')

                    source_text = ""
                    if source == 'webhook':
                        source_text = " (via invite tracker)"
                    elif source == 'manual':
                        source_text = f" (by <@{added_by}>)"
                    elif source == 'license':
                        source_text = " (license key)"

                    guild_access_text += f"**{guild_name}**: {access_type} (expires: {expiry}){source_text}\n"
                except:
                    guild_access_text += f"**Guild {guild_id}**: {access_data.get('access_type', 'Unknown')}\n"

            embed.add_field(name="Guild Access", value=guild_access_text[:1024], inline=False)

        # Subscription Status
        embed.add_field(name="Subscription Active", value=str(user_info['subscription_active']), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))

# Assuming 'bot' is defined elsewhere, e.g., bot = commands.Bot(...)
# You might need to adjust this depending on how your bot instance is created.
# I'm adding these lines to make the below code runnable

class KeygenView(discord.ui.View):  # Dummy class for KeygenView
    def __init__(self):
        super().__init__()

# Add license check debug command

@commands.command(name="keygen", description="Generate license keys (Owner only)")
async def keygen_command(ctx):
    # Check if user is the bot owner
    with open("config.json", "r") as f:
        import json
        config = json.load(f)
        owner_id = config.get("owner_id", "0")

    if str(ctx.author.id) != owner_id:
        await ctx.send("You don't have permission to use this command.")
        return

    embed = discord.Embed(
        title="Generate License Keys",
        description="Select the subscription type to generate 30 new license keys.",
        color=discord.Color.from_str("#c2ccf8")
    )

    view = KeygenView()
    await ctx.send(embed=embed, view=view)

@commands.command(name="checklicense", description="Check license status for a user (Admin only)")
async def check_license_command(ctx, user: discord.Member = None):
    # Check if user is admin or bot owner
    with open("config.json", "r") as f:
        import json
        config = json.load(f)
        owner_id = config.get("owner_id", "0")

    if str(ctx.author.id) != owner_id:
        await ctx.send("You don't have permission to use this command.")
        return

    if user is None:
        user = ctx.author

    # Check license status
    from utils.license_manager import LicenseManager
    license_status = await LicenseManager.is_subscription_active(str(user.id))

    embed = discord.Embed(
        title=f"License Status for {user.display_name}",
        color=discord.Color.green() if license_status else discord.Color.red()
    )

    embed.add_field(
        name="Status",
        value="Active" if license_status else "Inactive/Expired",
        inline=False
    )

    await ctx.send(embed=embed)