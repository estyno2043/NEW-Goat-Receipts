"""
Verify File Upload Commands
Lists all 80 brand file upload commands
"""

brands = [
    "6pm", "acnestudios", "adidas", "adwysd", "amazon", "amazonuk", "apple", "applepickup",
    "arcteryx", "argos", "balenciaga", "bape", "bijenkorf", "breuninger", "brokenplanet", 
    "burberry", "canadagoose", "cartier", "cernucci", "chanel", "chewforever", "chromehearts",
    "chrono", "coolblue", "corteiz", "crtz", "culturekings", "denimtears", "dior", "dyson",
    "ebayauth", "ebayconf", "end", "farfetch", "fightclub", "flannels", "futbolemotion",
    "gallerydept", "goat", "goyard", "grailed", "guapi", "gucci", "harrods", "hermes",
    "houseoffrasers", "istores", "jdsports", "jomashop", "kickgame", "legitapp", "loropiana",
    "lv", "maisonmargiela", "moncler", "nike", "nosauce", "offwhite", "pandora", "prada",
    "ralphlauren", "samsung", "sephora", "sneakerstorecz", "snkrs", "spider", "stockx",
    "stussy", "supreme", "synaworld", "tnf", "trapstar", "ugg", "vinted", "vw", "xerjoff",
    "zalandode", "zalandous", "zara", "zendesk"
]

brand_display_names = {
    "6pm": "6pm",
    "acnestudios": "Acne Studios",
    "adidas": "Adidas",
    "adwysd": "Adwysd",
    "amazon": "Amazon",
    "amazonuk": "Amazon UK",
    "apple": "Apple",
    "applepickup": "Apple Pickup",
    "arcteryx": "Arc'teryx",
    "argos": "Argos",
    "balenciaga": "Balenciaga",
    "bape": "BAPE",
    "bijenkorf": "Bijenkorf",
    "breuninger": "Breuninger",
    "brokenplanet": "Broken Planet",
    "burberry": "Burberry",
    "canadagoose": "Canada Goose",
    "cartier": "Cartier",
    "cernucci": "Cernucci",
    "chanel": "Chanel",
    "chewforever": "Chew Forever",
    "chromehearts": "Chrome Hearts",
    "chrono": "Chrono24",
    "coolblue": "Coolblue",
    "corteiz": "Corteiz",
    "crtz": "CRTZ",
    "culturekings": "Culture Kings",
    "denimtears": "Denim Tears",
    "dior": "Dior",
    "dyson": "Dyson",
    "ebayauth": "eBay Auth",
    "ebayconf": "eBay Conf",
    "end": "END.",
    "farfetch": "Farfetch",
    "fightclub": "Fight Club",
    "flannels": "Flannels",
    "futbolemotion": "Fútbol Emotion",
    "gallerydept": "Gallery Dept",
    "goat": "GOAT",
    "goyard": "Goyard",
    "grailed": "Grailed",
    "guapi": "Guapi",
    "gucci": "Gucci",
    "harrods": "Harrods",
    "hermes": "Hermès",
    "houseoffrasers": "House of Fraser",
    "istores": "iStores",
    "jdsports": "JD Sports",
    "jomashop": "Jomashop",
    "kickgame": "KickGame",
    "legitapp": "Legit App",
    "loropiana": "Loro Piana",
    "lv": "Louis Vuitton",
    "maisonmargiela": "Maison Margiela",
    "moncler": "Moncler",
    "nike": "Nike",
    "nosauce": "No Sauce",
    "offwhite": "Off-White",
    "pandora": "Pandora",
    "prada": "Prada",
    "ralphlauren": "Ralph Lauren",
    "samsung": "Samsung",
    "sephora": "Sephora",
    "sneakerstorecz": "Sneaker Store CZ",
    "snkrs": "SNKRS",
    "spider": "Spider",
    "stockx": "StockX",
    "stussy": "Stüssy",
    "supreme": "Supreme",
    "synaworld": "Syna World",
    "tnf": "The North Face",
    "trapstar": "Trapstar",
    "ugg": "UGG",
    "vinted": "Vinted",
    "vw": "VW",
    "xerjoff": "Xerjoff",
    "zalandode": "Zalando DE",
    "zalandous": "Zalando US",
    "zara": "Zara",
    "zendesk": "Zendesk"
}

print("=" * 80)
print("FILE UPLOAD COMMANDS FOR GOAT RECEIPTS")
print("=" * 80)
print()
print(f"Total Commands: {len(brands)}")
print()
print("Command List:")
print("-" * 80)

for i, brand in enumerate(brands, 1):
    display_name = brand_display_names.get(brand, brand.title())
    print(f"{i:2d}. /{brand:<20} - {display_name}")

print("-" * 80)
print(f"\n✅ Total: {len(brands)} file upload commands")
print()
print("Usage Example:")
print("  /nike product_image:<upload file>")
print("  → System stores the uploaded image")
print("  → Modal appears WITHOUT image URL field")
print("  → User fills in: Product Name, Price, Currency, Size, Order Date")
print("  → Receipt is generated using the uploaded image")
print()
print("=" * 80)
