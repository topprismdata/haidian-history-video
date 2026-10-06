# e30_shikongqiao_video/3d/export_print.py
# -*- coding: utf-8 -*-
"""P1-T6 打印导出器: inset 吃装配公差 -> 外翻 -> check -> STL/3MF -> manifest/coupon。

canonical 永远是 mesh+ledger; STL/3MF 是派生物(打印件毫米口径 = 模型米 x scale x 1000)。
- inset 语义(S2 裁决): clearance 只在装配接触面吃 -- 简化为对每石三轴 bbox 各面
  内缩 clearance_model_mm/1000 模型米(装配对 = 两石各退一缝 -> 成对间隙 2x clearance)。
  分档 FIT_TIERS 按块最小维: <0.3m TIGHT / <1.0m NORMAL / 否则 LOOSE, 分派结果
  连同 clearance 写进 manifest 可追溯。
- 绕向: 族库全体内翻(signed_volume<0); STL/3MF 出口必须外翻(法线朝外右手序),
  flip_outward 统一翻三角, 翻完过 printcheck.check_stone 复验(S3: post-inset 几何
  才准过, 在 inset 前跑 = 放行薄件)。
- 范围(S2 裁决): 本轮只导出砌体角色 MASONRY_ROLES; 雕件(CARVE/RAIL/POST)不导出,
  roles= 白名单可显式覆盖; 雕件 CSG union 方案归 P4。
- 导出几何一律取石账的局部族网格(底面贴床), 不应用 ledger transform(装配定位是
  拼装时的事); coupon 名义拼装间隙才用 transform 表达。
"""
import json
import os
import struct
import time
import zipfile
from typing import Any, Callable, List, Optional, Sequence, Tuple

import numpy as np

import ledger as L
import printcheck as PC
from families import family_mesh

PRINT_BED_MM = (220.0, 220.0)
FIT_TIERS = {"TIGHT": 0.15, "NORMAL": 0.3, "LOOSE": 0.5}   # 模型毫米
# (最小维上限 m, 档名): 逐界判定, 否则 LOOSE
_FIT_BOUNDS = ((0.3, "TIGHT"), (1.0, "NORMAL"))
MASONRY_ROLES = ("RING", "SPANDREL", "PIER", "IMPOST", "BACK", "CORE", "PAVING")
_3MF_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
_3MF_REL_TYPE = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
_STL_HEADER = b"e30 P1 export_print binary STL units=mm"


# ---------------------------------------------------------------- 几何基元

def signed_volume(verts, faces):
    # type: (List[Tuple[float, float, float]], List[Tuple[int, ...]]) -> float
    """散度定理带符号体积(法线朝外右手序为正; 族库内翻为负)。quad 扇形剖分。"""
    total = 0.0
    for fc in faces:
        a = verts[fc[0]]
        for i in range(1, len(fc) - 1):
            b, c = verts[fc[i]], verts[fc[i + 1]]
            total += (a[0] * (b[1] * c[2] - b[2] * c[1])
                      + a[1] * (b[2] * c[0] - b[0] * c[2])
                      + a[2] * (b[0] * c[1] - b[1] * c[0]))
    return total / 6.0


def fit_for_block(dims_m):
    # type: (Sequence[float]) -> Tuple[str, float]
    """按块最小维分派 (tier, clearance_model_mm): <0.3m TIGHT / <1.0m NORMAL /
    否则 LOOSE。边界负控: 恰在界上归更松一档。"""
    d0 = min(dims_m)
    for bound, tier in _FIT_BOUNDS:
        if d0 < bound:
            return tier, FIT_TIERS[tier]
    return "LOOSE", FIT_TIERS["LOOSE"]


def inset(verts, clearance_model_mm):
    # type: (List[Tuple[float, float, float]], float) -> List[Tuple[float, float, float]]
    """三轴各面内缩 clearance_model_mm/1000 模型米: 顶点逐轴按是否落在 bbox
    界分类(下界->+c, 上界->-c, 内部->0); 扁轴(extent~0)不动。只缩不涨;
    clearance 0 恒等返回。"""
    cm = float(clearance_model_mm) / 1000.0
    if cm == 0.0:
        return [(float(p[0]), float(p[1]), float(p[2])) for p in verts]
    V = np.asarray(verts, dtype=float)
    lo = V.min(axis=0)
    hi = V.max(axis=0)
    ext = hi - lo
    tol = np.maximum(1e-12, ext * 1e-9)
    off = np.zeros_like(V)
    for ax in range(3):
        if ext[ax] <= tol[ax]:
            continue
        off[:, ax] = (np.where(V[:, ax] <= lo[ax] + tol[ax], cm, 0.0)
                      + np.where(V[:, ax] >= hi[ax] - tol[ax], -cm, 0.0))
    V2 = V + off
    return [(float(p[0]), float(p[1]), float(p[2])) for p in V2]


def flip_outward(verts, faces):
    # type: (List[Tuple[float, float, float]], List[Tuple[int, ...]])
    # -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]
    """绕向归一: signed_volume<0(族库内翻) -> 每面反序成法线朝外右手序
    (signed>0)。幂等; 输入不被改写。"""
    faces_out = faces
    if signed_volume(verts, faces) < 0.0:
        faces_out = [tuple(reversed(fc)) for fc in faces]
    return [(float(p[0]), float(p[1]), float(p[2])) for p in verts], faces_out


def _extents_m(verts):
    # type: (List[Tuple[float, float, float]]) -> Tuple[float, float, float]
    V = np.asarray(verts, dtype=float)
    e = V.max(axis=0) - V.min(axis=0)
    return (float(e[0]), float(e[1]), float(e[2]))


# ---------------------------------------------------------------- 文件格式

def _tris_of(faces):
    # type: (List[Tuple[int, ...]]) -> List[Tuple[int, int, int]]
    return [(fc[0], fc[i], fc[i + 1])
            for fc in faces for i in range(1, len(fc) - 1)]


def _stl_bytes(verts_mm, faces):
    # type: (List[Tuple[float, float, float]], List[Tuple[int, ...]]) -> bytes
    """二进制 STL: 80B 头 + u32 三角数 + 每三角 50B(法线右手序朝外)。"""
    tris = _tris_of(faces)
    parts = [_STL_HEADER.ljust(80, b" "), struct.pack("<I", len(tris))]
    for i0, i1, i2 in tris:
        a = np.asarray(verts_mm[i0], dtype=float)
        b = np.asarray(verts_mm[i1], dtype=float)
        c = np.asarray(verts_mm[i2], dtype=float)
        n = np.cross(b - a, c - a)
        ln = float(np.linalg.norm(n))
        if ln > 0.0:
            n = n / ln
        parts.append(struct.pack("<3f", float(n[0]), float(n[1]), float(n[2])))
        for p in (a, b, c):
            parts.append(struct.pack("<3f", float(p[0]), float(p[1]), float(p[2])))
        parts.append(struct.pack("<H", 0))
    return b"".join(parts)


def _3mf_bytes(verts_mm, faces):
    # type: (List[Tuple[float, float, float]], List[Tuple[int, ...]]) -> bytes
    """最小 3MF(zip+[Content_Types].xml+_rels/.rels+3D/3dmodel.model),
    顶点为打印件毫米, 三角外翻。"""
    vs = "".join('<vertex x="%.6f" y="%.6f" z="%.6f"/>' % tuple(p)
                 for p in verts_mm)
    ts = "".join('<triangle v1="%d" v2="%d" v3="%d"/>' % t
                 for t in _tris_of(faces))
    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xml:lang="en-US" xmlns="%s">'
             '<resources><object id="1" type="model"><mesh>'
             '<vertices>%s</vertices><triangles>%s</triangles>'
             '</mesh></object></resources>'
             '<build><item objectid="1"/></build></model>') % (_3MF_NS, vs, ts)
    ct = ('<?xml version="1.0" encoding="UTF-8"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType='
          '"application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType='
          '"application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns='
            '"http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rel0" Type="%s" Target="/3D/3dmodel.model"/>'
            '</Relationships>') % _3MF_REL_TYPE
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", ct)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("3D/3dmodel.model", model)
    return buf.getvalue()


# ---------------------------------------------------------------- 导出

def export_stone(stone, verts, faces, out_dir, scale=1 / 50.0, fit="NORMAL"):
    # type: (Dict[str, Any], List[Tuple[float, float, float]], List[Tuple[int, ...]], str, float, Optional[str]) -> Dict[str, Any]
    """单石导出。fit=None 时按块最小维自动分档; 显式档名直接生效。
    管线: inset(clearance) -> flip_outward -> check_stone(post-inset, S3, 不过即
    raise) -> STL+3MF(打印件毫米, 材质分组目录)。返回
    {stl, stl3mf(全路径), volume_cm3(打印件), fit, clearance_mm};
    manifest 里由 export_ledger 转相对路径。"""
    if fit is None:
        fit, clr = fit_for_block(_extents_m(verts))
    else:
        if fit not in FIT_TIERS:
            raise ValueError("unknown fit tier: %r (expect one of %s)"
                             % (fit, sorted(FIT_TIERS)))
        clr = FIT_TIERS[fit]
    v2 = inset(verts, clr)
    v2, f2 = flip_outward(v2, faces)
    rep = PC.check_stone(v2, f2, scale=scale)
    if not rep["ok"]:
        raise ValueError("check_stone failed for %s: %s"
                         % (stone.get("id"), rep["issues"]))
    mm = [(p[0] * scale * 1000.0, p[1] * scale * 1000.0, p[2] * scale * 1000.0)
          for p in v2]
    d = os.path.join(out_dir, str(stone.get("material", "default")))
    os.makedirs(d, exist_ok=True)
    base = str(stone["id"]).replace(".", "_")
    stl_path = os.path.join(d, base + ".stl")
    with open(stl_path, "wb") as fh:
        fh.write(_stl_bytes(mm, f2))
    mf_path = os.path.join(d, base + ".3mf")
    with open(mf_path, "wb") as fh:
        fh.write(_3mf_bytes(mm, f2))
    return {"stl": stl_path,
            "stl3mf": mf_path,
            "volume_cm3": float(PC.volume(v2, f2) * (scale ** 3) * 1e6),
            "fit": fit,
            "clearance_mm": float(clr)}


def _pack_beds(items, bed_mm=PRINT_BED_MM):
    # type: (List[Tuple[float, float, str]], Tuple[float, float]) -> Tuple[Dict[str, int], List[Dict[str, Any]]]
    """220x220 床贪心货架装箱。items=(foot_w_mm, foot_d_mm, key), 按 max 维降序。
    超床件独占一批(oversize=True)。返回 (key->batch, batches 列表)。"""
    assign = {}     # type: Dict[str, int]
    batches = []    # type: List[Dict[str, Any]]
    cur_keys = None     # type: Optional[List[str]]
    cx = cy = row_h = ux = uy = 0.0
    for w, d, key in sorted(items, key=lambda t: -max(t[0], t[1])):
        if w > bed_mm[0] or d > bed_mm[1]:
            batches.append({"batch": len(batches), "stones": [key],
                            "used_mm": [float(w), float(d)], "oversize": True})
            assign[key] = batches[-1]["batch"]
            continue
        if cur_keys is None:
            cur_keys = []
            batches.append({"batch": len(batches), "stones": cur_keys,
                            "used_mm": [0.0, 0.0], "oversize": False})
            cx = cy = row_h = ux = uy = 0.0
        if cx + w > bed_mm[0]:              # 换行(同床)
            cx, cy, row_h = 0.0, cy + row_h, 0.0
        if cy + d > bed_mm[1]:              # 床深满 -> 新批
            cur_keys = []
            batches.append({"batch": len(batches), "stones": cur_keys,
                            "used_mm": [0.0, 0.0], "oversize": False})
            cx = cy = row_h = ux = uy = 0.0
        cur_keys.append(key)
        assign[key] = batches[-1]["batch"]
        cx += w
        row_h = max(row_h, d)
        ux = max(ux, cx)
        uy = max(uy, cy + row_h)
        batches[-1]["used_mm"] = [float(ux), float(uy)]
    return assign, batches


def export_ledger(led, mesh_fn, out_dir, roles=None, scale=1 / 50.0):
    # type: (Dict[str, Any], Callable[[Dict[str, Any]], Tuple[list, list]], str, Optional[Sequence[str]], float) -> Dict[str, Any]
    """整账导出。基础校验(过不了即 raise) -> 角色白名单(默认 MASONRY_ROLES,
    雕件归 P4, 过滤件记 manifest.skipped 不静默消失) -> 逐石 fit 自动分档 +
    clearance 置值(只置在导出账本 ledger_print.json 上, 原账目不改写) ->
    STL/3MF(材质分组目录) -> 床装箱 -> manifest.json。返回 manifest dict。"""
    errs = L.validate_ledger(led)
    if errs:
        raise ValueError("base ledger invalid: %s" % errs[:5])
    if roles is None:
        roles = MASONRY_ROLES
    roles = tuple(roles)
    os.makedirs(out_dir, exist_ok=True)
    led_print = json.loads(json.dumps(led))     # 深拷贝, 输入不被改写
    stones_out = []     # type: List[Dict[str, Any]]
    skipped = []        # type: List[Dict[str, Any]]
    footprint = []      # type: List[Tuple[float, float, str]]
    for src, dst in zip(led["stones"], led_print["stones"]):
        if src.get("role_struct") not in roles:
            skipped.append({"id": src["id"], "role": src.get("role_struct")})
            continue
        verts, faces = mesh_fn(src)
        rec = export_stone(src, verts, faces, out_dir, scale=scale, fit=None)
        dst["clearance_manufacturing_mm"] = rec["clearance_mm"]
        cm = rec["clearance_mm"] / 1000.0
        ext = _extents_m(verts)
        footprint.append((max(0.0, (ext[0] - 2 * cm) * scale * 1000.0),
                          max(0.0, (ext[1] - 2 * cm) * scale * 1000.0),
                          src["id"]))
        stones_out.append({"id": src["id"], "uuid": src["uuid"],
                           "family": src["family"],
                           "role": src.get("role_struct"),
                           "material": src.get("material"),
                           "fit": rec["fit"],
                           "clearance_mm": rec["clearance_mm"],
                           "stl": os.path.relpath(rec["stl"], out_dir),
                           "stl3mf": os.path.relpath(rec["stl3mf"], out_dir),
                           "volume_cm3": rec["volume_cm3"]})
    assign, batches = _pack_beds(footprint)
    by_uuid = {s["uuid"]: d for s, d in zip(led["stones"], led_print["stones"])}
    for s in stones_out:
        s["batch"] = assign[s["id"]]
        pdst = by_uuid[s["uuid"]]
        pdst["print"]["batch"] = assign[s["id"]]
        pdst["print"]["min_feature_ok"] = True
    ledger_path = os.path.join(out_dir, "ledger_print.json")
    chk = L.validate_ledger(led_print, allow_clearance=True)
    if chk:
        raise ValueError("post-assignment ledger invalid: %s" % chk[:5])
    L.save_ledger(led_print, ledger_path)
    fams = {}       # type: Dict[str, Dict[str, Any]]
    mats = {}       # type: Dict[str, int]
    for s in sorted(stones_out, key=lambda x: x["id"]):
        f = fams.setdefault(s["family"], {"count": 0, "volume_cm3": 0.0,
                                          "stl": s["stl"]})
        f["count"] += 1
        f["volume_cm3"] += s["volume_cm3"]
        mats[s["material"]] = mats.get(s["material"], 0) + 1
    manifest = {
        "meta": {"schema": 1, "scale": float(scale),
                 "bed_mm": list(PRINT_BED_MM), "roles": list(roles),
                 "curve_hash": led.get("meta", {}).get("curve_hash"),
                 "seed": led.get("meta", {}).get("seed"),
                 "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                              time.gmtime())},
        "materials": mats,
        "families": fams,
        "stones": stones_out,
        "batches": batches,
        "skipped": skipped,
        "ledger_print": os.path.relpath(ledger_path, out_dir),
    }
    with open(os.path.join(out_dir, "manifest.json"), "w",
              encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1, sort_keys=True)
    return manifest


# ---------------------------------------------------------------- coupon

_COUPON_WEDGE = {"w": 0.3, "h": 0.2, "d": 0.15, "proud": 0.006,
                 "back": 0.144, "hw_b": 0.25, "hw_t": 0.245}


def _coupon_mesh(rec, side):
    # type: (Dict[str, Any], str) -> Tuple[List[Tuple[float, float, float]], List[Tuple[int, ...]]]
    """coupon 单件 post-inset 局部网格(导出与名义拼装共用同一真相)。"""
    return rec["_mesh"][side]


def coupon_set(out_dir, scale=1 / 50.0):
    # type: (str, float) -> Dict[str, Dict[str, Any]]
    """三档间隙楔形对 coupon: 每档 A/B 两件各按该档 clearance inset(名义拼装
    间隙 = 2x clearance, 拼得上/拼不上的物理标尺)。out_dir/coupon/ 下 6 件 STL
    (+3MF)。返回 {tier: {clearance_mm, a, b, pair_gap_mm, w_m, _mesh}}。"""
    d = os.path.join(out_dir, "coupon")
    os.makedirs(d, exist_ok=True)
    va0, fa = family_mesh("wedge-std", _COUPON_WEDGE)
    out = {}    # type: Dict[str, Dict[str, Any]]
    for tier in ("TIGHT", "NORMAL", "LOOSE"):
        clr = FIT_TIERS[tier]
        meshes = {}
        paths = {}
        for side in ("a", "b"):
            v2, f2 = flip_outward(inset(va0, clr), fa)
            rep = PC.check_stone(v2, f2, scale=scale)
            if not rep["ok"]:
                raise ValueError("coupon %s/%s check_stone failed: %s"
                                 % (tier, side, rep["issues"]))
            mm = [(p[0] * scale * 1000.0, p[1] * scale * 1000.0,
                   p[2] * scale * 1000.0) for p in v2]
            base = "coupon_%s_%s" % (tier, side.upper())
            stl_path = os.path.join(d, base + ".stl")
            with open(stl_path, "wb") as fh:
                fh.write(_stl_bytes(mm, f2))
            with open(os.path.join(d, base + ".3mf"), "wb") as fh:
                fh.write(_3mf_bytes(mm, f2))
            meshes[side] = (v2, f2)
            paths[side] = stl_path
        out[tier] = {"clearance_mm": clr, "a": paths["a"], "b": paths["b"],
                     "pair_gap_mm": 2.0 * clr, "w_m": _COUPON_WEDGE["w"],
                     "_mesh": meshes}
    return out
