// Content script for scraping product information
console.log('GOAT Receipts scraper loaded');

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'scrapeProduct') {
    const productData = scrapeProductInfo(request.brand);
    sendResponse({ success: true, data: productData });
  }
  return true;
});

function scrapeProductInfo(brandConfig) {
  const data = {
    productName: '',
    productImage: '',
    productSKU: '',
    price: ''
  };

  if (!brandConfig || !brandConfig.selectors) {
    console.error('No brand config provided');
    return data;
  }

  const selectors = brandConfig.selectors;

  // Scrape product name
  if (selectors.productName) {
    const nameElement = document.querySelector(selectors.productName);
    if (nameElement) {
      data.productName = nameElement.textContent.trim();
    }
  }

  // Scrape product image
  if (selectors.productImage) {
    const imgElement = document.querySelector(selectors.productImage);
    if (imgElement) {
      data.productImage = imgElement.src || imgElement.getAttribute('data-src') || '';
    }
  }

  // Scrape product SKU
  if (selectors.productSKU) {
    const skuElement = document.querySelector(selectors.productSKU);
    if (skuElement) {
      data.productSKU = skuElement.textContent.trim();
    }
  }

  // Scrape price
  if (selectors.price) {
    const priceElement = document.querySelector(selectors.price);
    if (priceElement) {
      data.price = priceElement.textContent.trim().replace(/[^0-9.,]/g, '');
    }
  }

  console.log('Scraped product data:', data);
  return data;
}

// Alternative: Try to auto-detect using multiple selectors
function autoScrapeProduct() {
  const data = {
    productName: '',
    productImage: '',
    productSKU: '',
    price: ''
  };

  // Common product name selectors
  const nameSelectors = [
    'h1[class*="product"]',
    'h1[class*="title"]',
    'h1[itemprop="name"]',
    'h1.product-name',
    '#productTitle',
    '[data-test*="product-title"]'
  ];

  for (const selector of nameSelectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent.trim()) {
      data.productName = element.textContent.trim();
      break;
    }
  }

  // Common product image selectors
  const imgSelectors = [
    'img[class*="product"]',
    'img[itemprop="image"]',
    '#landingImage',
    'img[data-test*="product-image"]',
    '.product-image img'
  ];

  for (const selector of imgSelectors) {
    const element = document.querySelector(selector);
    if (element && element.src) {
      data.productImage = element.src;
      break;
    }
  }

  // Common SKU selectors
  const skuSelectors = [
    '[class*="sku"]',
    '[class*="style"]',
    '[class*="product-code"]',
    '[data-test*="sku"]',
    'span:contains("SKU")'
  ];

  for (const selector of skuSelectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent.trim()) {
      data.productSKU = element.textContent.trim();
      break;
    }
  }

  // Common price selectors
  const priceSelectors = [
    '[class*="price"]',
    '[itemprop="price"]',
    '[data-test*="price"]',
    '.price-value',
    '#priceblock_ourprice'
  ];

  for (const selector of priceSelectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent.trim()) {
      data.price = element.textContent.trim().replace(/[^0-9.,]/g, '');
      break;
    }
  }

  return data;
}
