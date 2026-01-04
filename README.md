# Rotoscoper

A web-based animation toolkit for creating custom frame-based animations and generating sprites with advanced color mapping capabilities. Built with Flask backend and vanilla JavaScript frontend.

## Tools

### 🎬 New Animation Tool
- Create custom animations by selecting frame ranges from existing animations
- Center point adjustment with red indicator line
- Frame alignment controls with "Apply to Rest" functionality
- Real-time animation preview and timing controls

### 🎨 Sprite Tool
- Generate sprites from animations with custom color mapping
- Extract colors from animation frames automatically
- Real-time color remapping with visual color picker interface
- Sprite opacity controls and frame visibility toggle

## Features

- ✅ Play/pause animation controls
- ✅ Adjustable frame delay (10ms - 1000ms)
- ✅ Frame range selection (start/end frames)
- ✅ Create new animations from frame ranges
- ✅ Switch between multiple animations
- ✅ Real-time animation statistics
- ✅ Color extraction and mapping
- ✅ Sprite generation and customization
- ✅ Center point alignment tools

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

### 2. Prepare Animation Frames

Place your animation frames under `Source/<animation_name>/` (for example `Source/Walk/`) with the naming pattern:
```
Source/Walk/frame_000_delay-0.03s.gif
Source/Walk/frame_001_delay-0.03s.gif
...
Source/Walk/frame_149_delay-0.03s.gif
```

### 3. Start the Server

```bash
python server.py
```

### 4. Open the Application

Navigate to: http://localhost:5000

You'll see the main tools page with links to both tools.

## Usage

### New Animation Tool
**Basic Playback:**
- Use **Play/Pause** button to control animation
- Adjust **Delay** slider to change playback speed
- Use **Frame** slider to scrub through frames

**Center Point Adjustment:**
- Use **Center X Offset** to adjust frame alignment
- Red indicator line shows current center position
- Click **Apply to Rest** to apply current offset to subsequent frames

**Creating New Animations:**
1. Set **Start Frame** and **End Frame** to select your range
2. Enter a **New animation name**
3. Click **Create Animation**
4. The new animation will be created with center adjustments applied

### Sprite Tool
**Color Extraction:**
1. Click **Extract Colors** to analyze all frames
2. Unique colors will be listed with pixel counts

**Color Mapping:**
1. Use color pickers to map source colors to target colors
2. Changes apply in real-time to all sprites

**Sprite Generation:**
1. Click **Generate Sprites** to create sprite overlays
2. Adjust **Sprite Opacity** to control visibility
3. Toggle **Show Frames** to hide/show original frames

**Switching Animations:**
- Use the **Animation dropdown** to switch between created animations
- Each tool maintains independent settings per animation

## API Endpoints

The Flask server provides these REST endpoints:

- `GET /api/animations` - List all animations with frame counts (includes per-animation `frames` and `sprites` lists)
- `POST /api/animations` - Create new animation from frame range with optional center point adjustments
- `POST /api/animations/{name}/sprites/save` - Save generated sprite images to animation folder
- `POST /api/files/save` - Save an arbitrary image file to a specified path
- `POST /api/animations/crop` - Create a cropped animation from existing animation frames and sprites

## File Structure

```
Rotoscoper/
├── index.html               # Main tools landing page
├── new-animation-tool.html  # New animation creation tool
├── sprite-tool.html         # Sprite generation tool
├── server.py               # Flask backend server
├── setup.py               # Setup script
├── requirements.txt       # Python dependencies
└── Source/                # Animation folders
    ├── Walk/             # Original animation
    │   ├── frame_000_delay-0.03s.gif
    │   ├── frame_001_delay-0.03s.gif
    │   └── ...
    ├── MyAnimation1/     # Created animations
    └── MyAnimation2/
```

## Technical Details

### Server-Side Features
- **Frame copying**: Copies selected frame ranges to new animation folders
- **Advanced padding**: Applies precise center point adjustments with transparent padding using PIL
- **Sequential renaming**: Renumbers copied frames starting from 0 for consistency
- **Input validation**: Validates frame ranges, animation names, and prevents overwrites
- **CORS support**: Enables cross-origin requests for local development
- **Sprite storage**: Saves generated sprites to dedicated folders within animations
- **Error handling**: Comprehensive error responses with cleanup on failure

### Client-Side Features
- **Modular architecture**: Each tool operates independently with isolated functionality
- **Dynamic content**: Real-time loading of animations and frame data from server
- **Live preview**: Instant visual feedback for animations and color changes
- **Color analysis**: Client-side pixel-level color extraction and histogram generation
- **Interactive controls**: Responsive sliders, dropdowns, and color pickers
- **State management**: Persistent settings per animation across tool switches

## Troubleshooting

### Server won't start
- Verify Python 3.6+ is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Check port 5000 availability (stop other Flask apps)
- Run setup script: `python setup.py`

### No animations visible
- If no animations are visible: add frame files under `Source/<animation_name>/` (e.g., `Source/Walk/`)
- Verify frame naming pattern: `frame_XXX_delay-0.03s.gif`
- Check browser console (F12) for JavaScript errors
- Confirm server is running at http://localhost:5000

### Animation creation fails
- Verify frame range is valid (start < end, within bounds)
- Check source animation exists and has frames
- Ensure new animation name is unique
- Verify sufficient disk space for frame copying

### Color mapping not working
- Check that frames are loaded properly
- Ensure browser supports HTML5 Canvas
- Verify image files are valid GIF/PNG formats
- Check for JavaScript errors in browser console

## Development

### Architecture
- **Frontend**: Vanilla JavaScript with HTML5 Canvas for image processing
- **Backend**: Flask with PIL for image manipulation and file operations
- **Communication**: RESTful API with JSON responses
- **Storage**: File-based with organized directory structure

### Making Changes
1. **Main Page**: Edit `index.html` for landing page and navigation
2. **Animation Tool**: Edit `new-animation-tool.html` for frame creation features
3. **Sprite Tool**: Edit `sprite-tool.html` for color mapping and sprite generation
4. **Backend Logic**: Edit `server.py` for API endpoints and image processing
5. **Dependencies**: Update `requirements.txt` for new Python packages

### Development Server
The Flask server runs in debug mode with auto-reload enabled:
- Python changes reload automatically
- HTML/JS changes require browser refresh
- Each tool is modular and independently testable

### Adding Features
- New API endpoints: Add routes to `server.py`
- UI components: Modify respective HTML files
- Image processing: Extend PIL functions in `server.py`
- Client-side logic: Add JavaScript to tool files