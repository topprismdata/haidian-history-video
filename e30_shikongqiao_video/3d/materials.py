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
                   bump_strength=0.38, base_rough=0.82,
                   course_w=None, z_phase=0.0, x_phase=0.0, uv_joints=False):
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
    _cw = course_w if course_w is not None else 2.0 * course_h
    z_off = nt.nodes.new("ShaderNodeMath"); z_off.operation = 'SUBTRACT'
    nt.links.new(sep.outputs["Z"], z_off.inputs[0]); z_off.inputs[1].default_value = z_phase
    z_scaled = nt.nodes.new("ShaderNodeMath"); z_scaled.operation = 'MULTIPLY'
    nt.links.new(z_off.outputs[0], z_scaled.inputs[0])
    z_scaled.inputs[1].default_value = 1.0 / course_h
    z_floor = nt.nodes.new("ShaderNodeMath"); z_floor.operation = 'FLOOR'
    nt.links.new(z_scaled.outputs[0], z_floor.inputs[0])
    z_frac = nt.nodes.new("ShaderNodeMath"); z_frac.operation = 'FRACT'
    nt.links.new(z_scaled.outputs[0], z_frac.inputs[0])
    # 奇偶层
    z_par = nt.nodes.new("ShaderNodeMath"); z_par.operation = 'PINGPONG'
    z_par.inputs[1].default_value = 1.0; z_par.inputs[2].default_value = 1.0
    nt.links.new(z_floor.outputs[0], z_par.inputs[0])
    # 竖向: X 按块宽 _cw 分缝, 奇数层错半块。[M17修bug] 原实现 (x_f+0.5)*z_par
    # 在奇数层(z_par=0)恒为 0 -> thin() 判整行为缝 -> jmin 恒 0 -> 奇偶行明暗交替
    # 横带 = "条纹贴面"棋盘真根因。改为 x_f + 0.5*(1-z_par)。
    x_off = nt.nodes.new("ShaderNodeMath"); x_off.operation = 'SUBTRACT'
    nt.links.new(sep.outputs["X"], x_off.inputs[0]); x_off.inputs[1].default_value = x_phase
    x_s = nt.nodes.new("ShaderNodeMath"); x_s.operation = 'MULTIPLY'
    nt.links.new(x_off.outputs[0], x_s.inputs[0])
    x_s.inputs[1].default_value = 1.0 / _cw
    x_f = nt.nodes.new("ShaderNodeMath"); x_f.operation = 'FRACT'
    nt.links.new(x_s.outputs[0], x_f.inputs[0])
    par_inv = nt.nodes.new("ShaderNodeMath"); par_inv.operation = 'SUBTRACT'
    par_inv.inputs[0].default_value = 1.0
    nt.links.new(z_par.outputs[0], par_inv.inputs[1])
    half_off = nt.nodes.new("ShaderNodeMath"); half_off.operation = 'MULTIPLY'
    nt.links.new(par_inv.outputs[0], half_off.inputs[0]); half_off.inputs[1].default_value = 0.5
    x_shift = nt.nodes.new("ShaderNodeMath"); x_shift.operation = 'ADD'
    nt.links.new(x_f.outputs[0], x_shift.inputs[0])
    nt.links.new(half_off.outputs[0], x_shift.inputs[1])
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
    if uv_joints:
        # [M17] 砧石前脸 UV 已按块局部米展平 -> 缝沿真实块界, 不跨收分斜面/不漂缝
        attr = nt.nodes.new("ShaderNodeAttribute")
        attr.attribute_name = "UVMap"
        usep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(attr.outputs["Vector"], usep.inputs["Vector"])
        vu_s = nt.nodes.new("ShaderNodeMath"); vu_s.operation = 'DIVIDE'
        nt.links.new(usep.outputs["X"], vu_s.inputs[0]); vu_s.inputs[1].default_value = _cw
        vu_f = nt.nodes.new("ShaderNodeMath"); vu_f.operation = 'FRACT'
        nt.links.new(vu_s.outputs[0], vu_f.inputs[0])
        vv_s = nt.nodes.new("ShaderNodeMath"); vv_s.operation = 'DIVIDE'
        nt.links.new(usep.outputs["Y"], vv_s.inputs[0]); vv_s.inputs[1].default_value = course_h
        vv_f = nt.nodes.new("ShaderNodeMath"); vv_f.operation = 'FRACT'
        nt.links.new(vv_s.outputs[0], vv_f.inputs[0])
        jz = thin(vv_f.outputs[0], joint / course_h)
        jx = thin(vu_f.outputs[0], joint / _cw)
    else:
        jz = thin(z_frac.outputs[0], joint / course_h)
        jx = thin(x_fin.outputs[0], joint / _cw)
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
    bx_mul.inputs[1].default_value = _cw
    bz_add = nt.nodes.new("ShaderNodeMath"); bz_add.operation = 'ADD'
    nt.links.new(z_floor.outputs[0], bz_add.inputs[0]); bz_add.inputs[1].default_value = 0.5
    bz_mul = nt.nodes.new("ShaderNodeMath"); bz_mul.operation = 'MULTIPLY'
    nt.links.new(bz_add.outputs[0], bz_mul.inputs[0])
    bz_mul.inputs[1].default_value = course_h
    bz_off = nt.nodes.new("ShaderNodeMath"); bz_off.operation = 'ADD'
    nt.links.new(bz_mul.outputs[0], bz_off.inputs[0]); bz_off.inputs[1].default_value = z_phase
    blk_vec = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(bx_mul.outputs[0], blk_vec.inputs["X"])
    nt.links.new(bz_off.outputs[0], blk_vec.inputs["Y"])
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
    blk_mul_d.inputs["Color2"].default_value = (0.975, 0.968, 0.955, 1.0)  # [八审x2] 块间色差减半(0.93级在提亮基色上读成棋盘格)
    blk_mul_l = nt.nodes.new("ShaderNodeMixRGB"); blk_mul_l.blend_type = 'MULTIPLY'
    blk_mul_l.inputs["Fac"].default_value = 1.0
    blk_mul_l.inputs["Color1"].default_value = (base_rgb[0], base_rgb[1], base_rgb[2], 1.0)
    blk_mul_l.inputs["Color2"].default_value = (1.025, 1.018, 1.005, 1.0)  # [八审x2] 同上
    mix_blk = nt.nodes.new("ShaderNodeMixRGB"); mix_blk.blend_type = 'MIX'
    nt.links.new(blk_fac.outputs[0], mix_blk.inputs["Fac"])
    nt.links.new(blk_mul_d.outputs["Color"], mix_blk.inputs["Color1"])
    nt.links.new(blk_mul_l.outputs["Color"], mix_blk.inputs["Color2"])

    # ── 风化斑驳: Noise 扰动基色 ──
    noise = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(geo.outputs["Position"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = 0.6   # [M17] 2.6->0.6: 真照色斑2~4m大软斑, 原尺度=每块一格读成棋盘
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.55
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.68
    # [八审材质刀] 风化色斑改"局部暖灰污染"(真石灰岩铁质浸染), 原默认黑白噪声
    # 乘出来偏冷灰脏。低值=暖褐积污, 高值=近白亮面。
    ramp.color_ramp.elements[0].color = (0.78, 0.72, 0.62, 1.0)
    ramp.color_ramp.elements[1].color = (1.06, 1.04, 0.99, 1.0)
    mix1 = nt.nodes.new("ShaderNodeMixRGB"); mix1.blend_type = 'MIX'
    nt.links.new(mix_blk.outputs["Color"], mix1.inputs["Color1"])
    nt.links.new(ramp.outputs["Color"], mix1.inputs["Color2"])
    mix1.inputs["Fac"].default_value = weather

    mix_dark = nt.nodes.new("ShaderNodeMixRGB"); mix_dark.blend_type = 'MULTIPLY'
    mix_dark.inputs["Color2"].default_value = (0.80, 0.79, 0.77, 1.0)   # [M17] 缝内变暗(侵蚀浅灰)
    # [M17修bug] 原 Fac=jmin(石面1/缝0) 把暗化乘在石面上、缝反而亮 —— 反向。
    jm_inv = nt.nodes.new("ShaderNodeMath"); jm_inv.operation = 'SUBTRACT'
    jm_inv.inputs[0].default_value = 1.0
    nt.links.new(jmin.outputs[0], jm_inv.inputs[1])
    nt.links.new(jm_inv.outputs[0], mix_dark.inputs["Fac"])
    nt.links.new(mix1.outputs["Color"], mix_dark.inputs["Color1"])
    # 水线以下更暗更绿(藻痕): 叠加低频噪声扰动 Z, 形成微小起伏与块石吸水率差异, 杜绝机械直横线
    w_noise = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(geo.outputs["Position"], w_noise.inputs["Vector"])
    w_noise.inputs["Scale"].default_value = 2.2
    w_noise.inputs["Detail"].default_value = 4.0
    w_pert = nt.nodes.new("ShaderNodeMath"); w_pert.operation = 'MULTIPLY_ADD'
    nt.links.new(w_noise.outputs["Fac"], w_pert.inputs[0])
    w_pert.inputs[1].default_value = 0.22      # ±0.11m 水线起伏
    w_pert.inputs[2].default_value = -0.11
    z_pert = nt.nodes.new("ShaderNodeMath"); z_pert.operation = 'ADD'
    nt.links.new(sep.outputs["Z"], z_pert.inputs[0])
    nt.links.new(w_pert.outputs[0], z_pert.inputs[1])

    wsub = nt.nodes.new("ShaderNodeMath"); wsub.operation = 'SUBTRACT'
    nt.links.new(z_pert.outputs[0], wsub.inputs[0]); wsub.inputs[1].default_value = waterline_z
    wdiv = nt.nodes.new("ShaderNodeMath"); wdiv.operation = 'DIVIDE'
    nt.links.new(wsub.outputs[0], wdiv.inputs[0]); wdiv.inputs[1].default_value = -waterline_h
    wcl = nt.nodes.new("ShaderNodeClamp")
    nt.links.new(wdiv.outputs[0], wcl.inputs["Value"])
    mix_water = nt.nodes.new("ShaderNodeMixRGB"); mix_water.blend_type = 'MIX'
    nt.links.new(wcl.outputs[0], mix_water.inputs["Fac"])
    nt.links.new(mix_dark.outputs["Color"], mix_water.inputs["Color1"])
    mix_water.inputs["Color2"].default_value = (base_rgb[0]*0.52, base_rgb[1]*0.56, base_rgb[2]*0.48, 1.0)  # [M17] 0.36过黑, 真照水渍带是中深灰
    # ── M10.2 风化层(五审残留1/3): 腔隙积垢 + 棱缘磨亮 + 竖向雨痕 ──
    geo2 = nt.nodes.new("ShaderNodeNewGeometry")
    pr = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(geo2.outputs["Pointiness"], pr.inputs["Fac"])
    pr.color_ramp.elements[0].position = 0.42
    pr.color_ramp.elements[1].position = 0.62
    # 腔隙暗: pointiness 低 -> 积垢乘暗
    cav = nt.nodes.new("ShaderNodeMath"); cav.operation = 'LESS_THAN'
    nt.links.new(geo2.outputs["Pointiness"], cav.inputs[0]); cav.inputs[1].default_value = 0.45
    mix_cav = nt.nodes.new("ShaderNodeMixRGB"); mix_cav.blend_type = 'MULTIPLY'
    nt.links.new(cav.outputs[0], mix_cav.inputs["Fac"])
    mix_cav.inputs["Color1"].default_value = (1.0, 1.0, 1.0, 1.0)
    mix_cav.inputs["Color2"].default_value = (0.66, 0.64, 0.60, 1.0)
    nt.links.new(mix_water.outputs["Color"], mix_cav.inputs["Color1"])
    # 棱缘亮: pointiness 高 -> 磨亮
    edg = nt.nodes.new("ShaderNodeMath"); edg.operation = 'GREATER_THAN'
    nt.links.new(geo2.outputs["Pointiness"], edg.inputs[0]); edg.inputs[1].default_value = 0.58
    mix_edg = nt.nodes.new("ShaderNodeMixRGB"); mix_edg.blend_type = 'MULTIPLY'
    nt.links.new(edg.outputs[0], mix_edg.inputs["Fac"])
    mix_edg.inputs["Color1"].default_value = (1.0, 1.0, 1.0, 1.0)
    mix_edg.inputs["Color2"].default_value = (1.22, 1.20, 1.16, 1.0)
    nt.links.new(mix_cav.outputs["Color"], mix_edg.inputs["Color1"])
    # 竖向雨痕: Z 拉伸噪声 -> 条带乘暗
    mapn = nt.nodes.new("ShaderNodeMapping")
    mapn.inputs["Scale"].default_value = (7.0, 7.0, 0.55)
    nt.links.new(geo2.outputs["Position"], mapn.inputs["Vector"])
    streak = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(mapn.outputs["Vector"], streak.inputs["Vector"])
    streak.inputs["Scale"].default_value = 1.6
    streak.inputs["Detail"].default_value = 4.0
    sramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(streak.outputs["Fac"], sramp.inputs["Fac"])
    sramp.color_ramp.elements[0].position = 0.52
    sramp.color_ramp.elements[1].position = 0.72
    mix_stk = nt.nodes.new("ShaderNodeMixRGB"); mix_stk.blend_type = 'MULTIPLY'
    nt.links.new(sramp.outputs["Color"], mix_stk.inputs["Fac"])
    mix_stk.inputs["Color1"].default_value = (1.0, 1.0, 1.0, 1.0)
    mix_stk.inputs["Color2"].default_value = (0.88, 0.87, 0.85, 1.0)
    nt.links.new(mix_edg.outputs["Color"], mix_stk.inputs["Color1"])
    nt.links.new(mix_stk.outputs["Color"], bsdf.inputs["Base Color"])
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
    # M10.2: 逐块粗糙度 ±0.08 (块噪声驱动)
    blk_r = nt.nodes.new("ShaderNodeMath"); blk_r.operation = 'MULTIPLY_ADD'
    nt.links.new(blk_noise.outputs["Fac"], blk_r.inputs[0])
    blk_r.inputs[1].default_value = 0.16
    blk_r.inputs[2].default_value = -0.08
    rg3 = nt.nodes.new("ShaderNodeMath"); rg3.operation = 'ADD'
    nt.links.new(rg2.outputs[0], rg3.inputs[0]); nt.links.new(blk_r.outputs[0], rg3.inputs[1])
    nt.links.new(rg3.outputs[0], bsdf.inputs["Roughness"])
    return m


def marble_material(name, base_rgb=(0.865, 0.840, 0.795)):
    """汉白玉: 暖象牙古玉白(栏杆/望柱/狮/靠山兽), 微雨蚀灰度, 消解纯白CGI感。"""
    return stone_material(name, base_rgb, joint=0.008, course_h=1.2,
                          weather=0.40, waterline_h=0.35, block_var=0.15,
                          bump_strength=0.36, base_rough=0.78)


def water_material(name="water", base=(0.05, 0.11, 0.14)):
    """湖面: 底色 + 四频波纹法线扰动(长涌/中浪/风纹/细碎浪) + 粗糙度斑块,
    让倒影柔碎有风纹感, 不再是完美镜面。只动 shader, 水面 mesh 保持单面。
    2026-10-05 WaterFix 调参(shot_hero 量化: 倒影竖抹/前景死水):
    bump .20→.32、风纹权 .18→.28+第四频 scale30、风纹方向转 90°、
    粗糙度底 .04→.02 斑块 .05→.09。函数签名不变。"""
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
    # 风纹沿 Y 拉长(2026-10-05 转 90°: 旧 (0.6,2,1) 把条纹沿桥纵深拉长,
    # hero 视图里拱倒影被抹成竖条; (2,0.6,1) 条纹横走, 倒影出现横向波痕)
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2.0, 0.6, 1.0)
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
    h3 = _noise(12.0, 2.0, 0.28)   # 风纹(细; 权 .18→.28 补近景可见度)
    h4 = _noise(30.0, 2.0, 0.14)   # 细碎浪(scale≈30, 低机位前景 sparkle)
    h5 = _noise(75.0, 2.0, 0.10)   # M10.2 第五频: 摄影级高频破碎(五审残留2/3)
    h6 = _noise(0.9, 3.0, 0.38)    # M10.2b 米级破碎频: 远距反射 breakup(hero 自检修)
    h12 = nt.nodes.new("ShaderNodeMath"); h12.operation = 'ADD'
    nt.links.new(h1.outputs[0], h12.inputs[0]); nt.links.new(h2.outputs[0], h12.inputs[1])
    h34 = nt.nodes.new("ShaderNodeMath"); h34.operation = 'ADD'
    nt.links.new(h3.outputs[0], h34.inputs[0]); nt.links.new(h4.outputs[0], h34.inputs[1])
    h45 = nt.nodes.new("ShaderNodeMath"); h45.operation = 'ADD'
    nt.links.new(h34.outputs[0], h45.inputs[0]); nt.links.new(h5.outputs[0], h45.inputs[1])
    h56 = nt.nodes.new("ShaderNodeMath"); h56.operation = 'ADD'
    nt.links.new(h45.outputs[0], h56.inputs[0]); nt.links.new(h6.outputs[0], h56.inputs[1])
    h34 = h56
    hsum = nt.nodes.new("ShaderNodeMath"); hsum.operation = 'ADD'
    nt.links.new(h12.outputs[0], hsum.inputs[0]); nt.links.new(h34.outputs[0], hsum.inputs[1])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.32
    bump.inputs["Distance"].default_value = 0.045
    nt.links.new(hsum.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    # 粗糙度: 基础 0.02 + 大尺度斑块 0..0.09 —— 底更镜、斑块更碎(倒影对比更强)
    pn = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(geo.outputs["Position"], pn.inputs["Vector"])
    pn.inputs["Scale"].default_value = 0.22
    pn.inputs["Detail"].default_value = 2.0
    pmul = nt.nodes.new("ShaderNodeMath"); pmul.operation = 'MULTIPLY'
    nt.links.new(pn.outputs["Fac"], pmul.inputs[0]); pmul.inputs[1].default_value = 0.09
    padd = nt.nodes.new("ShaderNodeMath"); padd.operation = 'ADD'
    padd.inputs[0].default_value = 0.015
    nt.links.new(pmul.outputs[0], padd.inputs[1])
    nt.links.new(padd.outputs[0], bsdf.inputs["Roughness"])
    return m


def earth_material(name="shore_earth", base=(0.105, 0.130, 0.088)):
    """岸坡地表: 深橄榄绿(远读为树冠/植被带), 斑块色差 + 细颗粒 bump。
    2026-10-05 WaterFix: 干基 ×0.8 压暗 + 亮斑倍率 (1.55,1.42,1.30)→(1.80,1.55,1.30)
    (治左岸被雾洗灰, 靠压暗提反差而非提亮找回植被读感); 增水线湿带 z∈[0,0.5] 渐变
    压暗(复用 stone_material waterline 节点式, 治岸水交界硬边)。函数签名不变。"""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Roughness"].default_value = 0.95
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    orig = base
    base = (orig[0] * 0.8, orig[1] * 0.8, orig[2] * 0.8)   # 干基压暗(留雾洗反差余量)
    n = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(geo.outputs["Position"], n.inputs["Vector"])
    n.inputs["Scale"].default_value = 1.2
    n.inputs["Detail"].default_value = 4.0
    mixc = nt.nodes.new("ShaderNodeMixRGB"); mixc.blend_type = 'MIX'
    mixc.inputs["Color1"].default_value = (base[0], base[1], base[2], 1.0)
    # 亮斑作用于"原 palette"(=干基的 2.25/1.9375/1.625 倍)。若乘在缩放后的 base 上,
    # 净对比 0.8*1.8=1.44 < 旧 1.55, 雾占比反升 —— hero A/B 实测左岸 sat 反降
    # (18.94 vs 旧 20.73); 本参数(1.80,1.55,1.30) 保 G>R>B 橄榄序, 实测 sat 23.38,
    # 治#4 达标(变体扫描 S2-S5, 2026-10-05 WaterFix)
    mixc.inputs["Color2"].default_value = (orig[0]*1.80, orig[1]*1.55, orig[2]*1.30, 1.0)
    nt.links.new(n.outputs["Fac"], mixc.inputs["Fac"])
    # 水线湿带: 石构 waterline 同款节点式 —— fac = clamp((z-0.5)/-0.5):
    # z>=0.5 干(fac=0), z=0 全湿(fac=1), 水下部分保持湿色
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs["Vector"])
    wsub = nt.nodes.new("ShaderNodeMath"); wsub.operation = 'SUBTRACT'
    nt.links.new(sep.outputs["Z"], wsub.inputs[0]); wsub.inputs[1].default_value = 0.5
    wdiv = nt.nodes.new("ShaderNodeMath"); wdiv.operation = 'DIVIDE'
    nt.links.new(wsub.outputs[0], wdiv.inputs[0]); wdiv.inputs[1].default_value = -0.5
    wcl = nt.nodes.new("ShaderNodeClamp")
    nt.links.new(wdiv.outputs[0], wcl.inputs["Value"])
    mix_water = nt.nodes.new("ShaderNodeMixRGB"); mix_water.blend_type = 'MIX'
    nt.links.new(wcl.outputs[0], mix_water.inputs["Fac"])
    nt.links.new(mixc.outputs["Color"], mix_water.inputs["Color1"])
    mix_water.inputs["Color2"].default_value = (base[0]*0.38, base[1]*0.42, base[2]*0.34, 1.0)
    nt.links.new(mix_water.outputs["Color"], bsdf.inputs["Base Color"])
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

def qingshi_material(name, base_rgb=(0.448, 0.440, 0.412), joint=0.024,
                     block_var=0.36, bump_strength=0.68,
                     course_h=0.40, course_w=0.90, z_phase=0.15, x_phase=0.5,
                     uv_joints=False):
    """青石(石灰岩)桥体: 冷灰蓝基色 + 鲜明大块条石横分层与纵错缝 + 块级灰度差。
    依据二审意见: 杜绝'程序噪声混凝土抹灰'观感, 强化规整石砌实体与竖缝凹槽。
    [六审B] joint/block_var/bump 开放为参数, 支撑砌缝视觉三级层级。"""
    # [八审x2] weather 0.42->0.22: 世界坐标噪声在每个独立石块面相位不同,
    # 高权重在提亮基色上读成"棋盘斑块"(块间对比主因已由此承担)。
    # [M17] 网格对齐几何砧石(course_h=0.40/course_w=0.90/z起0.15/x相位0.5);
    # 水线带抬到 z∈[0.55-0.9, 0.55] 覆盖贴面起砌带(原 z=0 半淹水下=干湿分界缺失)。
    return stone_material(name, base_rgb, joint=joint, course_h=course_h,
                          course_w=course_w, z_phase=z_phase, x_phase=x_phase,
                          weather=0.16, waterline_z=0.55, waterline_h=0.90,
                          block_var=block_var, uv_joints=uv_joints,
                          bump_strength=bump_strength, base_rough=0.86)
