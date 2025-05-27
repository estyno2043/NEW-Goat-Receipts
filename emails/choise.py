import discord
from emails.normal import SendNormal
from emails.spoofed import send_email_spoofed
import sqlite3

class choiseView(discord.ui.View):
    def __init__(self, owner_id, receipt_html, sender_email, subject, item_desc, image_url, link):
        super().__init__()
        self.owner_id = owner_id
        self.receipt_html = receipt_html
        self.sender_email = sender_email
        self.item_desc = item_desc
        self.subject = subject
        self.image_url = image_url
        self.link = link

    async def interaction_check(self, interaction):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your panel.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Spoofed Email", style=discord.ButtonStyle.blurple, custom_id="spoofed")
    async def spoofed_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)

        # Immediately show sending status
        sending_embed = discord.Embed(
            title="**Sending...**",
            description="Please wait while we process your email...",
            color=0x3498db
        )
        # Validate image URL before setting it as thumbnail
        if self.image_url and isinstance(self.image_url, str) and (self.image_url.startswith('http://') or self.image_url.startswith('https://')):
            try:
                sending_embed.set_thumbnail(url=self.image_url)
            except Exception as img_error:
                print(f"Error setting thumbnail: {str(img_error)}")
                # Continue without the thumbnail if there's an error

        await interaction.edit_original_response(embed=sending_embed, view=None)

        try:
            # Check rate limit before proceeding
            from utils.rate_limiter import ReceiptRateLimiter
            rate_limiter = ReceiptRateLimiter()

            is_allowed, count, reset_time, remaining_time = rate_limiter.check_rate_limit(self.owner_id)

            if not is_allowed:
                rate_limit_message = rate_limiter.get_rate_limit_message(self.owner_id)
                if rate_limit_message:
                    embed = discord.Embed(
                        title="Rate Limited",
                        description=rate_limit_message,
                        color=discord.Color.red()
                    )
                    await interaction.edit_original_response(embed=embed, view=None)
                    return

            # Get user email from database with enhanced error handling and debugging
            try:
                from utils.db_utils import get_user_details, save_user_email

                # Try the improved user details function first
                user_details = get_user_details(self.owner_id)

                # Debug print for troubleshooting
                print(f"User details for {self.owner_id}: {user_details}")

                user_email = None

                if user_details and len(user_details) >= 6:  # Ensure we have at least 6 elements including email
                    user_email = user_details[5]  # Email is the 6th element (index 5)
                    print(f"Found email from user_details: {user_email}")

                # If no email found or email is None, try all possible fallbacks
                if not user_email:
                    # Try user_emails table directly
                    conn = sqlite3.connect('data.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(self.owner_id),))
                    result = cursor.fetchone()

                    if result and result[0]:
                        user_email = result[0]
                        print(f"Found email from user_emails table: {user_email}")

                        # Save this email to the licenses table for future use
                        save_user_email(self.owner_id, user_email)

                    conn.close()

                if not user_email:
                    # Additional check in case email is stored in a different table
                    conn = sqlite3.connect('data.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    print(f"Available tables: {[table[1] for table in tables]}")

                    # Try to find any table with 'email' in the name or columns
                    for table in tables:
                        table_name = table[1]
                        if 'user' in table_name.lower() or 'email' in table_name.lower():
                            print(f"Checking table: {table_name}")
                            try:
                                cursor.execute(f"PRAGMA table_info({table_name})")
                                columns = cursor.fetchall()
                                print(f"Columns in {table_name}: {[col[1] for col in columns]}")

                                # Check if this table has user_id and email columns
                                if any('user' in col[1].lower() for col in columns) and any('email' in col[1].lower() for col in columns):
                                    try:
                                        user_col = next(col[1] for col in columns if 'user' in col[1].lower())
                                        email_col = next(col[1] for col in columns if 'email' in col[1].lower())
                                        cursor.execute(f"SELECT {email_col} FROM {table_name} WHERE {user_col} = ?", (str(self.owner_id),))
                                        email_result = cursor.fetchone()
                                        if email_result:
                                            user_email = email_result[0]
                                            print(f"Found email in table {table_name}: {user_email}")
                                            break
                                    except Exception as table_e:
                                        print(f"Error querying {table_name}: {str(table_e)}")
                            except Exception as col_e:
                                print(f"Error getting columns for {table_name}: {str(col_e)}")

                    conn.close()

                    if not 'user_email' in locals() or not user_email:
                        user_email = None
                        print(f"No email found for user ID: {self.owner_id}")
            except Exception as e:
                print(f"Error getting user details: {str(e)}")

                # Fallback method
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(self.owner_id),))
                result = cursor.fetchone()
                conn.close()

                if result:
                    user_email = result[0]
                    print(f"Found email from fallback method: {user_email}")
                else:
                    user_email = None
                    print(f"No email found from fallback method for user ID: {self.owner_id}")

            if user_email:
                # Send spoofed email
                await send_email_spoofed(user_email, self.receipt_html, self.sender_email, self.subject, self.link)

                # Update original message with success embed
                embed = discord.Embed(
                    title="Email Sent", 
                    description=f"{interaction.user.mention}, kindly check your Inbox/Spam folder\n-# » {self.item_desc}", 
                    color=0x2ecc71
                )
                if self.image_url and isinstance(self.image_url, str) and (self.image_url.startswith('http://') or self.image_url.startswith('https://')):
                    try:
                        embed.set_thumbnail(url=self.image_url)
                    except Exception as img_error:
                        print(f"Error setting success thumbnail: {str(img_error)}")
                        # Continue without the thumbnail if there's an error

                await interaction.edit_original_response(embed=embed, view=None)

                # Send additional plain text warning message for spoofed emails (non-ephemeral)
                warning_message = "Important: **Spoofed emails often go to spam folders**. Please check your Spam/Junk folder. If you still don't see the email, please try the **Normal Email** option instead.\n\nSome email providers (like Gmail, Outlook, Yahoo) have very strict spam filters that might block spoofed emails completely."
                await interaction.followup.send(warning_message, ephemeral=True)

                # Add receipt after successful email sending
                rate_limiter.add_receipt(self.owner_id)
            else:
                await interaction.followup.send(embed=discord.Embed(title="Error", description="No email found for your account. Please set up your email.", color=0xe74c3c), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(title="Error", description=f"An error occurred: {str(e)}", color=0xe74c3c), ephemeral=True)

    @discord.ui.button(label="Normal Email", style=discord.ButtonStyle.gray, custom_id="normal")
    async def normal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your button.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=False)

        # Immediately show sending status
        sending_embed = discord.Embed(
            title="**Sending...**",
            description="Please wait while we process your email...",
            color=0x3498db
        )
        # Validate image URL before setting it as thumbnail
        if self.image_url and isinstance(self.image_url, str) and (self.image_url.startswith('http://') or self.image_url.startswith('https://')):
            try:
                sending_embed.set_thumbnail(url=self.image_url)
            except Exception as img_error:
                print(f"Error setting thumbnail: {str(img_error)}")
                # Continue without the thumbnail if there's an error

        await interaction.edit_original_response(embed=sending_embed, view=None)

        try:
            # Check rate limit before proceeding
            from utils.rate_limiter import ReceiptRateLimiter
            rate_limiter = ReceiptRateLimiter()

            is_allowed, count, reset_time, remaining_time = rate_limiter.check_rate_limit(self.owner_id)

            if not is_allowed:
                rate_limit_message = rate_limiter.get_rate_limit_message(self.owner_id)
                if rate_limit_message:
                    embed = discord.Embed(
                        title="Rate Limited",
                        description=rate_limit_message,
                        color=discord.Color.red()
                    )
                    await interaction.edit_original_response(embed=embed, view=None)
                    return

            # Get user email from database with enhanced error handling and debugging
            try:
                from utils.db_utils import get_user_details, save_user_email

                # Try the improved user details function first
                user_details = get_user_details(self.owner_id)

                # Debug print for troubleshooting
                print(f"User details for {self.owner_id}: {user_details}")

                user_email = None

                if user_details and len(user_details) >= 6:  # Ensure we have at least 6 elements including email
                    user_email = user_details[5]  # Email is the 6th element (index 5)
                    print(f"Found email from user_details: {user_email}")

                # If no email found or email is None, try all possible fallbacks
                if not user_email:
                    # Try user_emails table directly
                    conn = sqlite3.connect('data.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(self.owner_id),))
                    result = cursor.fetchone()

                    if result and result[0]:
                        user_email = result[0]
                        print(f"Found email from user_emails table: {user_email}")

                        # Save this email to the licenses table for future use
                        save_user_email(self.owner_id, user_email)

                    conn.close()

                if not user_email:
                    # Additional check in case email is stored in a different table
                    conn = sqlite3.connect('data.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    print(f"Available tables: {[table[1] for table in tables]}")

                    # Try to find any table with 'email' in the name or columns
                    for table in tables:
                        table_name = table[1]
                        if 'user' in table_name.lower() or 'email' in table_name.lower():
                            print(f"Checking table: {table_name}")
                            try:
                                cursor.execute(f"PRAGMA table_info({table_name})")
                                columns = cursor.fetchall()
                                print(f"Columns in {table_name}: {[col[1] for col in columns]}")

                                # Check if this table has user_id and email columns
                                if any('user' in col[1].lower() for col in columns) and any('email' in col[1].lower() for col in columns):
                                    try:
                                        user_col = next(col[1] for col in columns if 'user' in col[1].lower())
                                        email_col = next(col[1] for col in columns if 'email' in col[1].lower())
                                        cursor.execute(f"SELECT {email_col} FROM {table_name} WHERE {user_col} = ?", (str(self.owner_id),))
                                        email_result = cursor.fetchone()
                                        if email_result:
                                            user_email = email_result[0]
                                            print(f"Found email in table {table_name}: {user_email}")
                                            break
                                    except Exception as table_e:
                                        print(f"Error querying {table_name}: {str(table_e)}")
                            except Exception as col_e:
                                print(f"Error getting columns for {table_name}: {str(col_e)}")

                    conn.close()

                    if not 'user_email' in locals() or not user_email:
                        user_email = None
                        print(f"No email found for user ID: {self.owner_id}")
            except Exception as e:
                print(f"Error getting user details: {str(e)}")

                # Fallback method
                conn = sqlite3.connect('data.db')
                cursor = conn.cursor()
                cursor.execute("SELECT email FROM user_emails WHERE user_id = ?", (str(self.owner_id),))
                result = cursor.fetchone()
                conn.close()

                if result:
                    user_email = result[0]
                    print(f"Found email from fallback method: {user_email}")
                else:
                    user_email = None
                    print(f"No email found from fallback method for user ID: {self.owner_id}")

            if user_email:
                # Send normal email
                await SendNormal.send_email(user_email, self.receipt_html, self.sender_email, self.subject)

                # Update original message with success embed
                embed = discord.Embed(
                    title="Email Sent", 
                    description=f"{interaction.user.mention}, kindly check your Inbox/Spam folder\n-# » {self.item_desc}", 
                    color=0x2ecc71
                )
                if self.image_url and isinstance(self.image_url, str) and (self.image_url.startswith('http://') or self.image_url.startswith('https://')):
                    try:
                        embed.set_thumbnail(url=self.image_url)
                    except Exception as img_error:
                        print(f"Error setting success thumbnail: {str(img_error)}")
                        # Continue without the thumbnail if there's an error

                await interaction.edit_original_response(embed=embed, view=None)
                
                # Add receipt after successful email sending
                rate_limiter.add_receipt(self.owner_id)
            else:
                await interaction.followup.send(embed=discord.Embed(title="Error", description="No email found for your account. Please set up your email.", color=0xe74c3c), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(embed=discord.Embed(title="Error", description=f"An error occurred: {str(e)}", color=0xe74c3c), ephemeral=True)