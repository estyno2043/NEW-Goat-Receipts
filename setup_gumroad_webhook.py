#!/usr/bin/env python3
"""
Script to set up Gumroad webhook using Resource Subscriptions API
Run this once to register your webhook endpoint with Gumroad
"""

import requests
import sys

# Your webhook URL
WEBHOOK_URL = "https://c8355908-504c-4aff-9b99-430cc644bb43-00-2om513qodt8ki.riker.replit.dev/webhook/gumroad"

def setup_webhook(access_token):
    """Subscribe to Gumroad sales webhook"""
    
    api_url = "https://api.gumroad.com/v2/resource_subscriptions"
    
    data = {
        "access_token": access_token,
        "resource_name": "sale",  # Subscribe to sales events
        "post_url": WEBHOOK_URL
    }
    
    print(f"Setting up webhook...")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print(f"Resource: sale")
    print()
    
    response = requests.put(api_url, data=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ SUCCESS! Webhook registered successfully!")
            print(f"Subscription ID: {result.get('resource_subscription', {}).get('id')}")
            print()
            print("Your webhook is now active. When someone purchases your product,")
            print("Gumroad will send a POST request to your webhook URL.")
            return True
        else:
            print("❌ ERROR: API returned success=false")
            print(f"Response: {result}")
            return False
    else:
        print(f"❌ ERROR: Request failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False

def check_existing_subscriptions(access_token):
    """Check if there are existing webhook subscriptions"""
    
    api_url = "https://api.gumroad.com/v2/resource_subscriptions"
    
    response = requests.get(api_url, params={"access_token": access_token})
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            subscriptions = result.get("resource_subscriptions", [])
            if subscriptions:
                print("Existing webhook subscriptions:")
                for sub in subscriptions:
                    print(f"  - {sub.get('resource_name')} → {sub.get('post_url')}")
                print()
            else:
                print("No existing webhook subscriptions found.")
                print()
            return subscriptions
        
    return []

if __name__ == "__main__":
    print("=" * 60)
    print("Gumroad Webhook Setup Script")
    print("=" * 60)
    print()
    
    # Get access token from user
    if len(sys.argv) > 1:
        access_token = sys.argv[1]
    else:
        print("To get your access token:")
        print("1. Go to: https://gumroad.com/settings/advanced#applications")
        print("2. Click on 'replit auto payment'")
        print("3. Click 'Generate access token'")
        print("4. Copy the token")
        print()
        access_token = input("Enter your Gumroad access token: ").strip()
    
    if not access_token:
        print("❌ Error: Access token is required")
        sys.exit(1)
    
    print()
    
    # Check existing subscriptions
    check_existing_subscriptions(access_token)
    
    # Set up the webhook
    success = setup_webhook(access_token)
    
    if success:
        print()
        print("Next steps:")
        print("1. Add 'Discord Username' custom field to your products")
        print("2. Test by making a purchase (use test mode if available)")
        print("3. Check your Discord bot logs for incoming webhooks")
    
    sys.exit(0 if success else 1)
