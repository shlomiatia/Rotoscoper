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

def check_source_directory():
    """Check if Source/Walk directory exists"""
    walk_dir = os.path.join('Source', 'Walk')
    if os.path.exists(walk_dir):
        frame_files = [f for f in os.listdir(walk_dir) if f.startswith('frame_') and f.endswith('.gif')]
        if frame_files:
            print(f"[OK] Found {len(frame_files)} frames in Source/Walk/")
            return True
        else:
            print("[ERROR] No frame files found in Source/Walk/")
            return False
    else:
        print("[ERROR] Source/Walk directory not found")
        print("Please make sure your animation frames are in Source/Walk/")
        return False

def main():
    print("Animation Player Setup")
    print("=" * 50)

    # Check Python
    if not check_python():
        sys.exit(1)

    # Check source directory
    if not check_source_directory():
        print("\nWarning: Animation frames not found.")
        print("The server will still start, but you won't see animations until")
        print("you place your frame files in Source/Walk/")

    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        print("\nIf pip install failed, try:")
        print("  python -m pip install Flask==2.3.3 Flask-CORS==4.0.0")
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