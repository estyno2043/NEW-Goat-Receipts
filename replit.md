# Overview

This is a Discord bot application that generates and sends fake receipts via email. The bot allows users to create receipt templates for various brands and retailers through Discord slash commands and modals. It integrates with MongoDB for data storage, handles user authentication and subscriptions, and provides webhook functionality for external integrations.

The application serves as a receipt generator service where users can input product details, customize receipt templates, and receive professionally formatted receipts via email. It supports multiple brands including Apple, Amazon, Nike, Walmart, and many luxury brands.

## Recent Updates (October 2025)

### File Upload Feature
- **80 Brand-Specific File Upload Commands**: Users can now upload product images directly via Discord slash commands (e.g., `/nike`, `/adidas`, `/apple`)
- **Simplified User Experience**: Eliminated the need for manual image URL input in modals
- **Local File Persistence**: Images are saved to `attached_assets/uploaded_images/` with unique filenames
- **Automatic Cleanup**: Background task runs every 30 minutes to remove expired uploads (15-minute expiration)
- **Guild-Agnostic Design**: Works in any Discord server where the bot is present
- **Private Image Storage**: Uploaded files are re-uploaded to a private bot-only "receipt-image-storage" channel for persistent URLs
  - Channel is created automatically with permission overwrites (users cannot view)
  - Fallback to bot owner DM if channel creation fails
  - Images NEVER displayed in public channels
  - Discord CDN URLs remain valid from private storage
- **Existing Modal Integration**: Upload commands directly invoke existing brand-specific modals (e.g., applemodal)
  - Preserves original sender names, subjects, and placeholder replacement logic
  - Image URL field becomes optional when image is uploaded
  - Auto-detects and uses uploaded images without user intervention
- **Error Handling**: Users receive clear error messages if image upload or persistence fails

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Bot Framework
- **Discord.py**: Core Discord bot framework handling commands, events, and UI interactions
- **Modal-based UI**: Extensive use of Discord modals for multi-step form collection
- **Command Structure**: Organized command system with separate modules for admin and guild management

## Data Storage
- **MongoDB**: Primary database using custom MongoDB manager for user data, subscriptions, and configurations
- **SQLite**: Secondary database for license management, user details, and guild configurations  
- **JSON Files**: File-based storage for valid/used keys, license backups, and configuration data

## Email System
- **Multiple Email Providers**: SMTP integration with Gmail accounts for different brands
- **Spoofed Email Support**: Custom spoofed email implementation for authentic-looking receipts
- **Template Engine**: HTML template system for receipt generation with dynamic content replacement

## Authentication & Authorization
- **License-based Access**: Time-limited access keys with different subscription tiers (1-day, 3-day, lifetime, etc.)
- **User Whitelisting**: File-based whitelist system for authorized users
- **Guild Access Control**: Server-specific permissions and role management
- **Rate Limiting**: Built-in rate limiting for receipt generation to prevent abuse

## Receipt Generation System
- **Brand Templates**: Modular template system supporting 50+ retail brands
- **Web Scraping**: Proxy-based scraping for product information from brand websites
- **Image Processing**: Utilities for fixing and processing receipt images
- **Template Variables**: Dynamic replacement of user details, prices, and product information

## External Integrations
- **Webhook Server**: Flask-based webhook server for external API integrations
- **Proxy Services**: Integration with Zyte proxy service for web scraping
- **Gumroad Integration**: Fully automated purchase system with webhook support
  - **Flexible User Identification**: Supports both Discord ID (recommended) and username lookup
    - Discord ID: Direct, instant, 100% reliable lookup (all numeric)
    - Username: Searches by member.name, display_name, and global_name (case-insensitive)
  - Seamless access granting based on product purchase
  - Automatic notifications to purchases channel and user DMs
  - Role assignment (Customer, Client, Subscription roles)
  - Product-to-subscription mapping for different tiers with exact Gumroad product name matching
    - GOAT 1-month subscription → 1 month access
    - Goat 3 Months Subscription → 3 months access
    - Lite Subscription → Lite (7 receipts, 30 days)
    - Guild Subscription - 1 month → Guild access (30 days)
    - Receipt Editor Add-on → Roles-only product
  - **24/7 Availability**: Configured for VM deployment to run continuously even when Replit IDE is closed
    - Both Discord bot and webhook server run in same process for shared bot instance access
    - Production runner (run_production.py) uses threading to start both services
    - Ensures webhook can look up Discord users and grant access automatically
  - **Editor Add-on Product**: Special roles-only product (goatreceipts.gumroad.com/l/rfbztg)
    - Assigns two specific roles: 1412498223842721903 and 1427636166126993418
    - No license/expiry tracking - purely for role management
    - Sends purchase notifications to user DM and purchases channel
    - Processed through dedicated notification handler
  - **Fallback Notification System**: When incorrect Discord username is entered during checkout
    - Queues notification to MongoDB gumroad_notifications collection
    - Background processor checks every 5 seconds for pending notifications
    - Sends detailed embed to fallback channel (1427592513299943535) including:
      - Username entered by customer
      - Purchase email address
      - Subscription type and duration
      - Product name and price
      - Purchase timestamp
    - Enables manual verification and access granting by administrators
  - **Improved Member Lookup**: Enhanced Discord member detection system (Oct 2025)
    - Primary: Checks Discord member cache using guild.get_member() for fast lookups
    - Fallback: Fetches directly from Discord API using guild.fetch_member() for reliability
    - Handles async operations properly within Flask webhook sync context
    - 10-second timeout for API fetches to prevent hanging requests
    - Graceful error handling for NotFound and timeout exceptions

## Architecture Patterns
- **Modular Design**: Separate modules for different brands, commands, and utilities
- **Error Handling**: Comprehensive error handling with user-friendly feedback
- **Async Processing**: Asynchronous operations for email sending and database operations
- **Background Tasks**: Notification processing and periodic cleanup tasks

# External Dependencies

## Third-party Services
- **Discord API**: Core platform for bot interactions and user interface
- **MongoDB Atlas**: Cloud database service for persistent data storage
- **Gmail SMTP**: Multiple Gmail accounts for email delivery across different brands
- **Zyte Proxy Service**: Web scraping proxy service for product information extraction

## Python Libraries
- **discord.py**: Discord bot framework and UI components
- **pymongo**: MongoDB database driver
- **flask**: Web server for webhook endpoints
- **requests**: HTTP client for web scraping and API calls
- **beautifulsoup4**: HTML parsing for web scraping
- **smtplib**: SMTP email sending functionality
- **sqlite3**: Local database operations
- **pystyle**: Console output styling

## Development Tools
- **dotenv**: Environment variable management
- **logging**: Application logging and debugging
- **asyncio**: Asynchronous programming support