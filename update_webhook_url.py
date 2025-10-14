#!/usr/bin/env python3
"""
Script to update Gumroad webhook URL for production deployment
Run this after deploying your app to update the webhook endpoint
"""

import requests
import sys
import os

def get_webhook_url():
    """Get the appropriate webhook URL based on environment"""
    
    # Use the deployed production URL
    prod_url = "https://new-goat-receipts-kuboestok.replit.app/webhook/gumroad"
    print(f"Using deployed production URL: {prod_url}")
    return prod_url

def update_webhook(access_token, webhook_url):
    """Update Gumroad webhook URL"""
    
    # First, delete existing subscription (if any)
    delete_url = "https://api.gumroad.com/v2/resource_subscriptions"
    
    # Get existing subscriptions
    response = requests.get(delete_url, params={"access_token": access_token})
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            subscriptions = result.get("resource_subscriptions", [])
            for sub in subscriptions:
                if sub.get("resource_name") == "sale":
                    # Delete old subscription
                    sub_id = sub.get("id")
                    print(f"Deleting old webhook subscription: {sub_id}")
                    delete_response = requests.delete(
                        f"{delete_url}/{sub_id}",
                        data={"access_token": access_token}
                    )
                    if delete_response.status_code == 200:
                        print("✅ Old webhook removed")
                    else:
                        print(f"⚠️ Could not delete old webhook: {delete_response.text}")
    
    # Now create new subscription
    api_url = "https://api.gumroad.com/v2/resource_subscriptions"
    
    data = {
        "access_token": access_token,
        "resource_name": "sale",
        "post_url": webhook_url
    }
    
    print(f"\nSetting up new webhook...")
    print(f"Webhook URL: {webhook_url}")
    print(f"Resource: sale")
    print()
    
    response = requests.put(api_url, data=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ SUCCESS! Webhook updated successfully!")
            print(f"Subscription ID: {result.get('resource_subscription', {}).get('id')}")
            print()
            print("Your webhook is now active with the new URL.")
            print("When someone purchases your product, Gumroad will send requests to:")
            print(f"  {webhook_url}")
            return True
        else:
            print("❌ ERROR: API returned success=false")
            print(f"Response: {result}")
            return False
    else:
        print(f"❌ ERROR: Request failed with status {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Gumroad Webhook URL Update Script")
    print("=" * 60)
    print()
    
    # Get the appropriate webhook URL
    webhook_url = get_webhook_url()
    if not webhook_url:
        sys.exit(1)
    
    # Get access token from environment or prompt
    access_token = os.environ.get('GUMROAD_ACCESS_TOKEN', '').strip()
    
    if not access_token:
        print("\nTo update your webhook, you need your Gumroad access token.")
        print("Get it from: https://app.gumroad.com/settings/advanced#application-form")
        print()
        
        access_token = input("Enter your Gumroad access token: ").strip()
        
        if not access_token:
            print("❌ Access token is required!")
            sys.exit(1)
    else:
        print("\n✅ Using access token from environment variable")
    
    # Update the webhook
    success = update_webhook(access_token, webhook_url)
    
    if success:
        print("\n✅ Webhook URL updated successfully!")
        print("The webhook will now work with your deployed app 24/7.")
    else:
        print("\n❌ Failed to update webhook URL")
        sys.exit(1)
