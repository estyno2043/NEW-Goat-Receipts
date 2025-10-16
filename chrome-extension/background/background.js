// Background service worker for GOAT Receipts Extension

// Install event
chrome.runtime.onInstalled.addListener(() => {
  console.log('GOAT Receipts Extension installed');
  
  // Set default settings
  chrome.storage.sync.set({
    apiEndpoint: 'https://workspace-estyboss4.replit.app/api/generate-receipt',
    apiKey: '',
    proxyEnabled: false,
    proxyUrl: ''
  });
});

// Listen for tab updates to detect supported brands
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    const isSupportedBrand = checkIfSupportedBrand(tab.url);
    
    if (isSupportedBrand) {
      // Update badge to indicate supported brand
      chrome.action.setBadgeText({ text: '✓', tabId: tabId });
      chrome.action.setBadgeBackgroundColor({ color: '#d4ff00', tabId: tabId });
    } else {
      chrome.action.setBadgeText({ text: '', tabId: tabId });
    }
  }
});

function checkIfSupportedBrand(url) {
  const supportedPatterns = [
    /amazon\.com/,
    /amazon\.co\.uk/,
    /apple\.com/,
    /nike\.com/,
    /adidas\.com/,
    /stockx\.com/,
    /goat\.com/,
    /supremenewyork\.com/,
    /balenciaga\.com/,
    /gucci\.com/,
    /zara\.(com|eu)/,
    /moncler\.com/,
    /prada\.com/,
    /dior\.com/,
    /louisvuitton\.com/,
    /hermes\.com/,
    /chanel\.com/,
    /arcteryx\.com/,
    /thenorthface\.com/,
    /canadagoose\.com/
  ];
  
  return supportedPatterns.some(pattern => pattern.test(url));
}

// Message handler
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getSettings') {
    chrome.storage.sync.get(['apiEndpoint', 'apiKey', 'proxyEnabled', 'proxyUrl'], (items) => {
      sendResponse(items);
    });
    return true;
  }
});
