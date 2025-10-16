// Popup script for GOAT Receipts Extension
let currentBrand = null;
let scrapedData = null;

// DOM Elements
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const receiptForm = document.getElementById('receiptForm');
const brandNameEl = document.getElementById('brandName');
const brandUrlEl = document.getElementById('brandUrl');
const generateBtn = document.getElementById('generateBtn');
const btnText = document.getElementById('btnText');
const btnSpinner = document.getElementById('btnSpinner');
const successMessage = document.getElementById('successMessage');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await initializeExtension();
  
  // Event listeners
  document.getElementById('retryBtn').addEventListener('click', initializeExtension);
  generateBtn.addEventListener('click', handleGenerateReceipt);
  document.getElementById('settingsBtn').addEventListener('click', openSettings);
  
  // Image preview
  document.getElementById('productImage').addEventListener('input', (e) => {
    const preview = document.getElementById('productImagePreview');
    if (e.target.value) {
      preview.src = e.target.value;
      preview.style.display = 'block';
    } else {
      preview.style.display = 'none';
    }
  });
  
  // Auto-set today's date + 3 days as default delivery
  const deliveryInput = document.getElementById('deliveryDate');
  const futureDate = new Date();
  futureDate.setDate(futureDate.getDate() + 3);
  deliveryInput.value = futureDate.toISOString().split('T')[0];
});

async function initializeExtension() {
  showLoading();
  
  try {
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab || !tab.url) {
      showError('Unable to detect current page');
      return;
    }
    
    // Detect brand
    currentBrand = detectBrand(tab.url);
    
    if (!currentBrand) {
      showError('This brand is not supported yet. Supported brands: Amazon, Nike, Apple, StockX, GOAT, and 20+ more.');
      return;
    }
    
    // Update UI with brand info
    brandNameEl.textContent = currentBrand.name;
    const urlObj = new URL(tab.url);
    brandUrlEl.textContent = urlObj.hostname.replace('www.', '');
    
    // Scrape product data
    scrapedData = await scrapeProductData(tab.id, currentBrand);
    
    if (!scrapedData.productName && !scrapedData.productImage) {
      showError('Could not auto-scrape product data. Please fill manually.');
      showForm();
      return;
    }
    
    // Auto-fill form
    autoFillForm(scrapedData);
    showForm();
    
  } catch (error) {
    console.error('Initialization error:', error);
    showError('An error occurred: ' + error.message);
  }
}

function detectBrand(url) {
  // Check each brand's URL patterns
  for (const [key, brand] of Object.entries(BRAND_CONFIG)) {
    for (const pattern of brand.urlPatterns) {
      if (pattern.test(url)) {
        return { key, ...brand };
      }
    }
  }
  return null;
}

async function scrapeProductData(tabId, brand) {
  try {
    const response = await chrome.tabs.sendMessage(tabId, {
      action: 'scrapeProduct',
      brand: brand
    });
    
    if (response && response.success) {
      return response.data;
    }
  } catch (error) {
    console.error('Scraping error:', error);
  }
  
  return {
    productName: '',
    productImage: '',
    productSKU: '',
    price: ''
  };
}

function autoFillForm(data) {
  if (data.productName) {
    document.getElementById('productName').value = data.productName;
  }
  
  if (data.productImage) {
    document.getElementById('productImage').value = data.productImage;
    const preview = document.getElementById('productImagePreview');
    preview.src = data.productImage;
    preview.style.display = 'block';
  }
  
  if (data.productSKU) {
    document.getElementById('productSKU').value = data.productSKU;
  }
  
  if (data.price) {
    document.getElementById('productPrice').value = data.price;
  }
}

async function handleGenerateReceipt() {
  // Validate required fields
  const fullName = document.getElementById('fullName').value.trim();
  const email = document.getElementById('email').value.trim();
  const productName = document.getElementById('productName').value.trim();
  
  if (!fullName || !email || !productName) {
    alert('Please fill in all required fields (Full Name, Email, Product Name)');
    return;
  }
  
  // Email validation
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    alert('Please enter a valid email address');
    return;
  }
  
  // Prepare receipt data
  const receiptData = {
    brand: currentBrand.key,
    brandName: currentBrand.name,
    fullName: fullName,
    email: email,
    productName: productName,
    productImage: document.getElementById('productImage').value.trim(),
    productSKU: document.getElementById('productSKU').value.trim(),
    orderNumber: document.getElementById('orderNumber').value.trim(),
    price: document.getElementById('productPrice').value.trim(),
    currency: document.getElementById('currency').value,
    deliveryDate: document.getElementById('deliveryDate').value,
    size: document.getElementById('size').value.trim(),
    color: document.getElementById('color').value.trim(),
    timestamp: new Date().toISOString()
  };
  
  // Show loading
  generateBtn.disabled = true;
  btnText.style.display = 'none';
  btnSpinner.style.display = 'block';
  
  try {
    // Get API endpoint from settings
    const settings = await chrome.storage.sync.get(['apiEndpoint', 'apiKey']);
    const apiEndpoint = settings.apiEndpoint || 'https://workspace-estyboss4.replit.app/api/generate-receipt';
    
    // Send to backend
    const response = await fetch(apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': settings.apiKey || ''
      },
      body: JSON.stringify(receiptData)
    });
    
    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }
    
    const result = await response.json();
    
    // Show success
    successMessage.style.display = 'block';
    setTimeout(() => {
      successMessage.style.display = 'none';
    }, 5000);
    
    // Reset button
    generateBtn.disabled = false;
    btnText.style.display = 'block';
    btnSpinner.style.display = 'none';
    
  } catch (error) {
    console.error('Generate receipt error:', error);
    alert('Failed to generate receipt: ' + error.message);
    
    generateBtn.disabled = false;
    btnText.style.display = 'block';
    btnSpinner.style.display = 'none';
  }
}

function showLoading() {
  loadingState.style.display = 'block';
  errorState.style.display = 'none';
  receiptForm.style.display = 'none';
}

function showError(message) {
  loadingState.style.display = 'none';
  errorState.style.display = 'block';
  receiptForm.style.display = 'none';
  document.getElementById('errorMessage').textContent = message;
}

function showForm() {
  loadingState.style.display = 'none';
  errorState.style.display = 'none';
  receiptForm.style.display = 'block';
}

function openSettings() {
  chrome.runtime.openOptionsPage();
}
