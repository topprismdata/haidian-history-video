"""程序化石材: 石砌分缝 + 风化 + 水线痕。全部节点生成, 无外部贴图。

2026-10-05 M4 表现层改版(只动 shader, 不动任何本体 mesh):
  - stone_material 增加逐块色差(块编号采样噪声)与 bump(砌缝凹槽+石面颗粒),
    解决"像塑料/像瓷砖"——之前只有颜色没有凹凸。
  - 桥体基色走"实拍优先"口径: 京报网 2025-12-24「以青石筑成桥体, 以汉白玉为栏杆」
    说的是石材种类; 主控采样 ref_elevation.jpg 实测桥身亮部 RGB(252,245,227),
    R-B=+25 偏暖白 —— 青石在阳光+大气散射下呈暖白, 基色必须暖白而非青灰。
  - water_material 三频波纹 bump + 粗糙度斑块, 解决"完美镜面"。
  - 新增 earth_material(岸坡植被/土坡读感) 与 fog_material(体积散射, 大气透视)。
"""
import bpy


def _principled(mat):
    return mat.node_tree.nodes.get("Principled BSDF")


def stone_material(name, base_rgb, joint=0.020, course_h=0.42, weather=0.55,
                   waterline_z=0.0, waterline_h=0.55, block_var=0.12,
                   bump_strength=0.38, base_rough=0.82):
    """古建石构材质: 分层砌缝(横向) + 竖向错缝 + 逐块色差 + 风化斑驳
    + 缝凹槽/石面颗粒 bump + 水线以下更深更绿。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.28

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

    # ── 逐块色差: 用"块编号"(层号+错缝列号)采样低频噪声, 同块同色邻块异色 ──
    # 块中心坐标 = (FLOOR(x_shift)+0.5)*块宽, (FLOOR(z/ch)+0.5)*层高 —— 跳变发生在
    # 缝处, 缝两侧各属自己的块。
    x_blk = nt.nodes.new("ShaderNodeMath"); x_blk.operation = 'FLOOR'
    nt.links.new(x_shift.outputs[0], x_blk.inputs[0])
    bx_add = nt.nodes.new("ShaderNodeMath"); bx_add.operation = 'ADD'
    nt.links.new(x_blk.outputs[0], bx_add.inputs[0]); bx_add.inputs[1].default_value = 0.5
    bx_mul = nt.nodes.new("ShaderNodeMath"); bx_mul.operation = 'MULTIPLY'
    nt.links.new(bx_add.outputs[0], bx_mul.inputs[0])
    bx_mul.inputs[1].default_value = course_h * 2.0
    bz_add = nt.nodes.new("ShaderNodeMath"); bz_add.operation = 'ADD'
    nt.links.new(z_floor.outputs[0], bz_add.inputs[0]); bz_add.inputs[1].default_value = 0.5
    bz_mul = nt.nodes.new("ShaderNodeMath"); bz_mul.operation = 'MULTIPLY'
    nt.links.new(bz_add.outputs[0], bz_mul.inputs[0])
    bz_mul.inputs[1].default_value = course_h
    blk_vec = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(bx_mul.outputs[0], blk_vec.inputs["X"])
    nt.links.new(bz_mul.outputs[0], blk_vec.inputs["Y"])
    blk_vec.inputs["Z"].default_value = 3.17
    blk_noise = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(blk_vec.outputs["Vector"], blk_noise.inputs["Vector"])
    blk_noise.inputs["Scale"].default_value = 0.55
    blk_noise.inputs["Detail"].default_value = 1.0
    blk_fac = nt.nodes.new("ShaderNodeMath"); blk_fac.operation = 'MULTIPLY'
    nt.links.new(blk_noise.outputs["Fac"], blk_fac.inputs[0])
    blk_fac.inputs[1].default_value = block_var
    blk_mul_d = nt.nodes.new("ShaderNodeMixRGB"); blk_mul_d.blend_type = 'MULTIPLY'
    blk_mul_d.inputs["Fac"].default_value = 1.0
    blk_mul_d.inputs["Color1"].default_value = (base_rgb[0], base_rgb[1], base_rgb[2], 1.0)
    blk_mul_d.inputs["Color2"].default_value = (0.93, 0.945, 0.915, 1.0)  # 偏冷偏暗块
    blk_mul_l = nt.nodes.new("ShaderNodeMixRGB"); blk_mul_l.blend_type = 'MULTIPLY'
    blk_mul_l.inputs["Fac"].default_value = 1.0
    blk_mul_l.inputs["Color1"].default_value = (base_rgb[0], base_rgb[1], base_rgb[2], 1.0)
    blk_mul_l.inputs["Color2"].default_value = (1.06, 1.042, 1.005, 1.0)  # 偏暖偏亮块
    mix_blk = nt.nodes.new("ShaderNodeMixRGB"); mix_blk.blend_type = 'MIX'
    nt.links.new(blk_fac.outputs[0], mix_blk.inputs["Fac"])
    nt.links.new(blk_mul_d.outputs["Color"], mix_blk.inputs["Color1"])
    nt.links.new(blk_mul_l.outputs["Color"], mix_blk.inputs["Color2"])

    # ── 风化斑驳: Noise 扰动基色 ──
    noise = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(geo.outputs["Position"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = 2.6
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.55
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.68
    mix1 = nt.nodes.new("ShaderNodeMixRGB"); mix1.blend_type = 'MIX'
    nt.links.new(mix_blk.outputs["Color"], mix1.inputs["Color1"])
    nt.links.new(ramp.outputs["Color"], mix1.inputs["Color2"])
    mix1.inputs["Fac"].default_value = weather

    mix_dark = nt.nodes.new("ShaderNodeMixRGB"); mix_dark.blend_type = 'MULTIPLY'
    mix_dark.inputs["Color2"].default_value = (0.74, 0.72, 0.70, 1.0)   # 缝内变暗
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

    # ── bump: 缝为凹槽(jmin: 缝0/面1) + 细颗粒 + 块间微错台 ──
    grain = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(geo.outputs["Position"], grain.inputs["Vector"])
    grain.inputs["Scale"].default_value = 7.5
    grain.inputs["Detail"].default_value = 8.0
    grain.inputs["Roughness"].default_value = 0.6
    g_off = nt.nodes.new("ShaderNodeMath"); g_off.operation = 'SUBTRACT'
    nt.links.new(grain.outputs["Fac"], g_off.inputs[0]); g_off.inputs[1].default_value = 0.5
    g_mul = nt.nodes.new("ShaderNodeMath"); g_mul.operation = 'MULTIPLY'
    nt.links.new(g_off.outputs[0], g_mul.inputs[0]); g_mul.inputs[1].default_value = 0.30
    b_a = nt.nodes.new("ShaderNodeMath"); b_a.operation = 'ADD'
    nt.links.new(jmin.outputs[0], b_a.inputs[0]); nt.links.new(g_mul.outputs[0], b_a.inputs[1])
    b_b = nt.nodes.new("ShaderNodeMath"); b_b.operation = 'MULTIPLY'
    nt.links.new(blk_noise.outputs["Fac"], b_b.inputs[0]); b_b.inputs[1].default_value = 0.15
    b_c = nt.nodes.new("ShaderNodeMath"); b_c.operation = 'ADD'
    nt.links.new(b_a.outputs[0], b_c.inputs[0]); nt.links.new(b_b.outputs[0], b_c.inputs[1])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.03
    nt.links.new(b_c.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    # 粗糙度: 缝更粗糙 + 风化斑块微差
    rg = nt.nodes.new("ShaderNodeMath"); rg.operation = 'MULTIPLY_ADD'
    nt.links.new(jmin.outputs[0], rg.inputs[0])
    rg.inputs[1].default_value = -0.15
    rg.inputs[2].default_value = base_rough
    wr_off = nt.nodes.new("ShaderNodeMath"); wr_off.operation = 'SUBTRACT'
    nt.links.new(noise.outputs["Fac"], wr_off.inputs[0]); wr_off.inputs[1].default_value = 0.5
    wr_mul = nt.nodes.new("ShaderNodeMath"); wr_mul.operation = 'MULTIPLY'
    nt.links.new(wr_off.outputs[0], wr_mul.inputs[0]); wr_mul.inputs[1].default_value = 0.10
    rg2 = nt.nodes.new("ShaderNodeMath"); rg2.operation = 'ADD'
    nt.links.new(rg.outputs[0], rg2.inputs[0]); nt.links.new(wr_mul.outputs[0], rg2.inputs[1])
    nt.links.new(rg2.outputs[0], bsdf.inputs["Roughness"])
    return m


def marble_material(name, base_rgb=(0.90, 0.893, 0.868)):
    """汉白玉: 近白(栏杆/望柱/狮/靠山兽), 细腻, 微斑驳微块差。"""
    return stone_material(name, base_rgb, joint=0.006, course_h=1.2,
                          weather=0.20, waterline_h=0.3, block_var=0.05,
                          bump_strength=0.22, base_rough=0.80)


def water_material(name="water", base=(0.05, 0.11, 0.14)):
    """湖面: 底色 + 三频波纹法线扰动(长涌/中浪/风纹) + 粗糙度斑块,
    让倒影柔碎有风纹感, 不再是完美镜面。只动 shader, 水面 mesh 保持单面。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (base[0], base[1], base[2], 1.0)
    if "IOR" in bsdf.inputs:
        bsdf.inputs["IOR"].default_value = 1.333
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    # 风纹沿 X 拉长(吹向南偏东的湖风在水面拉出条纹)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.6, 2.0, 1.0)
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])

    def _noise(scale, detail, w):
        n = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"])
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'
        nt.links.new(n.outputs["Fac"], mul.inputs[0]); mul.inputs[1].default_value = w
        return mul
    h1 = _noise(0.55, 2.0, 0.50)   # 长涌
    h2 = _noise(3.20, 3.0, 0.32)   # 中浪
    h3 = _noise(12.0, 2.0, 0.18)   # 风纹(细, 近景可见)
    h12 = nt.nodes.new("ShaderNodeMath"); h12.operation = 'ADD'
    nt.links.new(h1.outputs[0], h12.inputs[0]); nt.links.new(h2.outputs[0], h12.inputs[1])
    hsum = nt.nodes.new("ShaderNodeMath"); hsum.operation = 'ADD'
    nt.links.new(h12.outputs[0], hsum.inputs[0]); nt.links.new(h3.outputs[0], hsum.inputs[1])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.20
    bump.inputs["Distance"].default_value = 0.045
    nt.links.new(hsum.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # 粗糙度: 基础 0.05 + 大尺度斑块 0..0.08 —— 倒影局部柔碎
    pn = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(geo.outputs["Position"], pn.inputs["Vector"])
    pn.inputs["Scale"].default_value = 0.22
    pn.inputs["Detail"].default_value = 2.0
    pmul = nt.nodes.new("ShaderNodeMath"); pmul.operation = 'MULTIPLY'
    nt.links.new(pn.outputs["Fac"], pmul.inputs[0]); pmul.inputs[1].default_value = 0.05
    padd = nt.nodes.new("ShaderNodeMath"); padd.operation = 'ADD'
    padd.inputs[0].default_value = 0.04
    nt.links.new(pmul.outputs[0], padd.inputs[1])
    nt.links.new(padd.outputs[0], bsdf.inputs["Roughness"])
    return m


def earth_material(name="shore_earth", base=(0.105, 0.130, 0.088)):
    """岸坡地表: 深橄榄绿(远读为树冠/植被带), 斑块色差 + 细颗粒 bump。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = 0.95
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    n = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(geo.outputs["Position"], n.inputs["Vector"])
    n.inputs["Scale"].default_value = 1.2
    n.inputs["Detail"].default_value = 4.0
    mixc = nt.nodes.new("ShaderNodeMixRGB"); mixc.blend_type = 'MIX'
    mixc.inputs["Color1"].default_value = (base[0], base[1], base[2], 1.0)
    mixc.inputs["Color2"].default_value = (base[0]*1.55, base[1]*1.42, base[2]*1.30, 1.0)
    nt.links.new(n.outputs["Fac"], mixc.inputs["Fac"])
    nt.links.new(mixc.outputs["Color"], bsdf.inputs["Base Color"])
    g = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(geo.outputs["Position"], g.inputs["Vector"])
    g.inputs["Scale"].default_value = 3.0
    g.inputs["Detail"].default_value = 8.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.30
    bump.inputs["Distance"].default_value = 0.05
    nt.links.new(g.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def fog_material(name="fog", density=0.003, color=(0.70, 0.78, 0.88)):
    """大气透视: 纯体积散射材质(挂在罩盒上, 盒面本身不可见)。
    密度=每米散射消光系数(工作值): 48m 近远端差 -> 散射占比差约 13%。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)
    sc.inputs["Density"].default_value = density
    sc.inputs["Anisotropy"].default_value = 0.35
    nt.links.new(sc.outputs["Volume"], out.inputs["Volume"])
    return m


# ── C2 材质分工 (2026-10-05): 桥体=青石, 栏杆/望柱/狮=汉白玉 ──
# 来源核实(逐字, 两处原文直接抓取): 京报网 2025-12-09 07:14
# https://news.bjd.com.cn/2025/12/09/11451647.shtml (来源:北京青年报) 及
# 中新网 https://www.chinanews.com.cn/cul/2025/12-09/10529704.shtml:
#   「……仿照北京卢沟桥, 兼收苏州宝带桥特点,
#     以青石筑成桥体, 以汉白玉为栏杆, 因有17个拱券, 故名十七孔桥……」
# 另见本模块头部注记的京报网 2025-12-24 同句 (快照级互证)。
# 注意: 这只定石材种类; 「桥体亮部呈暖白」是主控实测 ref_elevation.jpg 的光照结果
# (RGB 252,245,227), 青石基色本身是冷灰蓝 —— 两件事不矛盾, A/B 对照见
# 3d/ab_qingshi_split.py 输出。

def qingshi_material(name, base_rgb=(0.305, 0.342, 0.381)):
    """青石(石灰岩)桥体: 冷灰蓝基色 + 可见砌缝 + 微斑驳。
    基色推导: 青石新出面 sRGB 约 (149,157,165), 转线性 = (0.305,0.342,0.381)
    (R<G<B 的冷灰蓝向)。参数比 stone_body 默认接法略强调砌缝与块差(青石块
    石砌法可见), 复用 stone_material 节点栈, 不新增节点逻辑。
    栏杆/望柱/狮仍用 marble_material —— 分工依据见上引文。"""
    return stone_material(name, base_rgb, joint=0.010, course_h=0.60,
                          weather=0.32, waterline_h=0.55, block_var=0.12,
                          bump_strength=0.30, base_rough=0.84)
