import os
import base64
import io
import shutil
from PIL import Image

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

    try:
        all_files = os.listdir(animation_path)
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
        sprite_files = [f for f in all_files if os.path.isfile(os.path.join(sprites_path, f))
                       and f.lower().endswith(('.png', '.gif', '.jpg', '.jpeg'))]
        return sorted(sprite_files)
    except OSError:
        return []


def calculate_padding_requirements(center_offsets):
    """Calculate padding requirements for frames based on center offsets"""
    if not center_offsets:
        return 0, 0, 0, 0, []

    # Handle both old format (list of numbers) and new format (list of {x, y} objects)
    if isinstance(center_offsets[0], dict):
        # New format: extract X and Y offsets
        x_offsets = [offset.get('x', 0) for offset in center_offsets]
        y_offsets = [offset.get('y', 0) for offset in center_offsets]
        min_x_offset = min(x_offsets)
        max_x_offset = max(x_offsets)
        min_y_offset = min(y_offsets)
        max_y_offset = max(y_offsets)
    else:
        # Old format: list of numbers (only X offsets)
        x_offsets = center_offsets
        min_x_offset = min(center_offsets)
        max_x_offset = max(center_offsets)
        min_y_offset = 0
        max_y_offset = 0

    # Calculate horizontal padding
    total_width_padding = max(2 * max_x_offset, -2 * min_x_offset)
    if total_width_padding % 2 == 1:
        total_width_padding += 1

    # Calculate vertical padding
    total_height_padding = max(2 * max_y_offset, -2 * min_y_offset)
    if total_height_padding % 2 == 1:
        total_height_padding += 1

    frame_paddings = []
    for i, offset in enumerate(center_offsets):
        if isinstance(offset, dict):
            x_offset = offset.get('x', 0)
            y_offset = offset.get('y', 0)
        else:
            x_offset = offset
            y_offset = 0

        left_pad = (total_width_padding - 2 * x_offset) // 2
        right_pad = (total_width_padding + 2 * x_offset) // 2
        top_pad = (total_height_padding - 2 * y_offset) // 2
        bottom_pad = (total_height_padding + 2 * y_offset) // 2
        frame_paddings.append((left_pad, right_pad, top_pad, bottom_pad))

    return total_width_padding, total_height_padding, total_width_padding // 2, total_height_padding // 2, frame_paddings


def pad_image(image_path, output_path, left_pad, right_pad, top_pad=0, bottom_pad=0):
    """Pad an image with transparent pixels"""
    with Image.open(image_path) as img:
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        original_width, original_height = img.size
        new_width = original_width + left_pad + right_pad
        new_height = original_height + top_pad + bottom_pad

        new_img = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
        new_img.paste(img, (left_pad, top_pad))
        
        # Determine format from output file extension
        output_ext = os.path.splitext(output_path)[1].lower()
        if output_ext == '.png':
            new_img.save(output_path, 'PNG')
        elif output_ext == '.gif':
            new_img.save(output_path, 'GIF', transparency=0, disposal=2)
        else:
            # Default to PNG for best quality
            new_img.save(output_path, 'PNG')
