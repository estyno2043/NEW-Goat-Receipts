# 🚀 Deployment Guide - 24/7 Automatic Purchase System

## ✅ Current Status

Your app is **configured correctly** for deployment! Here's what's working:

- ✅ Discord bot connects successfully
- ✅ Webhook server runs on port 5000
- ✅ Both services share the same bot instance
- ✅ Gumroad webhook processes purchases automatically
- ✅ Users receive access and DM notifications
- ✅ Deployment configuration set to VM (always on)

## 🔄 Running vs Deployed: What's the Difference?

### Running in Workspace (Current State)
- ⚠️ **Stops when you close Replit** - Your workspace must stay open
- ⚠️ **Development mode** - Only works while you're actively using Replit
- ✅ Good for testing and development

### Deployed (Production)
- ✅ **Runs 24/7** - Works even when you close Replit completely
- ✅ **Production mode** - Uses `run_production.py` to manage both services
- ✅ **Always available** - Gumroad webhooks work anytime
- ✅ **VM deployment** - Dedicated server keeps your bot online

## 📋 How to Deploy Your App

### Step 1: Click the Deploy Button

1. Look at the top-right of your Replit workspace
2. Click the **"Deploy"** button (rocket icon 🚀)
3. Replit will show you deployment options

### Step 2: Choose Deployment Type

Your app is already configured as **"VM" deployment** (always on). This means:
- Your bot runs continuously
- Webhook server stays online 24/7
- Both Discord bot and webhook work together

### Step 3: Deploy

1. Click **"Deploy"** or **"Update Deployment"**
2. Replit will build and deploy your app
3. Wait for deployment to complete (usually 1-2 minutes)

### Step 4: Verify Deployment

Once deployed, you'll see:
- **Deployment status**: "Running" or "Active"
- **Production URL**: `https://workspace-goatreceipts.replit.app`
- **Webhook URL**: `https://workspace-goatreceipts.replit.app/webhook/gumroad`

## ✅ How to Test Your Deployment

### Test 1: Check the Webhook URL

Visit your webhook URL in a browser:
```
https://workspace-goatreceipts.replit.app/webhook/gumroad
```

You should see:
- **405 Method Not Allowed** (this is correct - GET requests are not allowed)
- This confirms the webhook server is online

### Test 2: Close Replit Completely

1. Close your Replit workspace tab
2. Make a test purchase on Gumroad with your Discord ID
3. Check Discord - you should receive:
   - ✅ Access granted automatically
   - ✅ DM notification from the bot
   - ✅ Purchase notification in your purchases channel

### Test 3: Check Deployment Logs

1. Go to your Replit deployment dashboard
2. Click on "Logs" to see real-time activity
3. You should see:
   - Bot connected to Discord
   - Webhook server running on port 5000
   - Purchase processing logs when someone buys

## 🔧 Troubleshooting

### Webhook Not Working After Deployment?

**Problem**: Purchases don't grant access after deployment

**Solution**: Verify these settings:

1. **Gumroad Webhook URL** - Make sure it points to production:
   ```
   https://workspace-goatreceipts.replit.app/webhook/gumroad
   ```

2. **Check Deployment Status** - Make sure deployment is "Running"

3. **View Deployment Logs** - Check for errors in the deployment dashboard

### Deployment Keeps Stopping?

**Problem**: Deployment shuts down after a while

**Solutions**:
- Make sure you have a paid Replit plan (free plans have limited uptime)
- Check deployment logs for crash errors
- Verify MongoDB connection is working

### Bot Not Responding?

**Problem**: Bot doesn't appear online in Discord

**Solutions**:
1. Check deployment logs for connection errors
2. Verify Discord bot token is correct in Secrets
3. Make sure Members intent is enabled in Discord Developer Portal

## 📊 Monitoring Your Deployment

### Where to Check Status

1. **Replit Deployment Dashboard**
   - Shows if your app is running
   - Displays logs in real-time
   - Shows CPU/memory usage

2. **Discord Server**
   - Bot appears online
   - Commands work
   - Receipts generate successfully

3. **Gumroad Webhook Logs**
   - Check Gumroad dashboard for webhook delivery status
   - Should show "200 OK" for successful deliveries

## 🎯 What Happens When Deployed

When someone purchases on Gumroad:

1. **Purchase Made** → Gumroad sends webhook to your URL
2. **Webhook Receives** → Your Flask server processes the data
3. **User Lookup** → Bot finds the Discord user by ID
4. **Access Granted** → License created in MongoDB
5. **Notifications Sent** → User gets DM + admin channel notification
6. **All Automatic** → No manual intervention needed!

## 💡 Important Notes

### Environment Variables
All your secrets are stored securely:
- `DISCORD_TOKEN` - Bot token
- `MONGODB_URI` - Database connection
- `GUMROAD_ACCESS_TOKEN` - Gumroad API access

These are automatically available in deployment.

### Production URL
Your production URL is:
```
https://workspace-goatreceipts.replit.app
```

This URL:
- ✅ Works 24/7 when deployed
- ✅ Stays the same even after redeploying
- ✅ Is what Gumroad sends webhooks to

### Deployment Costs
- VM deployments require a paid Replit plan
- Check Replit pricing for current costs
- Deployment keeps your bot online 24/7

## 🚀 Ready to Deploy!

Your app is **100% ready for deployment**. All configuration is correct:

✅ Production runner configured  
✅ Both services integrated  
✅ Webhook URL updated in Gumroad  
✅ Database connections working  
✅ Discord bot operational  

**Just click the Deploy button and you're live!** 🎉
