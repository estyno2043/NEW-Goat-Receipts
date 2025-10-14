# Gumroad Integration Setup Guide

This guide explains how to set up automatic purchase processing with Gumroad webhooks for your Discord bot.

## Overview

The bot now supports automatic access granting when users purchase through Gumroad. When a purchase is made, the system:
1. Receives the webhook from Gumroad
2. Searches for the user in your Discord server by their Discord username
3. Automatically grants access based on the product purchased
4. Sends notifications to the purchases channel and the user's DMs
5. Assigns appropriate roles (Customer, Client, Subscription)

## Prerequisites

- A Gumroad account with products set up
- Your Discord bot running with webhook server active (port 5000)
- Public URL for your Replit (e.g., `https://your-repl-name.your-username.repl.co`)

## Step 1: Configure Gumroad Products

### Product Naming Convention
Your Gumroad product names should match the subscription types:

| Product Name Pattern | Subscription Type | Duration |
|---------------------|-------------------|----------|
| Contains "3 day" or "3day" | 3day | 3 Days |
| Contains "14 day" or "14day" | 14day | 14 Days |
| Contains "1 month" or "1month" | 1month | 1 Month |
| Contains "3 month" or "3month" | 3month | 3 Months |
| Contains "lifetime" | lifetime | Lifetime |
| Contains "lite" | lite | 7 Receipts |
| Contains "guild" and "lifetime" | guild_lifetime | Guild Lifetime |
| Contains "guild" | guild_30days | Guild 30 Days |

**Examples:**
- "Receipt Generator - 1 Month Access" → 1month subscription
- "Premium Guild Access (Lifetime)" → guild_lifetime subscription
- "Lite Package" → lite subscription

### Add Custom Field for Discord Username

1. Go to your Gumroad product settings
2. Navigate to "Custom fields" or "Checkout customization"
3. Add a **required** custom field:
   - **Label:** Discord Username
   - **Type:** Text field
   - **Required:** Yes
   - **Placeholder:** Enter your Discord username (e.g., username)

**Important:** The field must be named exactly "Discord Username" for the webhook to parse it correctly.

## Step 2: Configure Gumroad Webhook

1. Log in to your Gumroad account
2. Go to **Settings** → **Advanced** → **Webhooks**
3. Click **"Add a webhook URL"**
4. Enter your webhook URL:
   ```
   https://your-repl-name.your-username.repl.co/webhook/gumroad
   ```
   Replace `your-repl-name.your-username.repl.co` with your actual Replit URL

5. Select the event to trigger: **"Sale"**
6. Click **"Add webhook URL"**
7. Gumroad will send a test webhook - your bot should process it (it may fail if the Discord username doesn't exist in your server)

## Step 3: Test the Integration

### Manual Testing with curl

You can test the webhook locally:

```bash
curl -X POST http://localhost:5000/webhook/gumroad \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Receipt Generator - 1 Month",
    "price": "2000",
    "email": "customer@example.com",
    "full_name": "Test Customer",
    "custom_fields": {
      "Discord Username": "actualusername"
    }
  }'
```

### Test Purchase Flow

1. Make a test purchase on your Gumroad product
2. Enter a valid Discord username from your server
3. Complete the purchase
4. Check:
   - Purchases channel (ID: 1412500928187203606) for notification
   - User's DMs for confirmation message
   - User's roles (Customer, Client, Subscription should be added)
   - Database for updated subscription

## Webhook Data Flow

```
Gumroad Purchase
    ↓
POST to /webhook/gumroad
    ↓
Extract Discord username from custom_fields
    ↓
Search Discord server for user
    ↓
Determine subscription type from product name
    ↓
Grant access via MongoDB
    ↓
Queue notification in MongoDB
    ↓
Bot's background task processes notification (every 5 seconds)
    ↓
Send to purchases channel + DM user + Assign roles
```

## Expected Webhook Payload from Gumroad

```json
{
  "seller_id": "...",
  "product_id": "...",
  "product_name": "Receipt Generator - 1 Month",
  "permalink": "...",
  "product_permalink": "...",
  "email": "customer@example.com",
  "price": "2000",
  "gumroad_fee": "...",
  "currency": "usd",
  "quantity": "1",
  "discover_fee_charged": false,
  "can_contact": true,
  "referrer": "...",
  "card": {...},
  "order_number": 123456789,
  "sale_id": "...",
  "sale_timestamp": "2025-10-14T09:00:00Z",
  "purchaser_id": "...",
  "subscription_id": "...",
  "custom_fields": {
    "Discord Username": "actualusername"
  },
  "full_name": "John Doe"
}
```

## Notification Format

### Purchases Channel Message
```
@user mention
┌─────────────────────────────────────┐
│ Thank you for purchasing            │
│                                     │
│ @username, your subscription has    │
│ been updated. Check below           │
│                                     │
│ Run command /generate in            │
│ #commands to continue               │
│                                     │
│ Subscription Type                   │
│ `1 Month`                          │
│                                     │
│ Please consider leaving a review    │
│ at #reviews                         │
└─────────────────────────────────────┘
```

### User DM Message
Same format as above, sent directly to the user.

## Troubleshooting

### Webhook not triggering
- Verify webhook URL in Gumroad settings
- Check that webhook server is running (Flask on port 5000)
- Check logs: `grep "Gumroad webhook" /tmp/logs/Discord_Bot_*.log`

### User not found
- Ensure Discord username is exactly correct (case-sensitive)
- User must be a member of the main guild (ID: 1412488621293961226)
- Check logs for "Discord user not found" messages

### Access not granted
- Verify product name matches subscription type patterns
- Check MongoDB for user subscription updates
- Review logs for "Successfully granted access" messages

### Notifications not sending
- Verify purchases channel exists (ID: 1412500928187203606)
- Check notification queue in MongoDB (`gumroad_notifications` collection)
- Ensure bot has permission to send messages in purchases channel
- Verify background task is running (check for "Notification processor started" in logs)

### Roles not assigned
- Verify role IDs in config.json:
  - Customer role: 1412498223842721903
  - Client role: from config.json (`Client_ID`)
  - Subscription role: 1412498358248935634
- Ensure bot has permission to manage roles
- Check bot's role hierarchy (bot's role must be above assigned roles)

## Security Considerations

1. **Webhook Verification**: Consider adding Gumroad webhook signature verification for production
2. **Rate Limiting**: The webhook has basic duplicate purchase detection
3. **Error Handling**: All errors are logged; failed notifications are queued for retry
4. **User Privacy**: Discord usernames are stored only temporarily for processing

## Additional Notes

- The webhook endpoint is: `/webhook/gumroad`
- Notifications are processed every 5 seconds by the background task
- Guild subscriptions trigger different notifications (use `/configure_guild` command)
- Lite subscriptions do NOT receive the Subscription role (only Customer and Client)
- All purchases are logged to MongoDB for tracking and auditing
