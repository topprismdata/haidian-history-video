# EXIF 匹配机位: 复刻 winter_20201221160537 (D810 38mm 全幅, 西南岸向东北)
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]
px, py, pz, tx, ty, tz, lens = [float(v) for v in a[:7]]
sc = bpy.context.scene
cd = bpy.data.cameras.new("EXIF"); cd.lens = lens; cd.sensor_width = 36.0
cam = bpy.data.objects.new("EXIFcam", cd); sc.collection.objects.link(cam)
cam.location = (px, py, pz)
d = Vector((tx, ty, tz)) - Vector(cam.location)
cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
sc.camera = cam
sc.render.filepath = '/tmp/exifcam.png'
sc.render.resolution_x = 1600; sc.render.resolution_y = 1067
sc.cycles.samples = 32
bpy.ops.render.render(write_still=True)
print("WROTE", bpy.data.filepaths.render_file if hasattr(bpy.data,'filepaths') else '')
