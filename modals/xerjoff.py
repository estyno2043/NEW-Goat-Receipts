import discord
from discord import ui
import asyncio
from datetime import datetime
import random
import string

class XerjoffStatusView(ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @ui.select(
        placeholder="Choose receipt type...",
        options=[
            discord.SelectOption(label="Order Confirmation", value="ordered", description=""),
            discord.SelectOption(label="Payment Confirmation", value="payment", description="")
        ]
    )
    async def status_select(self, interaction: discord.Interaction, select: ui.Select):
        if select.values[0] == "payment":
            await interaction.response.send_modal(XerjoffPaymentModal())
        elif select.values[0] == "ordered":
            await interaction.response.send_modal(XerjoffOrderModal())

class XerjoffPaymentModal(ui.Modal, title="Xerjoff Payment Confirmation"):
    referencenum = ui.TextInput(label="Reference Number", placeholder="VTLBMDOZI", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        from utils.db_utils import get_user_details
        user_details = get_user_details(interaction.user.id)

        if not user_details:
            await interaction.response.send_message("Please set up your credentials in settings first.", ephemeral=True)
            return

        name, street, city, zipp, country, email = user_details

        # Read the payment template
        try:
            with open('receipt/xerjoffpayment.html', 'r', encoding='utf-8') as file:
                receipt_html = file.read()

            # Replace placeholders
            receipt_html = receipt_html.replace('{name}', name)
            receipt_html = receipt_html.replace('{referencenum}', self.referencenum.value)

            # Generate receipt filename
            receipt_filename = f"xerjoff_payment_{self.referencenum.value}.html"

            # Create embed for email choice
            embed = discord.Embed(
                title="Xerjoff Payment Receipt Generated",
                description=f"Receipt for reference number: **{self.referencenum.value}**\n\nChoose email delivery method:",
                color=discord.Color.from_str("#c2ccf8")
            )

            from emails.choise import EmailChoiceView
            view = EmailChoiceView(interaction.user.id, receipt_html, receipt_filename, "customer@xerjoff.com", "Xerjoff Customer Service", f"Payment Confirmation - {self.referencenum.value}")

            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except FileNotFoundError:
            await interaction.response.send_message("Xerjoff payment template not found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error generating receipt: {str(e)}", ephemeral=True)

class XerjoffOrderModal(ui.Modal, title="Xerjoff Order - Step 1/2"):
    productname = ui.TextInput(label="Product Name", placeholder="ERBA PURA DEODORANT SPRAY", required=True)
    price = ui.TextInput(label="Price (without currency)", placeholder="39.00", required=True)
    currency = ui.TextInput(label="Currency", placeholder="€", required=True, max_length=3)
    shipping = ui.TextInput(label="Shipping Cost", placeholder="14.00", required=True)
    tax = ui.TextInput(label="Tax Amount", placeholder="7.03", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        # Store form data globally for the second modal
        if 'xerjoff_form_data' not in globals():
            global xerjoff_form_data
            xerjoff_form_data = {}

        xerjoff_form_data[str(interaction.user.id)] = {
            'productname': self.productname.value,
            'price': self.price.value,
            'currency': self.currency.value,
            'shipping': self.shipping.value,
            'tax': self.tax.value
        }

        embed = discord.Embed(
            title="You are almost done...",
            description="Complete the next modal to receive the receipt.",
            color=discord.Color.from_str("#c2ccf8")
        )

        view = ui.View()
        continue_button = ui.Button(label="Continue to Step 2", style=discord.ButtonStyle.green)

        async def continue_callback(button_interaction):
            if button_interaction.user.id != interaction.user.id:
                await button_interaction.response.send_message("You can't use this button.", ephemeral=True)
                return
            await button_interaction.response.send_modal(XerjoffOrderSecondModal())

        continue_button.callback = continue_callback
        view.add_item(continue_button)

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class XerjoffOrderSecondModal(ui.Modal, title="Xerjoff Order - Step 2/2"):
    referencenum = ui.TextInput(label="Reference Number", placeholder="VTLBMDOZI", required=True)
    taxcost = ui.TextInput(label="Tax Cost", placeholder="7.03", required=True)
    orderdate = ui.TextInput(label="Order Date", placeholder="05/31/2025 12:49:28", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        from utils.db_utils import get_user_details
        user_details = get_user_details(interaction.user.id)

        if not user_details:
            await interaction.response.send_message("Please set up your credentials in settings first.", ephemeral=True)
            return

        name, street, city, zipp, country, email = user_details

        # Get first modal data
        if 'xerjoff_form_data' not in globals() or str(interaction.user.id) not in xerjoff_form_data:
            await interaction.response.send_message("Session expired. Please start over.", ephemeral=True)
            return

        first_data = xerjoff_form_data[str(interaction.user.id)]

        try:
            # Calculate total
            product_price = float(first_data['price'])
            shipping_cost = float(first_data['shipping'])
            tax_amount = float(self.taxcost.value)
            total = product_price + shipping_cost + tax_amount

            # Read the order template
            with open('receipt/xerjofforder.html', 'r', encoding='utf-8') as file:
                receipt_html = file.read()

            # Replace all placeholders
            receipt_html = receipt_html.replace('{name}', name)
            receipt_html = receipt_html.replace('{referencenum}', self.referencenum.value)
            receipt_html = receipt_html.replace('{orderdate}', self.orderdate.value)
            receipt_html = receipt_html.replace('{productname}', first_data['productname'])
            receipt_html = receipt_html.replace('{productprice}', first_data['price'])
            receipt_html = receipt_html.replace('{currency}', first_data['currency'])
            receipt_html = receipt_html.replace('{shipping}', first_data['shipping'])
            receipt_html = receipt_html.replace('{taxcost}', self.taxcost.value)
            receipt_html = receipt_html.replace('{total}', f"{total:.2f}")
            receipt_html = receipt_html.replace('{address}', street)
            receipt_html = receipt_html.replace('{city}', city)
            receipt_html = receipt_html.replace('{zip}', zipp)
            receipt_html = receipt_html.replace('{country}', country)

            # Generate receipt filename
            receipt_filename = f"xerjoff_order_{self.referencenum.value}.html"

            # Create embed for email choice
            embed = discord.Embed(
                title="Xerjoff Order Receipt Generated",
                description=f"Order receipt for reference: **{self.referencenum.value}**\n\nChoose email delivery method:",
                color=discord.Color.from_str("#c2ccf8")
            )

            from emails.choise import EmailChoiceView
            view = EmailChoiceView(interaction.user.id, receipt_html, receipt_filename, "customer@xerjoff.com", "Xerjoff Customer Service", f"Order Confirmation - {self.referencenum.value}")

            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

            # Clean up stored data
            del xerjoff_form_data[str(interaction.user.id)]

        except FileNotFoundError:
            await interaction.response.send_message("Xerjoff order template not found.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter valid numeric values for prices.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error generating receipt: {str(e)}", ephemeral=True)

# Main modal class for compatibility
class xerjoffmodal(ui.Modal, title="Xerjoff Receipt Generator"):
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Xerjoff Receipt Generator",
            description="Choose the type of receipt you want to generate:",
            color=discord.Color.from_str("#c2ccf8")
        )
        await interaction.response.send_message(embed=embed, view=XerjoffStatusView(), ephemeral=True)