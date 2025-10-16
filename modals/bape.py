import re
import discord
from discord import ui



import requests  # gen random guid









from bs4 import BeautifulSoup

from pystyle import Colors


r = Colors.red
lg = Colors.light_gray





def is_bape_link(link):
    bape_pattern = re.compile(r'^https?://(www\.)?eu.bape\.com/.+')

    return bool(bape_pattern.match(link))


class bapemodal(ui.Modal, title="discord.gg/goatreceipts"):
    Linkff = discord.ui.TextInput(label="Link", placeholder="eu.bape.com link", required=True)
    Priceff = discord.ui.TextInput(label="Price without currency", placeholder="790", required=True)
    delivery = discord.ui.TextInput(label="Shipping Costs without currency", placeholder="7.99", required=True)
    currencyff = discord.ui.TextInput(label="Currency ($, €, £)", placeholder="€", required=True, min_length=1, max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        global Linkff , Priceff, currencyff, name, delivery, street, city, zipp ,country
        from addons.nextsteps import Nextstepbape
        owner_id = interaction.user.id 

        from utils.db_utils import get_user_details
        user_details = get_user_details(owner_id)

        if user_details:
            name, street, city, zipp, country, email = user_details

            Linkff = self.Linkff.value
            currencyff = self.currencyff.value
            Priceff = self.Priceff.value
            delivery = self.delivery.value


            if not is_bape_link(Linkff):
                embed = discord.Embed(title="Error - Invalid Bape link", description="Please provide a valid Bape link.")
                await interaction.response.send_message(embed=embed, ephemeral=False)
                return


            embed = discord.Embed(title="You are almost done...", description="Complete the next modal to receive the receip.")
            await interaction.response.send_message(content=f"{interaction.user.mention}",embed=embed, view=Nextstepbape(owner_id), ephemeral=False)

        else:
            # Handle case where no user details are found
            embed = discord.Embed(title="Error", description="No user details found. Please ensure your information is set up.")
            await interaction.response.send_message(embed=embed, ephemeral=True)






class bapemodal2(ui.Modal, title="Bape Receipt"):
    colour = discord.ui.TextInput(label="Color", placeholder="BLACK", required=True)
    Size = discord.ui.TextInput(label="Size", placeholder="XL", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        global Linkff , Priceff, currencyff, name, delivery
        owner_id = interaction.user.id 

        try:
            embed = discord.Embed(title="Under Process...", description="Processing your email will be sent soon!", color=discord.Color.from_str("#826bc2"))
            await interaction.response.edit_message(content=f"{interaction.user.mention}",embed=embed, view=None)



            with open("receipt/bape.html", "r", encoding="utf-8") as file:
                html_content = file.read()



            url = Linkff

            response = requests.get(
                url=url,
                proxies={
                    "http": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                    "https": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
                },
                verify=False 
            )



            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                print()
                print(f"[{Colors.green}START Scraping{lg}] BAPE -> {interaction.user.id} ({interaction.user})" + lg)


                product_name = None
                product_name_meta = soup.find('meta', {'property': 'og:title'})
                if product_name_meta and 'content' in product_name_meta.attrs:
                    product_name = product_name_meta['content']
                    print(f"    [{Colors.cyan}Scraping{lg}] Product Name: {product_name}" + lg)


                image_url = soup.find('meta', {'property': 'og:image'})['content']
                print(f"    [{Colors.cyan}Scraping{lg}] Image URL: {image_url}" + lg)


                print(f"[{Colors.green}Scraping DONE{lg}] BAPE -> {interaction.user.id}" + lg)
                print()


            if currencyff == "€":
                currencyalp = "EUR"

            if currencyff == "$":
                currencyalp = "USD"

            if currencyff == "£":
                currencyalp = "GBP"

            cityzip = f"{city} {zipp}"
            size = self.Size.value
            colour = self.colour.value

            tax = 19.60 


            Priceff = float(Priceff)
            delivery = float(delivery)

            total = Priceff + delivery + tax


            total = round(total, 2)


            html_content = html_content.replace("{name}", name)
            html_content = html_content.replace("{street}", street)
            html_content = html_content.replace("{cityzip}", cityzip)
            html_content = html_content.replace("{country}", country)
            html_content = html_content.replace("{shipping}", str(delivery))

            html_content = html_content.replace("{price}", str(Priceff)) 
            html_content = html_content.replace("{currencyinalph}", currencyalp)

            html_content = html_content.replace("{imgsrc}", str(image_url))
            html_content = html_content.replace("{productname}", product_name)
            html_content = html_content.replace("{color}", colour)
            html_content = html_content.replace("{size}", size)



            html_content = html_content.replace("{currency}", str(currencyff)) 
            html_content = html_content.replace("{totalprice}", str(total))


            with open("receipt/updatedrecipies/updatedbape.html", "w", encoding="utf-8") as file:
                file.write(html_content)

            sender_email = "BAPE <webstore@bape.com>"
            subject = "Order #LE146-87-39111 confirmed"
            from emails.choise import choiseView


            embed = discord.Embed(title="Choose email provider", description="Email is ready to send choose Spoofed or Normal domain.", color=discord.Color.from_str("#826bc2"))
            view = choiseView(owner_id, html_content, sender_email, subject, product_name, image_url, Linkff)
            await interaction.edit_original_response(embed=embed, view=view)

        except Exception as e:
            embed = discord.Embed(title="Error", description=f"An error occurred: {str(e)}")
            await interaction.edit_original_response(embed=embed)