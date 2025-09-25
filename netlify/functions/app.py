"""
Netlify Functions wrapper for the Flask application
This file adapts the Flask app to work as a Netlify serverless function
"""
import json
import sys
import os

# Add the root directory to Python path so we can import the main app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import app

def handler(event, context):
    """
    Netlify Functions handler that wraps the Flask application
    """
    # Extract HTTP method and path from the event
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    query_params = event.get('queryStringParameters') or {}
    headers = event.get('headers', {})
    body = event.get('body', '')
    
    # Handle base64 encoded bodies (for binary data)
    if event.get('isBase64Encoded', False):
        import base64
        body = base64.b64decode(body).decode('utf-8')
    
    # Parse JSON body if content-type is JSON
    json_body = None
    if headers.get('content-type', '').startswith('application/json') and body:
        try:
            json_body = json.loads(body)
        except json.JSONDecodeError:
            pass
    
    # Create a test client for the Flask app
    with app.test_client() as client:
        # Build the URL with query parameters
        url = path
        if query_params:
            url += '?' + '&'.join([f"{k}={v}" for k, v in query_params.items()])
        
        # Prepare request data
        request_data = {
            'headers': headers,
            'environ_base': {
                'REQUEST_METHOD': http_method,
                'PATH_INFO': path,
                'QUERY_STRING': '&'.join([f"{k}={v}" for k, v in query_params.items()]) if query_params else '',
                'SERVER_NAME': 'localhost',
                'SERVER_PORT': '80',
                'wsgi.url_scheme': 'https'
            }
        }
        
        # Add body data for POST requests
        if http_method in ['POST', 'PUT', 'PATCH'] and body:
            if json_body:
                request_data['json'] = json_body
            else:
                request_data['data'] = body
        
        # Make the request to the Flask app
        if http_method == 'GET':
            response = client.get(url, **{k: v for k, v in request_data.items() if k != 'json' and k != 'data'})
        elif http_method == 'POST':
            response = client.post(url, **request_data)
        elif http_method == 'PUT':
            response = client.put(url, **request_data)
        elif http_method == 'DELETE':
            response = client.delete(url, **request_data)
        else:
            # Default to GET for unsupported methods
            response = client.get(url, **{k: v for k, v in request_data.items() if k != 'json' and k != 'data'})
    
    # Convert Flask response to Netlify Functions response format
    response_headers = dict(response.headers)
    
    # Handle different content types
    if response.content_type and response.content_type.startswith('application/json'):
        body = response.get_data(as_text=True)
    else:
        body = response.get_data(as_text=True)
    
    return {
        'statusCode': response.status_code,
        'headers': response_headers,
        'body': body,
        'isBase64Encoded': False
    }

# For local testing
if __name__ == '__main__':
    # Test the handler with a sample event
    test_event = {
        'httpMethod': 'GET',
        'path': '/health',
        'headers': {},
        'queryStringParameters': None,
        'body': None
    }
    
    result = handler(test_event, {})
    print(json.dumps(result, indent=2))