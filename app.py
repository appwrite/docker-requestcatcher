from datetime import datetime
from flask import Flask, request, jsonify
from os import environ

app = Flask('HTTP Request Catcher')

last_request = None
all_requests = []


@app.route('/__last_request__', methods=['GET'])
def get_last_request():
    return jsonify(last_request), 200


@app.route('/__all_requests__', methods=['GET'])
def get_all_requests():
    return jsonify(all_requests), 200


@app.route('/__clear__', methods=['POST', 'DELETE'])
def clear_requests():
    global last_request, all_requests
    last_request = None
    all_requests = []
    return '', 204


@app.route('/', defaults={'path': ''}, methods=['PUT', 'POST', 'GET', 'HEAD', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['PUT', 'POST', 'GET', 'HEAD', 'DELETE', 'PATCH', 'OPTIONS'])
def catch(path):
    global last_request, all_requests

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
