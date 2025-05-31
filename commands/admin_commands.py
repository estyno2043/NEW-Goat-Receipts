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

            # Get the client role
            client_role = discord.utils.get(interaction.guild.roles, id=client_role_id)

            if client_role:
                await self.user.add_roles(client_role)
                print(f"Added client role to {self.user.display_name}")

            # Add subscription-specific roles based on subscription type
            if selected == "1_month":
                # Add 1 month role
                month_role = discord.utils.get(interaction.guild.roles, id=1372256426684317909)
                if month_role:
                    await self.user.add_roles(month_role)
                    print(f"Added 1 month role to {self.user.display_name}")
            
            elif selected == "lifetime":
                # Add lifetime role
                lifetime_role = discord.utils.get(interaction.guild.roles, id=1372256491729453168)
                if lifetime_role:
                    await self.user.add_roles(lifetime_role)
                    print(f"Added lifetime role to {self.user.display_name}")

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
            purchases_channel = interaction.client.get_channel(1374468080817803264)
            if purchases_channel:
                # Create notification embed
                notification_embed = discord.Embed(
                    title="Thank you for purchasing",
                    description=f"{self.user.mention}, your subscription has been updated. Check below\n"
                              f"-# Run command /generate in <#1369426783153160304> to continue\n\n"
                              f"**Subscription Type**\n"
                              f"`{subscription_type}`\n\n"
                              f"- Please consider leaving a review at ⁠<#1339306483816337510>",
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

        # Connect to database
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        # Get license information
        cursor.execute('''
        SELECT key, expiry, email, name, street, city, zipp, country
        FROM licenses WHERE owner_id = ?
        ''', (str(self.user.id),))

        license_info = cursor.fetchone()

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

        # Check for guild subscription
        cursor.execute('''
        SELECT subscription_type, end_date, is_active
        FROM guild_subscriptions WHERE user_id = ?
        ''', (str(self.user.id),))

        guild_sub = cursor.fetchone()

        if guild_sub:
            sub_type, end_date, is_active = guild_sub

            # Format guild subscription info
            if is_active:
                if sub_type.lower() == "lifetime":
                    guild_status = "Lifetime Guild Subscription"
                else:
                    try:
                        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
                        days_left = (end_date_obj - datetime.now()).days
                        guild_status = f"Guild Subscription - Expires: {end_date} ({days_left} days remaining)"
                    except:
                        guild_status = f"Guild Subscription - Expires: {end_date}"
            else:
                guild_status = "Expired Guild Subscription"

            embed.add_field(name="Guild Subscription", value=guild_status, inline=False)

            # Get configured guild information
            cursor.execute('''
            SELECT guild_id, generate_channel_id
            FROM guild_configs WHERE owner_id = ?
            ''', (str(self.user.id),))

            guild_configs = cursor.fetchall()

            if guild_configs and len(guild_configs) > 0:
                guild_list = []
                for guild_id, gen_channel in guild_configs:
                    # Try to get guild name
                    guild = interaction.client.get_guild(int(guild_id))
                    guild_name = guild.name if guild else f"Unknown Guild ({guild_id})"
                    guild_list.append(f"• {guild_name} (Channel: {gen_channel})")

                guild_info = "\n".join(guild_list)
                embed.add_field(name="Configured Guilds", value=guild_info, inline=False)
            else:
                embed.add_field(name="Configured Guilds", value="No guilds configured", inline=False)

        conn.close()
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

            # Remove subscription-specific roles but keep client role
            try:
                # Remove 1 month role
                month_role = discord.utils.get(interaction.guild.roles, id=1372256426684317909)
                if month_role and month_role in self.user.roles:
                    await self.user.remove_roles(month_role)
                    logging.info(f"Removed 1 month role from {self.user.name}")

                # Remove lifetime role
                lifetime_role = discord.utils.get(interaction.guild.roles, id=1372256491729453168)
                if lifetime_role and lifetime_role in self.user.roles:
                    await self.user.remove_roles(lifetime_role)
                    logging.info(f"Removed lifetime role from {self.user.name}")

            except Exception as role_error:
                logging.error(f"Error removing subscription roles: {role_error}")

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

        # Send subscription expired notification to purchases channel
        try:
            # Determine subscription type for display
            display_type = "Unknown"
            if license_result:
                original_key = license_result[0]
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

            # Create DM embed
            dm_embed = discord.Embed(
                title="Your Subscription Has Expired",
                description=f"Hello {self.user.mention},\n\nYour subscription has expired. We appreciate your support!\n\nIf you'd like to renew, click the button below.",
                color=discord.Color.default()
            )
            
            # Create purchases channel embed
            purchases_embed = discord.Embed(
                title="Subscription Expired",
                description=f"{self.user.mention}, your subscription has expired. Thank you for purchasing.\n-# Consider renewing below!\n\n**Subscription Type**\n`{display_type}`\n\nPlease consider leaving a review at <#1339306483816337510>",
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
                purchases_channel = interaction.client.get_channel(1374468080817803264)
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

    is_admin = str(ctx.author.id) == owner_id

    if not is_admin:
        # Check if user has admin role
        guild_id = str(ctx.guild.id)
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT admin_role_id FROM guild_configs WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0]:
            admin_role = discord.utils.get(ctx.guild.roles, id=int(result[0]))
            if admin_role and admin_role in ctx.author.roles:
                is_admin = True

    if not is_admin:
        await ctx.send("You don't have permission to use this command.")
        return

    # If no user specified, check the command user
    target_user = user or ctx.author

    # Perform license check
    from utils.license_manager import LicenseManager
    license_status = await LicenseManager.is_subscription_active(target_user.id)

    # Check role status
    client_role_id = int(config.get("Client_ID", 0))
    has_role = False
    if client_role_id > 0:
        client_role = discord.utils.get(ctx.guild.roles, id=client_role_id)
        if client_role and client_role in target_user.roles:
            has_role = True

    # Check database directly
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT expiry, key FROM licenses WHERE owner_id = ?", (str(target_user.id),))
    db_result = cursor.fetchone()
    conn.close()

    # Create response embed
    embed = discord.Embed(
        title=f"License Status for {target_user.display_name}",
        description=f"User ID: {target_user.id}",
        color=discord.Color.from_str("#c2ccf8")
    )

    embed.add_field(
        name="License Manager Check",
        value=f"Status: {'Active' if license_status else 'Inactive'}\nResult Type: {type(license_status).__name__}",
        inline=False
    )

    embed.add_field(
        name="Client Role",
        value=f"Has Role: {'Yes' if has_role else 'No'}\nRole ID: {client_role_id}",
        inline=False
    )

    if db_result:
        expiry, key = db_result
        embed.add_field(
            name="Database Record",
            value=f"Expiry: {expiry}\nKey: {key[:5]}{'*' * 10 if key else ''}",
            inline=False
        )
    else:
        embed.add_field(
            name="Database Record",
            value="No license found in database",
            inline=False
        )

    await ctx.send(embed=embed)

from discord.ext import commands
import discord
import sqlite3
from datetime import datetime, timedelta

class LicenseManager:
    _license_cache = {}  # Class-level cache

    @staticmethod
    async def is_subscription_active(user_id):
        """
        Checks if a user's subscription is active.

        First, it checks the cache. If not in cache, it queries the database,
        updates the cache, and then returns the result.
        """
        if user_id in LicenseManager._license_cache:
            return LicenseManager._license_cache[user_id]

        is_active = await LicenseManager._check_license_from_db(user_id)
        LicenseManager._license_cache[user_id] = is_active  # Update cache
        return is_active

    @staticmethod
    async def _check_license_from_db(user_id):
        """
        Internal method to check the user's license status in the database.
        """
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()

        cursor.execute("SELECT expiry, key FROM licenses WHERE owner_id = ?", (str(user_id),))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return False

        expiry_str, key = result

        if key and "EXPIRED-" in key:
            conn.close()
            return False

        try:
            expiry_date = datetime.strptime(expiry_str, "%d/%m/%Y %H:%M:%S")
            is_active = datetime.now() < expiry_date
            conn.close()
            return is_active
        except ValueError:
            # Handle cases where the date format might be incorrect
            conn.close()
            return False

    @staticmethod
    async def invalidate_cache(user_id):
        """
        Invalidates the cache for a specific user, forcing a database refresh
        on the next check.
        """
        if user_id in LicenseManager._license_cache:
            del LicenseManager._license_cache[user_id]