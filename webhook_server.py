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
        
        # Get user
        user = guild.get_member(target_user_id)
        if not user:
            return render_template('admin_dashboard.html', 
                                 message=f"User with ID {target_user_id} not found in guild {guild.name}. Make sure they are in the server and the bot has permission to see them.", success=False)
        
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
    app.run(host='0.0.0.0', port=5000, debug=True)