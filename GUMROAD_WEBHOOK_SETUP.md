# Gumroad Webhook Setup Instructions

## 🚨 IMPORTANT: Update Webhook URL for Production

When your bot is deployed, you **MUST** update the Gumroad webhook URL to point to your production deployment, not the development URL.

## Production URL
Your production webhook URL is:
```
https://workspace-goatreceipts.replit.app/webhook/gumroad
```

## How to Update the Webhook

### Method 1: Using the Update Script (Recommended)

1. Run the update script:
   ```bash
   python update_webhook_url.py
   ```

2. Enter your Gumroad access token when prompted
   - Get your token from: https://app.gumroad.com/settings/advanced#application-form

3. The script will automatically:
   - Detect your production URL
   - Remove the old webhook subscription
   - Register the new production webhook URL

### Method 2: Manual Update via Gumroad Dashboard

1. Go to https://app.gumroad.com/settings/advanced#application-form

2. Find your existing webhook subscription for "sale" events

3. Delete the old subscription pointing to the development URL

4. Create a new webhook subscription:
   - Resource: `sale`
   - URL: `https://workspace-goatreceipts.replit.app/webhook/gumroad`

## Testing the Webhook

After updating the webhook URL:

1. **Deploy your app** - Click "Deploy" button in Replit

2. **Test with a purchase**:
   - Make a test purchase with your Discord ID
   - Check if access is granted automatically
   - Check if DM notification is sent

3. **Test fallback system**:
   - Make a test purchase with an incorrect Discord username
   - Check if fallback notification appears in channel 1427592513299943535

## Troubleshooting

### Webhook not working after deployment?

1. **Check the webhook URL** - Make sure Gumroad is pointing to your production URL, not development URL

2. **Verify both services are running**:
   - Check deployment logs
   - Both Discord bot and webhook server should be running

3. **Check MongoDB connection**:
   - Ensure MongoDB is accessible from production
   - Check environment variables are set

### Common Issues

- **Port conflict**: Fixed by using run_production.py which manages both services
- **Wrong URL**: Development URL doesn't work when IDE is closed
- **Services not running**: Both Discord bot and Flask server must be running

## Architecture

The production system runs two services:

1. **Discord Bot** (main.py) - Handles Discord interactions
2. **Webhook Server** (webhook_server.py) - Receives Gumroad webhooks on port 5000

Both are managed by `run_production.py` which ensures they run together in production.

## Important Notes

- The webhook URL MUST match your deployment URL
- Development URL only works when Replit IDE is open
- Production URL works 24/7 when deployed as VM
- Always test after updating the webhook URL