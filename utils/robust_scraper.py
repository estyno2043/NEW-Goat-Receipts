"""
Robust web scraping utility with multiple fallback methods and enhanced error handling.
Handles proxy failures gracefully and ensures images are properly scraped.
"""

import requests
import time
import random
import re
import json
from typing import Optional, Dict, List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib3

# Disable SSL warnings globally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RobustScraper:
    """Enhanced scraper with multiple fallback methods and retry logic"""
    
    def __init__(self):
        # Zyte proxy configuration
        self.zyte_proxy = {
            "http": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/",
            "https": "http://a9abed72c425496584d422cfdba283d2:@api.zyte.com:8011/"
        }
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
        
        # Headers for better success rate
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
    
    def get_random_headers(self) -> Dict[str, str]:
        """Get headers with random user agent"""
        headers = self.headers.copy()
        headers["User-Agent"] = random.choice(self.user_agents)
        return headers
    
    def fetch_with_proxy(self, url: str, timeout: int = 30, max_retries: int = 3) -> Optional[requests.Response]:
        """Fetch URL using Zyte proxy with retry logic"""
        for attempt in range(max_retries):
            try:
                headers = self.get_random_headers()
                response = requests.get(
                    url,
                    proxies=self.zyte_proxy,
                    headers=headers,
                    verify=False,
                    timeout=timeout,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 503:
                    # Service unavailable, wait and retry
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    print(f"[Proxy] Service unavailable, waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                else:
                    print(f"[Proxy] Got status {response.status_code} for {url}")
                    
            except requests.exceptions.Timeout:
                print(f"[Proxy] Timeout on attempt {attempt + 1}/{max_retries}")
            except requests.exceptions.ProxyError:
                print(f"[Proxy] Proxy error on attempt {attempt + 1}/{max_retries}")
            except Exception as e:
                print(f"[Proxy] Error on attempt {attempt + 1}/{max_retries}: {str(e)}")
            
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
        
        return None
    
    def fetch_direct(self, url: str, timeout: int = 20) -> Optional[requests.Response]:
        """Fetch URL directly without proxy as fallback"""
        try:
            headers = self.get_random_headers()
            response = requests.get(
                url,
                headers=headers,
                verify=False,
                timeout=timeout,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                print(f"[Direct] Successfully fetched {url}")
                return response
            else:
                print(f"[Direct] Got status {response.status_code} for {url}")
                
        except Exception as e:
            print(f"[Direct] Failed to fetch {url}: {str(e)}")
        
        return None
    
    def fetch_with_zyte_api(self, url: str) -> Optional[Dict]:
        """Use Zyte API extraction endpoint as alternative method"""
        try:
            api_response = requests.post(
                "https://api.zyte.com/v1/extract",
                auth=("a9abed72c425496584d422cfdba283d2", ""),
                json={
                    "url": url,
                    "browserHtml": True,
                    "product": True,
                    "productOptions": {"extractFrom": "browserHtml"},
                },
                timeout=30
            )
            
            if api_response.status_code == 200:
                print(f"[Zyte API] Successfully extracted data from {url}")
                return api_response.json()
            else:
                print(f"[Zyte API] Got status {api_response.status_code}")
                
        except Exception as e:
            print(f"[Zyte API] Failed: {str(e)}")
        
        return None
    
    def extract_product_image(self, html: str, base_url: str) -> str:
        """Extract product image URL using multiple methods"""
        soup = BeautifulSoup(html, 'html.parser')
        image_url = None
        
        # Method 1: Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            image_url = og_image['content']
            print(f"[Image] Found via og:image: {image_url[:100]}...")
            return self.normalize_url(image_url, base_url)
        
        # Method 2: Twitter card image
        twitter_image = soup.find('meta', {'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            image_url = twitter_image['content']
            print(f"[Image] Found via twitter:image: {image_url[:100]}...")
            return self.normalize_url(image_url, base_url)
        
        # Method 3: Schema.org product image
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for Product schema
                    if data.get('@type') == 'Product' and data.get('image'):
                        images = data['image']
                        if isinstance(images, list) and images:
                            image_url = images[0]
                        elif isinstance(images, str):
                            image_url = images
                        if image_url:
                            print(f"[Image] Found via schema.org: {image_url[:100]}...")
                            return self.normalize_url(image_url, base_url)
            except:
                pass
        
        # Method 4: Product gallery images
        gallery_selectors = [
            ('img', {'class': re.compile(r'product.*image|gallery.*image|main.*image', re.I)}),
            ('img', {'class': re.compile(r'pdp.*image|detail.*image', re.I)}),
            ('img', {'data-testid': re.compile(r'product.*image|gallery.*image', re.I)}),
            ('div', {'class': re.compile(r'product.*gallery|image.*gallery', re.I)}),
            ('picture', {'class': re.compile(r'product|gallery', re.I)})
        ]
        
        for tag, attrs in gallery_selectors:
            element = soup.find(tag, attrs)
            if element:
                # Check for img src
                if tag == 'img' and element.get('src'):
                    image_url = element['src']
                    print(f"[Image] Found via gallery selector: {image_url[:100]}...")
                    return self.normalize_url(image_url, base_url)
                # Check for data-src (lazy loading)
                elif element.get('data-src'):
                    image_url = element['data-src']
                    print(f"[Image] Found via data-src: {image_url[:100]}...")
                    return self.normalize_url(image_url, base_url)
                # Check for srcset
                elif element.get('srcset'):
                    srcset = element['srcset']
                    # Get the highest resolution image from srcset
                    images = srcset.split(',')
                    if images:
                        image_url = images[-1].strip().split(' ')[0]
                        print(f"[Image] Found via srcset: {image_url[:100]}...")
                        return self.normalize_url(image_url, base_url)
        
        # Method 5: Any product image in page
        img_tags = soup.find_all('img', src=True, limit=50)
        for img in img_tags:
            src = img['src']
            # Filter out tracking pixels, icons, etc.
            if any(keyword in src.lower() for keyword in ['product', 'item', 'pdp', 'detail', 'large', 'zoom']):
                if not any(skip in src.lower() for skip in ['pixel', 'tracking', 'icon', 'logo', 'badge', '1x1', 'blank']):
                    image_url = src
                    print(f"[Image] Found via img tag scan: {image_url[:100]}...")
                    return self.normalize_url(image_url, base_url)
        
        # Method 6: Background images in style attributes
        style_elements = soup.find_all(style=re.compile(r'background.*url', re.I))
        for element in style_elements:
            style = element.get('style', '')
            match = re.search(r'url\(["\']?([^"\'()]+)["\']?\)', style)
            if match:
                image_url = match.group(1)
                if any(keyword in image_url.lower() for keyword in ['product', 'item', 'large']):
                    print(f"[Image] Found via style attribute: {image_url[:100]}...")
                    return self.normalize_url(image_url, base_url)
        
        print("[Image] No product image found with any method")
        return "https://via.placeholder.com/400x400/f0f0f0/999999?text=Product+Image"
    
    def normalize_url(self, url: str, base_url: str) -> str:
        """Normalize relative URLs to absolute URLs"""
        if not url:
            return ""
        
        # Already absolute URL
        if url.startswith('http://') or url.startswith('https://'):
            return url
        
        # Protocol-relative URL
        if url.startswith('//'):
            return 'https:' + url
        
        # Relative URL
        return urljoin(base_url, url)
    
    def scrape_product(self, url: str) -> Tuple[str, str, Dict]:
        """
        Main method to scrape product information with multiple fallbacks.
        Returns: (product_name, image_url, additional_data)
        """
        print(f"\n[Scraper] Starting robust scrape for: {url}")
        
        product_name = "Product"
        image_url = "https://via.placeholder.com/400x400/f0f0f0/999999?text=Product+Image"
        additional_data = {}
        
        # Try Method 1: Proxy with retries
        print("[Scraper] Attempting proxy fetch...")
        response = self.fetch_with_proxy(url)
        
        # Try Method 2: Direct fetch if proxy fails
        if not response:
            print("[Scraper] Proxy failed, attempting direct fetch...")
            response = self.fetch_direct(url)
        
        # Try Method 3: Zyte API extraction
        if not response:
            print("[Scraper] Direct fetch failed, attempting Zyte API...")
            api_data = self.fetch_with_zyte_api(url)
            
            if api_data:
                # Extract from Zyte API response
                if 'product' in api_data:
                    product_info = api_data['product']
                    if product_info.get('name'):
                        product_name = product_info['name']
                        print(f"[Scraper] Got product name from API: {product_name}")
                    
                    if product_info.get('mainImage'):
                        image_url = product_info['mainImage'].get('url', image_url)
                        print(f"[Scraper] Got image from API: {image_url[:100]}...")
                    elif product_info.get('images'):
                        images = product_info['images']
                        if images and len(images) > 0:
                            image_url = images[0].get('url', image_url)
                            print(f"[Scraper] Got image from API images array: {image_url[:100]}...")
                    
                    # Additional data
                    if product_info.get('price'):
                        additional_data['price'] = product_info['price']
                    if product_info.get('currency'):
                        additional_data['currency'] = product_info['currency']
                
                # Also try to parse browserHtml if available
                if 'browserHtml' in api_data and not image_url.startswith('http'):
                    image_url = self.extract_product_image(api_data['browserHtml'], url)
        
        # Process successful response
        if response and response.text:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract product name
            name_sources = [
                ('meta', {'property': 'og:title'}),
                ('meta', {'name': 'twitter:title'}),
                ('title', {}),
                ('h1', {'class': re.compile(r'product.*name|product.*title', re.I)}),
                ('h1', {})
            ]
            
            for tag, attrs in name_sources:
                element = soup.find(tag, attrs)
                if element:
                    if tag == 'meta':
                        content = element.get('content')
                        if content:
                            product_name = content.strip()
                            print(f"[Scraper] Got product name: {product_name[:100]}...")
                            break
                    else:
                        text = element.get_text(strip=True)
                        if text:
                            product_name = text
                            print(f"[Scraper] Got product name: {product_name[:100]}...")
                            break
            
            # Extract image
            image_url = self.extract_product_image(response.text, url)
        
        # Final validation of image URL
        if image_url and image_url.startswith('http'):
            # Try to validate the image URL is accessible
            try:
                img_check = requests.head(image_url, timeout=5, allow_redirects=True, verify=False)
                if img_check.status_code != 200:
                    print(f"[Scraper] Image URL returned {img_check.status_code}, using placeholder")
                    image_url = "https://via.placeholder.com/400x400/f0f0f0/999999?text=Product+Image"
            except:
                print("[Scraper] Could not validate image URL, keeping it anyway")
        
        print(f"[Scraper] Final results - Name: {product_name[:50]}..., Image: {image_url[:100]}...")
        return product_name, image_url, additional_data

# Global instance for easy import
scraper = RobustScraper()