from flask import Blueprint, jsonify, request
import os
import base64
import io
from PIL import Image
from utils import SOURCE_DIR

sprites_bp = Blueprint('sprites', __name__)


@sprites_bp.route('/api/animations/<animation_name>/sprites/save', methods=['POST'])
def save_sprite(animation_name):
    """Save a sprite image to the sprites folder"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        image_data = data.get('imageData')
        frame_name = data.get('frameName')

        if not image_data:
            return jsonify({'success': False, 'error': 'Image data is required'}), 400

        if not frame_name:
            return jsonify({'success': False, 'error': 'Frame name is required'}), 400

        animation_path = os.path.join(SOURCE_DIR, animation_name)
        if not os.path.exists(animation_path):
            return jsonify({'success': False, 'error': f'Animation "{animation_name}" not found'}), 404

        sprites_path = os.path.join(animation_path, 'sprites')
        if not os.path.exists(sprites_path):
            os.makedirs(sprites_path)

        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            sprite_filename = f"{frame_name}.png"
            sprite_path = os.path.join(sprites_path, sprite_filename)
            image.save(sprite_path, 'PNG')

            return jsonify({'success': True, 'message': f'Sprite saved as {sprite_filename}', 'path': sprite_path})

        except Exception as e:
            return jsonify({'success': False, 'error': f'Failed to process image: {str(e)}'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500