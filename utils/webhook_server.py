
import json
import asyncio
import logging
import aiohttp
from aiohttp import web
from utils.sellauth_webhook import SellAuthWebhook

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class WebhookServer:
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.sellauth_webhook = SellAuthWebhook(bot)
        self.setup_routes()
        
    def setup_routes(self):
        """Set up the webhook routes"""
        self.app.router.add_post('/webhook/sellauth', self.handle_sellauth_webhook)
        self.app.router.add_get('/', self.handle_healthcheck)
        
    async def handle_healthcheck(self, request):
        """Simple health check endpoint"""
        return web.Response(text="Webhook server is running!")
        
    async def handle_sellauth_webhook(self, request):
        """Handle SellAuth webhook requests"""
        try:
            # Get signature from headers if available
            signature = request.headers.get('X-SellAuth-Signature')
            
            # Get JSON payload
            payload = await request.text()
            data = json.loads(payload)
            
            # Process the webhook
            success, message = await self.sellauth_webhook.process_webhook(data, signature)
            
            if success:
                return web.Response(text=message, status=200)
            else:
                return web.Response(text=message, status=400)
                
        except json.JSONDecodeError:
            return web.Response(text="Invalid JSON payload", status=400)
        except Exception as e:
            logging.error(f"Error handling webhook: {str(e)}")
            return web.Response(text=f"Server error: {str(e)}", status=500)
    
    async def start(self, host='0.0.0.0', port=8080):
        """Start the webhook server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logging.info(f"Webhook server started on {host}:{port}")
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour
