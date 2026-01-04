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

# Route: GET /api/animations
# Implemented in controllers/animations.py as part of the `animations_bp` Blueprint.
# This file only registers blueprints and serves static files to keep the
# application entrypoint minimal and focused.



# Route: POST /api/animations
# Implemented in controllers/animations.py as part of the `animations_bp` Blueprint.
# See controllers/animations.py:create_animation for implementation details.


# Removed endpoint: GET /api/animations/<animation_name>/sprites
# Sprite listings are now included in the GET /api/animations response to keep
# listing and metadata centralized and avoid duplicate file system scans.


# Route: POST /api/animations/<animation_name>/sprites/save
# Implemented in controllers/sprites.py as part of the `sprites_bp` Blueprint.


# Route: POST /api/files/save
# Implemented in controllers/files.py as part of the `files_bp` Blueprint.


# Route: POST /api/animations/crop
# Implemented in controllers/animations.py as part of the `animations_bp` Blueprint.


if __name__ == '__main__':
    print("Starting Animation Server...")
    print("Server will be available at: http://localhost:5000")
    print("Make sure your Source/Walk folder exists with animation frames")
    print("\nPress Ctrl+C to stop the server")

    app.run(debug=True, host='0.0.0.0', port=5000)