import os
import discord
import json
from discord import ui
from datetime import datetime, timedelta
import sqlite3


conn = sqlite3.connect('data.db')
cursor = conn.cursor()

config = json.load(open("config.json", encoding="utf-8"))



class adminDrop(discord.ui.Select):
    def __init__(self, owner_id, user):
        self.owner_id = owner_id
        self.user = user

        options = [
            discord.SelectOption(label='1 Day', description='Standard', emoji='⚡', value="1dstandard"),
            discord.SelectOption(label='14 Days', description='Standard', emoji='🔥', value="14dstandard"),
            discord.SelectOption(label='1 Month', description='Standard', emoji='🚀', value="1mstandard"),
            discord.SelectOption(label='Lifetime', description='Standard', emoji='⭐', value="lftstandard"),
        ]


        super().__init__(placeholder='Select an option to proceed...', min_values=1, max_values=1, options=options)


    async def callback(self, interaction: discord.Interaction):
        try:
            if interaction.user.id != self.owner_id:
                await interaction.response.send_message(content="That is not your panel", ephemeral=True)
                return
            
            # Defer the response immediately
            await interaction.response.defer(ephemeral=True)
            value = self.values[0]
        except discord.errors.InteractionResponded:
            # Interaction already responded to, continue with the value
            value = self.values[0]
        except Exception as e:
            try:
                await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
            except discord.errors.InteractionResponded:
                await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
            return

        user = self.user
        guild = interaction.guild  # Getting the guild from the interaction
        user = guild.get_member(user)

        role_mapping = {
            'lftstandard': (1500, 'LifetimeKey'),
            '1mstandard': (30, '1Month'),
            '14dstandard': (14, '14Days'),
            '1dstandard': (1, '1Day'),
            'lftpremium': (1500, 'LifetimeKey'),
            '1mpremium': (30, '1Month')
        }

        # Try to get server-specific role ID first
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT client_id FROM server_configs WHERE guild_id = ?", (str(interaction.guild.id),))
        server_role = cursor.fetchone()
        conn.close()

        # Use server-specific role ID if available, otherwise fall back to config
        if server_role and server_role[0]:
            buyer_role_id = int(server_role[0])
        else:
            buyer_role_id = int(config.get("Client_ID"))

        buyer_role = discord.utils.get(interaction.guild.roles, id=buyer_role_id)
        print(f"Guild: {interaction.guild.id}, Role ID: {buyer_role_id}, Role: {buyer_role}")

        # Check if the role exists
        if buyer_role is None:
            try:
                await interaction.response.send_message(content=f"Error: Role with ID {buyer_role_id} not found. Please set up a proper role using /serverconfig command first.", ephemeral=True)
            except discord.errors.InteractionResponded:
                await interaction.followup.send(content=f"Error: Role with ID {buyer_role_id} not found. Please set up a proper role using /serverconfig command first.", ephemeral=True)
            return

        paper_role_name = 'Paper Access'  # Change this to the name of the role you want to give
        paper_role = discord.utils.get(interaction.guild.roles, name=paper_role_name)

        emu_role_name = 'Emu Access'  # Change this to the name of the role you want to give
        emu_role = discord.utils.get(interaction.guild.roles, name=emu_role_name)



        if value == '1mstandard':

            expiry_days, key_prefix = role_mapping[value]

            # Get server-specific channel IDs from database
            conn_config = sqlite3.connect('data.db')
            cursor_config = conn_config.cursor()
            cursor_config.execute("SELECT tutorial_channel, review_channel FROM server_configs WHERE guild_id = ?", 
                                 (str(interaction.guild.id),))
            channel_config = cursor_config.fetchone()
            conn_config.close()

            # Set default channel messages
            tutorial_channel_msg = "<#1339520924596043878>"  # Default fallback
            review_channel_msg = "<#1339306483816337510>"    # Default fallback

            # Override with server-specific channels if available
            if channel_config and channel_config[0]:  # Tutorial channel
                tutorial_channel_msg = f"<#{channel_config[0]}>"
            if channel_config and channel_config[1]:  # Review channel
                review_channel_msg = f"<#{channel_config[1]}>"

            embed = discord.Embed(title="Thanks for choosing us!", description=f"Successfully added `1 Month` access to {user.mention} subscription.")
            embed.add_field(name="", value=f"**»** Go to {tutorial_channel_msg} and read the setup guide.\n**»** Please make a vouch in this format `+rep <10/10> <experience>` \n{review_channel_msg}")
            embed.set_footer(text="Email can be changed once a week!.", icon_url="https://cdn.discordapp.com/emojis/1278802261748879390.webp?size=96&quality=lossless")

            try:
                await user.add_roles(buyer_role)
            except discord.errors.Forbidden:
                embed.description = f"Added access to database for {user.mention}, but couldn't add role due to missing permissions. Please add the role manually."
                embed.color = discord.Color.orange()

            expiry_days, key_prefix = role_mapping[value]
            expiry_date = datetime.now() + timedelta(days=expiry_days)
            expiry_str = expiry_date.strftime('%d/%m/%Y %H:%M:%S')

            # Ensure database connection is open
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO licenses (owner_id, key, expiry, emailtf, credentialstf)
            VALUES (?, ?, ?, 'False', 'False')
            ON CONFLICT(owner_id) DO UPDATE SET
            key=excluded.key, expiry=excluded.expiry
            ''', (str(user.id), f"{key_prefix}-{user.id}", expiry_str))

            conn.commit()
            conn.close()



            await interaction.followup.send(embed=embed)

        elif value == 'lftstandard':

            expiry_days, key_prefix = role_mapping[value]

            # Get server-specific channel IDs from database
            conn_config = sqlite3.connect('data.db')
            cursor_config = conn_config.cursor()
            cursor_config.execute("SELECT tutorial_channel, review_channel FROM server_configs WHERE guild_id = ?", 
                                 (str(interaction.guild.id),))
            channel_config = cursor_config.fetchone()
            conn_config.close()

            # Set default channel messages
            tutorial_channel_msg = "<#1339520924596043878>"  # Default fallback
            review_channel_msg = "<#1339306483816337510>"    # Default fallback

            # Override with server-specific channels if available
            if channel_config and channel_config[0]:  # Tutorial channel
                tutorial_channel_msg = f"<#{channel_config[0]}>"
            if channel_config and channel_config[1]:  # Review channel
                review_channel_msg = f"<#{channel_config[1]}>"

            embed = discord.Embed(title="Thanks for choosing us!", description=f"Successfully added `Lifetime` access to {user.mention} subscription.")
            embed.add_field(name="", value=f"**»** Go to {tutorial_channel_msg} and read the setup guide.\n**»** Please make a vouch in this format `+rep <10/10> <experience>` \n{review_channel_msg}")
            embed.set_footer(text="Email can be changed once a week!.", icon_url="https://cdn.discordapp.com/emojis/1278802261748879390.webp?size=96&quality=lossless")

            try:
                await user.add_roles(buyer_role)
            except discord.errors.Forbidden:
                embed.description = f"Added access to database for {user.mention}, but couldn't add role due to missing permissions. Please add the role manually."
                embed.color = discord.Color.orange()


            expiry_days, key_prefix = role_mapping[value]
            expiry_date = datetime.now() + timedelta(days=expiry_days)
            expiry_str = expiry_date.strftime('%d/%m/%Y %H:%M:%S')

            # Ensure database connection is open
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO licenses (owner_id, key, expiry, emailtf, credentialstf)
            VALUES (?, ?, ?, 'False', 'False')
            ON CONFLICT(owner_id) DO UPDATE SET
            key=excluded.key, expiry=excluded.expiry
            ''', (str(user.id), f"{key_prefix}-{user.id}", expiry_str))

            conn.commit()
            conn.close()


            await interaction.followup.send(embed=embed)
        elif value == '14dstandard':
            expiry_days, key_prefix = role_mapping[value]
            expiry_date = datetime.now() + timedelta(days=expiry_days)
            expiry_str = expiry_date.strftime('%d/%m/%Y %H:%M:%S')
            # Ensure database connection is open
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO licenses (owner_id, key, expiry, emailtf, credentialstf)
            VALUES (?, ?, ?, 'False', 'False')
            ON CONFLICT(owner_id) DO UPDATE SET
            key=excluded.key, expiry=excluded.expiry
            ''', (str(user.id), f"{key_prefix}-{user.id}", expiry_str))

            conn.commit()
            conn.close()
            # Get server-specific channel IDs from database
            conn_config = sqlite3.connect('data.db')
            cursor_config = conn_config.cursor()
            cursor_config.execute("SELECT tutorial_channel, review_channel FROM server_configs WHERE guild_id = ?", 
                                 (str(interaction.guild.id),))
            channel_config = cursor_config.fetchone()
            conn_config.close()

            # Set default channel messages
            tutorial_channel_msg = "<#1339520924596043878>"  # Default fallback
            review_channel_msg = "<#1339306483816337510>"    # Default fallback

            # Override with server-specific channels if available
            if channel_config and channel_config[0]:  # Tutorial channel
                tutorial_channel_msg = f"<#{channel_config[0]}>"
            if channel_config and channel_config[1]:  # Review channel
                review_channel_msg = f"<#{channel_config[1]}>"

            embed = discord.Embed(title="Thanks for choosing us!", description=f"Successfully added `14 Days` access to {user.mention} subscription.")
            embed.add_field(name="", value=f"**»** Go to {tutorial_channel_msg} and read the setup guide.\n**»** Please make a vouch in this format `+rep <10/10> <experience>` \n{review_channel_msg}")
            embed.set_footer(text="Email can be changed once a week!.", icon_url="https://cdn.discordapp.com/emojis/1278802261748879390.webp?size=96&quality=lossless")
            try:
                await user.add_roles(buyer_role)
            except discord.errors.Forbidden:
                embed.description = f"Added access to database for {user.mention}, but couldn't add role due to missing permissions. Please add the role manually."
                embed.color = discord.Color.orange()
            await interaction.followup.send(embed=embed)
        elif value == '1dstandard':
            expiry_days, key_prefix = role_mapping[value]
            expiry_date = datetime.now() + timedelta(days=expiry_days)
            expiry_str = expiry_date.strftime('%d/%m/%Y %H:%M:%S')
            # Ensure database connection is open
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            cursor.execute('''
            INSERT INTO licenses (owner_id, key, expiry, emailtf, credentialstf)
            VALUES (?, ?, ?, 'False', 'False')
            ON CONFLICT(owner_id) DO UPDATE SET
            key=excluded.key, expiry=excluded.expiry
            ''', (str(user.id), f"{key_prefix}-{user.id}", expiry_str))

            conn.commit()
            conn.close()
            # Get server-specific channel IDs from database
            conn_config = sqlite3.connect('data.db')
            cursor_config = conn_config.cursor()
            cursor_config.execute("SELECT tutorial_channel, review_channel FROM server_configs WHERE guild_id = ?", 
                                 (str(interaction.guild.id),))
            channel_config = cursor_config.fetchone()
            conn_config.close()

            # Set default channel messages
            tutorial_channel_msg = "<#1339520924596043878>"  # Default fallback
            review_channel_msg = "<#1339306483816337510>"    # Default fallback

            # Override with server-specific channels if available
            if channel_config and channel_config[0]:  # Tutorial channel
                tutorial_channel_msg = f"<#{channel_config[0]}>"
            if channel_config and channel_config[1]:  # Review channel
                review_channel_msg = f"<#{channel_config[1]}>"

            embed = discord.Embed(title="Thanks for choosing us!", description=f"Successfully added `1 Day` access to {user.mention} subscription.")
            embed.add_field(name="", value=f"**»** Go to {tutorial_channel_msg} and read the setup guide.\n**»** Please make a vouch in this format `+rep <10/10> <experience>` \n{review_channel_msg}")
            embed.set_footer(text="Email can be changed once a week!.", icon_url="https://cdn.discordapp.com/emojis/1278802261748879390.webp?size=96&quality=lossless")
            try:
                await user.add_roles(buyer_role)
            except discord.errors.Forbidden:
                embed.description = f"Added access to database for {user.mention}, but couldn't add role due to missing permissions. Please add the role manually."
                embed.color = discord.Color.orange()
            await interaction.followup.send(embed=embed)









class PanelView(discord.ui.View):
    def __init__(self, owner_id, user, bot_owner_id=None):
        super().__init__(timeout=None)
        self.owner_id = owner_id  # ID of user who invoked the command
        self.user = user  # ID of user being edited
        self.bot_owner_id = bot_owner_id  # ID of the bot owner

    def is_owner_editing_self(self):
        # Check if a user is trying to edit themselves
        return str(self.owner_id) == str(self.user)

    @discord.ui.button(label="Information", emoji="<:informationn:1329647518874730527>")
    async def handle_checktime(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.owner_id:
            user = self.user
            guild = interaction.guild  # Getting the guild from the interaction
            user = guild.get_member(user)

            embed = discord.Embed(title="")
            user_found = False

            # Create a new connection for this operation
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()

            try:
                # SQL-Abfrage zur Überprüfung der Lizenzinformationen
                cursor.execute('''
                SELECT owner_id, key, expiry, email FROM licenses WHERE owner_id = ?
                ''', (str(user.id),))
                license_info = cursor.fetchone()

                if license_info:
                    owner_id, key, expiry_str, email = license_info
                    expiry_date = datetime.strptime(expiry_str, "%d/%m/%Y %H:%M:%S")
                    current_date = datetime.now()

                    remaining_days = (expiry_date - current_date).days

                    embed.add_field(name="", value=f"User: <@{owner_id}>\nExpiry: {expiry_str} ``{remaining_days} Days``\nEmail: `{email}`", inline=False)
                    user_found = True

                if not user_found:
                    embed.add_field(name="Error", value="User not found or does not exist.", inline=False)
            except Exception as e:
                embed.add_field(name="Error", value=f"Failed to retrieve user information: {str(e)}", inline=False)
            finally:
                conn.close()

            await interaction.response.send_message(embed=embed, ephemeral=True)

        else:
            await interaction.response.send_message(content="This is not your Panel", ephemeral=True)


    @discord.ui.button(label="Add Access", emoji="<:Tools:1329647517276700722>")
    async def handle_addaccess(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        # Check if user is the one who created the panel
        if interaction.user.id != self.owner_id:
            return await interaction.followup.send(
                "You did not create this interaction.", ephemeral=True
            )

        # Check if user is trying to edit themselves
        if self.is_owner_editing_self() and str(interaction.user.id) != self.bot_owner_id:
            # Prevent all users (including whitelisted ones) from editing themselves
            return await interaction.followup.send(
                "You cannot edit your own access. Please contact the bot owner for any changes to your own permissions.", 
                ephemeral=True
            )


        owner = self.owner_id
        user = self.user

        view = discord.ui.View()
        view.add_item(adminDrop(owner, user))  # Add the dropdown as an item
        await interaction.followup.send(content="", view=view, ephemeral=True)


    @discord.ui.button(label="Remove Access", emoji="<:Trash:1329647515963883671>")
    async def handle_removeaccess(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        # Check if user is the one who created the panel
        if interaction.user.id != self.owner_id:
            return await interaction.followup.send(
                "You did not create this interaction.", ephemeral=True
            )

        # Check if user is trying to edit themselves
        if self.is_owner_editing_self() and str(interaction.user.id) != self.bot_owner_id:
            # Prevent all users (including whitelisted ones) from editing themselves
            return await interaction.followup.send(
                "You cannot edit your own access. Please contact the bot owner for any changes to your own permissions.", 
                ephemeral=True
            )

        user = self.user
        guild = interaction.guild  # Getting the guild from the interaction
        user = guild.get_member(user)


        try:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM licenses WHERE owner_id = ?', (str(user.id),))
            conn.commit()
            conn.close()
        except sqlite3.OperationalError:
            import time
            time.sleep(1)
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM licenses WHERE owner_id = ?', (str(user.id),))
            conn.commit()
            conn.close()

        config = json.load(open("config.json", encoding="utf-8"))
        buyer_role_id = int(config.get("Client_ID"))
        buyer_role = discord.utils.get(interaction.guild.roles, id=buyer_role_id)

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT client_id FROM server_configs WHERE guild_id = ?", (str(interaction.guild.id),))
        server_role = cursor.fetchone()
        conn.close()

        if server_role and server_role[0]:
            buyer_role_id = int(server_role[0])
        else:
            buyer_role_id = int(config.get("Client_ID"))

        buyer_role = discord.utils.get(interaction.guild.roles, id=buyer_role_id)

        if buyer_role and buyer_role in user.roles:
            await user.remove_roles(buyer_role)

        roles_to_remove = []
        paper_role = discord.utils.get(interaction.guild.roles, name='Paper Access')
        if paper_role and paper_role in user.roles:
            roles_to_remove.append(paper_role)

        emu_role = discord.utils.get(interaction.guild.roles, name='Emu Access')
        if emu_role and emu_role in user.roles:
            roles_to_remove.append(emu_role)

        if roles_to_remove:
            await user.remove_roles(*roles_to_remove)

        await interaction.followup.send(embed=discord.Embed(
            title="Removed access from user",
            description=f"The access for {user.mention} has been removed successfully.",
            color=discord.Color.green()
        ), ephemeral=True)



    @discord.ui.button(label="Remove Email", emoji="<:Trash:1329647515963883671>")
    async def handle_removeemail(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        # Check if user is the one who created the panel
        if interaction.user.id != self.owner_id:
            return await interaction.followup.send(
                "You did not create this interaction.", ephemeral=True
            )

        # Check if user is trying to edit themselves
        if self.is_owner_editing_self() and str(interaction.user.id) != self.bot_owner_id:
            # Prevent all users (including whitelisted ones) from editing themselves
            return await interaction.followup.send(
                "You cannot edit your own access. Please contact the bot owner for any changes to your own permissions.", 
                ephemeral=True
            )

        user = self.user
        guild = interaction.guild  # Getting the guild from the interaction
        user = guild.get_member(user)

        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''
        UPDATE licenses
        SET email = NULL, last_email_update = NULL, emailtf = 'False'
        WHERE owner_id = ?
        ''', (str(user.id),))
        conn.commit()
        conn.close()

        await interaction.followup.send(embed=discord.Embed(
            title="Removed email from user",
            description=f"The email for {user.mention} has been removed successfully.",
            color=discord.Color.green()
        ), ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True #Always allow access