# src/che_blender_mcp/server.py
"""
Blender MCP Server - Control Blender via MCP protocol

Tools:
- execute_script: Execute Python code in Blender
- list_objects: List all scene objects
- get_object_info: Get detailed info about an object
- screenshot: Capture viewport screenshot
- render: Render current view and return image
- get_scene_info: Get scene information (camera, lights, settings)
"""

import asyncio
import subprocess
import tempfile
import base64
import json
import os
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent

app = Server("che-blender-mcp")

# Default Blender path for macOS
BLENDER_PATH = os.environ.get(
    "BLENDER_PATH",
    "/Applications/Blender.app/Contents/MacOS/Blender"
)


def run_blender_script(script: str, background: bool = True) -> dict:
    """Execute a Python script in Blender and return the result."""

    # Create a wrapper script that captures output
    wrapper_script = '''
import bpy
import json
import sys

# Redirect stdout to capture print statements
import io
old_stdout = sys.stdout
sys.stdout = captured_output = io.StringIO()

result = {"success": True, "output": "", "error": ""}

try:
    # Execute the user script
    exec("""''' + script.replace('"""', '\\"\\"\\"') + '''""")
    result["output"] = captured_output.getvalue()
except Exception as e:
    result["success"] = False
    result["error"] = str(e)
    result["output"] = captured_output.getvalue()
finally:
    sys.stdout = old_stdout

# Write result to a temp file
import tempfile
result_file = tempfile.gettempdir() + "/blender_mcp_result.json"
with open(result_file, "w") as f:
    json.dump(result, f)

print("BLENDER_MCP_RESULT:" + result_file)
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(wrapper_script)
        script_path = f.name

    try:
        cmd = [BLENDER_PATH]
        if background:
            cmd.append("--background")
        cmd.extend(["--python", script_path])

        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Find result file path from output
        result_file = None
        for line in process.stdout.split('\n'):
            if line.startswith("BLENDER_MCP_RESULT:"):
                result_file = line.split(":", 1)[1].strip()
                break

        if result_file and os.path.exists(result_file):
            with open(result_file) as f:
                return json.load(f)
        else:
            return {
                "success": False,
                "output": process.stdout,
                "error": process.stderr or "Could not find result file"
            }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Script execution timed out (60s)"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}
    finally:
        os.unlink(script_path)


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="execute_script",
            description="Execute arbitrary Python code in Blender. The script has full access to bpy module.",
            inputSchema={
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "Python code to execute in Blender"
                    },
                    "blend_file": {
                        "type": "string",
                        "description": "Optional: Path to .blend file to open first"
                    }
                },
                "required": ["script"]
            }
        ),
        Tool(
            name="list_objects",
            description="List all objects in the current Blender scene with basic info",
            inputSchema={
                "type": "object",
                "properties": {
                    "blend_file": {
                        "type": "string",
                        "description": "Optional: Path to .blend file to open"
                    },
                    "object_type": {
                        "type": "string",
                        "description": "Filter by type: MESH, CAMERA, LIGHT, EMPTY, ARMATURE, etc."
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_object_info",
            description="Get detailed information about a specific object",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_name": {
                        "type": "string",
                        "description": "Name of the object to inspect"
                    },
                    "blend_file": {
                        "type": "string",
                        "description": "Optional: Path to .blend file to open"
                    }
                },
                "required": ["object_name"]
            }
        ),
        Tool(
            name="render",
            description="Render the current scene and return the image as base64",
            inputSchema={
                "type": "object",
                "properties": {
                    "blend_file": {
                        "type": "string",
                        "description": "Path to .blend file to render"
                    },
                    "resolution_x": {
                        "type": "integer",
                        "description": "Render width in pixels (default: 1920)"
                    },
                    "resolution_y": {
                        "type": "integer",
                        "description": "Render height in pixels (default: 1080)"
                    },
                    "samples": {
                        "type": "integer",
                        "description": "Render samples for Cycles (default: 128)"
                    },
                    "engine": {
                        "type": "string",
                        "description": "Render engine: CYCLES or BLENDER_EEVEE_NEXT (default: CYCLES)"
                    }
                },
                "required": ["blend_file"]
            }
        ),
        Tool(
            name="get_scene_info",
            description="Get comprehensive scene information including cameras, lights, and render settings",
            inputSchema={
                "type": "object",
                "properties": {
                    "blend_file": {
                        "type": "string",
                        "description": "Optional: Path to .blend file to open"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="screenshot",
            description="Capture a viewport screenshot (requires Blender to be running with UI)",
            inputSchema={
                "type": "object",
                "properties": {
                    "blend_file": {
                        "type": "string",
                        "description": "Path to .blend file to open"
                    },
                    "view": {
                        "type": "string",
                        "description": "Camera view: CAMERA, TOP, FRONT, RIGHT, etc. (default: CAMERA)"
                    }
                },
                "required": ["blend_file"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent]:

    if name == "execute_script":
        script = arguments.get("script", "")
        blend_file = arguments.get("blend_file")

        if blend_file:
            script = 'bpy.ops.wm.open_mainfile(filepath="' + blend_file + '")\n' + script

        result = run_blender_script(script)

        if result["success"]:
            output = result["output"] if result["output"] else "Script executed successfully (no output)"
            return [TextContent(type="text", text=output)]
        else:
            error_msg = "Script failed: " + result["error"]
            if result["output"]:
                error_msg = error_msg + "\nOutput before error:\n" + result["output"]
            return [TextContent(type="text", text=error_msg)]

    elif name == "list_objects":
        blend_file = arguments.get("blend_file")
        object_type = arguments.get("object_type")

        script = '''
import bpy
import json

objects = []
for obj in bpy.data.objects:
    obj_info = {
        "name": obj.name,
        "type": obj.type,
        "location": [round(x, 3) for x in obj.location],
        "visible": obj.visible_get()
    }
    objects.append(obj_info)

'''
        if object_type:
            script += 'objects = [o for o in objects if o["type"] == "' + object_type + '"]\n'

        script += 'print(json.dumps(objects, indent=2))'

        if blend_file:
            script = 'bpy.ops.wm.open_mainfile(filepath="' + blend_file + '")\n' + script

        result = run_blender_script(script)

        if result["success"]:
            return [TextContent(type="text", text=result["output"])]
        else:
            return [TextContent(type="text", text="Error: " + result["error"])]

    elif name == "get_object_info":
        object_name = arguments.get("object_name", "")
        blend_file = arguments.get("blend_file")

        script = '''
import bpy
import json

obj = bpy.data.objects.get("''' + object_name + '''")
if obj is None:
    print(json.dumps({"error": "Object not found: ''' + object_name + '''"}))
else:
    info = {
        "name": obj.name,
        "type": obj.type,
        "location": [round(x, 3) for x in obj.location],
        "rotation_euler": [round(x, 3) for x in obj.rotation_euler],
        "scale": [round(x, 3) for x in obj.scale],
        "dimensions": [round(x, 3) for x in obj.dimensions],
        "visible": obj.visible_get(),
        "parent": obj.parent.name if obj.parent else None,
        "children": [c.name for c in obj.children],
    }

    # Add mesh-specific info
    if obj.type == "MESH":
        mesh = obj.data
        info["mesh"] = {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "faces": len(mesh.polygons),
            "materials": [m.name if m else None for m in obj.data.materials]
        }

    # Add light-specific info
    elif obj.type == "LIGHT":
        light = obj.data
        info["light"] = {
            "type": light.type,
            "energy": light.energy,
            "color": [round(c, 3) for c in light.color]
        }

    # Add camera-specific info
    elif obj.type == "CAMERA":
        cam = obj.data
        info["camera"] = {
            "type": cam.type,
            "lens": cam.lens,
            "sensor_width": cam.sensor_width
        }

    print(json.dumps(info, indent=2))
'''

        if blend_file:
            script = 'bpy.ops.wm.open_mainfile(filepath="' + blend_file + '")\n' + script

        result = run_blender_script(script)

        if result["success"]:
            return [TextContent(type="text", text=result["output"])]
        else:
            return [TextContent(type="text", text="Error: " + result["error"])]

    elif name == "render":
        blend_file = arguments.get("blend_file")
        resolution_x = arguments.get("resolution_x", 1920)
        resolution_y = arguments.get("resolution_y", 1080)
        samples = arguments.get("samples", 128)
        engine = arguments.get("engine", "CYCLES")

        if not blend_file:
            return [TextContent(type="text", text="Error: blend_file is required for rendering")]

        output_path = tempfile.gettempdir() + "/blender_mcp_render.png"

        script = '''
import bpy

# Open the blend file
bpy.ops.wm.open_mainfile(filepath="''' + blend_file + '''")

# Set render settings
scene = bpy.context.scene
scene.render.engine = "''' + engine + '''"
scene.render.resolution_x = ''' + str(resolution_x) + '''
scene.render.resolution_y = ''' + str(resolution_y) + '''
scene.render.resolution_percentage = 100
scene.render.filepath = "''' + output_path + '''"
scene.render.image_settings.file_format = "PNG"

# Set samples for Cycles
if scene.render.engine == "CYCLES":
    scene.cycles.samples = ''' + str(samples) + '''
    scene.cycles.use_denoising = True

# Render
bpy.ops.render.render(write_still=True)
print("Render complete: ''' + output_path + '''")
'''

        result = run_blender_script(script)

        if result["success"] and os.path.exists(output_path):
            with open(output_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            os.unlink(output_path)
            return [
                TextContent(type="text", text="Render completed successfully"),
                ImageContent(type="image", data=image_data, mimeType="image/png")
            ]
        else:
            return [TextContent(type="text", text="Render failed: " + result.get("error", "Unknown error"))]

    elif name == "get_scene_info":
        blend_file = arguments.get("blend_file")

        script = '''
import bpy
import json

scene = bpy.context.scene
info = {
    "name": scene.name,
    "frame_current": scene.frame_current,
    "frame_start": scene.frame_start,
    "frame_end": scene.frame_end,
    "fps": scene.render.fps,
    "render": {
        "engine": scene.render.engine,
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y,
        "resolution_percentage": scene.render.resolution_percentage,
    },
    "cameras": [],
    "lights": [],
    "object_count": len(bpy.data.objects),
    "mesh_count": len(bpy.data.meshes),
    "material_count": len(bpy.data.materials)
}

# Active camera
if scene.camera:
    info["active_camera"] = scene.camera.name

# List all cameras
for obj in bpy.data.objects:
    if obj.type == "CAMERA":
        info["cameras"].append({
            "name": obj.name,
            "location": [round(x, 3) for x in obj.location],
            "lens": obj.data.lens
        })
    elif obj.type == "LIGHT":
        info["lights"].append({
            "name": obj.name,
            "type": obj.data.type,
            "energy": obj.data.energy,
            "location": [round(x, 3) for x in obj.location]
        })

# Cycles specific
if scene.render.engine == "CYCLES":
    info["render"]["cycles"] = {
        "samples": scene.cycles.samples,
        "use_denoising": scene.cycles.use_denoising,
        "device": scene.cycles.device
    }

print(json.dumps(info, indent=2))
'''

        if blend_file:
            script = 'bpy.ops.wm.open_mainfile(filepath="' + blend_file + '")\n' + script

        result = run_blender_script(script)

        if result["success"]:
            return [TextContent(type="text", text=result["output"])]
        else:
            return [TextContent(type="text", text="Error: " + result["error"])]

    elif name == "screenshot":
        blend_file = arguments.get("blend_file")
        view = arguments.get("view", "CAMERA")

        if not blend_file:
            return [TextContent(type="text", text="Error: blend_file is required for screenshot")]

        output_path = tempfile.gettempdir() + "/blender_mcp_screenshot.png"

        # Note: Viewport screenshot requires Blender with UI, so we use render instead
        script = '''
import bpy

bpy.ops.wm.open_mainfile(filepath="''' + blend_file + '''")

# Set view
view_type = "''' + view + '''"
if view_type != "CAMERA":
    # For non-camera views, we need to set up a temporary camera
    # This is a simplified approach - full viewport screenshot would need UI
    pass

# Use render for now as viewport requires UI
scene = bpy.context.scene
scene.render.filepath = "''' + output_path + '''"
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 50  # Lower res for quick preview

bpy.ops.render.render(write_still=True)
print("Screenshot saved: ''' + output_path + '''")
'''

        result = run_blender_script(script)

        if result["success"] and os.path.exists(output_path):
            with open(output_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            os.unlink(output_path)
            return [
                TextContent(type="text", text="Screenshot captured"),
                ImageContent(type="image", data=image_data, mimeType="image/png")
            ]
        else:
            return [TextContent(type="text", text="Screenshot failed: " + result.get("error", "Unknown error"))]

    raise ValueError("Unknown tool: " + name)


def main():
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    asyncio.run(run())


if __name__ == "__main__":
    main()
