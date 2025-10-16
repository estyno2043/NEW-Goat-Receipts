// Brand configuration with URL patterns and scraping selectors
const BRAND_CONFIG = {
  'amazon': {
    name: 'Amazon',
    urlPatterns: [/^https?:\/\/(www\.)?amazon\.com\/.+$/],
    selectors: {
      productName: '#productTitle',
      productImage: '#landingImage, #imgTagWrapperId img',
      productSKU: 'th:contains("ASIN") + td, [class*="asin"]',
      price: '.a-price-whole, #priceblock_ourprice, #priceblock_dealprice'
    }
  },
  'amazonuk': {
    name: 'Amazon UK',
    urlPatterns: [/^https?:\/\/(www\.)?amazon\.co\.uk\/.+$/],
    selectors: {
      productName: '#productTitle',
      productImage: '#landingImage, #imgTagWrapperId img',
      productSKU: 'th:contains("ASIN") + td',
      price: '.a-price-whole'
    }
  },
  'apple': {
    name: 'Apple',
    urlPatterns: [/^https?:\/\/(www\.)?apple\.com\/.+$/],
    selectors: {
      productName: 'h1.rf-pdp-title, h1[data-autom="productName"]',
      productImage: '.rf-pdp-gallery-image img, img[data-autom="heroImage"]',
      productSKU: '[data-autom="dimensionScreensize"], [data-autom="dimensionCapacity"]',
      price: '.rf-pdp-pricing-price, [data-autom="price"]'
    }
  },
  'nike': {
    name: 'Nike',
    urlPatterns: [/^https?:\/\/(www\.)?nike\.com\/.+$/],
    selectors: {
      productName: '#pdp_product_title, h1[data-test="product-title"]',
      productImage: 'img[data-sub-media-type="image"]',
      productSKU: 'div[class*="style-color"]',
      price: 'div[data-test="product-price"]'
    }
  },
  'adidas': {
    name: 'Adidas',
    urlPatterns: [/^https?:\/\/(www\.)?adidas\.com\/.+$/],
    selectors: {
      productName: 'h1[class*="name"], h1.product-title',
      productImage: 'img.image___3ByV2',
      productSKU: 'div[class*="style-code"]',
      price: 'div[class*="price"]'
    }
  },
  'stockx': {
    name: 'StockX',
    urlPatterns: [/^https?:\/\/(www\.)?stockx\.com\/.+$/],
    selectors: {
      productName: 'h1[data-testid="product-name"]',
      productImage: 'img[data-testid="product-detail-image"]',
      productSKU: 'div[data-testid="product-detail-style"]',
      price: 'div[data-testid="highest-bid"]'
    }
  },
  'goat': {
    name: 'GOAT',
    urlPatterns: [/^https?:\/\/(www\.)?goat\.com\/.+$/],
    selectors: {
      productName: 'h1.ProductDetailsHeader__title',
      productImage: 'img.ProductMedia__image',
      productSKU: 'span.ProductDetailsHeader__sku',
      price: 'div.ProductPrice__value'
    }
  },
  'supreme': {
    name: 'Supreme',
    urlPatterns: [/^https?:\/\/(www\.)?supremenewyork\.com\/.+$/],
    selectors: {
      productName: 'h1[itemprop="name"]',
      productImage: 'img[itemprop="image"]',
      productSKU: 'p[itemprop="model"]',
      price: 'p[itemprop="price"]'
    }
  },
  'balenciaga': {
    name: 'Balenciaga',
    urlPatterns: [/^https?:\/\/(www\.)?balenciaga\.com\/.+$/],
    selectors: {
      productName: 'h1.product-name',
      productImage: 'img.product-image',
      productSKU: 'span.product-code',
      price: 'span.price-sales'
    }
  },
  'gucci': {
    name: 'Gucci',
    urlPatterns: [/^https?:\/\/(www\.)?gucci\.com\/.+$/],
    selectors: {
      productName: 'h1[data-test="product-name"]',
      productImage: 'img[data-test="product-image"]',
      productSKU: 'span[data-test="product-code"]',
      price: 'span[data-test="product-price"]'
    }
  },
  'zara': {
    name: 'Zara',
    urlPatterns: [/^https?:\/\/(www\.)?zara\.(com|eu)\/.+$/],
    selectors: {
      productName: 'h1.product-detail-info__header-name',
      productImage: 'img.media-image__image',
      productSKU: 'span.product-detail-info__header-id',
      price: 'span.price__amount'
    }
  },
  'moncler': {
    name: 'Moncler',
    urlPatterns: [/^https?:\/\/(www\.)?moncler\.com\/.+$/],
    selectors: {
      productName: 'h1.pdp-name',
      productImage: 'img.product-image',
      productSKU: 'span.product-id',
      price: 'span.price-value'
    }
  },
  'prada': {
    name: 'Prada',
    urlPatterns: [/^https?:\/\/(www\.)?prada\.com\/.+$/],
    selectors: {
      productName: 'h1.product__name',
      productImage: 'img.product__image',
      productSKU: 'span.product__code',
      price: 'span.product__price'
    }
  },
  'dior': {
    name: 'Dior',
    urlPatterns: [/^https?:\/\/(www\.)?dior\.com\/.+$/],
    selectors: {
      productName: 'h1.product-name',
      productImage: 'img.product-image',
      productSKU: 'div.product-reference',
      price: 'span.product-price'
    }
  },
  'lv': {
    name: 'Louis Vuitton',
    urlPatterns: [/^https?:\/\/(www\.)?louisvuitton\.com\/.+$/],
    selectors: {
      productName: 'h1.lv-product__name',
      productImage: 'img.lv-product__image',
      productSKU: 'span.lv-product__code',
      price: 'span.lv-product__price'
    }
  },
  'hermes': {
    name: 'Hermès',
    urlPatterns: [/^https?:\/\/(www\.)?hermes\.com\/.+$/],
    selectors: {
      productName: 'h1.product-name',
      productImage: 'img.product-image',
      productSKU: 'div.product-code',
      price: 'span.product-price'
    }
  },
  'chanel': {
    name: 'Chanel',
    urlPatterns: [/^https?:\/\/(www\.)?chanel\.com\/.+$/],
    selectors: {
      productName: 'h1.product__name',
      productImage: 'img.product__image',
      productSKU: 'div.product__code',
      price: 'span.product__price'
    }
  },
  'arcteryx': {
    name: "Arc'teryx",
    urlPatterns: [/^https?:\/\/(www\.)?arcteryx\.com\/.+$/],
    selectors: {
      productName: 'h1.product-name',
      productImage: 'img.product-image',
      productSKU: 'span.product-sku',
      price: 'span.product-price'
    }
  },
  'tnf': {
    name: 'The North Face',
    urlPatterns: [/^https?:\/\/(www\.)?thenorthface\.(com|co\.uk|de|fr|it|es|ca|com\.au|jp|kr|cn)\/.+$/],
    selectors: {
      productName: 'h1.product-name',
      productImage: 'img.product-image',
      productSKU: 'span.product-number',
      price: 'span.product-price'
    }
  },
  'canadagoose': {
    name: 'Canada Goose',
    urlPatterns: [/^https?:\/\/(www\.)?canadagoose\.com\/.+$/],
    selectors: {
      productName: 'h1.product-name',
      productImage: 'img.product-image',
      productSKU: 'span.style-number',
      price: 'span.price-value'
    }
  }
};

// Add more brands with similar patterns...
// You can expand this configuration based on your needs
