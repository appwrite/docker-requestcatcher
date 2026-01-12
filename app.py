from collections import deque
from datetime import datetime
from flask import Flask, request, jsonify
from os import environ

app = Flask('HTTP Request Catcher')

# Maximum number of requests to store in history (configurable via environment variable)
MAX_REQUEST_HISTORY = int(environ.get('MAX_REQUEST_HISTORY', 1000))

last_request = None
all_requests = deque(maxlen=MAX_REQUEST_HISTORY)


@app.route('/__last_request__', methods=['GET'])
def get_last_request():
    return jsonify(last_request), 200


@app.route('/__all_requests__', methods=['GET'])
def get_all_requests():
    return jsonify(list(all_requests)), 200


@app.route('/__find_request__', methods=['GET'])
def find_request():
    """
    Find requests matching header or body values.
    Query parameters:
    - header_<name>=<value>: Match requests with specific header value
    - body=<value>: Match requests containing this value in body
    - method=<value>: Match requests with specific HTTP method
    - url=<value>: Match requests with URL containing this value
    """
    matches = []
    
    for req in all_requests:
        match = True
        
        for key, value in request.args.items():
            if key.startswith('header_'):
                header_name = key[7:]  # Remove 'header_' prefix
                req_headers = {k.lower(): v for k, v in req['headers'].items()}
                if req_headers.get(header_name.lower()) != value:
                    match = False
                    break
            elif key == 'body':
                if value not in req.get('data', ''):
                    match = False
                    break
            elif key == 'method':
                if req.get('method', '').upper() != value.upper():
                    match = False
                    break
            elif key == 'url':
                if value not in req.get('url', ''):
                    match = False
                    break
        
        if match:
            matches.append(req)
    
    return jsonify(matches), 200


@app.route('/__clear__', methods=['POST', 'DELETE'])
def clear_requests():
    global last_request
    last_request = None
    all_requests.clear()
    return '', 204


@app.route('/', defaults={'path': ''}, methods=['PUT', 'POST', 'GET', 'HEAD', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['PUT', 'POST', 'GET', 'HEAD', 'DELETE', 'PATCH', 'OPTIONS'])
def catch(path):
    global last_request

    last_request = {
        'method': request.method,
        'data': request.data.decode('utf-8'),
        'headers': dict(request.headers),
        'url': request.url,
        'time': datetime.now().isoformat(),
    }
    all_requests.append(last_request)

    return '', 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
