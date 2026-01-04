# Rotoscoper

A web-based animation toolkit for creating custom frame-based animations and generating sprites with advanced color mapping capabilities. Built with Flask backend and vanilla JavaScript frontend.

## Tools

- **New Animation Tool** — Create custom animations from existing frames.
- **Sprite Tool** — Generate and edit sprites and color mappings.
- **Texture Tool** — Apply textures and save processed images.
- **Crop Tool** — Crop animations and export cropped animations.
- **Export Tool** — Export generated assets for use in projects.

## Quick Start

### 1. Install Dependencies

**Automated Setup:**
```bash
python setup.py
```

**Manual Installation:**
```bash
pip install -r requirements.txt
```

**Dependencies:**
- Python 3.6+
- Flask 2.3.3
- Flask-CORS 4.0.0
- Pillow 10.0.0+

### 2. Start the Server

```bash
python server.py
```

### 3. Open the Application

Navigate to: http://localhost:5000

You'll see the main tools page with links to the available tools.

## API Endpoints

The Flask server provides these REST endpoints:

- `GET /api/animations` - List all animations with frame counts (includes per-animation `frames` and `sprites` lists)
- `POST /api/animations` - Create new animation from frame range with optional center point adjustments
- `POST /api/animations/{name}/sprites/save` - Save generated sprite images to animation folder
- `POST /api/files/save` - Save an arbitrary image file to a specified path
- `POST /api/animations/crop` - Create a cropped animation from existing animation frames and sprites

