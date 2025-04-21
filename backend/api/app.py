from flask import Flask, send_from_directory
from flask_cors import CORS
import os

def create_app():
    app = Flask(__name__, static_folder='../../frontend', static_url_path='/')
    CORS(app)

    # Serve frontend
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def static_proxy(path):
        return send_from_directory(app.static_folder, path)

    # Import routes
    from .routes.data_routes import bp as data_bp
    app.register_blueprint(data_bp, url_prefix='/api')

    return app

app = create_app()
