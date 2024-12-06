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
        
        # verifica daca folderul pentru cache exista
        if os.path.exists(cache_dir):
            # elimina cache-ul existent
            for file in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, file))
        else:
            os.makedirs(cache_dir)
        
        # setarea rutelor
        self.app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE'])(self.proxy)
        self.app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])(self.proxy)

    # generarea cheiei unice pentru cache in baza detaliilor requestului
    def _generate_cache_key(self, url, method, headers, data=None):
        key_components = [
            url, 
            method, 
            json.dumps(dict(headers), sort_keys=True),
            str(data) if data else ''
        ]
        return hashlib.md5(''.join(key_components).encode()).hexdigest()

    # generarea caii pentru fisierul cache
    def _get_cache_path(self, cache_key):
        return os.path.join(self.cache_dir, f"{cache_key}.cache")

    # validarea raspunsului stocat in cache
    def _is_cache_valid(self, cache_path, max_age=3600):
        try:
            if not os.path.exists(cache_path):
                return False
            
            # incearcarea de a deschide fisierul
            with open(cache_path, 'r') as f:
                json.load(f)
            
            # verificarea varstei fisierului si valideaza fisierul
            return (time.time() - os.path.getmtime(cache_path)) < max_age
        except (json.JSONDecodeError, IOError):
            # daca apar erori la citire, considera fisierul invalid
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return False

    # salvarea raspunsului serverului in cache
    def _save_to_cache(self, cache_key, response):
        try:
            cache_path = self._get_cache_path(cache_key)
            
            cache_data = {
                'content': base64.b64encode(response.content).decode('utf-8'),
                'headers': dict(response.headers),
                'status_code': response.status_code
            }
            
            # scriere intr-un fisier temporar
            temp_path = cache_path + '.tmp'
            with open(temp_path, 'w') as f:
                json.dump(cache_data, f)
            
            # transferarea fisierului temporar in cache
            os.replace(temp_path, cache_path)
        except Exception as e:
            print(f"Error saving to cache: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # incarcarea raspunsului din cache
    def _load_from_cache(self, cache_key):
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
            # daca apar erori la citire, elimina fisierul
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return None

    # metoda principala de operare a proxy
    def proxy(self, path=''):
        url = f"{self.target_url.rstrip('/')}/{path}"
        
        # generarea cheilor
        cache_key = self._generate_cache_key(
            url, 
            request.method, 
            request.headers, 
            request.get_data()
        )

        # incercarea de a incarca raspunsul din cache
        if request.method == 'GET':
            cached_response = self._load_from_cache(cache_key)
            if cached_response:
                return cached_response

        # in caz contrar, trimite requestul catre server
        headers = {key: value for (key, value) in request.headers if key != 'Host'}
        try:
            response = requests.request(
                method=request.method,
                url=url,
                headers=headers,
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False
            )

            # salvarea raspunsului in cache
            if request.method == 'GET':
                self._save_to_cache(cache_key, response)

            return Response(
                response.content, 
                status=response.status_code, 
                headers=dict(response.headers)
            )

        except requests.RequestException as e:
            return Response(str(e), status=500)

    # functia de rularea a proxy
    def run(self, host='0.0.0.0', port=5001):
        self.app.run(host=host, port=port, debug=True)

def create_proxy():
    proxy = WebProxy(target_url='http://localhost:5000')
    proxy.run()

if __name__ == '__main__':
    create_proxy()