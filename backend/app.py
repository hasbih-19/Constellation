from flask import Flask, send_from_directory
import os
import redis


r = redis.Redis()
app = Flask(__name__)

@app.route('/')
def serve_frontend():
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/data')
def data():
    value = r.get('my_key')
    return value


if __name__ == '__main__':
    app.run(debug=True)



