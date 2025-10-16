// Settings page script

document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  
  document.getElementById('saveBtn').addEventListener('click', saveSettings);
});

function loadSettings() {
  chrome.storage.sync.get([
    'apiEndpoint',
    'apiKey',
    'proxyEnabled',
    'proxyUrl'
  ], (items) => {
    document.getElementById('apiEndpoint').value = items.apiEndpoint || 'https://workspace-estyboss4.replit.app/api/generate-receipt';
    document.getElementById('apiKey').value = items.apiKey || '';
    document.getElementById('proxyEnabled').checked = items.proxyEnabled || false;
    document.getElementById('proxyUrl').value = items.proxyUrl || '';
  });
}

function saveSettings() {
  const settings = {
    apiEndpoint: document.getElementById('apiEndpoint').value.trim(),
    apiKey: document.getElementById('apiKey').value.trim(),
    proxyEnabled: document.getElementById('proxyEnabled').checked,
    proxyUrl: document.getElementById('proxyUrl').value.trim()
  };
  
  chrome.storage.sync.set(settings, () => {
    // Show success message
    const successMsg = document.getElementById('successMsg');
    successMsg.style.display = 'block';
    
    setTimeout(() => {
      successMsg.style.display = 'none';
    }, 3000);
  });
}
