# Rotoscoper Tools

A collection of web-based animation tools for creating custom animations and generating sprites with color mapping capabilities.

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

```bash
# Install Python dependencies
python setup.py
```

Or manually:
```bash
pip install Flask==2.3.3 Flask-CORS==4.0.0
```

### 2. Prepare Animation Frames

Make sure your animation frames are in the `Source/Walk/` directory with the naming pattern:
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

The Flask server provides these endpoints:

- `GET /api/animations` - List all animations
- `POST /api/animations` - Create new animation from frame range
- `GET /api/animations/{name}/frames` - Get animation info
- `DELETE /api/animations/{name}` - Delete animation (except original)

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
- **Frame copying**: Copies selected frame ranges to new folders
- **Center point padding**: Applies frame alignment adjustments during creation
- **Automatic renaming**: Renumbers frames sequentially (0, 1, 2, ...)
- **Validation**: Checks for duplicate names, invalid ranges
- **CORS support**: Enables cross-origin requests

### Client-Side Features
- **Isolated tools**: Each tool runs independently with its own functionality
- **Dynamic loading**: Fetches available animations from server
- **Real-time updates**: Updates UI based on server responses
- **Color processing**: Client-side color extraction and sprite generation
- **Error handling**: Graceful fallbacks for network issues

## Troubleshooting

### Server won't start
- Check that Python 3.6+ is installed
- Install dependencies: `pip install -r requirements.txt`
- Check that port 5000 is available

### No animations visible
- Ensure `Source/Walk/` directory exists
- Check that frame files follow naming pattern: `frame_XXX_delay-0.03s.gif`
- Check browser console for errors

### Animation creation fails
- Verify frame range is valid (start < end)
- Check that source animation exists
- Ensure animation name doesn't already exist

## Development

To modify the tools:

1. **Main Page**: Edit `index.html`
2. **New Animation Tool**: Edit `new-animation-tool.html`
3. **Sprite Tool**: Edit `sprite-tool.html`
4. **Backend**: Edit `server.py`
5. **Restart server** to see changes (for HTML files)

The server runs in debug mode by default, so Python changes are auto-reloaded. Each tool is completely isolated, so changes to one won't affect the other.