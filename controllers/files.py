from flask import Blueprint, jsonify, request
import os
import base64
import io
from PIL import Image
from utils import SOURCE_DIR

files_bp = Blueprint('files', __name__)


@files_bp.route('/api/files/save', methods=['POST'])
def save_file():
    """Save a file to any specified path"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        image_data = data.get('imageData')
        file_path = data.get('filePath')

        if not image_data:
            return jsonify({'success': False, 'error': 'Image data is required'}), 400

        if not file_path:
            return jsonify({'success': False, 'error': 'File path is required'}), 400

        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            image.save(file_path, 'PNG')

            return jsonify({'success': True, 'message': f'File saved as {os.path.basename(file_path)}', 'path': file_path})

        except Exception as e:
            return jsonify({'success': False, 'error': f'Failed to process image: {str(e)}'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500