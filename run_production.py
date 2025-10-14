#!/usr/bin/env python3
"""
Production runner that starts both Discord bot and webhook server
This ensures both services run when deployed
"""

import os
import sys
import threading
import subprocess
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_webhook_server():
    """Run the Flask webhook server"""
    logging.info("Starting webhook server on port 5000...")
    try:
        subprocess.run([sys.executable, "webhook_server.py"], check=True)
    except Exception as e:
        logging.error(f"Webhook server crashed: {e}")
        sys.exit(1)

def run_discord_bot():
    """Run the Discord bot"""
    logging.info("Starting Discord bot...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except Exception as e:
        logging.error(f"Discord bot crashed: {e}")
        sys.exit(1)

def main():
    """Start both services"""
    logging.info("=" * 60)
    logging.info("GOAT Receipts Production Server")
    logging.info("=" * 60)
    
    # Display production URL
    repl_slug = os.environ.get('REPL_SLUG', '')
    repl_owner = os.environ.get('REPL_OWNER', '')
    
    if repl_slug and repl_owner:
        prod_url = f"https://{repl_slug}-{repl_owner.lower()}.replit.app"
        logging.info(f"Production URL: {prod_url}")
        logging.info(f"Webhook endpoint: {prod_url}/webhook/gumroad")
    else:
        logging.info("Running in development mode")
    
    logging.info("Starting services...")
    
    # Start webhook server in a thread
    webhook_thread = threading.Thread(target=run_webhook_server, daemon=False)
    webhook_thread.start()
    
    # Give Flask time to start
    time.sleep(3)
    
    # Start Discord bot in a thread
    bot_thread = threading.Thread(target=run_discord_bot, daemon=False)
    bot_thread.start()
    
    logging.info("Both services started successfully!")
    logging.info("Press Ctrl+C to stop")
    
    try:
        # Keep the main thread alive
        webhook_thread.join()
        bot_thread.join()
    except KeyboardInterrupt:
        logging.info("Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()