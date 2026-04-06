from flask import Blueprint, jsonify, request
import os
import shutil
import io
import tempfile
import subprocess
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


@animations_bp.route('/api/animations/import-video', methods=['POST'])
def import_video():
    """Import a video file into a new animation folder using ffmpeg"""
    try:
        ensure_source_directory()

        if 'video' not in request.files:
            return jsonify({'success': False, 'error': 'No video file provided'}), 400

        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'success': False, 'error': 'No video file selected'}), 400

        animation_name = request.form.get('animationName', '').strip()
        if not animation_name:
            return jsonify({'success': False, 'error': 'Animation name is required'}), 400

        fps = request.form.get('fps', '').strip()
        try:
            fps = int(fps) if fps else 24
            if fps <= 0:
                raise ValueError()
        except ValueError:
            return jsonify({'success': False, 'error': 'FPS must be a positive integer'}), 400

        target_dir = os.path.join(SOURCE_DIR, animation_name)
        if os.path.exists(target_dir):
            return jsonify({'success': False, 'error': f'Animation "{animation_name}" already exists'}), 409

        os.makedirs(target_dir, exist_ok=False)

        if hasattr(video_file, 'save'):
            ext = os.path.splitext(video_file.filename)[1].lower() or '.mp4'
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                temp_video_path = tmp_file.name
                video_file.save(temp_video_path)

        ffmpeg_cmd = [
            'ffmpeg',
            '-y',
            '-i', temp_video_path,
            '-vf', f'fps={fps}',
            os.path.join(target_dir, 'frame_%05d.png')
        ]

        proc = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if proc.returncode != 0:
            shutil.rmtree(target_dir, ignore_errors=True)
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            return jsonify({'success': False, 'error': f'ffmpeg error: {proc.stderr.strip()[:300]}'}), 500

        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)

        frame_files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f)) and f.lower().endswith('.png')]
        frame_count = len(sorted(frame_files))

        if frame_count == 0:
            shutil.rmtree(target_dir, ignore_errors=True)
            return jsonify({'success': False, 'error': 'No frames were generated from video'}), 400

        return jsonify({'success': True, 'message': f'Imported video into "{animation_name}"', 'name': animation_name, 'frameCount': frame_count})

    except FileNotFoundError as e:
        # ffmpeg not installed or not in PATH
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir, ignore_errors=True)
        return jsonify({'success': False, 'error': 'ffmpeg not found. Install ffmpeg and ensure it is in your PATH.'}), 500

    except Exception as e:
        if 'target_dir' in locals() and os.path.exists(target_dir):
            shutil.rmtree(target_dir, ignore_errors=True)
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
                        # Preserve original format
                        file_ext = os.path.splitext(frame_file)[1]
                        original_format = img.format
                        
                        if img.mode != 'RGBA':
                            img = img.convert('RGBA')

                        width, height = img.size
                        crop_box = (crop_left, crop_top, width - crop_right, height - crop_bottom)
                        cropped_img = img.crop(crop_box)
                        new_frame_name = f'frame_{i:03d}_delay-0.03s{file_ext}'
                        new_frame_path = os.path.join(new_path, new_frame_name)
                        
                        # Save in original format to preserve quality
                        if original_format and original_format.upper() in ['PNG', 'JPEG', 'GIF', 'BMP', 'TIFF', 'WEBP']:
                            save_format = original_format.upper()
                            if save_format == 'JPEG':
                                save_format = 'JPEG'
                            cropped_img.save(new_frame_path, save_format)
                        else:
                            # Default to PNG if format is unknown
                            cropped_img.save(new_frame_path, 'PNG')
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
                            # Preserve original sprite format
                            file_ext = os.path.splitext(sprite_file)[1]
                            original_format = img.format
                            
                            if img.mode != 'RGBA':
                                img = img.convert('RGBA')

                            width, height = img.size
                            crop_box = (crop_left, crop_top, width - crop_right, height - crop_bottom)
                            cropped_img = img.crop(crop_box)
                            new_sprite_name = f'frame_{i:03d}_delay-0.03s{file_ext}'
                            new_sprite_path = os.path.join(new_sprites_path, new_sprite_name)
                            
                            # Save in original format to preserve quality
                            if original_format and original_format.upper() in ['PNG', 'JPEG', 'GIF', 'BMP', 'TIFF', 'WEBP']:
                                save_format = original_format.upper()
                                cropped_img.save(new_sprite_path, save_format)
                            else:
                                # Default to PNG if format is unknown
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


@animations_bp.route('/api/create-zoomed-animation', methods=['POST'])
def create_zoomed_animation():
    """Create a new animation by scaling frames to match the largest cropped region (centered, no interpolation)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        source_animation = data.get('sourceAnimation', '').strip()
        new_animation_name = data.get('newAnimationName', '').strip()
        crop_top_values = data.get('cropTop', [])
        crop_bottom_values = data.get('cropBottom', [])

        if not source_animation:
            return jsonify({'success': False, 'error': 'Source animation is required'}), 400
        if not new_animation_name:
            return jsonify({'success': False, 'error': 'New animation name is required'}), 400
        if not isinstance(crop_top_values, list) or not isinstance(crop_bottom_values, list):
            return jsonify({'success': False, 'error': 'cropTop and cropBottom must be arrays'}), 400

        source_path = os.path.join(SOURCE_DIR, source_animation)
        if not os.path.exists(source_path):
            return jsonify({'success': False, 'error': f'Source animation "{source_animation}" not found'}), 404

        new_path = os.path.join(SOURCE_DIR, new_animation_name)
        if os.path.exists(new_path):
            return jsonify({'success': False, 'error': f'Animation "{new_animation_name}" already exists'}), 409

        source_frame_files = get_frame_files(source_animation)
        if not source_frame_files:
            return jsonify({'success': False, 'error': f'No frames found in source animation "{source_animation}"'}), 400

        frame_count = len(source_frame_files)
        crop_top = [int(v) if str(v).strip() else 0 for v in crop_top_values]
        crop_bottom = [int(v) if str(v).strip() else 0 for v in crop_bottom_values]

        if len(crop_top) < frame_count:
            crop_top.extend([0] * (frame_count - len(crop_top)))
        if len(crop_bottom) < frame_count:
            crop_bottom.extend([0] * (frame_count - len(crop_bottom)))

        crop_top = crop_top[:frame_count]
        crop_bottom = crop_bottom[:frame_count]

        from PIL import Image

        first_frame_path = os.path.join(source_path, source_frame_files[0])
        with Image.open(first_frame_path) as first_img:
            original_width, original_height = first_img.size

        cropped_heights = []
        for i in range(frame_count):
            top = max(0, crop_top[i])
            bottom = max(0, crop_bottom[i])
            cropped_height = original_height - top - bottom
            if cropped_height <= 0:
                return jsonify({'success': False, 'error': f'Invalid crop values at frame {i}: top+bottom must be less than frame height'}), 400
            cropped_heights.append(cropped_height)

        max_cropped_height = max(cropped_heights)
        os.makedirs(new_path, exist_ok=False)

        frames_processed = 0
        for i, frame_file in enumerate(source_frame_files):
            source_frame_path = os.path.join(source_path, frame_file)
            if not os.path.exists(source_frame_path):
                continue

            try:
                with Image.open(source_frame_path) as img:
                    original_format = img.format
                    file_ext = os.path.splitext(frame_file)[1]

                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')

                    width, height = img.size
                    top = max(0, crop_top[i])
                    bottom = max(0, crop_bottom[i])
                    cropped_img = img.crop((0, top, width, height - bottom))

                    cropped_height = cropped_heights[i]
                    if cropped_height == max_cropped_height:
                        scaled_img = cropped_img
                    else:
                        scale_factor = max_cropped_height / cropped_height
                        scaled_width = max(1, int(round(width * scale_factor)))
                        scaled_height = max(1, int(round(cropped_img.height * scale_factor)))
                        scaled_img = cropped_img.resize((scaled_width, scaled_height), resample=Image.NEAREST)

                    final_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
                    paste_x = (width - scaled_img.width) // 2
                    paste_y = (height - scaled_img.height) // 2
                    final_img.paste(scaled_img, (paste_x, paste_y), scaled_img)

                    new_frame_name = f'frame_{i:03d}_delay-0.03s{file_ext}'
                    new_frame_path = os.path.join(new_path, new_frame_name)

                    if original_format and original_format.upper() in ['PNG', 'JPEG', 'GIF', 'BMP', 'TIFF', 'WEBP']:
                        save_format = original_format.upper()
                        final_img.save(new_frame_path, save_format)
                    else:
                        final_img.save(new_frame_path, 'PNG')

                    frames_processed += 1
            except Exception as e:
                print(f"Warning: Failed to process frame {frame_file}: {e}")

        if frames_processed == 0:
            shutil.rmtree(new_path, ignore_errors=True)
            return jsonify({'success': False, 'error': 'No frames were processed'}), 400

        return jsonify({
            'success': True,
            'message': f'Zoomed animation "{new_animation_name}" created successfully',
            'frameCount': frames_processed,
            'name': new_animation_name,
            'maxCroppedHeight': max_cropped_height
        })

    except Exception as e:
        if 'new_path' in locals() and os.path.exists(new_path):
            shutil.rmtree(new_path, ignore_errors=True)
        return jsonify({'success': False, 'error': str(e)}), 500