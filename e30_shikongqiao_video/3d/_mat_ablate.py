# M17 受控二分: 覆盖全场景材质为纯平色, 判定暗三角是几何自投影还是贴图
import bpy
m = bpy.data.materials.new("flat"); m.use_nodes = True
b = m.node_tree.nodes.get("Principled BSDF")
b.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
b.inputs["Roughness"].default_value = 0.9
for obj in bpy.data.objects:
    if obj.type == 'MESH' and "water" not in obj.name and "shore" not in obj.name and "tree" not in obj.name.lower():
        obj.data.materials.clear(); obj.data.materials.append(m)
