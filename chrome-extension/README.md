# 🐐 GOAT Receipts Chrome Extension

Automatically scrape product information from 80+ supported brands and generate professional receipts sent directly to your email.

## ✨ Features

- **Auto-Detection**: Automatically detects the brand from the current webpage
- **Smart Scraping**: Extracts product name, image, SKU, and price automatically
- **80+ Brands Supported**: Amazon, Nike, Apple, StockX, GOAT, Supreme, Gucci, Balenciaga, and many more
- **One-Click Generation**: Fill in your details and generate receipts instantly
- **Email Delivery**: Receipts are sent directly to your email
- **Proxy Support**: Optional proxy configuration for advanced scraping

## 🚀 Installation

### Method 1: Load Unpacked Extension (Development)

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right corner)
3. Click "Load unpacked"
4. Select the `chrome-extension` folder
5. The extension icon should appear in your toolbar

### Method 2: Package and Install

1. Package the extension:
   ```bash
   cd chrome-extension
   zip -r goat-receipts-extension.zip .
   ```

2. Install the packaged extension in Chrome

## 📋 How to Use

1. **Browse** to any supported product page (e.g., Nike shoes, Apple MacBook, etc.)
2. **Click** the GOAT Receipts extension icon in your toolbar
3. **Review** the auto-filled product information
4. **Fill** in your personal details (name, email, etc.)
5. **Click** "Generate Receipt" - done! 📧

## 🎯 Supported Brands

### Popular Brands
- Amazon (US & UK)
- Apple & Apple Pickup
- Nike & SNKRS
- Adidas
- StockX
- GOAT
- Supreme

### Luxury Brands
- Gucci
- Balenciaga
- Dior
- Prada
- Louis Vuitton
- Hermès
- Chanel
- Moncler

### Streetwear
- Corteiz (CRTZ)
- Trapstar
- Spider
- Gallery Dept
- Broken Planet
- Stüssy

### And 60+ more brands!

## ⚙️ Configuration

### API Settings
1. Click the extension icon
2. Click the "⚙️ Settings" button
3. Configure:
   - **API Endpoint**: Your backend API URL (default provided)
   - **API Key**: Optional authentication key
   - **Proxy Settings**: Enable proxy for enhanced scraping

### Default API Endpoint
```
https://workspace-estyboss4.replit.app/api/generate-receipt
```

## 🔧 Backend Integration

The extension sends receipt data to your backend API in the following format:

```json
{
  "brand": "nike",
  "brandName": "Nike",
  "fullName": "John Doe",
  "email": "john@example.com",
  "productName": "Air Jordan 1 Retro High OG",
  "productImage": "https://...",
  "productSKU": "555088-134",
  "orderNumber": "123456789",
  "price": "170.00",
  "currency": "$",
  "deliveryDate": "2025-10-20",
  "size": "10",
  "color": "White/Black",
  "timestamp": "2025-10-16T12:00:00.000Z"
}
```

## 🛠️ Development

### File Structure
```
chrome-extension/
├── manifest.json           # Extension manifest
├── icons/                  # Extension icons
├── popup/                  # Popup interface
│   ├── popup.html
│   ├── popup.css
│   └── popup.js
├── content/               # Content scripts
│   └── scraper.js
├── background/            # Background worker
│   └── background.js
├── config/                # Brand configurations
│   └── brands.js
├── options.html          # Settings page
└── options.js           # Settings logic
```

### Adding New Brands

Edit `config/brands.js` to add a new brand:

```javascript
'newbrand': {
  name: 'New Brand',
  urlPatterns: [/^https?:\/\/(www\.)?newbrand\.com\/.+$/],
  selectors: {
    productName: 'h1.product-title',
    productImage: 'img.product-image',
    productSKU: 'span.sku',
    price: 'div.price'
  }
}
```

## 🔐 Security & Privacy

- All data is sent securely via HTTPS
- No data is stored locally except user preferences
- Product scraping is done client-side
- API keys are stored securely in Chrome's sync storage

## 🐛 Troubleshooting

### Extension doesn't detect the brand
- Make sure you're on a product page, not the homepage
- Check if the brand is in our supported list
- Try refreshing the page

### Auto-scraping fails
- Some websites have anti-scraping measures
- You can still manually fill in the product details
- Try enabling proxy in settings

### Receipt not received
- Check your spam/junk folder
- Verify the email address is correct
- Check API settings are configured properly

## 📝 License

This extension is part of the GOAT Receipts system.

## 🤝 Support

For issues or feature requests, please contact the development team.

---

Made with 💛 by the GOAT Receipts Team
