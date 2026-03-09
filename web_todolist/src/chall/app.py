from flask import request, Flask, send_from_directory
import requests
import os

HEADLESS_URL = os.getenv('HEADLESS_URL', 'http://headless:5000')
CHALL_URL = os.getenv('CHALL_URL', 'http://web:5000')
FLAG = os.getenv('FLAG', 'srdnlen{example}')
app = Flask(__name__)

@app.route('/')
def index():
    response = send_from_directory('templates', 'index.html', mimetype='text/html')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)