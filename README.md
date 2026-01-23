# che-blender-mcp

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![macOS](https://img.shields.io/badge/macOS-13.0%2B-blue)](https://www.apple.com/macos/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

**Blender MCP Server** - Execute scripts, capture renders, and control 3D scenes via Claude.

---

## Features

- **6 tools** for comprehensive Blender control
- **Execute arbitrary Python** code with full `bpy` access
- **Render scenes** and return images directly to Claude
- **Supports Cycles & EEVEE** render engines
- **Zero GUI required** - runs Blender in background mode

---

## Quick Start

### For Claude Code (CLI)

```bash
# Clone and install
git clone https://github.com/kiki830621/che-blender-mcp.git
cd che-blender-mcp
pip install -e .

# Add to Claude Code
claude mcp add che-blender-mcp -- python3 -m che_blender_mcp
```

### For Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "che-blender-mcp": {
      "command": "python3",
      "args": ["-m", "che_blender_mcp"],
      "env": {
        "BLENDER_PATH": "/Applications/Blender.app/Contents/MacOS/Blender"
      }
    }
  }
}
```

---

## Configuration

### Blender Path

By default, the server looks for Blender at:
```
/Applications/Blender.app/Contents/MacOS/Blender
```

To use a different path, set the `BLENDER_PATH` environment variable:

**Claude Code:**
```bash
claude mcp add che-blender-mcp \
  --env BLENDER_PATH=/path/to/blender \
  -- python3 -m che_blender_mcp
```

**Claude Desktop:**
```json
{
  "mcpServers": {
    "che-blender-mcp": {
      "command": "python3",
      "args": ["-m", "che_blender_mcp"],
      "env": {
        "BLENDER_PATH": "/path/to/blender"
      }
    }
  }
}
```

---

## All 6 Tools

| Tool | Description |
|------|-------------|
| `execute_script` | Execute arbitrary Python code in Blender with full `bpy` access |
| `list_objects` | List all scene objects with name, type, location, visibility |
| `get_object_info` | Get detailed info: mesh vertices/faces, light energy/color, camera lens |
| `render` | Render scene and return base64-encoded PNG image |
| `get_scene_info` | Get cameras, lights, render settings, frame range |
| `screenshot` | Capture a viewport screenshot (renders at 50% resolution for speed) |

---

## Tool Parameters

### execute_script

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `script` | string | ✅ | Python code to execute |
| `blend_file` | string | | Path to .blend file to open first |

### list_objects

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `blend_file` | string | | Path to .blend file to open |
| `object_type` | string | | Filter: MESH, CAMERA, LIGHT, EMPTY, ARMATURE |

### get_object_info

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `object_name` | string | ✅ | Name of the object to inspect |
| `blend_file` | string | | Path to .blend file to open |

### render

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `blend_file` | string | ✅ | Path to .blend file to render |
| `resolution_x` | integer | | Width in pixels (default: 1920) |
| `resolution_y` | integer | | Height in pixels (default: 1080) |
| `samples` | integer | | Cycles samples (default: 128) |
| `engine` | string | | CYCLES or BLENDER_EEVEE_NEXT (default: CYCLES) |

### get_scene_info

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `blend_file` | string | | Path to .blend file to open |

### screenshot

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `blend_file` | string | ✅ | Path to .blend file |
| `view` | string | | CAMERA, TOP, FRONT, RIGHT (default: CAMERA) |

---

## Usage Examples

```
"Open my_scene.blend and list all objects"
"Render /path/to/scene.blend at 1080p with 256 samples"
"Execute this script in Blender: bpy.ops.mesh.primitive_cube_add()"
"Get info about the object named 'Camera'"
"Show me the scene information for my project"
```

### Example: Create and Render a Scene

```
"Execute this script:
import bpy
bpy.ops.mesh.primitive_monkey_add(location=(0, 0, 0))
bpy.ops.object.shade_smooth()
"

"Now render the scene at 720p"
```

---

## Requirements

- macOS 13.0 (Ventura) or later
- [Blender](https://www.blender.org/) 4.0+ (recommended: Blender 5.0)
- Python 3.10+

---

## Privacy

This extension:
- Runs entirely locally on your Mac
- Does not transmit any data externally
- Only accesses local Blender installation and specified blend files
- See [PRIVACY.md](mcpb/PRIVACY.md) for full details

---

## Version History

| Version | Changes |
|---------|---------|
| v0.1.0 | Initial release with 6 tools: execute_script, list_objects, get_object_info, render, get_scene_info, screenshot |

---

## Related Projects

- [che-things-mcp](https://github.com/kiki830621/che-things-mcp) - MCP server for Things 3 task management
- [che-ical-mcp](https://github.com/kiki830621/che-ical-mcp) - MCP server for macOS Calendar & Reminders

---

## License

MIT

## Author

[Che Cheng](https://github.com/kiki830621)
