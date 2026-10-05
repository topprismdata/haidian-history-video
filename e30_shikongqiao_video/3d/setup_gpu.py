"""把 Metal GPU 写入用户偏好, 避免每次 --factory-startup 重置。
官方建议(Blender 手册 / 社区): Apple 统一内存架构下只勾 Metal GPU, 不要同时勾 CPU。
"""
import bpy
cp = bpy.context.preferences.addons['cycles'].preferences
print("available compute types:", [i.identifier for i in cp.bl_rna.properties['compute_device_type'].enum_items])
for t in ('METAL', 'NONE'):
    try:
        cp.compute_device_type = t
        devs = cp.get_devices_for_type(t)
        print("set %s -> %s" % (t, [(d.name, d.type) for d in cp.devices]))
        if any(d.type == 'METAL' for d in cp.devices):
            for d in cp.devices:
                d.use = (d.type == 'METAL')
            print("ENABLED METAL:", [(d.name, d.type, d.use) for d in cp.devices])
            bpy.ops.wm.save_userpref()
            print("SAVED_PREFS")
            break
    except Exception as e:
        print("try", t, "fail:", e)
