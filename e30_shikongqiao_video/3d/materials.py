"""程序化石材: 石砌分缝 + 风化 + 水线痕。全部节点生成, 无外部贴图。"""
import bpy


def _principled(mat):
    return mat.node_tree.nodes.get("Principled BSDF")


def stone_material(name, base_rgb, joint=0.020, course_h=0.42, weather=0.55,
                   waterline_z=0.0, waterline_h=0.55):
    """古建石构材质: 分层砌缝(横向) + 竖向错缝 + 风化斑驳 + 水线以下更深更绿。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = 0.85
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.30

    # 世界坐标 -> 分离 XYZ (单位=米)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])

    # ── 砌缝: 横向按 course_h 分层, 每层内竖向错缝(奇偶层半宽偏移) ──
    z_scaled = nt.nodes.new("ShaderNodeMath"); z_scaled.operation = 'MULTIPLY'
    nt.links.new(sep.outputs["Z"], z_scaled.inputs[0])
    z_scaled.inputs[1].default_value = 1.0 / course_h
    z_floor = nt.nodes.new("ShaderNodeMath"); z_floor.operation = 'FLOOR'
    nt.links.new(z_scaled.outputs[0], z_floor.inputs[0])
    z_frac = nt.nodes.new("ShaderNodeMath"); z_frac.operation = 'FRACT'
    nt.links.new(z_scaled.outputs[0], z_frac.inputs[0])
    # 奇偶层
    z_par = nt.nodes.new("ShaderNodeMath"); z_par.operation = 'PINGPONG'
    z_par.inputs[1].default_value = 1.0; z_par.inputs[2].default_value = 1.0
    nt.links.new(z_floor.outputs[0], z_par.inputs[0])
    # 竖向: X 方向按半块错开
    x_s = nt.nodes.new("ShaderNodeMath"); x_s.operation = 'MULTIPLY'
    nt.links.new(sep.outputs["X"], x_s.inputs[0])
    x_s.inputs[1].default_value = 1.0 / (course_h * 2.0)
    x_f = nt.nodes.new("ShaderNodeMath"); x_f.operation = 'FRACT'
    nt.links.new(x_s.outputs[0], x_f.inputs[0])
    # 奇数层: 竖缝位置反向
    x_add = nt.nodes.new("ShaderNodeMath"); x_add.operation = 'ADD'
    nt.links.new(x_f.outputs[0], x_add.inputs[0])
    x_add.inputs[1].default_value = 0.5
    x_shift = nt.nodes.new("ShaderNodeMath"); x_shift.operation = 'MULTIPLY'
    nt.links.new(x_add.outputs[0], x_shift.inputs[0])
    nt.links.new(z_par.outputs[0], x_shift.inputs[1])
    x_fin = nt.nodes.new("ShaderNodeMath"); x_fin.operation = 'FRACT'
    nt.links.new(x_shift.outputs[0], x_fin.inputs[0])

    def thin(frac_out, width):
        """frac 靠近 0 或 1 处为缝 -> 返回 0(缝) .. 1(石面)"""
        a = nt.nodes.new("ShaderNodeMath"); a.operation = 'LESS_THAN'
        nt.links.new(frac_out, a.inputs[0]); a.inputs[1].default_value = width
        b = nt.nodes.new("ShaderNodeMath"); b.operation = 'GREATER_THAN'
        nt.links.new(frac_out, b.inputs[0]); b.inputs[1].default_value = 1.0 - width
        mx = nt.nodes.new("ShaderNodeMath"); mx.operation = 'MAXIMUM'
        nt.links.new(a.outputs[0], mx.inputs[0]); nt.links.new(b.outputs[0], mx.inputs[1])
        inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'
        inv.inputs[0].default_value = 1.0
        nt.links.new(mx.outputs[0], inv.inputs[1])
        return inv
    jz = thin(z_frac.outputs[0], joint / course_h)
    jx = thin(x_fin.outputs[0], joint / (course_h * 2.0))
    jmin = nt.nodes.new("ShaderNodeMath"); jmin.operation = 'MINIMUM'
    nt.links.new(jz.outputs[0], jmin.inputs[0]); nt.links.new(jx.outputs[0], jmin.inputs[1])

    # ── 风化斑驳: Noise 扰动基色与粗糙 ──
    noise = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(geo.outputs["Position"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = 2.6
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.55
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.68

    # 混色: 基色 <- 风化色, 再按缝隙变暗
    mix1 = nt.nodes.new("ShaderNodeMixRGB"); mix1.blend_type = 'MIX'
    mix1.inputs["Color1"].default_value = (base_rgb[0], base_rgb[1], base_rgb[2], 1.0)
    nt.links.new(ramp.outputs["Color"], mix1.inputs["Color2"])
    mix1.inputs["Fac"].default_value = weather
    mix_dark = nt.nodes.new("ShaderNodeMixRGB"); mix_dark.blend_type = 'MULTIPLY'
    mix_dark.inputs["Color2"].default_value = (0.62, 0.60, 0.58, 1.0)   # 缝内变暗
    nt.links.new(jmin.outputs[0], mix_dark.inputs["Fac"])
    nt.links.new(mix1.outputs["Color"], mix_dark.inputs["Color1"])
    # 水线以下更暗更绿(藻痕)
    wsub = nt.nodes.new("ShaderNodeMath"); wsub.operation = 'SUBTRACT'
    nt.links.new(sep.outputs["Z"], wsub.inputs[0]); wsub.inputs[1].default_value = waterline_z
    wdiv = nt.nodes.new("ShaderNodeMath"); wdiv.operation = 'DIVIDE'
    nt.links.new(wsub.outputs[0], wdiv.inputs[0]); wdiv.inputs[1].default_value = -waterline_h
    wcl = nt.nodes.new("ShaderNodeClamp")
    nt.links.new(wdiv.outputs[0], wcl.inputs["Value"])
    mix_water = nt.nodes.new("ShaderNodeMixRGB"); mix_water.blend_type = 'MIX'
    nt.links.new(wcl.outputs[0], mix_water.inputs["Fac"])
    nt.links.new(mix_dark.outputs["Color"], mix_water.inputs["Color1"])
    mix_water.inputs["Color2"].default_value = (base_rgb[0]*0.42, base_rgb[1]*0.46, base_rgb[2]*0.36, 1.0)
    nt.links.new(mix_water.outputs["Color"], bsdf.inputs["Base Color"])

    # 粗糙度: 缝更粗糙
    rg = nt.nodes.new("ShaderNodeMath"); rg.operation = 'MULTIPLY_ADD'
    nt.links.new(jmin.outputs[0], rg.inputs[0])
    rg.inputs[1].default_value = -0.18
    rg.inputs[2].default_value = 0.88
    nt.links.new(rg.outputs[0], bsdf.inputs["Roughness"])
    return m


def marble_material(name, base_rgb=(0.86, 0.855, 0.825)):
    """汉白玉: 细腻、无明显砌缝, 轻微斑驳。"""
    return stone_material(name, base_rgb, joint=0.004, course_h=1.2,
                          weather=0.28, waterline_h=0.3)


def water_material(name="water", base=(0.045, 0.105, 0.135)):
    """湖面: 底色 + 两层错频波纹法线扰动, 模拟风纹, 让倒影有细节。"""
    import bmesh
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (base[0], base[1], base[2], 1.0)
    bsdf.inputs["Roughness"].default_value = 0.06
    if "IOR" in bsdf.inputs:
        bsdf.inputs["IOR"].default_value = 1.333
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.9
    n1.inputs["Detail"].default_value = 3.0
    nt.links.new(geo.outputs["Position"], n1.inputs["Vector"])
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 4.5
    n2.inputs["Detail"].default_value = 2.0
    nt.links.new(geo.outputs["Position"], n2.inputs["Vector"])
    mixn = nt.nodes.new("ShaderNodeMixRGB")
    nt.links.new(n1.outputs["Fac"], mixn.inputs["Color1"])
    nt.links.new(n2.outputs["Fac"], mixn.inputs["Color2"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.06
    bump.inputs["Distance"].default_value = 0.02
    nt.links.new(mixn.outputs["Color"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m
