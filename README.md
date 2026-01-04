# Rotoscoper

A web-based animation toolkit for creating custom frame-based animations and generating sprites with advanced color mapping capabilities. Built with Flask backend and vanilla JavaScript frontend.

## Tools

The `index.html` file links to all available tools. Tool files:

- `new-animation-tool.html` — Create custom animations from existing frames.
- `sprite-tool.html` — Generate and edit sprites and color mappings.
- `texture-tool.html` — Apply textures and save processed images.
- `crop-tool.html` — Crop animations and export cropped animations.
- `remove-background-tool.html` — Remove backgrounds from animation frames and save a transparent animation.
- `export-tool.html` — Export generated assets for use in projects.

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
- rembg (for background removal)

Note: After pulling changes, run:

```bash
pip install -r requirements.txt
```

`rembg` requires additional model downloads the first time it's used; this will happen automatically when the server runs the first background-removal job.

If you hit an import error mentioning `onnxruntime`, install the runtime manually. For most users (CPU-only):

```bash
python -m pip install onnxruntime
```

If you have a CUDA-enabled GPU and want GPU acceleration, install the GPU build instead (ensure your CUDA/cuDNN versions are compatible):

```bash
python -m pip install onnxruntime-gpu
```

After installing, verify imports in the same Python environment used to run the server:

```bash
python -c "import rembg; import onnxruntime; print('rembg OK, onnxruntime', onnxruntime.__version__)"
```

If verification fails, make sure you ran the pip install with the same Python executable (for example: `C:\Path\To\python.exe -m pip install -r requirements.txt`).
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

