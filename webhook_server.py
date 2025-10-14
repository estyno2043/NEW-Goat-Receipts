from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from datetime import datetime, timedelta
import json
import logging
import os
import asyncio
import discord
from utils.mongodb_manager import mongo_manager

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

# Configure logging
logging.basicConfig(level=logging.INFO)

# Global bot instance variable
bot_instance = None

def set_bot_instance(bot):
    """Set the bot instance for admin operations"""
    global bot_instance
    bot_instance = bot

@app.route('/api/grant-access', methods=['POST'])
def grant_access():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        user_id = data.get('userId')
        username = data.get('username', 'Unknown User')
        guild_id = data.get('guildId')
        guild_name = data.get('guildName', 'Unknown Guild')
        access_duration = data.get('accessDuration', 1)  # Default 1 day
        timestamp = data.get('timestamp', str(int(datetime.now().timestamp())))
        source = data.get('source', 'invite-tracker')

        if not user_id or not guild_id:
            return jsonify({'error': 'Missing required fields: userId, guildId'}), 400

        if not access_duration or access_duration <= 0:
            return jsonify({'error': 'Invalid accessDuration'}), 400

        logging.info(f"Granting {access_duration} days access to user {user_id} ({username}) in guild {guild_id} ({guild_name})")

        # Calculate expiry date
        expiry_date = datetime.now() + timedelta(days=access_duration)
        expiry_str = expiry_date.strftime('%Y-%m-%d %H:%M:%S')

        # Check if this is the main guild or a configured guild
        with open("config.json", "r") as f:
            config = json.load(f)
            main_guild_id = config.get("guild_id", "1412488621293961226")

        is_main_guild = (str(guild_id) == main_guild_id)

        if is_main_guild:
            # For main guild, create a license
            license_data = {
                "key": f"invite-access-{user_id}-{timestamp}",
                "expiry": expiry_date.strftime('%d/%m/%Y %H:%M:%S'),
                "subscription_type": f"{access_duration}day",
                "is_active": True,
                "emailtf": "False",
                "credentialstf": "False",
                "granted_by": source,
                "granted_at": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                "username": username,
                "guild_name": guild_name
            }

            success = mongo_manager.create_or_update_license(user_id, license_data)

            if not success:
                return jsonify({'error': 'Failed to create license'}), 500
        else:
            # For other guilds, save server access
            success = mongo_manager.save_server_access(
                guild_id,
                user_id,
                source,
                f"{access_duration} Days",
                expiry_str
            )

            if not success:
                return jsonify({'error': 'Failed to save server access'}), 500

            # Also create guild-specific license
            license_data = {
                "key": f"invite-guild-{guild_id}-{user_id}-{timestamp}",
                "expiry": expiry_date.strftime('%d/%m/%Y %H:%M:%S'),
                "subscription_type": f"{access_duration}day",
                "redeemed": True,
                "redeemed_at": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                "granted_by": source,
                "username": username,
                "guild_name": guild_name
            }

            mongo_manager.save_guild_user_license(guild_id, user_id, license_data)

        # Send notification (similar to purchase notifications)
        try:
            import asyncio
            import discord
            from utils.mongodb_manager import mongo_manager as db_manager

            # Try to get bot instance and send notification
            def send_notification():
                try:
                    # This will be handled by the bot's notification system
                    # Store notification data for the bot to pick up
                    notification_data = {
                        "type": "access_granted",
                        "user_id": str(user_id),
                        "username": username,
                        "guild_id": str(guild_id),
                        "guild_name": guild_name,
                        "access_duration": access_duration,
                        "expiry_date": expiry_date.isoformat(),
                        "source": source,
                        "timestamp": datetime.now().isoformat()
                    }

                    # Store in database for bot to process
                    db = db_manager.get_database()
                    if db:
                        db.notifications.insert_one(notification_data)
                        logging.info(f"Notification queued for user {user_id}")

                except Exception as e:
                    logging.error(f"Error queuing notification: {e}")

            send_notification()

        except Exception as e:
            logging.warning(f"Could not send notification: {e}")
            # Don't fail the request if notification fails

        logging.info(f"Successfully granted access to user {user_id}")

        return jsonify({
            'success': True,
            'message': f'Access granted for {access_duration} days',
            'expiryDate': expiry_date.isoformat(),
            'userId': user_id,
            'guildId': guild_id,
            'username': username,
            'guildName': guild_name,
            'expiresAt': expiry_date.isoformat()
        }), 200

    except Exception as e:
        logging.error(f"Error granting access: {str(e)}")
        return jsonify({'error': f'Failed to grant access: {str(e)}'}), 500

@app.route('/webhook/gumroad', methods=['POST'])
def gumroad_webhook():
    """Handle Gumroad purchase webhooks for automatic access granting"""
    try:
        # Import mongo_manager at function start so it's available everywhere
        from utils.mongodb_manager import mongo_manager
        
        # Get the raw data
        data = request.form.to_dict() if request.form else request.get_json()
        
        if not data:
            logging.error("No data received from Gumroad webhook")
            return jsonify({'error': 'No data provided'}), 400
        
        logging.info(f"Received Gumroad webhook: {data}")
        
        # Extract purchase information
        product_name = data.get('product_name', '')
        product_permalink = data.get('product_permalink', '')
        price = data.get('price', '')
        email = data.get('email', '')
        sale_id = data.get('sale_id', '')
        gumroad_license_key = data.get('license_key', '')  # Get Gumroad's license key
        
        # Get Discord username or ID from custom field (Gumroad sends it with bracket notation)
        # Try multiple variations of the field name
        discord_identifier = None
        for key in data.keys():
            # Look for any key containing "discord" (could be username or ID)
            if 'discord' in key.lower():
                discord_identifier = data.get(key, '').strip()
                if discord_identifier:
                    logging.info(f"Found Discord identifier '{discord_identifier}' in field '{key}'")
                    break
        
        # Fallback to standard field names
        if not discord_identifier:
            discord_identifier = (
                data.get('custom_fields[Discord Username]', '') or
                data.get('custom_fields[Discord ID]', '') or
                data.get('Discord Username', '') or 
                data.get('Discord ID', '') or
                data.get('discord_username', '') or
                data.get('discord_id', '') or 
                data.get('custom_fields', {}).get('Discord Username', '') or
                data.get('custom_fields', {}).get('Discord ID', '')
            )
        
        # If custom fields is a string, try to parse it
        if isinstance(data.get('custom_fields'), str):
            try:
                import json as json_lib
                custom_fields = json_lib.loads(data.get('custom_fields'))
                discord_identifier = discord_identifier or custom_fields.get('Discord Username', '') or custom_fields.get('Discord ID', '')
            except:
                pass
        
        if not discord_identifier:
            logging.error(f"No Discord username or ID found in webhook data: {data}")
            return jsonify({'error': 'Discord username or ID not provided'}), 400
        
        logging.info(f"Processing purchase for Discord identifier: {discord_identifier}")
        
        # Map product to subscription type and duration using exact Gumroad product names
        subscription_mapping = {
            # Exact product name matches (from Gumroad)
            'GOAT 1-month subscription': {'type': '1month', 'days': 30},
            'Goat 3 Months Subscription': {'type': '3month', 'days': 90},
            'Lite Subscription': {'type': 'lite', 'days': 30},
            'Guild Subscription - 1 month': {'type': 'guild_30days', 'days': 30},
            'Receipt Editor Add-on': {'type': 'editor_addon', 'days': 0, 'roles_only': True},
            
            # Legacy/fallback patterns
            '3 day': {'type': '3day', 'days': 3},
            '14 day': {'type': '14day', 'days': 14},
            '1 month': {'type': '1month', 'days': 30},
            '1-month': {'type': '1month', 'days': 30},
            '3 month': {'type': '3month', 'days': 90},
            'lifetime': {'type': 'lifetime', 'days': 36500},
            'guild': {'type': 'guild_30days', 'days': 30},
            'lite': {'type': 'lite', 'days': 30},
            'editor': {'type': 'editor_addon', 'days': 0, 'roles_only': True}
        }
        
        # Determine subscription type - try exact match first, then partial match
        subscription_info = None
        product_name_lower = product_name.lower()
        
        # First try exact match
        for product_key, info in subscription_mapping.items():
            if product_key.lower() == product_name_lower:
                subscription_info = info
                logging.info(f"Exact product match: '{product_name}' -> {info['type']}")
                break
        
        # Then try partial match
        if not subscription_info:
            for product_key, info in subscription_mapping.items():
                if product_key.lower() in product_name_lower:
                    subscription_info = info
                    logging.info(f"Partial product match: '{product_name}' contains '{product_key}' -> {info['type']}")
                    break
        
        # Last resort: use price to determine
        if not subscription_info:
            logging.warning(f"No product match for '{product_name}', using price-based detection")
            try:
                price_val = float(price)
                if price_val <= 5:
                    subscription_info = {'type': '3day', 'days': 3}
                elif price_val <= 10:
                    subscription_info = {'type': '14day', 'days': 14}
                elif price_val <= 20:
                    subscription_info = {'type': '1month', 'days': 30}
                elif price_val <= 50:
                    subscription_info = {'type': '3month', 'days': 90}
                else:
                    subscription_info = {'type': 'lifetime', 'days': 36500}
                logging.info(f"Price-based match: ${price} -> {subscription_info['type']}")
            except:
                subscription_info = {'type': '1month', 'days': 30}  # Default
                logging.warning(f"Failed to parse price, using default 1month")
        
        subscription_type = subscription_info['type']
        days = subscription_info['days']
        
        # Calculate expiry
        expiry_date = datetime.now() + timedelta(days=days)
        expiry_str = expiry_date.strftime('%d/%m/%Y %H:%M:%S')
        
        # Load config to get guild ID
        with open("config.json", "r") as f:
            config = json.load(f)
            guild_id = int(config.get("guild_id", "1412488621293961226"))
        
        # Find user in guild by ID or username
        user_id = None
        username_display = discord_identifier
        
        # Check if the identifier is a Discord ID (all digits)
        is_discord_id = discord_identifier.isdigit()
        
        if bot_instance:
            guild = bot_instance.get_guild(guild_id)
            if guild:
                if is_discord_id:
                    # Direct ID lookup - much faster and more reliable!
                    logging.info(f"Looking up user by Discord ID: {discord_identifier}")
                    member = guild.get_member(int(discord_identifier))
                    if member:
                        user_id = str(member.id)
                        username_display = member.display_name
                        logging.info(f"Found user {username_display} (ID: {user_id}) by direct ID lookup")
                    else:
                        logging.warning(f"User ID {discord_identifier} not found in guild")
                else:
                    # Username search (slower, less reliable)
                    logging.info(f"Searching for user '{discord_identifier}' by username in guild with {len(guild.members)} members")
                    
                    # Search for user by username (case-insensitive)
                    # Check: member.name (username), member.display_name (server nickname), member.global_name (display name)
                    for member in guild.members:
                        # Get all possible name variations
                        member_username = member.name.lower() if member.name else ""
                        member_display = member.display_name.lower() if member.display_name else ""
                        member_global = member.global_name.lower() if hasattr(member, 'global_name') and member.global_name else ""
                        search_name = discord_identifier.lower()
                        
                        if (member_username == search_name or 
                            member_display == search_name or 
                            member_global == search_name):
                            user_id = str(member.id)
                            username_display = member.display_name
                            logging.info(f"Found user {username_display} (ID: {user_id}, username: {member.name}) in guild")
                            break
        
        if not user_id:
            logging.error(f"Could not find user {discord_identifier} in guild {guild_id}")
            
            # Queue a notification for user not found
            try:
                db = mongo_manager.get_database()
                
                notification_data = {
                    "type": "gumroad_user_not_found",
                    "discord_username": discord_identifier,
                    "email": email,
                    "subscription_type": subscription_type,
                    "product_name": product_name,
                    "price": price,
                    "timestamp": datetime.now().isoformat(),
                    "sale_id": sale_id,
                    "license_key": gumroad_license_key,  # Include the license key for manual redemption
                    "processed": False
                }
                
                result = db.gumroad_notifications.insert_one(notification_data)
                logging.info(f"Queued user-not-found notification for {discord_identifier}")
            except Exception as e:
                logging.error(f"Error queuing user-not-found notification: {e}")
            
            return jsonify({'error': f'User {discord_identifier} not found in Discord server'}), 404
        
        # Check if this is a roles-only product (Editor Add-on)
        is_roles_only = subscription_info.get('roles_only', False)
        
        if is_roles_only:
            # Editor Add-on: assign roles only, no license
            logging.info(f"Processing Editor Add-on purchase for user {user_id}")
            
            editor_roles = [1412498223842721903, 1427636166126993418]
            
            # Queue role assignment notification for bot to handle asynchronously
            notification_data = {
                "type": "gumroad_editor_addon",
                "user_id": user_id,
                "username": username_display,
                "discord_username": discord_identifier,
                "subscription_type": subscription_type,
                "product_name": product_name,
                "price": price,
                "email": email,
                "roles_to_assign": editor_roles,
                "guild_id": guild_id,
                "timestamp": datetime.now().isoformat()
            }
            
            db = mongo_manager.get_database()
            if db is not None:
                db.notifications.insert_one(notification_data)
                logging.info(f"Editor Add-on notification queued for user {user_id}")
            
            return jsonify({
                'success': True,
                'message': f'Editor Add-on roles will be assigned to {discord_identifier}',
                'user_id': user_id,
                'subscription_type': subscription_type,
                'roles_to_assign': editor_roles
            }), 200
        
        # Automatically redeem the Gumroad license key (for non-roles-only products)
        if gumroad_license_key:
            logging.info(f"Attempting to auto-redeem Gumroad license key for user {user_id}: {gumroad_license_key}")
            
            try:
                from utils.key_manager import KeyManager
                key_manager = KeyManager()
                
                # First, we need to add the Gumroad key to our valid keys with the subscription info
                import json as json_lib
                
                # Load valid keys
                try:
                    with open("data/valid_keys.json", "r") as f:
                        valid_keys = json_lib.load(f)
                except:
                    valid_keys = {}
                
                # Add the Gumroad license key to valid keys
                valid_keys[gumroad_license_key] = {
                    "subscription_type": subscription_type,
                    "expiry_date": expiry_str,
                    "source": "gumroad",
                    "sale_id": sale_id
                }
                
                # Save updated valid keys
                with open("data/valid_keys.json", "w") as f:
                    json_lib.dump(valid_keys, f, indent=2)
                
                logging.info(f"Added Gumroad key {gumroad_license_key} to valid keys")
                
                # Now redeem it for the user
                result = key_manager.redeem_key(gumroad_license_key, user_id)
                
                if result["success"]:
                    logging.info(f"Successfully auto-redeemed Gumroad key for user {user_id}")
                else:
                    logging.error(f"Failed to auto-redeem key: {result.get('message')}")
                    # Fall back to manual license creation if redemption fails
                    raise Exception("Key redemption failed")
                    
            except Exception as redeem_error:
                logging.error(f"Error during auto-redemption: {redeem_error}, falling back to manual license creation")
                
                # Fallback: Create license data manually
                license_key = f"gumroad-{sale_id}-{user_id}"
                license_data = {
                    "key": license_key,
                    "expiry": expiry_str,
                    "subscription_type": subscription_type,
                    "is_active": True,
                    "emailtf": "False",
                    "credentialstf": "False",
                    "source": "gumroad",
                    "purchase_email": email,
                    "product_name": product_name,
                    "sale_id": sale_id,
                    "gumroad_license_key": gumroad_license_key
                }
                
                # Add receipt count for lite subscription
                if subscription_type == "lite":
                    license_data["receipt_count"] = 0
                    license_data["max_receipts"] = 7
                
                # Save license to MongoDB
                success = mongo_manager.create_or_update_license(user_id, license_data)
                
                if not success:
                    logging.error(f"Failed to create license for user {user_id}")
                    return jsonify({'error': 'Failed to create license'}), 500
        else:
            logging.warning("No Gumroad license key found in webhook data, creating manual license")
            
            # Create license data manually (old method)
            license_key = f"gumroad-{sale_id}-{user_id}"
            license_data = {
                "key": license_key,
                "expiry": expiry_str,
                "subscription_type": subscription_type,
                "is_active": True,
                "emailtf": "False",
                "credentialstf": "False",
                "source": "gumroad",
                "purchase_email": email,
                "product_name": product_name,
                "sale_id": sale_id
            }
            
            # Add receipt count for lite subscription
            if subscription_type == "lite":
                license_data["receipt_count"] = 0
                license_data["max_receipts"] = 7
            
            # Save license to MongoDB
            success = mongo_manager.create_or_update_license(user_id, license_data)
            
            if not success:
                logging.error(f"Failed to create license for user {user_id}")
                return jsonify({'error': 'Failed to create license'}), 500
        
        # Queue notification for bot to send
        notification_data = {
            "type": "gumroad_purchase",
            "user_id": user_id,
            "username": username_display,
            "discord_username": discord_identifier,
            "subscription_type": subscription_type,
            "expiry_date": expiry_str,
            "product_name": product_name,
            "price": price,
            "email": email,
            "timestamp": datetime.now().isoformat()
        }
        
        db = mongo_manager.get_database()
        if db is not None:
            db.notifications.insert_one(notification_data)
            logging.info(f"Purchase notification queued for user {user_id}")
        
        logging.info(f"Successfully granted {subscription_type} access to user {user_id} via Gumroad")
        
        return jsonify({
            'success': True,
            'message': f'Access granted to {discord_identifier}',
            'user_id': user_id,
            'subscription_type': subscription_type,
            'expires': expiry_str
        }), 200
        
    except Exception as e:
        logging.error(f"Error processing Gumroad webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to process webhook: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/api/check-access/<user_id>', methods=['GET'])
def check_access(user_id):
    """Check if a user has active access"""
    try:
        guild_id = request.args.get('guildId')

        if not guild_id:
            return jsonify({'error': 'guildId parameter required'}), 400

        # Check if this is the main guild
        with open("config.json", "r") as f:
            config = json.load(f)
            main_guild_id = config.get("guild_id", "1412488621293961226")

        is_main_guild = (str(guild_id) == main_guild_id)

        if is_main_guild:
            # Check main guild license
            license_doc = mongo_manager.get_license(user_id)
            if license_doc and license_doc.get("is_active"):
                expiry_str = license_doc.get("expiry")
                if expiry_str:
                    try:
                        expiry_date = datetime.strptime(expiry_str, '%d/%m/%Y %H:%M:%S')
                        if datetime.now() < expiry_date:
                            return jsonify({
                                'hasAccess': True,
                                'expiryDate': expiry_date.isoformat(),
                                'subscriptionType': license_doc.get("subscription_type")
                            }), 200
                    except ValueError:
                        pass
        else:
            # Check guild-specific access
            server_access = mongo_manager.get_server_access(guild_id, user_id)
            if server_access:
                expiry_str = server_access.get("expiry")
                if expiry_str:
                    try:
                        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S')
                        if datetime.now() < expiry_date:
                            return jsonify({
                                'hasAccess': True,
                                'expiryDate': expiry_date.isoformat(),
                                'accessType': server_access.get("access_type")
                            }), 200
                    except ValueError:
                        pass

        return jsonify({'hasAccess': False}), 200

    except Exception as e:
        logging.error(f"Error checking access: {str(e)}")
        return jsonify({'error': f'Failed to check access: {str(e)}'}), 500

# Admin Dashboard Routes

def require_admin_auth():
    """Check if user is authenticated as admin"""
    if 'user_id' not in session:
        return False
    
    # Load owner ID from config
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            owner_id = config.get("owner_id", "1412486645953069076")
        return str(session['user_id']) == owner_id
    except:
        return False

@app.route('/admin', methods=['GET'])
def admin_dashboard():
    """Main admin dashboard"""
    if not require_admin_auth():
        return redirect(url_for('admin_login'))
    
    return render_template('admin_dashboard.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                owner_id = config.get("owner_id", "1412486645953069076")
            
            if str(user_id) == owner_id:
                session['user_id'] = user_id
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template('login.html', error="Invalid User ID. Access denied.")
        except Exception as e:
            return render_template('login.html', error="Configuration error. Please try again.")
    
    return render_template('login.html')

@app.route('/admin/logout', methods=['GET'])
def admin_logout():
    """Admin logout"""
    session.pop('user_id', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/assign-role', methods=['POST'])
def admin_assign_role():
    """Assign the specific role to the alt account"""
    if not require_admin_auth():
        return redirect(url_for('admin_login'))
    
    if not bot_instance:
        return render_template('admin_dashboard.html', message="Bot instance not available", success=False)
    
    try:
        # Load config
        with open("config.json", "r") as f:
            config = json.load(f)
            guild_id = int(config.get("guild_id", "1412488621293961226"))
        
        # Target user and role IDs
        target_user_id = 1392897052924444845  # Your alt account
        target_role_id = 1412537344585633922  # The role you want to assign
        
        # Get the guild and user
        guild = bot_instance.get_guild(guild_id)
        if not guild:
            return render_template('admin_dashboard.html', 
                                 message=f"Guild with ID {guild_id} not found", success=False)
        
        # Try to get member from cache first, then try fetching
        user = guild.get_member(target_user_id)
        if not user:
            # If not in cache, create a task to fetch the user
            def get_user_sync():
                async def fetch_user():
                    try:
                        return await guild.fetch_member(target_user_id)
                    except discord.NotFound:
                        return None
                    except Exception:
                        return None
                
                try:
                    if hasattr(bot_instance, 'loop') and bot_instance.loop.is_running():
                        future = asyncio.run_coroutine_threadsafe(fetch_user(), bot_instance.loop)
                        return future.result(timeout=5)
                    else:
                        return None
                except:
                    return None
            
            user = get_user_sync()
            
            if not user:
                return render_template('admin_dashboard.html', 
                                     message=f"User 'brazyfn_' (ID: {target_user_id}) not found in guild {guild.name}. Make sure they are in the server and the bot has permission to see them.", success=False)
        
        role = discord.utils.get(guild.roles, id=target_role_id)
        if not role:
            return render_template('admin_dashboard.html', 
                                 message=f"Role with ID {target_role_id} not found", success=False)
        
        # Check if user already has the role
        if role in user.roles:
            return render_template('admin_dashboard.html', 
                                 message=f"{user.display_name} already has the role '{role.name}'", success=False)
        
        # Check bot permissions and role hierarchy
        bot_member = guild.get_member(bot_instance.user.id)
        if not bot_member:
            return render_template('admin_dashboard.html', 
                                 message="Bot member not found in guild", success=False)
        
        # Check if bot has manage_roles permission
        if not bot_member.guild_permissions.manage_roles:
            return render_template('admin_dashboard.html', 
                                 message="Bot doesn't have 'Manage Roles' permission", success=False)
        
        # Check role hierarchy - bot's highest role must be higher than the target role
        bot_top_role = bot_member.top_role
        if role.position >= bot_top_role.position:
            return render_template('admin_dashboard.html', 
                                 message=f"Cannot assign role '{role.name}' (position {role.position}). Bot's highest role '{bot_top_role.name}' is at position {bot_top_role.position}. The role to assign must be lower in the hierarchy.", success=False)
        
        # Assign the role using the bot's loop
        async def assign_role():
            try:
                await user.add_roles(role)
                return True, f"Successfully assigned role '{role.name}' to {user.display_name}"
            except Exception as e:
                return False, f"Error assigning role: {str(e)}"
        
        # Run the async function in the bot's event loop
        if bot_instance.loop.is_running():
            # Create a future and run it in the bot's loop
            future = asyncio.run_coroutine_threadsafe(assign_role(), bot_instance.loop)
            success, message = future.result(timeout=10)
        else:
            # Fallback to new loop if bot loop isn't running
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, message = loop.run_until_complete(assign_role())
            loop.close()
        
        return render_template('admin_dashboard.html', message=message, success=success)
        
    except Exception as e:
        logging.error(f"Error in role assignment: {e}")
        return render_template('admin_dashboard.html', 
                             message=f"Error: {str(e)}", success=False)

@app.route('/admin/remove-role', methods=['POST'])
def admin_remove_role():
    """Remove the specific role from the alt account"""
    if not require_admin_auth():
        return redirect(url_for('admin_login'))
    
    if not bot_instance:
        return render_template('admin_dashboard.html', message="Bot instance not available", success=False)
    
    try:
        # Load config
        with open("config.json", "r") as f:
            config = json.load(f)
            guild_id = int(config.get("guild_id", "1412488621293961226"))
        
        # Target user and role IDs
        target_user_id = 1392897052924444845  # Your alt account
        target_role_id = 1412537344585633922  # The role you want to remove
        
        # Get the guild and user
        guild = bot_instance.get_guild(guild_id)
        if not guild:
            return render_template('admin_dashboard.html', 
                                 message=f"Guild with ID {guild_id} not found", success=False)
        
        # Try to get member from cache first, then try fetching
        user = guild.get_member(target_user_id)
        if not user:
            # If not in cache, create a task to fetch the user
            def get_user_sync():
                async def fetch_user():
                    try:
                        return await guild.fetch_member(target_user_id)
                    except discord.NotFound:
                        return None
                    except Exception:
                        return None
                
                try:
                    if hasattr(bot_instance, 'loop') and bot_instance.loop.is_running():
                        future = asyncio.run_coroutine_threadsafe(fetch_user(), bot_instance.loop)
                        return future.result(timeout=5)
                    else:
                        return None
                except:
                    return None
            
            user = get_user_sync()
            
            if not user:
                return render_template('admin_dashboard.html', 
                                     message=f"User 'brazyfn_' (ID: {target_user_id}) not found in guild {guild.name}. Make sure they are in the server and the bot has permission to see them.", success=False)
        
        role = discord.utils.get(guild.roles, id=target_role_id)
        if not role:
            return render_template('admin_dashboard.html', 
                                 message=f"Role with ID {target_role_id} not found", success=False)
        
        # Check if user has the role
        if role not in user.roles:
            return render_template('admin_dashboard.html', 
                                 message=f"{user.display_name} doesn't have the role '{role.name}'", success=False)
        
        # Remove the role
        async def remove_role():
            try:
                await user.remove_roles(role)
                return True, f"Successfully removed role '{role.name}' from {user.display_name}"
            except Exception as e:
                return False, f"Error removing role: {str(e)}"
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success, message = loop.run_until_complete(remove_role())
        loop.close()
        
        return render_template('admin_dashboard.html', message=message, success=success)
        
    except Exception as e:
        logging.error(f"Error in role removal: {e}")
        return render_template('admin_dashboard.html', 
                             message=f"Error: {str(e)}", success=False)

@app.route('/admin/custom-assign', methods=['POST'])
def admin_custom_assign():
    """Assign custom role to custom user"""
    if not require_admin_auth():
        return redirect(url_for('admin_login'))
    
    if not bot_instance:
        return render_template('admin_dashboard.html', message="Bot instance not available", success=False)
    
    try:
        user_id = int(request.form.get('user_id'))
        role_id = int(request.form.get('role_id'))
        
        # Load config
        with open("config.json", "r") as f:
            config = json.load(f)
            guild_id = int(config.get("guild_id", "1412488621293961226"))
        
        # Get the guild, user, and role
        guild = bot_instance.get_guild(guild_id)
        if not guild:
            return render_template('admin_dashboard.html', 
                                 message=f"Guild with ID {guild_id} not found", success=False)
        
        user = guild.get_member(user_id)
        if not user:
            # Try to fetch the member if not in cache
            def get_user_sync():
                async def fetch_user():
                    try:
                        return await guild.fetch_member(user_id)
                    except discord.NotFound:
                        return None
                    except Exception:
                        return None
                
                try:
                    if hasattr(bot_instance, 'loop') and bot_instance.loop.is_running():
                        future = asyncio.run_coroutine_threadsafe(fetch_user(), bot_instance.loop)
                        return future.result(timeout=5)
                    else:
                        return None
                except:
                    return None
            
            user = get_user_sync()
            
            if not user:
                return render_template('admin_dashboard.html', 
                                     message=f"User with ID {user_id} not found in guild {guild.name}", success=False)
        
        role = discord.utils.get(guild.roles, id=role_id)
        if not role:
            return render_template('admin_dashboard.html', 
                                 message=f"Role with ID {role_id} not found", success=False)
        
        # Check if user already has the role
        if role in user.roles:
            return render_template('admin_dashboard.html', 
                                 message=f"{user.display_name} already has the role '{role.name}'", success=False)
        
        # Assign the role
        async def assign_role():
            try:
                await user.add_roles(role)
                return True, f"Successfully assigned role '{role.name}' to {user.display_name}"
            except Exception as e:
                return False, f"Error assigning role: {str(e)}"
        
        # Run the async function in the bot's event loop
        if hasattr(bot_instance, 'loop') and bot_instance.loop.is_running():
            future = asyncio.run_coroutine_threadsafe(assign_role(), bot_instance.loop)
            success, message = future.result(timeout=10)
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success, message = loop.run_until_complete(assign_role())
            loop.close()
        
        return render_template('admin_dashboard.html', message=message, success=success)
        
    except ValueError:
        return render_template('admin_dashboard.html', 
                             message="Invalid User ID or Role ID format", success=False)
    except Exception as e:
        logging.error(f"Error in custom role assignment: {e}")
        return render_template('admin_dashboard.html', 
                             message=f"Error: {str(e)}", success=False)

@app.route('/admin/custom-remove', methods=['POST'])
def admin_custom_remove_role():
    """Remove a custom role from a user"""
    if not require_admin_auth():
        return redirect(url_for('admin_login'))
    
    if not bot_instance:
        return render_template('admin_dashboard.html', message="Bot instance not available", success=False)
    
    try:
        # Get form data
        target_user_id = int(request.form.get('user_id'))
        target_role_id = int(request.form.get('role_id'))
        
        # Load config
        with open("config.json", "r") as f:
            config = json.load(f)
            guild_id = int(config.get("guild_id", "1412488621293961226"))
        
        guild = bot_instance.get_guild(guild_id)
        if not guild:
            return render_template('admin_dashboard.html', 
                                 message=f"Guild with ID {guild_id} not found", success=False)
        
        # Get user with improved lookup (same method as other functions)
        user = guild.get_member(target_user_id)
        if not user:
            # If not in cache, create a task to fetch the user
            def get_user_sync():
                async def fetch_user():
                    try:
                        return await guild.fetch_member(target_user_id)
                    except discord.NotFound:
                        return None
                    except Exception:
                        return None
                
                try:
                    if hasattr(bot_instance, 'loop') and bot_instance.loop.is_running():
                        future = asyncio.run_coroutine_threadsafe(fetch_user(), bot_instance.loop)
                        return future.result(timeout=5)
                    else:
                        return None
                except:
                    return None
            
            user = get_user_sync()
            
            if not user:
                # Get detailed debugging info
                guild_member_count = guild.member_count
                bot_can_see_members = len(guild.members)
                guild_info = f"Guild: {guild.name} (ID: {guild.id}), Members cached: {bot_can_see_members}/{guild_member_count}"
                
                return render_template('admin_dashboard.html', 
                                     message=f"User with ID {target_user_id} not found in {guild_info}. This could be due to: 1) User not in server, 2) Bot missing member intents, 3) User has blocked the bot. Try the diagnostics to check bot permissions.", success=False)
        
        role = discord.utils.get(guild.roles, id=target_role_id)
        if not role:
            return render_template('admin_dashboard.html', 
                                 message=f"Role with ID {target_role_id} not found", success=False)
        
        # Check if user doesn't have the role
        if role not in user.roles:
            return render_template('admin_dashboard.html', 
                                 message=f"{user.display_name} doesn't have the role '{role.name}'", success=False)
        
        # Check bot permissions and role hierarchy
        bot_member = guild.get_member(bot_instance.user.id)
        if not bot_member:
            return render_template('admin_dashboard.html', 
                                 message="Bot member not found in guild", success=False)
        
        # Check if bot has manage_roles permission
        if not bot_member.guild_permissions.manage_roles:
            return render_template('admin_dashboard.html', 
                                 message="Bot doesn't have 'Manage Roles' permission", success=False)
        
        # Check role hierarchy - bot's highest role must be higher than the target role
        bot_top_role = bot_member.top_role
        if role.position >= bot_top_role.position:
            return render_template('admin_dashboard.html', 
                                 message=f"Cannot remove role '{role.name}' (position {role.position}). Bot's highest role '{bot_top_role.name}' is at position {bot_top_role.position}. The role to remove must be lower in the hierarchy.", success=False)
        
        # Remove the role using the bot's loop
        async def remove_role():
            try:
                await user.remove_roles(role, reason="Admin dashboard role removal")
                return True, None
            except Exception as e:
                return False, str(e)
        
        # Execute the async function in the bot's event loop
        future = asyncio.run_coroutine_threadsafe(remove_role(), bot_instance.loop)
        success, error = future.result(timeout=10)
        
        if success:
            return render_template('admin_dashboard.html', 
                                 message=f"Successfully removed role '{role.name}' from {user.display_name}!", success=True)
        else:
            return render_template('admin_dashboard.html', 
                                 message=f"Error removing role: {error}", success=False)
    
    except ValueError:
        return render_template('admin_dashboard.html', 
                             message="Invalid User ID or Role ID. Please enter valid numbers.", success=False)
    except Exception as e:
        logging.error(f"Error in custom role removal: {e}")
        return render_template('admin_dashboard.html', 
                             message=f"Error: {str(e)}", success=False)

@app.route('/admin/diagnostics', methods=['GET'])
def admin_diagnostics():
    """Get bot diagnostics including permissions and role hierarchy"""
    if not require_admin_auth():
        return redirect(url_for('admin_login'))
    
    if not bot_instance:
        return render_template('admin_dashboard.html', message="Bot instance not available", success=False)
    
    try:
        # Load config
        with open("config.json", "r") as f:
            config = json.load(f)
            guild_id = int(config.get("guild_id", "1412488621293961226"))
        
        guild = bot_instance.get_guild(guild_id)
        if not guild:
            return render_template('admin_dashboard.html', 
                                 message=f"Guild with ID {guild_id} not found", success=False)
        
        bot_member = guild.get_member(bot_instance.user.id)
        if not bot_member:
            return render_template('admin_dashboard.html', 
                                 message="Bot member not found in guild", success=False)
        
        # Get target role info
        target_role_id = 1412537344585633922
        target_role = discord.utils.get(guild.roles, id=target_role_id)
        
        # Check member visibility issues
        guild_member_count = guild.member_count
        bot_can_see_members = len(guild.members)
        
        # Test if bot can see the specific user
        test_user_id = 1392897052924444845
        test_user_cached = guild.get_member(test_user_id)
        test_user_fetchable = None
        try:
            if bot_instance.loop.is_running():
                future = asyncio.run_coroutine_threadsafe(guild.fetch_member(test_user_id), bot_instance.loop)
                test_user_fetchable = future.result(timeout=5)
        except:
            test_user_fetchable = False
        
        diagnostics_info = {
            'bot_name': str(bot_instance.user),
            'bot_id': bot_instance.user.id,
            'guild_name': guild.name,
            'guild_id': guild.id,
            'bot_permissions': {
                'administrator': bot_member.guild_permissions.administrator,
                'manage_roles': bot_member.guild_permissions.manage_roles,
                'manage_guild': bot_member.guild_permissions.manage_guild,
            },
            'member_visibility': {
                'total_members': guild_member_count,
                'cached_members': bot_can_see_members,
                'cache_percentage': round((bot_can_see_members / guild_member_count * 100), 1) if guild_member_count > 0 else 0,
                'test_user_cached': test_user_cached is not None,
                'test_user_fetchable': test_user_fetchable is not None and test_user_fetchable is not False,
            },
            'bot_intents': {
                'guild_members': bot_instance.intents.members,
                'message_content': bot_instance.intents.message_content,
                'guilds': bot_instance.intents.guilds,
            },
            'bot_roles': [{'name': role.name, 'id': role.id, 'position': role.position} for role in bot_member.roles if role.name != '@everyone'],
            'bot_top_role': {
                'name': bot_member.top_role.name,
                'id': bot_member.top_role.id,
                'position': bot_member.top_role.position
            },
            'target_role': {
                'name': target_role.name if target_role else 'Role not found',
                'id': target_role_id,
                'position': target_role.position if target_role else 'N/A'
            } if target_role else None,
            'can_assign_target_role': target_role and target_role.position < bot_member.top_role.position if target_role else False,
            'highest_roles_in_server': [{'name': role.name, 'id': role.id, 'position': role.position} for role in sorted(guild.roles, key=lambda r: r.position, reverse=True)[:10] if role.name != '@everyone']
        }
        
        return render_template('admin_dashboard.html', diagnostics_info=diagnostics_info, success=True)
        
    except Exception as e:
        logging.error(f"Error getting diagnostics: {e}")
        return render_template('admin_dashboard.html', 
                             message=f"Error getting diagnostics: {str(e)}", success=False)

@app.route('/admin/user-info', methods=['GET'])
def admin_user_info():
    """Get user information"""
    if not require_admin_auth():
        return redirect(url_for('admin_login'))
    
    if not bot_instance:
        return render_template('admin_dashboard.html', message="Bot instance not available", success=False)
    
    try:
        user_id = int(request.args.get('user_id'))
        
        # Load config
        with open("config.json", "r") as f:
            config = json.load(f)
            guild_id = int(config.get("guild_id", "1412488621293961226"))
        
        # Get the guild and user
        guild = bot_instance.get_guild(guild_id)
        if not guild:
            return render_template('admin_dashboard.html', 
                                 message=f"Guild with ID {guild_id} not found", success=False)
        
        user = guild.get_member(user_id)
        if not user:
            # Try to fetch the member if not in cache
            def get_user_sync():
                async def fetch_user():
                    try:
                        return await guild.fetch_member(user_id)
                    except discord.NotFound:
                        return None
                    except Exception:
                        return None
                
                try:
                    if hasattr(bot_instance, 'loop') and bot_instance.loop.is_running():
                        future = asyncio.run_coroutine_threadsafe(fetch_user(), bot_instance.loop)
                        return future.result(timeout=5)
                    else:
                        return None
                except:
                    return None
            
            user = get_user_sync()
            
            if not user:
                return render_template('admin_dashboard.html', 
                                     message=f"User with ID {user_id} not found in guild {guild.name}", success=False)
        
        # Prepare user info
        user_info = {
            'username': str(user),
            'display_name': user.display_name,
            'id': user.id,
            'joined_at': user.joined_at.strftime('%Y-%m-%d %H:%M:%S') if user.joined_at else 'Unknown',
            'roles': [{'name': role.name, 'id': role.id} for role in user.roles if role.name != '@everyone']
        }
        
        return render_template('admin_dashboard.html', user_info=user_info, success=True)
        
    except ValueError:
        return render_template('admin_dashboard.html', 
                             message="Invalid User ID format", success=False)
    except Exception as e:
        logging.error(f"Error getting user info: {e}")
        return render_template('admin_dashboard.html', 
                             message=f"Error: {str(e)}", success=False)

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'status': 'GOAT Receipts Webhook Server',
        'endpoints': {
            'health': '/api/health',
            'grant_access': '/api/grant-access (POST)',
            'check_access': '/api/check-access/<user_id> (GET)',
            'admin_dashboard': '/admin (GET)'
        }
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': {
            'root': '/',
            'health': '/api/health',
            'grant_access': '/api/grant-access (POST)',
            'check_access': '/api/check-access/<user_id> (GET)'
        }
    }), 404

if __name__ == '__main__':
    # Check if we're in production
    import os
    is_production = os.environ.get('REPL_SLUG') and os.environ.get('REPL_OWNER')
    
    if is_production:
        # Production mode - no debug, no reloader
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    else:
        # Development mode - debug enabled
        app.run(host='0.0.0.0', port=5000, debug=True)