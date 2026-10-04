"""LOD-M 蹲狮: 按 GPT v4 给的 11 体块方案程序化生成。
尺寸: 总高 H, 总长 0.78H, 总宽 0.42H。雄狮抱绣球 / 雌狮护幼狮 两变体。
识别五特征: 大头 / 胸鼓臀低蹲姿 / 前腿并立 / 鬃毛卷 / 尾卷侧后。"""
import bmesh
import math
from mathutils import Vector, Matrix


def _ellipsoid(bm, center, radii, seg=12, ring=8, rot_y=0.0):
    cx, cy, cz = center
    rx, ry, rz = radii
    R = Matrix.Rotation(rot_y, 3, 'Y')
    vs = {}
    for i in range(1, ring):
        phi = math.pi * i / ring
        for j in range(seg):
            th = 2 * math.pi * j / seg
            p = Vector((rx*math.sin(phi)*math.cos(th),
                        ry*math.sin(phi)*math.sin(th),
                        rz*math.cos(phi)))
            p = R @ p
            vs[(i, j)] = bm.verts.new((cx+p.x, cy+p.y, cz+p.z))
    for i in range(1, ring-1):
        for j in range(seg):
            a, b = vs[(i, j)], vs[(i, (j+1) % seg)]
            c, d = vs[(i+1, (j+1) % seg)], vs[(i+1, j)]
            try: bm.faces.new((a, b, c, d))
            except ValueError: pass
    return vs


def _box(bm, center, size, rot_y=0.0):
    cx, cy, cz = center
    sx, sy, sz = (s/2.0 for s in size)
    R = Matrix.Rotation(rot_y, 3, 'Y')
    corners = [Vector((x, y, z)) for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)]
    vs = [bm.verts.new(tuple(Vector((cx, cy, cz)) + (R @ c))) for c in corners]
    for f in ((0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)):
        try: bm.faces.new([vs[k] for k in f])
        except ValueError: pass


def lion_bm(H=0.22, variant=0, seed=0):
    """variant: 0=雄狮抱绣球, 1=雌狮护幼狮。其余微扰由 seed 决定。"""
    bm = bmesh.new()
    r = (lambda k: ((k*1103515245 + 12345 + seed*97) >> 16 & 255) / 255.0)
    jit = lambda k, amt: 1.0 + (r(k) - 0.5) * amt
    # 1 躯干
    _ellipsoid(bm, (0.00*H, 0.00, 0.36*H), (0.42*0.78*H*jit(1,0.06), 0.26*0.42*H*jit(2,0.06), 0.28*H))
    # 2 胸块(前胸鼓起)
    _ellipsoid(bm, (0.18*H, 0.00, 0.42*H), (0.18*0.78*H, 0.24*0.42*H, 0.24*H*jit(3,0.08)))
    # 3 臀块(后蹲)
    _ellipsoid(bm, (-0.18*H, 0.00, 0.30*H), (0.20*0.78*H, 0.24*0.42*H, 0.20*H))
    # 4 头(偏大 —— 远景识别关键)
    hs = 1.0 * jit(4, 0.10)
    _ellipsoid(bm, (0.28*H, 0.00, 0.64*H*hs), (0.24*0.78*H, 0.22*0.42*H*hs, 0.22*H*hs))
    # 5 口鼻
    _box(bm, (0.39*H, 0.00, 0.58*H), (0.10*0.78*H, 0.08*0.42*H, 0.06*H))
    # 6 鬃毛圈: 薄环 + 8 小卷块
    mane_n = 8
    mr = 0.14*0.78*H
    for k in range(mane_n):
        a = 2*math.pi*k/mane_n
        _ellipsoid(bm, (0.28*H + math.cos(a)*mr*0.55, math.sin(a)*mr*0.75, 0.64*H*hs + math.sin(a)*mr*0.30),
                   (0.045*0.78*H, 0.045*0.42*H, 0.045*H), seg=8, ring=5)
    # 7 耳 x2
    for sy in (-1, 1):
        _box(bm, (0.26*H, sy*0.06*0.42*H, 0.74*H*hs), (0.05*0.78*H, 0.03*0.42*H, 0.06*H))
    # 8 前腿组
    _box(bm, (0.22*H, 0.00, 0.12*H), (0.18*0.78*H, 0.20*0.42*H, 0.22*H))
    _box(bm, (0.22*H, 0.00, 0.12*H), (0.18*0.78*H, 0.03*0.42*H, 0.22*H))   # 中缝
    # 9 前爪
    for sy in (-1, 1):
        _box(bm, (0.26*H, sy*0.06*0.42*H, 0.03*H), (0.07*0.78*H, 0.06*0.42*H, 0.04*H))
    # 10 后腿/后座
    _box(bm, (-0.10*H, 0.00, 0.10*H), (0.22*0.78*H, 0.24*0.42*H, 0.16*H))
    # 11 尾巴(卷在侧后)
    for k in range(7):
        t = k/6.0
        a = math.pi*0.6 + t*math.pi*1.5
        rr = 0.10*0.78*H
        _ellipsoid(bm, (-0.24*H - math.cos(a)*rr*0.8, 0.10*0.42*H + t*0.06*0.42*H, 0.16*H + math.sin(a)*rr*0.5),
                   (0.025*0.78*H, 0.025*0.42*H, 0.025*H), seg=7, ring=5)
    # 变体: 抱绣球 / 护幼狮
    if variant == 0:
        _ellipsoid(bm, (0.28*H, -0.07*0.42*H, 0.05*H), (0.06*0.78*H, 0.06*0.42*H, 0.06*H), seg=10, ring=6)
    else:
        _ellipsoid(bm, (0.25*H, 0.06*0.42*H, 0.05*H), (0.08*0.78*H, 0.06*0.42*H, 0.06*H), seg=10, ring=6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.normal_update()
    return bm


if __name__ == "__main__":
    for v in (0, 1):
        bm = lion_bm(0.22, v, seed=v*7)
        print("变体%d: verts=%d faces=%d" % (v, len(bm.verts), len(bm.faces)))
