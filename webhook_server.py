
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import json
import logging
from utils.mongodb_manager import mongo_manager

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/api/grant-access', methods=['POST'])
def grant_access():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = data.get('userId')
        username = data.get('username')
        guild_id = data.get('guildId')
        guild_name = data.get('guildName')
        access_duration = data.get('accessDuration', 1)  # Default 1 day
        timestamp = data.get('timestamp')
        
        if not user_id or not guild_id:
            return jsonify({'error': 'Missing required fields: userId, guildId'}), 400
        
        logging.info(f"Granting {access_duration} days access to user {user_id} in guild {guild_id}")
        
        # Calculate expiry date
        expiry_date = datetime.now() + timedelta(days=access_duration)
        expiry_str = expiry_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Check if this is the main guild or a configured guild
        with open("config.json", "r") as f:
            config = json.load(f)
            main_guild_id = config.get("guild_id", "1339298010169086072")
        
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
                "granted_by": "invite_tracker",
                "granted_at": datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }
            
            success = mongo_manager.create_or_update_license(user_id, license_data)
            
            if not success:
                return jsonify({'error': 'Failed to create license'}), 500
        else:
            # For other guilds, save server access
            success = mongo_manager.save_server_access(
                guild_id,
                user_id,
                "invite_tracker",
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
                "granted_by": "invite_tracker"
            }
            
            mongo_manager.save_guild_user_license(guild_id, user_id, license_data)
        
        logging.info(f"Successfully granted access to user {user_id}")
        
        return jsonify({
            'success': True,
            'message': f'Access granted for {access_duration} days',
            'expiryDate': expiry_date.isoformat(),
            'userId': user_id,
            'guildId': guild_id
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
            main_guild_id = config.get("guild_id", "1339298010169086072")
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
