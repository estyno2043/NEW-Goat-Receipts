# 🚀 Quick Installation Guide

## Step 1: Load Extension in Chrome

1. Open Chrome browser
2. Navigate to `chrome://extensions/`
3. Enable **Developer mode** (toggle in top-right corner)
4. Click **"Load unpacked"**
5. Navigate to and select the `chrome-extension` folder
6. ✅ The extension is now installed!

## Step 2: Configure API Settings (Optional)

The extension is pre-configured with the default backend API, but you can customize it:

1. Click the extension icon in your Chrome toolbar
2. Click the "⚙️ Settings" button at the bottom
3. Configure your settings:
   - **API Endpoint**: Keep default or enter your custom backend URL
   - **API Key**: (Optional) Enter if your backend requires authentication
   - **Proxy**: (Optional) Enable for enhanced scraping

Default API: `https://workspace-estyboss4.replit.app/api/generate-receipt`

## Step 3: Test the Extension

1. Visit any supported product page, for example:
   - Nike: https://www.nike.com/t/air-jordan-1-retro-high-og
   - Amazon: https://www.amazon.com/dp/B08N5WRWNW
   - Apple: https://www.apple.com/shop/buy-iphone
   - StockX: https://stockx.com/nike-air-jordan-1

2. Click the extension icon
3. The extension will automatically:
   - Detect the brand
   - Scrape product information
   - Pre-fill the form

4. Enter your details:
   - Full Name
   - Email Address
   - Review auto-filled product info

5. Click **"Generate Receipt"**
6. Check your email! 📧

## Supported Brands

✅ The extension supports **80+ brands** including:

**Popular:**
- Amazon (US/UK)
- Apple
- Nike
- Adidas
- StockX
- GOAT

**Luxury:**
- Gucci
- Balenciaga
- Dior
- Louis Vuitton
- Hermès
- Prada

**Streetwear:**
- Supreme
- Corteiz
- Trapstar
- Gallery Dept

[See full list in README.md]

## Troubleshooting

### Extension doesn't appear after installation
- Refresh the `chrome://extensions/` page
- Make sure Developer mode is enabled
- Check for any error messages

### Brand not detected
- Ensure you're on a product page (not homepage)
- Check if the brand is in the supported list
- Try refreshing the page

### Auto-scraping doesn't work
- Some sites have anti-bot protection
- You can still manually enter product details
- Try enabling proxy in settings

### Receipt not received
- Check spam/junk folder
- Verify email address is correct
- Check backend API is running

## Advanced Usage

### Adding New Brands

Edit `config/brands.js` and add:

```javascript
'brandname': {
  name: 'Brand Name',
  urlPatterns: [/^https?:\/\/(www\.)?brandname\.com\/.+$/],
  selectors: {
    productName: 'h1.title',
    productImage: 'img.product',
    productSKU: 'span.sku',
    price: 'div.price'
  }
}
```

### Using with Custom Backend

1. Set your API endpoint in settings
2. Backend should accept POST to `/api/generate-receipt` with:

```json
{
  "brand": "nike",
  "fullName": "John Doe",
  "email": "john@example.com",
  "productName": "Air Jordan 1",
  "productImage": "https://...",
  "price": "170.00",
  ...
}
```

3. Backend should return:
```json
{
  "success": true,
  "message": "Receipt sent"
}
```

## Packaging for Distribution

To create a `.crx` package:

```bash
cd chrome-extension
zip -r goat-receipts-v1.0.0.zip ./*
```

Then submit to Chrome Web Store or distribute the ZIP file.

---

Need help? Check the [full README](README.md) or contact support!
