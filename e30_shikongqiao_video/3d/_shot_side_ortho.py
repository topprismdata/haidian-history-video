# 正交侧视: 与历史侧视照做曲线直接叠比
import bpy, sys, math
from mathutils import Vector
sc = bpy.context.scene
cd = bpy.data.cameras.new("SO"); cd.type = 'ORTHO'; cd.ortho_scale = 160
cam = bpy.data.objects.new("SOcam", cd); sc.collection.objects.link(cam)
cam.location = (0, -120, 4.2)
cam.rotation_euler = (math.radians(90), 0, 0)
sc.camera = cam
sc.render.filepath = '/tmp/side_ortho.png'
sc.render.resolution_x = 1600; sc.render.resolution_y = 500
sc.cycles.samples = 24
bpy.ops.render.render(write_still=True)
print("WROTE side_ortho")
