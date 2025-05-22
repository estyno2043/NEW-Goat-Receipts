import discord
from discord import ui
import sqlite3
import random
from datetime import datetime
import re

class HermesModal(ui.Modal, title="Hermes Order"):
    product_name = ui.TextInput(label="Product Name", placeholder="Izmir sandal", required=True)
    product_price = ui.TextInput(label="Price without currency", placeholder="790.00", required=True)
    currency = ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=1)
    color = ui.TextInput(label="Color", placeholder="Black", required=True)
    size = ui.TextInput(label="Size", placeholder="41", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner_id = interaction.user.id 

        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, street, city, zipp, country FROM licenses WHERE owner_id = ?", (str(owner_id),))
        user_details = cursor.fetchone()
        conn.close()

        if user_details:
            name, street, city, zipp, country = user_details

            # Store form data in a global dictionary
            if 'hermes_form_data' not in globals():
                global hermes_form_data
                hermes_form_data = {}

            hermes_form_data[str(owner_id)] = {
                'product_name': self.product_name.value,
                'product_price': self.product_price.value,
                'currency': self.currency.value,
                'color': self.color.value,
                'size': self.size.value,
                'name': name,
                'street': street,
                'city': city,
                'zipp': zipp,
                'country': country
            }

            # Create a "Next Page" button view
            view = HermesNextButton(owner_id)

            # Send message with button to continue
            await interaction.response.send_message(
                "Click 'Next Page' to continue to the next set of inputs.",
                view=view,
                ephemeral=True
            )
        else:
            embed = discord.Embed(title="Error", description="User details not found. Please set up your credentials in settings.")
            await interaction.response.send_message(embed=embed, ephemeral=True)

class HermesNextButton(discord.ui.View):
    def __init__(self, owner_id):
        super().__init__(timeout=300)  # 5 minute timeout
        self.owner_id = owner_id

    @discord.ui.button(label="Next Page", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your form.", ephemeral=True)
            return

        # Send second modal
        modal = HermesSecondModal(interaction.user.id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("This is not your form.", ephemeral=True)
            return

        await interaction.response.edit_message(content="Form cancelled.", view=None)

class HermesSecondModal(ui.Modal, title="Hermes Order - Step 2"):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = str(user_id)

        self.add_item(ui.TextInput(label="Image URL", placeholder="https://example.com/image.jpg", required=True))
        self.add_item(ui.TextInput(label="Reference Number", placeholder="H0418S", required=True))
        self.add_item(ui.TextInput(label="Order Date (MM/DD/YYYY)", placeholder="04/06/2025", required=True))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Retrieve data from first form
            if 'hermes_form_data' not in globals() or self.user_id not in hermes_form_data:
                await interaction.response.send_message("Error: Your session has expired. Please start over.", ephemeral=True)
                return

            data = hermes_form_data[self.user_id]

            # Get values from second form
            image_url = self.children[0].value
            ref = self.children[1].value
            order_date = self.children[2].value

            # Format city and zip together
            cityzip = f"{data['city']} {data['zipp']}"

            # Generate a random receipt
            with open('receipt/hermes.html', 'r', encoding='utf-8') as f:
                html_content = f.read()

            # Replace placeholders with actual values
            html_content = html_content.replace('{name}', data['name'])
            html_content = html_content.replace('{street}', data['street'])
            html_content = html_content.replace('{city}', data['city'])
            html_content = html_content.replace('{zipp}', data['zipp'])
            html_content = html_content.replace('{cityzip}', cityzip)
            html_content = html_content.replace('{country}', data['country'])
            html_content = html_content.replace('{product_name}', data['product_name'])
            html_content = html_content.replace('{imageurl}', image_url)
            html_content = html_content.replace('{color}', data['color'])
            html_content = html_content.replace('{size}', data['size'])
            html_content = html_content.replace('{currency}', data['currency'])
            html_content = html_content.replace('{price}', data['product_price'])
            html_content = html_content.replace('{ref}', ref)
            html_content = html_content.replace('{orderdate}', order_date)
            html_content = html_content.replace('{productprice}', data['product_price'])

            # Save the modified HTML to a file
            file_name = f"hermes_receipt_{interaction.user.id}.html"
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Send the file to the user
            with open(file_name, 'rb') as f:
                file = discord.File(f, filename=file_name)
                await interaction.response.send_message(file=file, ephemeral=True) #Added ephemeral here

            # Set up email sending options
            try:
                from emails.choise import choiseView

                # Use the specified email for Hermes
                sender_email = "Hermes <hermes@noreply.org>"
                subject = "Your Hermes Purchase Confirmation"
                link = "https://www.hermes.com"

                # Create embed for email provider choice
                embed = discord.Embed(title="Choose email provider", description="Email is ready to send. Choose Spoofed or Normal domain.", color=0x1e1f22)
                view = choiseView(interaction.user.id, html_content, sender_email, subject, data['product_name'], image_url, link)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True) #Added ephemeral here

            except Exception as e:
                await interaction.followup.send(f"Failed to prepare email options: {str(e)}", ephemeral=True)

            # Clean up temporary data
            if self.user_id in hermes_form_data:
                del hermes_form_data[self.user_id]

        except Exception as e:
            # Use followup instead of response if there's an error after the initial response
            try:
                await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
            except:
                pass  # If we can't send the error, just suppress it to avoid error messages in console

# Initialize global dictionary to store form data between steps
hermes_form_data = {}