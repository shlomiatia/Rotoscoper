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
SOURCE_DIR = 'Source'

def ensure_source_directory():
    """Ensure the Source directory exists"""
    if not os.path.exists(SOURCE_DIR):
        os.makedirs(SOURCE_DIR)

def get_animation_folders():
    """Get list of available animation folders"""
    ensure_source_directory()
    animations = []
    for item in os.listdir(SOURCE_DIR):
        item_path = os.path.join(SOURCE_DIR, item)
        if os.path.isdir(item_path):
            animations.append(item)
    return sorted(animations)

def get_frame_files(animation_name):
    """Get the list of frame files in an animation folder"""
    animation_path = os.path.join(SOURCE_DIR, animation_name)
    if not os.path.exists(animation_path):
        return []

    # Get all files in the directory
    try:
        all_files = os.listdir(animation_path)
        # Filter to only include files (not subdirectories) and sort them
        frame_files = [f for f in all_files if os.path.isfile(os.path.join(animation_path, f))]
        return sorted(frame_files)
    except OSError:
        return []

def get_sprite_files(animation_name):
    """Get the list of sprite files in an animation's sprites folder"""
    animation_path = os.path.join(SOURCE_DIR, animation_name)
    sprites_path = os.path.join(animation_path, 'sprites')

    if not os.path.exists(sprites_path):
        return []

    try:
        all_files = os.listdir(sprites_path)
        # Filter to only include image files and sort them
        sprite_files = [f for f in all_files if os.path.isfile(os.path.join(sprites_path, f))
                       and f.lower().endswith(('.png', '.gif', '.jpg', '.jpeg'))]
        return sorted(sprite_files)
    except OSError:
        return []

def calculate_padding_requirements(center_offsets):
    """Calculate padding requirements for frames based on center offsets

    Requirements:
    1. ALL frames must have identical final width
    2. Each frame's content positioned according to its offset
    3. Offset 0 = content centered, +N = content N pixels right of center, -N = content N pixels left

    Strategy: Calculate the maximum total padding needed, then distribute per frame.
    """
    if not center_offsets:
        return 0, 0, []

    # Find the range of offsets
    min_offset = min(center_offsets)
    max_offset = max(center_offsets)

    # Calculate the total padding needed to accommodate all offsets
    # We need enough padding so that:
    # - For max positive offset: enough left padding to push content right
    # - For max negative offset: enough right padding to push content left
    # - No frame gets negative padding

    # If offset is +N, content should be N pixels right of center
    # This requires: left_padding - right_padding = 2*N (mathematical relationship)
    # Combined with: left_padding + right_padding = total_padding (uniform width)
    # Solving: left_padding = (total_padding + 2*N) / 2, right_padding = (total_padding - 2*N) / 2

    # To ensure no negative padding for any frame:
    # For max_offset: (total_padding - 2*max_offset) / 2 >= 0 → total_padding >= 2*max_offset
    # For min_offset: (total_padding + 2*min_offset) / 2 >= 0 → total_padding >= -2*min_offset

    total_padding = max(2 * max_offset, -2 * min_offset)

    # Ensure total_padding is even for clean division
    if total_padding % 2 == 1:
        total_padding += 1


    # Calculate padding for each frame (FLIPPED: positive offset = more right padding)
    frame_paddings = []
    for i, offset in enumerate(center_offsets):
        # FLIP: positive offset should have more RIGHT padding, negative should have more LEFT
        left_pad = (total_padding - 2 * offset) // 2
        right_pad = (total_padding + 2 * offset) // 2

        frame_paddings.append((left_pad, right_pad))

    return total_padding, total_padding // 2, frame_paddings

def pad_image(image_path, output_path, left_pad, right_pad):
    """Pad an image with transparent pixels"""
    with Image.open(image_path) as img:
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        original_width, original_height = img.size
        new_width = original_width + left_pad + right_pad

        # Create new image with transparent background
        new_img = Image.new('RGBA', (new_width, original_height), (0, 0, 0, 0))

        # Paste the original image with the left padding offset
        new_img.paste(img, (left_pad, 0))

        # Save as GIF (preserving transparency)
        new_img.save(output_path, 'GIF', transparency=0, disposal=2)

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

@app.route('/api/animations/<animation_name>/frames', methods=['GET'])
def get_animation_info(animation_name):
    """Get information about a specific animation"""
    try:
        animation_path = os.path.join(SOURCE_DIR, animation_name)
        if not os.path.exists(animation_path):
            return jsonify({
                'success': False,
                'error': f'Animation "{animation_name}" not found'
            }), 404

        frame_files = get_frame_files(animation_name)

        return jsonify({
            'success': True,
            'name': animation_name,
            'frameCount': len(frame_files),
            'frames': frame_files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

@app.route('/api/animations/<animation_name>', methods=['DELETE'])
def delete_animation(animation_name):
    """Delete an animation (except the original Walk animation)"""
    try:
        if animation_name == 'Walk':
            return jsonify({
                'success': False,
                'error': 'Cannot delete the original Walk animation'
            }), 403

        animation_path = os.path.join(SOURCE_DIR, animation_name)
        if not os.path.exists(animation_path):
            return jsonify({
                'success': False,
                'error': f'Animation "{animation_name}" not found'
            }), 404

        shutil.rmtree(animation_path)

        return jsonify({
            'success': True,
            'message': f'Animation "{animation_name}" deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/animations/<animation_name>/sprites', methods=['GET'])
def get_animation_sprites(animation_name):
    """Get list of sprite files for an animation"""
    try:
        animation_path = os.path.join(SOURCE_DIR, animation_name)
        if not os.path.exists(animation_path):
            return jsonify({
                'success': False,
                'error': f'Animation "{animation_name}" not found'
            }), 404

        sprites_path = os.path.join(animation_path, 'sprites')
        if not os.path.exists(sprites_path):
            return jsonify({
                'success': True,
                'sprites': []
            })

        # Get all sprite files
        sprite_files = []
        try:
            all_files = os.listdir(sprites_path)
            for filename in all_files:
                file_path = os.path.join(sprites_path, filename)
                if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.gif', '.jpg', '.jpeg')):
                    # Extract frame index from filename if it follows the pattern
                    frame_index = -1
                    if filename.startswith('frame_') and '_delay-' in filename:
                        try:
                            frame_part = filename.split('_')[1]
                            frame_index = int(frame_part)
                        except (IndexError, ValueError):
                            pass

                    sprite_files.append({
                        'filename': filename,
                        'frameIndex': frame_index
                    })
        except OSError:
            sprite_files = []

        return jsonify({
            'success': True,
            'sprites': sprite_files
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

if __name__ == '__main__':
    print("Starting Animation Server...")
    print("Server will be available at: http://localhost:5000")
    print("Make sure your Source/Walk folder exists with animation frames")
    print("\nPress Ctrl+C to stop the server")

    app.run(debug=True, host='0.0.0.0', port=5000)