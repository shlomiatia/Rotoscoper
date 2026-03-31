from flask import Blueprint, jsonify, request
import os
import shutil
import io
# rembg is imported lazily inside remove_background() so the server can run without it installed
from utils import (ensure_source_directory, get_animation_folders,
                   get_frame_files, get_sprite_files, calculate_padding_requirements, pad_image, SOURCE_DIR)

animations_bp = Blueprint('animations', __name__)


@animations_bp.route('/api/animations', methods=['GET'])
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


@animations_bp.route('/api/animations', methods=['POST'])
def create_animation():
    """Create a new animation by copying frames from an existing one"""
    try:
        data = request.get_json()

        # Validate input
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        new_name = data.get('name', '').strip()
        source_animation = data.get('sourceAnimation', '').strip()
        start_frame = data.get('startFrame')
        end_frame = data.get('endFrame')
        center_offsets = data.get('centerOffsets', [])

        if not new_name:
            return jsonify({'success': False, 'error': 'Animation name is required'}), 400

        if not source_animation:
            return jsonify({'success': False, 'error': 'Source animation is required'}), 400

        if start_frame is None or end_frame is None:
            return jsonify({'success': False, 'error': 'Start and end frames are required'}), 400

        if start_frame > end_frame:
            return jsonify({'success': False, 'error': 'Start frame must not be greater than end frame'}), 400

        source_path = os.path.join(SOURCE_DIR, source_animation)
        if not os.path.exists(source_path):
            return jsonify({'success': False, 'error': f'Source animation "{source_animation}" not found'}), 404

        new_path = os.path.join(SOURCE_DIR, new_name)
        if os.path.exists(new_path):
            return jsonify({'success': False, 'error': f'Animation "{new_name}" already exists'}), 409

        os.makedirs(new_path)

        frame_paddings = []
        if center_offsets:
            total_width_increase, total_height_increase, max_center_offset_x, max_center_offset_y, frame_paddings = calculate_padding_requirements(center_offsets)

        source_frame_files = get_frame_files(source_animation)
        if not source_frame_files:
            os.rmdir(new_path)
            return jsonify({'success': False, 'error': f'No frames found in source animation "{source_animation}"'}), 400

        frames_copied = 0
        for i, source_frame_idx in enumerate(range(start_frame, min(end_frame + 1, len(source_frame_files)))):
            source_filename = source_frame_files[source_frame_idx]
            source_file_path = os.path.join(source_path, source_filename)

            if os.path.exists(source_file_path):
                file_ext = os.path.splitext(source_filename)[1]
                new_filename = f'frame_{i:03d}_delay-0.03s{file_ext}'
                new_file_path = os.path.join(new_path, new_filename)

                if frame_paddings and i < len(frame_paddings):
                    left_pad, right_pad, top_pad, bottom_pad = frame_paddings[i]
                    if left_pad > 0 or right_pad > 0 or top_pad > 0 or bottom_pad > 0:
                        try:
                            pad_image(source_file_path, new_file_path, left_pad, right_pad, top_pad, bottom_pad)
                        except Exception:
                            shutil.copy2(source_file_path, new_file_path)
                    else:
                        shutil.copy2(source_file_path, new_file_path)
                else:
                    shutil.copy2(source_file_path, new_file_path)

                frames_copied += 1
            else:
                print(f"Warning: Frame {source_filename} not found in {source_animation}")

        if frames_copied == 0:
            os.rmdir(new_path)
            return jsonify({'success': False, 'error': 'No frames were found in the specified range'}), 400

        return jsonify({'success': True, 'message': f'Animation "{new_name}" created successfully', 'frameCount': frames_copied, 'name': new_name})

    except Exception as e:
        try:
            if 'new_path' in locals() and os.path.exists(new_path):
                shutil.rmtree(new_path)
        except:
            pass

        return jsonify({'success': False, 'error': str(e)}), 500


@animations_bp.route('/api/create-cropped-animation', methods=['POST'])
def create_cropped_animation():
    """Create a new animation by applying minimum crop values from all frames uniformly"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        source_animation = data.get('sourceAnimation', '').strip()
        new_animation_name = data.get('newAnimationName', '').strip()
        crop_left = int(data.get('cropLeft', 0))
        crop_right = int(data.get('cropRight', 0))
        crop_top = int(data.get('cropTop', 0))
        crop_bottom = int(data.get('cropBottom', 0))

        if not source_animation:
            return jsonify({'success': False, 'error': 'Source animation is required'}), 400

        if not new_animation_name:
            return jsonify({'success': False, 'error': 'New animation name is required'}), 400

        if crop_left < 0 or crop_right < 0 or crop_top < 0 or crop_bottom < 0:
            return jsonify({'success': False, 'error': 'Invalid crop values'}), 400

        source_path = os.path.join(SOURCE_DIR, source_animation)
        if not os.path.exists(source_path):
            return jsonify({'success': False, 'error': f'Source animation "{source_animation}" not found'}), 404

        new_path = os.path.join(SOURCE_DIR, new_animation_name)
        if os.path.exists(new_path):
            return jsonify({'success': False, 'error': f'Animation "{new_animation_name}" already exists'}), 409

        os.makedirs(new_path)
        new_sprites_path = os.path.join(new_path, 'sprites')
        os.makedirs(new_sprites_path, exist_ok=True)

        source_frame_files = get_frame_files(source_animation)
        source_sprite_files = get_sprite_files(source_animation)

        if not source_frame_files:
            try:
                os.rmdir(new_sprites_path)
                os.rmdir(new_path)
            except:
                pass
            return jsonify({'success': False, 'error': f'No frames found in source animation "{source_animation}"'}), 400

        frames_processed = 0
        sprites_processed = 0

        from PIL import Image

        for i, frame_file in enumerate(source_frame_files):
            source_frame_path = os.path.join(source_path, frame_file)
            if os.path.exists(source_frame_path):
                try:
                    with Image.open(source_frame_path) as img:
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')

                        width, height = img.size
                        crop_box = (crop_left, crop_top, width - crop_right, height - crop_bottom)
                        cropped_img = img.crop(crop_box)
                        new_frame_name = f'frame_{i:03d}_delay-0.03s.gif'
                        new_frame_path = os.path.join(new_path, new_frame_name)
                        cropped_img.save(new_frame_path, 'GIF', transparency=0, disposal=2)
                        frames_processed += 1

                except Exception as e:
                    print(f"Warning: Failed to process frame {frame_file}: {e}")

        # Process sprites if they exist
        source_sprites_path = os.path.join(source_path, 'sprites')
        if os.path.exists(source_sprites_path):
            for i, sprite_file in enumerate(source_sprite_files):
                source_sprite_path = os.path.join(source_sprites_path, sprite_file)
                if os.path.exists(source_sprite_path):
                    try:
                        with Image.open(source_sprite_path) as img:
                            if img.mode != 'RGBA':
                                img = img.convert('RGBA')

                            width, height = img.size
                            crop_box = (crop_left, crop_top, width - crop_right, height - crop_bottom)
                            cropped_img = img.crop(crop_box)
                            new_sprite_name = f'frame_{i:03d}_delay-0.03s.png'
                            new_sprite_path = os.path.join(new_sprites_path, new_sprite_name)
                            cropped_img.save(new_sprite_path, 'PNG')
                            sprites_processed += 1

                    except Exception as e:
                        print(f"Warning: Failed to process sprite {sprite_file}: {e}")

        if frames_processed == 0:
            try:
                os.rmdir(new_sprites_path)
                os.rmdir(new_path)
            except:
                pass
            return jsonify({'success': False, 'error': 'No frames were processed'}), 400

        return jsonify({'success': True, 'message': f'Cropped animation "{new_animation_name}" created successfully', 'frameCount': frames_processed, 'spriteCount': sprites_processed, 'name': new_animation_name})

    except Exception as e:
        try:
            if 'new_path' in locals() and os.path.exists(new_path):
                shutil.rmtree(new_path)
        except:
            pass

        return jsonify({'success': False, 'error': str(e)}), 500
