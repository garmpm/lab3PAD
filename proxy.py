import requests
from flask import Flask, request, Response
import time
import hashlib
import os
import json
import base64

class WebProxy:
    def __init__(self, target_url, cache_dir='proxy_cache'):
        self.app = Flask(__name__)
        self.target_url = target_url
        self.cache_dir = cache_dir
        
        # Ensure cache directory exists
        if os.path.exists(cache_dir):
            # Clear existing cache files
            for file in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, file))
        else:
            os.makedirs(cache_dir)
        
        # Set up routes
        self.app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])(self.proxy)
        self.app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])(self.proxy)

    def _generate_cache_key(self, url, method, headers, data=None):
        """Generate a unique cache key based on request details."""
        key_components = [
            url, 
            method, 
            json.dumps(dict(headers), sort_keys=True),
            str(data) if data else ''
        ]
        return hashlib.md5(''.join(key_components).encode()).hexdigest()

    def _get_cache_path(self, cache_key):
        """Generate full path for cache file."""
        return os.path.join(self.cache_dir, f"{cache_key}.cache")

    def _is_cache_valid(self, cache_path, max_age=3600):
        """Check if cached response is still valid."""
        try:
            if not os.path.exists(cache_path):
                return False
            
            # Attempt to read the cache file to verify it's valid
            with open(cache_path, 'r') as f:
                json.load(f)
            
            # Check file age
            return (time.time() - os.path.getmtime(cache_path)) < max_age
        except (json.JSONDecodeError, IOError):
            # If there's any error reading the cache, consider it invalid
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return False

    def _save_to_cache(self, cache_key, response):
        """Save response to cache."""
        try:
            cache_path = self._get_cache_path(cache_key)
            
            cache_data = {
                'content': base64.b64encode(response.content).decode('utf-8'),
                'headers': dict(response.headers),
                'status_code': response.status_code
            }
            
            # Write to a temporary file first
            temp_path = cache_path + '.tmp'
            with open(temp_path, 'w') as f:
                json.dump(cache_data, f)
            
            # Rename the temporary file to the actual cache file
            os.replace(temp_path, cache_path)
        except Exception as e:
            print(f"Error saving to cache: {e}")
            # If there's any error, make sure we clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _load_from_cache(self, cache_key):
        """Load cached response."""
        try:
            cache_path = self._get_cache_path(cache_key)
            
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            
            return Response(
                base64.b64decode(cached_data['content']), 
                status=cached_data['status_code'], 
                headers=cached_data['headers']
            )
        except Exception as e:
            print(f"Error loading from cache: {e}")
            # If there's any error reading the cache, remove the file
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return None

    def proxy(self, path=''):
        """Main proxy method to handle all requests."""
        # Construct full URL
        url = f"{self.target_url.rstrip('/')}/{path}"
        
        # Generate cache key
        cache_key = self._generate_cache_key(
            url, 
            request.method, 
            request.headers, 
            request.get_data()
        )

        # Try to get from cache for GET requests
        if request.method == 'GET':
            cached_response = self._load_from_cache(cache_key)
            if cached_response:
                return cached_response

        # Forward request to target server
        headers = {key: value for (key, value) in request.headers if key != 'Host'}
        try:
            # Prepare the request to the target server
            response = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False
            )

            # Cache GET responses
            if request.method == 'GET':
                self._save_to_cache(cache_key, response)

            # Return the response
            return Response(
                response.content, 
                status=response.status_code, 
                headers=dict(response.headers)
            )

        except requests.RequestException as e:
            return Response(str(e), status=500)

    def run(self, host='0.0.0.0', port=5001):
        """Run the proxy server."""
        self.app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    # Replace with your actual target URL
    proxy = WebProxy(target_url='http://localhost:5000')  # Your Flask app URL
    proxy.run()