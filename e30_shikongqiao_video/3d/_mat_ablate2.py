# 消融2: 全平色 + 分别隐藏 coursing/voussoir, 定暗三角归属
import bpy, sys
m = bpy.data.materials.new("flat"); m.use_nodes = True
b = m.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
b.inputs["Roughness"].default_value = 0.9
for obj in bpy.data.objects:
    if obj.type == 'MESH' and not any(k in obj.name for k in ("water", "shore", "fog")):
        obj.data.materials.clear(); obj.data.materials.append(m)
mode = sys.argv[-1]
if mode == "nocourse":
    bpy.data.objects['coursing'].hide_render = True
elif mode == "nobody":
    bpy.data.objects['bridge_body'].hide_render = True
