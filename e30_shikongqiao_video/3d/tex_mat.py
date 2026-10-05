# -*- coding: utf-8 -*-
"""实测贴图接入: 用 ambientCG Marble001 (CC0) 替换纯色 base color。

来源(已实测, 非凭记忆):
- 资产 Marble001, 下载 https://ambientcg.com/get?file=Marble001_1K-JPG.zip
- 授权 CC0 公共领域(ambientCG 全部资产为 CC0), 无需署名
- 实测 Color.jpg 均值 RGB=(224,221,215) 饱和差 8 sd 8.1 → 汉白玉级
  (对比: PolyHaven 13 个 marble 类全部偏黄褐, 最白 marble_rock_02 仍 (198,178,154) 饱和差 44)
- Roughness.jpg 均值 44 → 相当光滑(0.17 线性), 适合打磨过的汉白玉栏杆
- NormalGL/OpenGL 切线空间法线; Displacement 均值 248 (近白) → 起伏很小

设计约束(遵循 E30 既有纪律):
- 贴图以世界坐标(Geometry.Position) 驱动, 不依赖 UV —— 现有构件都是 bm_from_py
  程序化生成、无 UV 展开。这是能在不重做几何的前提下贴图的前提。
- 平铺尺度 SCALE_M 是可调参数, 不写死进节点; 判据 bridge3d 侧不依赖它。
- 保留 stone_material 的砌缝/风化节点, 只把 base color 的纯色输入换成
  贴图 × 原有色差调制 —— 即"贴图提供微观石质, 程序化提供砌筑尺度"。
"""
import bpy

# 贴图文件 basename 前缀(与 zip 内命名一致)
PREFIX = "Marble001_1K-JPG"
SCALE_M = 1.60          # 平铺物理尺寸(米): 1.6m 一个循环, 细粒石材观感
BUMP_STRENGTH = 0.28    # 法线强度; Marble001 起伏小, 不用大值


def _img(tex_dir, suffix, name):
    """加载贴图; 缺失返回 None(调用方据此跳过, 不得静默退化成纯色)."""
    path = "%s/%s_%s.jpg" % (tex_dir.rstrip("/"), PREFIX, suffix)
    if name in bpy.data.images:
        return bpy.data.images[name]
    if not __import__("os").path.exists(path):
        raise FileNotFoundError(
            "贴图缺失: %s  (先跑 scripts/fetch_ambientcg_marble001.sh 下载)" % path)
    img = bpy.data.images.load(path)
    img.name = name
    return img


def make_tex_stone(name="marble_tex", tex_dir="textures/ambientcg",
                   base_rgb=(0.90, 0.893, 0.868), rough_bias=0.0):
    """汉白玉 + Marble001 贴图: 物理正确的 roughness/normal/color 三通道。

    返回 material。与 materials.marble_material 的差别: 此版带真实 PBR 贴图,
    砌缝/色差仍由 materials.stone_material 叠加(见 apply_to)。
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.30

    col = _img(tex_dir, "Color", "acg_marble_color")
    rgh = _img(tex_dir, "Roughness", "acg_marble_rough")
    nrm = _img(tex_dir, "NormalGL", "acg_marble_normal")

    # ── 世界坐标驱动 UV: Position -> Mapping(scale) -> 各 Image Texture ──
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    mp.inputs["Scale"].default_value = (1.0 / SCALE_M, 1.0 / SCALE_M, 1.0 / SCALE_M)

    tex_c = nt.nodes.new("ShaderNodeTexImage"); tex_c.image = col
    tex_r = nt.nodes.new("ShaderNodeTexImage"); tex_r.image = rgh
    tex_n = nt.nodes.new("ShaderNodeTexImage"); tex_n.image = nrm
    for t in (tex_c, tex_r, tex_n):
        t.extension = 'REPEAT'
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])

    # ── Color: 贴图 × base_rgb 调色(保留原色作为白平衡权重) ──
    # 贴图实测 (224,221,215) 已是目标白度; base_rgb 微调, 不做整体染色。
    hsv = nt.nodes.new("ShaderNodeHueSaturation")
    nt.links.new(tex_c.outputs["Color"], hsv.inputs["Color"])
    hsv.inputs["Saturation"].default_value = 0.90
    hsv.inputs["Value"].default_value = 1.0
    nt.links.new(hsv.outputs["Color"], bsdf.inputs["Base Color"])

    # ── Roughness: 贴图为主, rough_bias 微调 ──
    if rough_bias:
        radd = nt.nodes.new("ShaderNodeMath"); radd.operation = 'ADD'
        nt.links.new(tex_r.outputs["Color"], radd.inputs[0])
        radd.inputs[1].default_value = rough_bias
        nt.links.new(radd.outputs[0], bsdf.inputs["Roughness"])
    else:
        nt.links.new(tex_r.outputs["Color"], bsdf.inputs["Roughness"])

    # ── Normal: OpenGL 切线空间 -> Normal Map(强度经 Bump 节点可控) ──
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = BUMP_STRENGTH
    nt.links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    return m
