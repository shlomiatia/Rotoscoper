#!/usr/bin/env python3
"""
Animation Server - Flask backend for the Animation Player
Handles file operations for creating and managing animations
"""

import os
import shutil
import json
import glob
import base64
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image
import tempfile
import io

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
from utils import SOURCE_DIR, ensure_source_directory

# Import and register blueprints that handle the API routes
from controllers.animations import animations_bp
from controllers.sprites import sprites_bp
from controllers.files import files_bp

app.register_blueprint(animations_bp)
app.register_blueprint(sprites_bp)
app.register_blueprint(files_bp)

@app.route('/')
def index():
    """Serve the main HTML file"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    """Serve static files"""
    return send_from_directory('.', filename)

if __name__ == '__main__':
    print("Starting Animation Server...")
    print("Server will be available at: http://localhost:5000")
    print("If you have animation frames, place them under Source/<animation_name>/ (e.g., Source/Walk)")
    print("\nPress Ctrl+C to stop the server")

    app.run(debug=True, host='0.0.0.0', port=5000)