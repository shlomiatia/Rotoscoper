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

@app.route('/api/animations', methods=['GET'])
def list_animations():
    """Get list of available animations with their frame counts"""
    try:
        animations = get_animation_folders()
        animation_data = []

        for animation in animations:
            frame_files = get_frame_files(animation)
            sprite_files = get_sprite_files(animation)
            animation_data.append({
                'name': animation,
                'frameCount': len(frame_files),
                'frames': frame_files,
                'sprites': sprite_files
            })

        return jsonify({
            'success': True,
            'animations': animation_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Removed endpoint: GET /api/animations/<animation_name>/frames
# Frame lists are included in the GET /api/animations response. If a dedicated
# per-animation frames endpoint is required in the future, it can be reintroduced
# with proper pagination or filtering to avoid duplicating listing logic.


@app.route('/api/animations', methods=['POST'])
def create_animation():
    """Create a new animation by copying frames from an existing one"""
    try:
        data = request.get_json()

        # Validate input
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        new_name = data.get('name', '').strip()
        source_animation = data.get('sourceAnimation', '').strip()
        start_frame = data.get('startFrame')
        end_frame = data.get('endFrame')
        center_offsets = data.get('centerOffsets', [])

        if not new_name:
            return jsonify({
                'success': False,
                'error': 'Animation name is required'
            }), 400

        if not source_animation:
            return jsonify({
                'success': False,
                'error': 'Source animation is required'
            }), 400

        if start_frame is None or end_frame is None:
            return jsonify({
                'success': False,
                'error': 'Start and end frames are required'
            }), 400

        if start_frame >= end_frame:
            return jsonify({
                'success': False,
                'error': 'Start frame must be less than end frame'
            }), 400

        # Check if source animation exists
        source_path = os.path.join(SOURCE_DIR, source_animation)
        if not os.path.exists(source_path):
            return jsonify({
                'success': False,
                'error': f'Source animation "{source_animation}" not found'
            }), 404

        # Check if new animation already exists
        new_path = os.path.join(SOURCE_DIR, new_name)
        if os.path.exists(new_path):
            return jsonify({
                'success': False,
                'error': f'Animation "{new_name}" already exists'
            }), 409

        # Create new animation directory
        os.makedirs(new_path)

        # Calculate padding requirements if center offsets are provided
        frame_paddings = []
        if center_offsets:
            total_width_increase, max_center_offset, frame_paddings = calculate_padding_requirements(center_offsets)

        # Get source animation frame files
        source_frame_files = get_frame_files(source_animation)
        if not source_frame_files:
            os.rmdir(new_path)
            return jsonify({
                'success': False,
                'error': f'No frames found in source animation "{source_animation}"'
            }), 400

        # Copy and optionally pad frames
        frames_copied = 0
        for i, source_frame_idx in enumerate(range(start_frame, min(end_frame + 1, len(source_frame_files)))):
            source_filename = source_frame_files[source_frame_idx]
            source_file_path = os.path.join(source_path, source_filename)

            if os.path.exists(source_file_path):
                # Create new filename with sequential numbering starting from 0
                # Keep the same extension as the source file
                file_ext = os.path.splitext(source_filename)[1]
                new_filename = f'frame_{i:03d}_delay-0.03s{file_ext}'
                new_file_path = os.path.join(new_path, new_filename)

                # Apply padding if center offsets are provided
                if frame_paddings and i < len(frame_paddings):
                    left_pad, right_pad = frame_paddings[i]
                    try:
                        pad_image(source_file_path, new_file_path, left_pad, right_pad)
                    except Exception as pad_error:
                        print(f"Warning: Failed to pad frame {i}: {pad_error}")
                        # Fallback to regular copy
                        shutil.copy2(source_file_path, new_file_path)
                else:
                    # Regular copy without padding
                    shutil.copy2(source_file_path, new_file_path)

                frames_copied += 1
            else:
                print(f"Warning: Frame {source_filename} not found in {source_animation}")

        if frames_copied == 0:
            # Clean up empty directory
            os.rmdir(new_path)
            return jsonify({
                'success': False,
                'error': 'No frames were found in the specified range'
            }), 400

        return jsonify({
            'success': True,
            'message': f'Animation "{new_name}" created successfully',
            'frameCount': frames_copied,
            'name': new_name
        })

    except Exception as e:
        # Clean up if something went wrong
        try:
            if 'new_path' in locals() and os.path.exists(new_path):
                shutil.rmtree(new_path)
        except:
            pass

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Removed endpoint: DELETE /api/animations/<animation_name>
# Deleting animations is intentionally disabled in the public API. If deletion
# functionality is required, add a protected admin endpoint or a confirmation
# flow to prevent accidental removals.


# Removed endpoint: GET /api/animations/<animation_name>/sprites
# Sprite listings are now included in the GET /api/animations response to keep
# listing and metadata centralized and avoid duplicate file system scans.


@app.route('/api/animations/<animation_name>/sprites/save', methods=['POST'])
def save_sprite(animation_name):
    """Save a sprite image to the sprites folder"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        image_data = data.get('imageData')
        frame_name = data.get('frameName')

        if not image_data:
            return jsonify({
                'success': False,
                'error': 'Image data is required'
            }), 400

        if not frame_name:
            return jsonify({
                'success': False,
                'error': 'Frame name is required'
            }), 400

        # Check if animation exists
        animation_path = os.path.join(SOURCE_DIR, animation_name)
        if not os.path.exists(animation_path):
            return jsonify({
                'success': False,
                'error': f'Animation "{animation_name}" not found'
            }), 404

        # Create sprites directory if it doesn't exist
        sprites_path = os.path.join(animation_path, 'sprites')
        if not os.path.exists(sprites_path):
            os.makedirs(sprites_path)

        # Decode base64 image data
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            # Decode base64
            image_bytes = base64.b64decode(image_data)

            # Open image with PIL
            image = Image.open(io.BytesIO(image_bytes))

            # Save as PNG in sprites folder
            sprite_filename = f"{frame_name}.png"
            sprite_path = os.path.join(sprites_path, sprite_filename)
            image.save(sprite_path, 'PNG')

            return jsonify({
                'success': True,
                'message': f'Sprite saved as {sprite_filename}',
                'path': sprite_path
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to process image: {str(e)}'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files/save', methods=['POST'])
def save_file():
    """Save a file to any specified path"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        image_data = data.get('imageData')
        file_path = data.get('filePath')

        if not image_data:
            return jsonify({
                'success': False,
                'error': 'Image data is required'
            }), 400

        if not file_path:
            return jsonify({
                'success': False,
                'error': 'File path is required'
            }), 400

        # Handle directory creation
        dir_path = os.path.dirname(file_path)
        if dir_path:  # Only create directories if there's a directory path
            os.makedirs(dir_path, exist_ok=True)

        # Decode base64 image data
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            # Decode base64
            image_bytes = base64.b64decode(image_data)

            # Open image with PIL
            image = Image.open(io.BytesIO(image_bytes))

            # Save image
            image.save(file_path, 'PNG')

            return jsonify({
                'success': True,
                'message': f'File saved as {os.path.basename(file_path)}',
                'path': file_path
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to process image: {str(e)}'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/animations/crop', methods=['POST'])
def crop_animation():
    """Create a new animation with cropped frames and sprites"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        source_animation = data.get('sourceAnimation', '').strip()
        new_name = data.get('newName', '').strip()
        crop_bounds = data.get('cropBounds', {})

        if not source_animation:
            return jsonify({
                'success': False,
                'error': 'Source animation is required'
            }), 400

        if not new_name:
            return jsonify({
                'success': False,
                'error': 'New animation name is required'
            }), 400

        if not crop_bounds:
            return jsonify({
                'success': False,
                'error': 'Crop bounds are required'
            }), 400

        # Check if source animation exists
        source_path = os.path.join(SOURCE_DIR, source_animation)
        if not os.path.exists(source_path):
            return jsonify({
                'success': False,
                'error': f'Source animation "{source_animation}" not found'
            }), 404

        # Check if new animation already exists
        new_path = os.path.join(SOURCE_DIR, new_name)
        if os.path.exists(new_path):
            return jsonify({
                'success': False,
                'error': f'Animation "{new_name}" already exists'
            }), 409

        # Create new animation directory
        os.makedirs(new_path)

        # Create sprites directory
        new_sprites_path = os.path.join(new_path, 'sprites')
        os.makedirs(new_sprites_path, exist_ok=True)

        # Get crop bounds
        left = int(crop_bounds.get('left', 0))
        right = int(crop_bounds.get('right', 0))
        top = int(crop_bounds.get('top', 0))
        bottom = int(crop_bounds.get('bottom', 0))

        if left < 0 or right < 0 or top < 0 or bottom < 0:
            os.rmdir(new_sprites_path)
            os.rmdir(new_path)
            return jsonify({
                'success': False,
                'error': 'Invalid crop bounds'
            }), 400

        # Get source files
        source_frame_files = get_frame_files(source_animation)
        source_sprite_files = get_sprite_files(source_animation)

        frames_processed = 0
        sprites_processed = 0

        # Process frames
        for i, frame_file in enumerate(source_frame_files):
            source_frame_path = os.path.join(source_path, frame_file)
            if os.path.exists(source_frame_path):
                try:
                    with Image.open(source_frame_path) as img:
                        # Convert to RGBA if not already
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')

                        # Get original dimensions
                        width, height = img.size

                        # Calculate crop box (left, top, right, bottom)
                        crop_box = (
                            left,
                            top,
                            width - right,
                            height - bottom
                        )

                        # Crop the image
                        cropped_img = img.crop(crop_box)

                        # Create new filename
                        new_frame_name = f'frame_{i:03d}_delay-0.03s.gif'
                        new_frame_path = os.path.join(new_path, new_frame_name)

                        # Save as GIF with transparency
                        cropped_img.save(new_frame_path, 'GIF', transparency=0, disposal=2)
                        frames_processed += 1

                except Exception as e:
                    print(f"Warning: Failed to process frame {frame_file}: {e}")

        # Process sprites
        source_sprites_path = os.path.join(source_path, 'sprites')
        if os.path.exists(source_sprites_path):
            for i, sprite_file in enumerate(source_sprite_files):
                source_sprite_path = os.path.join(source_sprites_path, sprite_file)
                if os.path.exists(source_sprite_path):
                    try:
                        with Image.open(source_sprite_path) as img:
                            # Convert to RGBA if not already
                            if img.mode != 'RGBA':
                                img = img.convert('RGBA')

                            # Get original dimensions
                            width, height = img.size

                            # Calculate crop box (left, top, right, bottom)
                            crop_box = (
                                left,
                                top,
                                width - right,
                                height - bottom
                            )

                            # Crop the image
                            cropped_img = img.crop(crop_box)

                            # Create new filename
                            new_sprite_name = f'frame_{i:03d}_delay-0.03s.png'
                            new_sprite_path = os.path.join(new_sprites_path, new_sprite_name)

                            # Save as PNG
                            cropped_img.save(new_sprite_path, 'PNG')
                            sprites_processed += 1

                    except Exception as e:
                        print(f"Warning: Failed to process sprite {sprite_file}: {e}")

        if frames_processed == 0:
            # Clean up empty directories
            try:
                os.rmdir(new_sprites_path)
                os.rmdir(new_path)
            except:
                pass
            return jsonify({
                'success': False,
                'error': 'No frames were processed'
            }), 400

        return jsonify({
            'success': True,
            'message': f'Cropped animation "{new_name}" created successfully',
            'frameCount': frames_processed,
            'spriteCount': sprites_processed,
            'name': new_name,
            'cropBounds': crop_bounds
        })

    except Exception as e:
        # Clean up if something went wrong
        try:
            if 'new_path' in locals() and os.path.exists(new_path):
                shutil.rmtree(new_path)
        except:
            pass

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Animation Server...")
    print("Server will be available at: http://localhost:5000")
    print("Make sure your Source/Walk folder exists with animation frames")
    print("\nPress Ctrl+C to stop the server")

    app.run(debug=True, host='0.0.0.0', port=5000)