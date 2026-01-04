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
        return 0, 0, []

    min_offset = min(center_offsets)
    max_offset = max(center_offsets)
    total_padding = max(2 * max_offset, -2 * min_offset)
    if total_padding % 2 == 1:
        total_padding += 1

    frame_paddings = []
    for i, offset in enumerate(center_offsets):
        left_pad = (total_padding - 2 * offset) // 2
        right_pad = (total_padding + 2 * offset) // 2
        frame_paddings.append((left_pad, right_pad))

    return total_padding, total_padding // 2, frame_paddings


def pad_image(image_path, output_path, left_pad, right_pad):
    """Pad an image with transparent pixels"""
    with Image.open(image_path) as img:
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        original_width, original_height = img.size
        new_width = original_width + left_pad + right_pad

        new_img = Image.new('RGBA', (new_width, original_height), (0, 0, 0, 0))
        new_img.paste(img, (left_pad, 0))
        new_img.save(output_path, 'GIF', transparency=0, disposal=2)
