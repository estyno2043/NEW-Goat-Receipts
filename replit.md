# Overview

This is a Discord bot application that generates and sends fake receipts via email. The bot allows users to create receipt templates for various brands and retailers through Discord slash commands and modals. It integrates with MongoDB for data storage, handles user authentication and subscriptions, and provides webhook functionality for external integrations.

The application serves as a receipt generator service where users can input product details, customize receipt templates, and receive professionally formatted receipts via email. It supports multiple brands including Apple, Amazon, Nike, Walmart, and many luxury brands.

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
- **Gumroad Integration**: Webhook support for payment processing (configured but not fully implemented)

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