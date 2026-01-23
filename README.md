# che-blender-mcp

MCP Server for Blender integration - execute scripts, capture renders, and control scenes via Claude.

## Features

- **execute_script**: Execute arbitrary Python code in Blender with full bpy access
- **list_objects**: List all scene objects with basic info (name, type, location, visibility)
- **get_object_info**: Get detailed information about a specific object (mesh data, light settings, camera params)
- **render**: Render the current scene and return the image (supports Cycles and EEVEE)
- **get_scene_info**: Get comprehensive scene information (cameras, lights, render settings)
- **screenshot**: Capture a viewport screenshot

## Requirements

- macOS (tested on Mac M4 Max)
- Blender 4.0+ (recommended: Blender 5.0)
- Python 3.10+

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/kiki830621/che-blender-mcp.git
cd che-blender-mcp

# Install in development mode
pip install -e .
```

### Configure Blender Path

By default, the server looks for Blender at `/Applications/Blender.app/Contents/MacOS/Blender`.

To use a different path, set the `BLENDER_PATH` environment variable:

```bash
export BLENDER_PATH="/path/to/blender"
```

## Usage

### With Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "che-blender-mcp": {
      "command": "che-blender-mcp",
      "args": [],
      "env": {
        "BLENDER_PATH": "/Applications/Blender.app/Contents/MacOS/Blender"
      }
    }
  }
}
```

### Running Manually

```bash
che-blender-mcp
```

## Tool Examples

### Execute Script

```python
# Create a cube
import bpy
bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))
print(f"Created cube: {bpy.context.active_object.name}")
```

### List Objects

Lists all objects in the scene with their type, location, and visibility status.

### Render Scene

Renders the scene with configurable:
- Resolution (default: 1920x1080)
- Samples (default: 128 for Cycles)
- Engine (CYCLES or BLENDER_EEVEE_NEXT)

Returns the rendered image as base64-encoded PNG.

## Development

### Project Structure

```
che-blender-mcp/
├── src/
│   └── che_blender_mcp/
│       ├── __init__.py
│       ├── __main__.py
│       └── server.py          # Main MCP server implementation
├── mcpb/
│   ├── manifest.json          # mcpb package manifest
│   └── PRIVACY.md
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── LICENSE
```

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Che Cheng

## Links

- [GitHub Repository](https://github.com/kiki830621/che-blender-mcp)
- [Issues](https://github.com/kiki830621/che-blender-mcp/issues)
