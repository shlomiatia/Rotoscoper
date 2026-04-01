#!/usr/bin/env python3
"""
Setup script for the Animation Player
This script will install dependencies and set up the server
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[OK] {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_python():
    """Check if Python is available"""
    try:
        version = sys.version_info
        if version.major >= 3 and version.minor >= 6:
            print(f"[OK] Python {version.major}.{version.minor}.{version.micro} is available")
            return True
        else:
            print("[ERROR] Python 3.6 or higher is required")
            return False
    except Exception as e:
        print(f"[ERROR] Error checking Python version: {e}")
        return False

def check_ffmpeg():
    """Verify ffmpeg is installed and try to install it via package manager."""
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('[OK] ffmpeg is installed')
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print('[WARN] ffmpeg not found on PATH')

    platform = sys.platform
    if platform.startswith('linux'):
        print('[INFO] Trying to install ffmpeg with apt-get')
        if run_command('sudo apt-get update && sudo apt-get install -y ffmpeg', 'Installing ffmpeg (Linux apt)'):
            return True
    elif platform == 'darwin':
        print('[INFO] Trying to install ffmpeg with brew')
        if run_command('brew install ffmpeg', 'Installing ffmpeg (macOS brew)'):
            return True
    elif platform.startswith('win'):
        print('[INFO] Trying to install ffmpeg with winget (or Chocolatey)')
        if run_command('winget install --id Gyan.FFmpeg -e --silent', 'Installing ffmpeg (Windows winget)'):
            return True
        if run_command('choco install ffmpeg -y', 'Installing ffmpeg (Windows chocolatey)'):
            return True

    print('[ERROR] ffmpeg is required for video import; please install it manually from https://ffmpeg.org/download.html')
    return False


def main():
    print("Animation Player Setup")
    print("=" * 50)

    # Check Python
    if not check_python():
        sys.exit(1)

    # Install dependencies using the same Python executable to avoid environment mismatches
    pip_cmd = f'"{sys.executable}" -m pip install -r requirements.txt'
    if not run_command(pip_cmd, "Installing Python dependencies"):
        print("\nIf pip install failed, try:\n  python -m pip install Flask==2.3.3 Flask-CORS==4.0.0 Pillow rembg")
        print("Or install requirements directly using the same python executable:\n  {sys.executable} -m pip install -r requirements.txt")
        sys.exit(1)

    # Ensure ffmpeg is installed
    if not check_ffmpeg():
        print('\n[ERROR] ffmpeg installation/check failed. Video import will not work until ffmpeg is installed.')
        sys.exit(1)

    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("\nTo start the server, run:")
    print("  python server.py")
    print("\nThen open your browser to:")
    print("  http://localhost:5000")
    print("\nPress Ctrl+C to stop the server when running.")

if __name__ == '__main__':
    main()