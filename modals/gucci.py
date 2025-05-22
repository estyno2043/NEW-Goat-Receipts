import discord
import random
from discord import ui
from discord.ui import TextInput

class guccimodal1(discord.ui.Modal, title="Gucci Receipt Generator (1/2)"):
    def __init__(self):
        super().__init__()
        self.productname = TextInput(
            label="Product Name",
            placeholder="Gucci Flora Gorgeous Orchid, 50ml, eau de parfum",
            required=True
        )
        self.productimage = TextInput(
            label="Product Image URL",
            placeholder="Image URL of the product",
            required=True
        )
        self.productsku = TextInput(
            label="Product SKU",
            placeholder="792064999990099",
            required=True
        )
        self.productsize = TextInput(
            label="Product Size",
            placeholder="50ml",
            required=True
        )
        self.productprice = TextInput(
            label="Product Price",
            placeholder="Price without currency symbol (e.g. 120)",
            required=True
        )

        self.add_item(self.productname)
        self.add_item(self.productimage)
        self.add_item(self.productsku)
        self.add_item(self.productsize)
        self.add_item(self.productprice)

    async def on_submit(self, interaction: discord.Interaction):
        from addons.nextsteps import NextstepGucci
        await interaction.response.send_message(content=f"Processing your Gucci receipt...", ephemeral=True)
        view = NextstepGucci(interaction.user.id)

        # Store values for the next step
        view.productname = self.productname.value
        view.productimage = self.productimage.value
        view.productsku = self.productsku.value
        view.productsize = self.productsize.value
        view.productprice = self.productprice.value

        await interaction.followup.send(view=view, ephemeral=True)

class guccimodal2(discord.ui.Modal, title="Gucci Receipt Generator (2/2)"):
    def __init__(self):
        super().__init__()
        self.productcurrency = TextInput(
            label="Currency Symbol",
            placeholder="€, £, $, etc.",
            required=True
        )
        self.productcolor = TextInput(
            label="Product Color",
            placeholder="Black, Red, etc.",
            required=True
        )

        self.add_item(self.productcurrency)
        self.add_item(self.productcolor)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(content="Generating your Gucci receipt...", ephemeral=True)

        # Retrieve user data
        member = interaction.user
        if hasattr(member, 'global_name') and member.global_name:
            name = member.global_name
        else:
            name = member.name

        # Get values from the previous form stored in nextsteps.py
        from addons.nextsteps import store
        user_id = interaction.user.id
        if user_id in store:
            productname = store[user_id].get('productname', 'Gucci Flora Gorgeous Orchid, 50ml, eau de parfum')
            productimage = store[user_id].get('productimage', '')
            productsku = store[user_id].get('productsku', '792064999990099')
            productsize = store[user_id].get('productsize', '50ml')
            productprice = store[user_id].get('productprice', '120')
        else:
            await interaction.followup.send("Session expired. Please start again.", ephemeral=True)
            return

        # Get shipping details from database
        import sqlite3
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, street, city, zipp, country, email FROM licenses WHERE owner_id = ?", (str(interaction.user.id),))
        user_details = cursor.fetchone()

        if user_details:
            name, street, city, zipp, country, email = user_details
        else:
            # Fallback to default values if no user details found
            street = "123 Example Street"
            city = "London"
            zipp = "SW1A 1AA"
            country = "United Kingdom"

        try:
            # Open and read the HTML template
            with open("receipt/gucci.html", "r", encoding="utf-8") as file:
                html_content = file.read()

            # Replace all placeholders in the HTML template
            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{city}", city)
            html_content = html_content.replace("{zipp}", zipp)
            html_content = html_content.replace("{zip}", zipp)  # Add this for compatibility
            html_content = html_content.replace("{country}", country)
            html_content = html_content.replace("{productname}", productname)
            html_content = html_content.replace("{productimage}", productimage)
            html_content = html_content.replace("{productsku}", productsku)
            html_content = html_content.replace("{productsize}", productsize)
            html_content = html_content.replace("{productprice}", f"{self.productcurrency.value}{productprice}")
            html_content = html_content.replace("{productcurrency}", self.productcurrency.value)
            html_content = html_content.replace("{productcolor}", self.productcolor.value)

            # Save the updated HTML
            with open("receipt/updatedrecipies/updatedgucci.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            # Set up email information
            sender_email = "Gucci <client.service@gucci.com>"
            subject = "Gucci - Order confirmation - UK89720960"

            # Send the generated receipt
            from emails.choise import choiseView
            owner_id = interaction.user.id
            link = "https://gucci.com"

            embed = discord.Embed(title="Choose email provider", description="Email is ready to send. Choose Spoofed or Normal domain.", color=0x1e1f22)
            view = choiseView(owner_id, html_content, sender_email, subject, productname, productimage, link)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.followup.send(embed=embed, ephemeral=True)