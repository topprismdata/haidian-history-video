# -*- coding: utf-8 -*-
"""桥头靠山兽 v9(beasts2): 前压蹲纵式+解剖级重塑批, 真拍重雕批(2026-10-06)。

历史依据(实拍 17_Arch_Bridge_Statue_over_Kunming_Lake_(3627588283) 剪影实证,
八审P2/九轮第一刀"解剖级重塑"): GPT 八审判词"真兽是向湖面压出去的猛兽,
模型还是站直的胖而昂首的幻想兽"。六刀落位: ①躯干拉长(约一个头长 10-15%:
臀球后拉 0.04+腰腹/胸 rx 增长) ②胸腹压低(胸底 0.21→0.14/腹线 0.19→0.13)
③肩胛前移 0.265→0.315 形成前倾力线(肩峰 0.577>臀上 0.425, 背线前高后低)
④头颈进一步前伸且减仰角(颈 -0.50→-0.30/吻轴 -0.21→-0.06 近水平/吻端
出座缘悬于湖面) ⑤四肢"圆柱+爪"→负重肩-肘-腕折线(肘部内折角≈92°, 宽爪
前踏) ⑥背脊火焰最后随新脊线重雕(瓣根落回下沉背线, 主峰尖 0.90>冠顶 0.737)。
七审 P2 雕刻化火焰瓣五特征(厚根薄尖/整体后掠/前后遮叠/大小不一/间距不均)
保留; 废 v8 直撑圆柱前肢与昂首头位; 更早废 v4 高颈直立坐犬态 / v5 伏卧
前探+单片巨卷 / v6 蹲坐昂首+圆泡云脊 / v7 规则晶体齿脊。

交付形态: beast_bm(size, variant, seed) -> 单只水密 bmesh; place_beasts(spots) ->
4 个 linked duplicate 共享 NVARIANTS 套 mesh。variant 0 张口 / 1 含珠微合。
Python 3.9 兼容(禁 match / X|None 注解)。
"""
import bmesh
import math

import bpy
from mathutils import Matrix, Vector

_CACHE = {}
NVARIANTS = 2

_SEG, _RING = 18, 10
_SEG_S, _RING_S = 14, 8
_SEG_M, _RING_M = 12, 7


def _ell(c, r, seg=_SEG, ring=_RING, rot_x=0.0, rot_y=0.0, rot_z=0.0):
    """闭合椭球(独立 bmesh)。极点扇面收口, 保证水密; 支持绕心旋转(鬃瓦/脊棱定向)。"""
    cx, cy, cz = c
    rx, ry, rz = r
    R = (Matrix.Rotation(rot_x, 3, 'X') @ Matrix.Rotation(rot_y, 3, 'Y')
         @ Matrix.Rotation(rot_z, 3, 'Z'))
    bm = bmesh.new()
    pt = R @ Vector((0.0, 0.0, rz))
    pb = R @ Vector((0.0, 0.0, -rz))
    top = bm.verts.new((pt.x + cx, pt.y + cy, pt.z + cz))
    bot = bm.verts.new((pb.x + cx, pb.y + cy, pb.z + cz))
    rows = []
    for i in range(1, ring):
        phi = math.pi * i / ring
        sp, cp = math.sin(phi), math.cos(phi)
        rows.append([])
        for j in range(seg):
            p = R @ Vector((rx * sp * math.cos(2 * math.pi * j / seg),
                            ry * sp * math.sin(2 * math.pi * j / seg),
                            rz * cp))
            rows[-1].append(bm.verts.new((p.x + cx, p.y + cy, p.z + cz)))
    for j in range(seg):
        bm.faces.new((top, rows[0][j], rows[0][(j + 1) % seg]))
        bm.faces.new((bot, rows[-1][(j + 1) % seg], rows[-1][j]))
    for i in range(len(rows) - 1):
        for j in range(seg):
            bm.faces.new((rows[i][j], rows[i + 1][j],
                          rows[i + 1][(j + 1) % seg], rows[i][(j + 1) % seg]))
    for f in bm.faces:
        f.smooth = True
    return bm


def _box(c, s, rot_y=0.0, rot_x=0.0, rot_z=0.0):
    """闭合盒(独立 bmesh), 支持绕 Y/X/Z 旋转(片状鬃/S 尾带定向)。"""
    cx, cy, cz = c
    sx, sy, sz = (v / 2.0 for v in s)
    R = (Matrix.Rotation(rot_x, 3, 'X') @ Matrix.Rotation(rot_y, 3, 'Y')
         @ Matrix.Rotation(rot_z, 3, 'Z'))
    bm = bmesh.new()
    vs = []
    for x in (-sx, sx):
        for y in (-sy, sy):
            for z in (-sz, sz):
                p = R @ Vector((x, y, z))
                vs.append(bm.verts.new((p.x + cx, p.y + cy, p.z + cz)))
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
              (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([vs[k] for k in f])
    for f in bm.faces:
        f.smooth = True
    return bm


def _frustum(c, s, tx=1.0, tz=1.0, rot_y=0.0, rot_x=0.0):
    """闭合楔形棱台(独立 bmesh)。+X 端面 y/z 缩 tx(前窄后宽), 顶面 x/y 缩 tz(楔形上收)。"""
    cx, cy, cz = c
    sx, sy, sz = (v / 2.0 for v in s)
    R = Matrix.Rotation(rot_x, 3, 'X') @ Matrix.Rotation(rot_y, 3, 'Y')
    bm = bmesh.new()
    vs = []
    for x in (-sx, sx):
        for y in (-sy, sy):
            for z in (-sz, sz):
                p = Vector((x, y, z))
                if x > 0.0:
                    p.y *= tx
                    p.z *= tx
                if z > 0.0:
                    p.x *= tz
                    p.y *= tz
                p = R @ p
                vs.append(bm.verts.new((p.x + cx, p.y + cy, p.z + cz)))
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
              (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([vs[k] for k in f])
    for f in bm.faces:
        f.smooth = True
    return bm


def _blade(c, h, w, t, rot_y=-0.10):
    """火焰瓣(独立 bmesh): 八棱根环 + 厚根段 + 内收腰 + 薄尖段 + 后掠尖锋 + 前埋钝底。

    七审 P2 雕刻化(废"规则晶体齿"读感): 四段母线 0/0.40h/0.68h/0.85h,
    根段保持 0.80w 到 0.40h(厚根) → 0.68h 收至 0.34w(内凹腰) → 0.85h 只剩
    0.21w(薄尖) → 尖锋(合成顶点=环心+rot 后掠), 根粗尖细一气呵成; 前缘
    xoffset 0/−0.06/−0.18/−0.25/−0.28h 递增后收(中段收速最快=凹弧焰舌卷,
    非直边晶体); 八棱环前后棱增宽 1.18·|cos a|³(石棱正面折带, 侧面圆浑);
    尖锋配 rot_y 后掠角(布片 -0.20→-0.52 递增=整体后掠);
    钝底下沉 0.16h 前埋 0.06h, 令根环整条埋入背脊体块(防切线退化/防瓣底悬丝)。
    """
    cx, cy, cz = c
    R = Matrix.Rotation(rot_y, 3, 'Y')
    bm = bmesh.new()
    NS = 8
    prof = ((0.0, 0.0, 1.0, 1.0), (0.40, -0.06, 0.80, 0.88),
            (0.68, -0.18, 0.34, 0.52), (0.85, -0.25, 0.21, 0.34))
    rows = []
    for (zh, xo, ws, ts) in prof:
        row = []
        for j in range(NS):
            a = 2.0 * math.pi * j / NS
            k = 1.0 + 0.18 * abs(math.cos(a)) ** 3
            p = R @ Vector((w * ws * k * math.cos(a) + xo * h,
                            t * ts * math.sin(a), zh * h))
            row.append(bm.verts.new((p.x + cx, p.y + cy, p.z + cz)))
        rows.append(row)
    tp = R @ Vector((-0.28 * h, 0.0, h))
    bt = R @ Vector((0.06 * h, 0.0, -0.16 * h))
    va = bm.verts.new((tp.x + cx, tp.y + cy, tp.z + cz))
    vb = bm.verts.new((bt.x + cx, bt.y + cy, bt.z + cz))
    for i in range(len(rows) - 1):
        for j in range(NS):
            k = (j + 1) % NS
            bm.faces.new((rows[i][j], rows[i][k], rows[i + 1][k], rows[i + 1][j]))
    for j in range(NS):
        k = (j + 1) % NS
        bm.faces.new((rows[0][k], rows[0][j], vb))
        bm.faces.new((rows[-1][j], rows[-1][k], va))
    return bm


def _sculpt_parts(variant):
    """前压蹲纵式靠山兽部件(单位高 1.0, 朝 +X)。返回 (P, N, F)。

    八审P2/九轮第一刀(2026-10-06, GPT 八审"解剖级重塑"; 实拍 3627588283
    剪影对照, 真兽=向湖面压出去的猛兽):
    1. 躯干拉长(一个头长约 15%: 吻端0.78-颅后0.31=0.47, 胸前缘0.30→0.335 +
       臀球后拉0.045, 躯干 0.835→0.915); 侧读去胖: 腰腹 rz 0.13/臀沉座。
    2. 胸腹压低: 胸底 0.21→0.14, 腹线 0.19→0.13(腿间净空≈0.045, 实拍腹线
       贴座)。
    3. 肩胛前移 0.265→0.315(+0.05): 肩峰 0.577 显著高于臀上 0.425, 背线
       前高后低下行 ≈12°, 与前探头颈合成"向湖面压出去"的前倾力线。
    4. 头颈进一步前伸且减仰角: 颈 rot_y -0.50→-0.30, 吻轴 -0.21→-0.06
       (近水平), 头组整体 +x/-z; 吻端 0.678→0.748, 越出石座前缘 0.72。
    5. 四肢"圆柱+爪"→负重折线: 前肢肩段(顶入胸底, 后倾26°)-肘(内折角
       ≈92°)-前臂(前下撑61°)-宽爪前踏 0.44; 后肢折叠随臀后移。
    6. 背脊火焰最后随新脊线重雕: 瓣根全部落回下沉后的背线(0.50→0.31),
       主峰尖 0.90>冠顶 0.737(超出量 0.163≈总高 18%, 对齐实拍焰峰明显
       高头); 七审雕刻化五特征(厚根薄尖/整体后掠/前后遮叠/大小不一/
       间距不均)保留。
    体块=椭球/盒(rot_y 定向: 负角 +X 端上仰/顶部向后倒伏, 正角相反);
    火焰瓣/披鬃/云/尾=C 壳先并再总并(瓣环刃/鬃锚/尾根均深埋体块保连通);
    五官=负刀 crease+后并凸件。剪影验收: 前倾力线(肩峰高/背线下行/头前压)/
    腹线贴座/前肢肘折前踏/吻近水平/焰峰高过头顶/尾贴腿侧。
    (七审 P2 头颈降低与胸削参数被本轮前伸减仰角取代; v8 直撑圆柱前肢已废。)
    """
    P, N, F = [], [], []
    C = []

    def add(bm, lst=None):
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.normal_update()
        (lst if lst is not None else P).append(bm)

    def ell(c, r, seg=_SEG, ring=_RING, rot_x=0.0, rot_y=0.0, rot_z=0.0,
            carve=False):
        add(_ell(c, r, seg, ring, rot_x=rot_x, rot_y=rot_y, rot_z=rot_z),
            C if carve else None)

    def blade(c, h, w, t, rot_y=-0.10, carve=True):
        add(_blade(c, h, w, t, rot_y=rot_y), C if carve else None)

    def box(c, s, rot_y=0.0, rot_x=0.0, rot_z=0.0):
        add(_box(c, s, rot_y, rot_x, rot_z))

    def neg(bm):
        add(bm, N)

    def fin(bm):
        add(bm, F)

    hy = 0.0 if variant == 0 else 0.012
    tsy = 1.0 if variant == 0 else -1.0

    # 1. 长方石座(随躯干拉长 1.55→1.62; 吻端越出前缘 0.72 悬于湖面)
    box((-0.09, 0, 0.042), (1.62, 0.58, 0.095))

    # 2. 前压躯干(九轮: 拉长+压低+肩胛前移=前倾力线; 背线 肩峰0.577→臀上0.425)
    ell((-0.36, 0, 0.245), (0.21, 0.205, 0.18))     # 臀球(后拉0.045, 沉入座面)
    ell((-0.075, 0, 0.265), (0.235, 0.20, 0.135))   # 腰腹(腹线0.13 不变, 顶升0.40填背谷)
    ell((0.185, 0, 0.29), (0.15, 0.19, 0.15))       # 胸(压低前顶: 底0.14 前缘0.335)
    ell((0.315, 0, 0.465), (0.105, 0.175, 0.112))   # 肩胛(前移+0.05, 肩峰0.577)
    ell((0.36, 0, 0.445), (0.10, 0.115, 0.10), rot_y=-0.30)  # 咽喉填充(随颈前移)
    # 2b. 后肢折叠: 大腿 + 飞节 + 前伸后爪 + 三趾(随臀后拉 -0.035)
    for sy in (1, -1):
        ell((-0.345, sy * 0.15, 0.185), (0.13, 0.085, 0.115))
        ell((-0.195, sy * 0.16, 0.13), (0.075, 0.06, 0.08))
        box((-0.075, sy * 0.155, 0.10), (0.16, 0.11, 0.05))
        for ty in (-0.032, 0.002, 0.036):
            ell((0.01, sy * 0.155 + ty, 0.095), (0.03, 0.016, 0.022),
                _SEG_S, _RING_S)

    # 3. 前肢负重折线(九轮: "圆柱+爪"→肩-肘-腕): 肩段顶入胸底后倾26°,
    #    肘部内折≈92°, 前臂前下撑61°, 宽爪前踏 0.44(胸前缘 0.335 之前)
    for sy in (1, -1):
        ell((0.265, sy * 0.135, 0.27), (0.078, 0.07, 0.125), rot_y=0.45)
        ell((0.30, sy * 0.14, 0.15), (0.115, 0.062, 0.062), rot_y=0.50)
        box((0.44, sy * 0.145, 0.093), (0.17, 0.13, 0.055))
        for ty in (-0.036, 0.002, 0.040):
            ell((0.535, sy * 0.145 + ty, 0.088), (0.034, 0.018, 0.025),
                _SEG_S, _RING_S)

    # 4. 头颈前伸且减仰角(九轮: 颈 -0.50→-0.30, 吻轴 -0.21→-0.06 近水平,
    #    头组 +x/-z: 冠顶 0.737/吻端 0.748 越座缘; 颏须垂桥接胸)
    ell((0.37, 0, 0.475), (0.115, 0.125, 0.115), rot_y=-0.30)      # 颈
    ell((0.44, hy, 0.60), (0.13, 0.14, 0.12))                      # 颅
    ell((0.425, hy, 0.692), (0.108, 0.14, 0.045), rot_y=-0.08,
        carve=True)                                                # 冠盖
    ell((0.515, hy, 0.655), (0.095, 0.12, 0.038), rot_y=-0.06)     # 额檐(眉上收)
    ell((0.60, hy, 0.652), (0.105, 0.10, 0.06), rot_y=-0.06)       # 鼻梁
    ell((0.695, hy, 0.650), (0.06, 0.085, 0.048), rot_y=-0.06)     # 吻端
    ell((0.748, hy, 0.663), (0.032, 0.058, 0.028), rot_y=-0.06)    # 鼻镜(与鼻梁齐平, 不上翘)
    for sy in (1, -1):
        ell((0.74, hy + sy * 0.05, 0.665), (0.026, 0.026, 0.022),
            _SEG_S, _RING_S)                                       # 鼻翼
        ell((0.50, hy + sy * 0.10, 0.59), (0.07, 0.055, 0.055))    # 颊垫
    ell((0.565, hy, 0.575), (0.10, 0.085, 0.05), rot_y=-0.06)      # 下颌(埋入鼻梁下缘)
    ell((0.445, hy, 0.52), (0.075, 0.08, 0.075), rot_y=-0.30,
        carve=True)                                                # 颏须
    for sy in (1, -1):
        ell((0.355, hy + sy * 0.09, 0.665), (0.035, 0.026, 0.042),
            _SEG_S, _RING_S, rot_x=sy * -0.4, rot_y=-0.35)         # 贴颅伏耳
        ell((0.51, hy + sy * 0.09, 0.67), (0.05, 0.04, 0.022),
            _SEG_S, _RING_S, rot_x=sy * 0.2, rot_y=-0.06)          # 眉脊

    # 5. 背脊火焰瓣(九轮: 火焰最后随新脊线重雕——躯干压低后瓣根全部落回
    #    下沉背线 0.50→0.31; 七审 P2 雕刻化五特征保留):
    #    ①厚根薄尖——_blade 四段母线(根 0.80w 保持到 0.40h, 0.85h 只剩 0.21w);
    #    ②整体后掠——每瓣独立后掠角 -0.20→-0.52 向后递增, 尖锋自身后掠;
    #    ③峰位随新脊线(主峰臀上), 尖 0.90 明确高过新冠顶 0.737(头顶降后
    #    超出量 ≈总高 18%, 对齐实拍); ④大小不一/间距不均; ⑤主 7 瓣根宽
    #    互叠 + 3 矮瓣嵌谷。根环全部深埋新背线 ≥0.03(钝底下沉 0.16h 加固)。
    for (bx, bz, bh, bw, bt_, brot) in (
            (0.27, 0.50, 0.27, 0.055, 0.068, -0.20),    # 项后鬃锋(尖0.716)
            (0.16, 0.40, 0.34, 0.10, 0.082, -0.30),     # 尖0.672
            (0.02, 0.345, 0.55, 0.17, 0.10, -0.36),     # 前峰 尖0.784
            (-0.21, 0.33, 0.715, 0.21, 0.115, -0.42),   # 主峰(臀上) 尖0.90
            (-0.34, 0.385, 0.54, 0.16, 0.10, -0.48),    # 次峰 尖0.815
            (-0.445, 0.37, 0.275, 0.10, 0.078, -0.50),  # 尖0.59
            (-0.535, 0.31, 0.225, 0.075, 0.065, -0.52)):  # 尖0.49(臀后收)
        blade((bx, 0, bz), bh, bw, bt_, rot_y=brot)
    # 5a. 谷间矮瓣 x3(前后遮叠中景层; 根环埋背线/臀球/垂云 ≥0.05)
    #    (瓣高参数 h 的实际尖锋到达 ≈0.80h, v8 同一约定: 0.395+0.60*0.8=0.874)
    for (bx, bz, bh, bw, bt_, brot) in (
            (0.10, 0.37, 0.215, 0.075, 0.058, -0.28),   # 2/3 谷(尖0.54)
            (-0.27, 0.36, 0.225, 0.08, 0.06, -0.45),    # 4/5 谷(尖0.54)
            (-0.49, 0.345, 0.175, 0.065, 0.052, -0.58)):  # 6/7 谷(尖0.485)
        blade((bx, 0, bz), bh, bw, bt_, rot_y=brot)
    ell((-0.575, 0, 0.32), (0.09, 0.13, 0.085), rot_y=0.8, carve=True)  # 臀后垂云
    ell((-0.605, 0, 0.185), (0.085, 0.12, 0.10))                    # 垂云落地
    # 5b. 瓣缘两侧披鬃三对(向后顺披, 随下沉背线降位; 锚端嵌入瓣体+体侧双锚)
    #     + 头后卷勾
    for sy in (1, -1):
        ell((0.17, sy * 0.10, 0.40), (0.062, 0.05, 0.095),
            _SEG_S, _RING_S, rot_x=sy * 0.3, rot_y=-0.9, carve=True)
        ell((-0.10, sy * 0.10, 0.36), (0.065, 0.05, 0.10),
            _SEG_S, _RING_S, rot_x=sy * 0.3, rot_y=-0.9, carve=True)
        ell((-0.36, sy * 0.095, 0.39), (0.06, 0.048, 0.09),
            _SEG_S, _RING_S, rot_x=sy * 0.3, rot_y=-0.9, carve=True)
        ell((0.37, hy + sy * 0.095, 0.665), (0.04, 0.026, 0.05),
            _SEG_S, _RING_S, rot_y=-1.1, carve=True)               # 头后云卷勾

    # 6. 尾: 贴体侧后腿旁 S 卷, 梢上勾(variant 换侧); 首节锚入臀球,
    #    尾根瓦并壳(保雕饰簇单连通); 随臀后拉 -0.035
    ell((-0.45, tsy * 0.165, 0.30), (0.075, 0.055, 0.075), carve=True)
    tail_anchors = ((-0.47, 0.21, 0.35), (-0.52, 0.245, 0.31),
                    (-0.50, 0.25, 0.14), (-0.365, 0.235, 0.095),
                    (-0.265, 0.22, 0.115), (-0.22, 0.215, 0.17))
    for k in range(15):
        t = k / 14.0 * (len(tail_anchors) - 1)
        i = min(int(t), len(tail_anchors) - 2)
        f = t - i
        a, b = tail_anchors[i], tail_anchors[i + 1]
        cp = tuple(a[d] + (b[d] - a[d]) * f for d in range(3))
        ell((cp[0], tsy * cp[1], cp[2]), (0.034, 0.033, 0.034),
            _SEG_S, _RING_S, carve=True)
    ell((-0.215, tsy * 0.185, 0.21), (0.044, 0.040, 0.044), _SEG_S, _RING_S,
        carve=True)

    # 7. (旧云面波纹刻槽随 v6 圆泡云删除; 火焰瓣以六棱面与凹口承担雕刻语汇)

    # 8. 减法(负刀半凸穿出表面): 口裂楔刀(沿新吻轴 -0.06) / 眼窝上割 / 鼻孔
    if variant == 0:
        neg(_frustum((0.655, hy, 0.612), (0.24, 0.052, 0.034),
                     tx=1.25, rot_y=-0.06))
    else:
        neg(_frustum((0.655, hy, 0.614), (0.24, 0.052, 0.024),
                     tx=1.25, rot_y=-0.06))
    for sy in (1, -1):
        neg(_ell((0.545, hy + sy * 0.088, 0.676), (0.038, 0.016, 0.018),
                 _SEG_S, _RING_S))
        neg(_ell((0.758, hy + sy * 0.024, 0.696), (0.012, 0.012, 0.010),
                 _SEG_S, _RING_S))

    # 8b. 后置凸件(负刀后并回): 凸眼珠 / 上唇獠牙(张口) 或 含珠(微合)
    for sy in (1, -1):
        # 眼珠中心须在眼窝负刀(0.545,±0.088,0.676)下外方, 埋入额檐实体,
        # 仅顶面探入窝内(否则整体悬在窝腔中成孤岛, 六审布尔诊断)
        fin(_ell((0.538, hy + sy * 0.096, 0.656), (0.026, 0.028, 0.026),
                 _SEG_S, _RING_S))
    if variant == 0:
        for sy in (1, -1):
            # 獠牙顶端须越过口裂楔刀上缘(x=0.655 处≈0.653)嵌入上颌实体
            fin(_ell((0.655, hy + sy * 0.040, 0.632), (0.015, 0.018, 0.048),
                     _SEG_S, _RING_S, rot_y=-0.06))
    else:
        # 含珠顶端同样越过楔刀上缘嵌入上颌(否则负刀后悬空断连)
        fin(_ell((0.66, hy, 0.630), (0.036, 0.036, 0.036), _SEG_S, _RING_S))

    # 9. 雕饰簇(鬃/云/尾)先并成单一壳, 再与体块一次并(避免切线布尔退化壳)
    if C:
        shell = _union_parts(C)
        bmc = bmesh.new()
        bmc.from_mesh(shell)
        bpy.data.meshes.remove(shell)
        bmesh.ops.recalc_face_normals(bmc, faces=bmc.faces[:])
        bmc.normal_update()
        P.append(bmc)
    return P, N, F

def _bool_step(me, tool_bm, op):
    """单步 EXACT 布尔(并/差), 返回新 mesh(临时对象用后即焚)。"""
    col = bpy.context.scene.collection
    tme = bpy.data.meshes.new("_beast2_tool")
    tool_bm.to_mesh(tme)
    ob = bpy.data.objects.new("_beast2_tool", tme)
    col.objects.link(ob)
    base = bpy.data.objects.new("_beast2_acc", me)
    col.objects.link(base)
    md = base.modifiers.new("op", 'BOOLEAN')
    md.operation = op
    md.solver = 'EXACT'
    md.object = ob
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(base.evaluated_get(dg))
    col.objects.unlink(ob)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(tme)
    col.objects.unlink(base)
    bpy.data.objects.remove(base)
    return new_me


def _union_parts(parts):
    """成对平衡树并集。长 EXACT 串链易在切线面处生退化壳, 两两归并降单步复杂度。"""
    level = []
    for pbm in parts:
        me = bpy.data.meshes.new("_beast2_part")
        pbm.to_mesh(me)
        pbm.free()
        level.append(me)
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level) - 1, 2):
            tbm = bmesh.new()
            tbm.from_mesh(level[i + 1])
            nxt.append(_bool_step(level[i], tbm, 'UNION'))
            tbm.free()
        if len(level) % 2:
            nxt.append(level[-1])
        level = nxt
    return level[0]


def _weld(me):
    """焊缝清理(三审: 黑缝/破面): 重合点焊接 + 法线一致化。"""
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(me)
    bm.free()
    me.update()


def _normalize(bm):
    zs = [v.co.z for v in bm.verts]
    zmin, zmax = min(zs), max(zs)
    s = 1.0 / (zmax - zmin)
    bmesh.ops.scale(bm, vec=(s, s, s), verts=bm.verts)
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    bmesh.ops.translate(bm, verts=bm.verts,
                        vec=(-(min(xs) + max(xs)) / 2.0,
                             -(min(ys) + max(ys)) / 2.0,
                             -min(v.co.z for v in bm.verts)))


def _densify(me):
    col = bpy.context.scene.collection
    ob = bpy.data.objects.new("_beast2_densify", me)
    col.objects.link(ob)
    md = ob.modifiers.new("s", 'SUBSURF')
    md.subdivision_type = 'SIMPLE'
    md.levels = 1
    md.render_levels = 1
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    col.objects.unlink(ob)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    return new_me


def _mark_smooth(bm, angle_deg=45.0):
    thr = math.radians(angle_deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(math.pi) > thr:
            e.smooth = False
        else:
            e.smooth = True


def _purge_slivers(bm, min_verts=32):
    """清除布尔退化小碎片(<min_verts 的离连域)。返回 False 表示存在大块断裂。"""
    for v in bm.verts:
        v.tag = False
    comps = []
    for v0 in bm.verts:
        if v0.tag:
            continue
        comp = [v0]
        v0.tag = True
        stack = [v0]
        while stack:
            v = stack.pop()
            for e in v.link_edges:
                o = e.other_vert(v)
                if not o.tag:
                    o.tag = True
                    stack.append(o)
                    comp.append(o)
        comps.append(comp)
    if len(comps) <= 1:
        return True
    comps.sort(key=len, reverse=True)
    for comp in comps[1:]:
        if len(comp) >= min_verts:
            return False
        bmesh.ops.delete(bm, geom=comp, context='VERTS')
    return True


def _build_master(variant):
    pos, negl, finl = _sculpt_parts(variant)
    me = _union_parts(pos)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    _purge_slivers(bm)
    me = bpy.data.meshes.new("_beast2_struct")
    bm.to_mesh(me)
    bm.free()
    for nbm in negl:
        me = _bool_step(me, nbm, 'DIFFERENCE')
    for fbm in finl:
        me = _bool_step(me, fbm, 'UNION')
    _weld(me)
    bm = bmesh.new()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # M10.1 补洞硬工序: 并集窄缝/切线交留下的穿透洞(四审 22 号图体侧黑缝根因)
    bedges = [e for e in bm.edges if len(e.link_faces) == 1]
    if bedges:
        bmesh.ops.holes_fill(bm, edges=bedges, sides=0)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bedges2 = [e for e in bm.edges if len(e.link_faces) == 1]
    if bedges2:
        # holes_fill 失败的残余开边: voxel remesh 兜底(保证闭合流形, 面数代价可接受)
        tmp_me = bpy.data.meshes.new("_beast2_vox")
        bm.to_mesh(tmp_me)
        bm.free()
        ob = bpy.data.objects.new("_beast2_vox", tmp_me)
        bpy.context.scene.collection.objects.link(ob)
        md = ob.modifiers.new("vox", 'REMESH')
        md.mode = 'VOXEL'
        md.voxel_size = 0.016
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        tmp_me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        bpy.context.scene.collection.objects.unlink(ob)
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(tmp_me)
        bm = bmesh.new()
        bm.from_mesh(tmp_me2)
        bpy.data.meshes.remove(tmp_me2)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bedges2 = [e for e in bm.edges if len(e.link_faces) == 1]
    print("beasts2 boundary edges: %d -> %d" % (len(bedges), len(bedges2)))
    if not _purge_slivers(bm):
        bm.free()
        raise RuntimeError("beasts2: variant %d 母模存在大块离连域(布尔断裂)" % variant)
    ncomp = count_components(bm)
    if ncomp != 1:
        bm.free()
        raise RuntimeError("beasts2: variant %d 母模不水密(连通域=%d>1)" % (variant, ncomp))
    _normalize(bm)
    me2 = bpy.data.meshes.new("_beast2_pre_densify")
    bm.to_mesh(me2)
    bm.free()
    out_me = _densify(me2) if len(me2.polygons) < 20000 else me2
    bm2 = bmesh.new()
    bm2.from_mesh(out_me)
    bpy.data.meshes.remove(out_me)
    _mark_smooth(bm2)
    out = bpy.data.meshes.new("_beast2_master_%d" % variant)
    bm2.to_mesh(out)
    bm2.free()
    return out


def _master(variant):
    if variant not in _CACHE:
        _CACHE[variant] = _build_master(variant)
    return _CACHE[variant]


def dispose_cache():
    for me in _CACHE.values():
        try:
            if me.users == 0:
                bpy.data.meshes.remove(me)
        except ReferenceError:
            pass
    _CACHE.clear()


def beast_bm(size=1.12, variant=0, seed=0):
    """靠山兽 bmesh。原点=底面中心, 朝 +X, 总高=size(含座)。连通域=1(水密)。"""
    bm = bmesh.new()
    bm.from_mesh(_master(variant % NVARIANTS))
    bmesh.ops.scale(bm, vec=(size, size, size), verts=bm.verts)
    return bm


def place_beasts(spots, name="beasts", size=1.12, material=None):
    """4 只靠山兽 linked duplicate 放置。spots: (x, y, z, idx, facing)。"""
    meshes = {}
    obs = []
    for i, sp in enumerate(spots):
        x, y, z, idx, facing = sp
        variant = int(idx) % NVARIANTS
        if variant not in meshes:
            bm = beast_bm(size, variant, seed=variant)
            me = bpy.data.meshes.new("%s_%d" % (name, variant))
            bm.to_mesh(me)
            bm.free()
            if material is not None:
                me.materials.append(material)
            meshes[variant] = me
        ob = bpy.data.objects.new("%s_%d" % (name, i), meshes[variant])
        ob.location = (x, y, z)
        ob.rotation_euler = (0.0, 0.0, 0.0 if facing >= 0 else math.pi)
        bpy.context.collection.objects.link(ob)
        obs.append(ob)
    return obs


def count_components(bm):
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        v.tag = False
    n = 0
    for v0 in bm.verts:
        if v0.tag:
            continue
        n += 1
        stack = [v0]
        v0.tag = True
        while stack:
            v = stack.pop()
            for e in v.link_edges:
                o = e.other_vert(v)
                if not o.tag:
                    o.tag = True
                    stack.append(o)
    return n


if __name__ == "__main__":
    for v in range(NVARIANTS):
        bm = beast_bm(1.12, v, seed=v)
        zs = [vt.co.z for vt in bm.verts]
        xs = [vt.co.x for vt in bm.verts]
        ys = [vt.co.y for vt in bm.verts]
        print("variant %d: verts=%d faces=%d comps=%d bbox x[%.3f,%.3f] y[%.3f,%.3f] z[%.3f,%.3f]"
              % (v, len(bm.verts), len(bm.faces), count_components(bm),
                 min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
