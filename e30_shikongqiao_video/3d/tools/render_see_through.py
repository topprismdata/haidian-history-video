# -*- coding: utf-8 -*-
"""Debug机位: 低水位、明亮天空、正对中央大拱(第9孔), 穿透整个券洞看到对侧水面与地平线。

二审硬核要求: 彻底终结"券洞未切穿/内部横杠"的疑虑, 证明贯通几何真实性。
用法: blender -b e30_bridge.blend --python tools/render_see_through.py
"""
import bpy, os, sys, math
from mathutils import Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

# Open current blend file
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, "e30_bridge.blend"))
sc = bpy.context.scene

# Metal GPU setup
cp = bpy.context.preferences.addons['cycles'].preferences
try: cp.compute_device_type = 'METAL'
except Exception: pass
for d in cp.devices: d.use = (d.type == 'METAL')
sc.cycles.device = 'GPU'
sc.cycles.samples = 64
sc.cycles.use_denoising = True

# Central arch is at local x=0. Bridge axis is rotated -112 deg (BRIDGE_AXIS_AZ = 112)
AXIS = math.radians(112.0)
# Bridge direction B (rotated)
B = Vector((math.cos(-AXIS), math.sin(-AXIS), 0.0))
# Bridge normal N (pointing perpendicular to bridge face)
N = Vector((-B.y, B.x, 0.0))

# Center arch position in world:
# Central arch center is at (0, 0, Z_springer) in local coordinates
# In world coordinates, local (0, 0, 0) is at world (0, 0, 0)
arch_center = Vector((0.0, 0.0, 2.5)) # middle of the 8.5m arch

# Camera positioned in front of central arch along normal N
cam_dist = 28.0
cam_pos = arch_center + N * cam_dist + Vector((0.0, 0.0, -0.6)) # low elevation ~1.9m

cd = bpy.data.cameras.new("CamSeeThrough")
cd.lens = 65.0  # slight telephoto to look right down the throat of the arch
cam = bpy.data.objects.new("CamSeeThrough", cd)
bpy.context.collection.objects.link(cam)
cam.location = cam_pos

# Aim straight through the arch center
aim = arch_center + Vector((0.0, 0.0, 0.2))
direction = aim - cam.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot_quat.to_euler()
sc.camera = cam

# Adjust lighting: bright sky with low sun reflecting through
for light in bpy.data.lights:
    light.energy = 4.5

# Render
out_path = os.path.join(HERE, "delivery", "render_arch_see_through.png")
sc.render.resolution_x = 1600
sc.render.resolution_y = 900
sc.render.filepath = out_path
bpy.ops.render.render(write_still=True)
print("WROTE", out_path)
