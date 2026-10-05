# -*- coding: utf-8 -*-
"""WaterFix A/B 量化: 四个像素带 A(旧材质) vs B(新材质)。

带坐标来自 WaterEnvScout 对 shot_hero.png(1600x900) 的侦察值; 本目录渲染为
800x450 时按 W/1600 等比缩放(两图必须同分辨率)。

  前景水带 y650-900 全宽   高频能量(laplacian |mean|)      预期 B > A(治#2 死水)
  倒影带   x340-1520 y460-610  水平/竖直梯度比 Gx/Gy      预期 B < A(治#1 竖抹柱:
                             竖纹=列间变化强→Gx 主导; 转横纹后 Gy 升、比值降)
  水线带   y445-465 全宽   相邻行均亮最大跳变 / 带内方差    预期跳变 B < A(硬边软化);
                             方差两列(B 应不再是一条纯直线)
  左岸带   x0-135 y420-485  HSV 饱和度均值(兼报 V)          预期 B > A(治#4 被雾洗灰)

用法: python3 measure_ab.py A.png B.png [out.json]
"""
import sys, json, os
import numpy as np
from PIL import Image


def load(path):
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im, np.float32)
    L = arr @ np.array([0.299, 0.587, 0.114], np.float32)
    return im, arr, L


def bands(W, H):
    s = W / 1600.0
    y0_fw, y1_fw = int(650 * s), min(H, int(900 * s))
    return {
        "foreground_water": (0, y0_fw, W, y1_fw),
        "reflection": (int(340 * s), int(460 * s), int(1520 * s), int(610 * s)),
        "waterline": (0, int(445 * s), W, min(H, int(465 * s))),
        "left_bank": (0, int(420 * s), int(135 * s), int(485 * s)),
    }


def high_freq_energy(L):
    """|laplacian| 均值(内部区), 即高频能量。"""
    lap = (4.0 * L[1:-1, 1:-1] - L[:-2, 1:-1] - L[2:, 1:-1]
           - L[1:-1, :-2] - L[1:-1, 2:])
    return float(np.mean(np.abs(lap))), float(np.std(L))


def grad_ratio(L):
    """水平/竖直一阶差分均值比。竖抹柱: 同列亮度近恒 → Gy 小, Gx/Gy 大。"""
    gx = float(np.mean(np.abs(np.diff(L, axis=1))))
    gy = float(np.mean(np.abs(np.diff(L, axis=0))))
    return gx, gy, gx / max(gy, 1e-6)


def waterline_metrics(L):
    """带内相邻行均亮最大跳变(硬边探针) + 带内亮度方差。"""
    rowmean = L.mean(axis=1)
    maxadj = float(np.max(np.abs(np.diff(rowmean)))) if len(rowmean) > 1 else 0.0
    return maxadj, float(np.std(L))


def bank_metrics(im):
    """HSV 饱和度/明度均值。"""
    hsv = np.asarray(im.convert("HSV"), np.float32)
    return float(np.mean(hsv[..., 1])), float(np.mean(hsv[..., 2]))


def measure(path, W, H):
    im, arr, L = load(path)
    bd = bands(W, H)
    out = {}
    x0, y0, x1, y1 = bd["foreground_water"]
    e, sd = high_freq_energy(L[y0:y1, x0:x1])
    out["foreground_water"] = {"hf_energy": e, "std": sd}
    x0, y0, x1, y1 = bd["reflection"]
    gx, gy, r = grad_ratio(L[y0:y1, x0:x1])
    out["reflection"] = {"gx": gx, "gy": gy, "ratio_gx_over_gy": r}
    x0, y0, x1, y1 = bd["waterline"]
    ma, sd2 = waterline_metrics(L[y0:y1, x0:x1])
    out["waterline"] = {"max_row_jump": ma, "std": sd2}
    x0, y0, x1, y1 = bd["left_bank"]
    s, v = bank_metrics(im.crop((x0, y0, x1, y1)))
    out["left_bank"] = {"sat": s, "val": v}
    out["bands_px"] = {k: v for k, v in bd.items()}
    return out


def main():
    a = [p for p in sys.argv[1:]]
    if len(a) < 2:
        print("usage: measure_ab.py A.png B.png [out.json]"); sys.exit(2)
    pa, pb, outp = a[0], a[1], (a[2] if len(a) > 2 else None)
    ia = Image.open(pa); ib = Image.open(pb)
    assert ia.size == ib.size, "A/B 分辨率不同: %s vs %s" % (ia.size, ib.size)
    W, H = ia.size
    A, B = measure(pa, W, H), measure(pb, W, H)
    expect = {  # (方向, 语义)
        ("foreground_water", "hf_energy"): ("B>A", "前景水高频能量升(治死水)"),
        ("reflection", "ratio_gx_over_gy"): ("B<A", "倒影水平/竖直梯度比降(竖抹消退)"),
        ("waterline", "max_row_jump"): ("B<A", "水线硬边跳变降"),
        ("waterline", "std"): ("B>A", "水线带出现湿带结构"),
        ("left_bank", "sat"): ("B>A", "左岸饱和度升"),
    }
    print("A=%s B=%s (%dx%d)" % (os.path.basename(pa), os.path.basename(pb), W, H))
    hdr = "%-18s %-18s %10s %10s %10s  %s" % ("band", "metric", "A", "B", "delta", "expect")
    print(hdr); print("-" * len(hdr))
    rep = {"A": A, "B": B, "expect": {}}
    hits = 0
    for (band, met), (dirn, why) in expect.items():
        va, vb = A[band][met], B[band][met]
        d = vb - va
        ok = (d > 0) if dirn == "B>A" else (d < 0)
        hits += ok
        print("%-18s %-18s %10.4f %10.4f %+10.4f  %s %s -> %s"
              % (band, met, va, vb, d, dirn, "OK" if ok else "MISS", why))
        rep["expect"]["%s.%s" % (band, met)] = {
            "dir": dirn, "A": va, "B": vb, "delta": d, "ok": bool(ok), "why": why}
    print("DIRECTION_HITS %d/%d" % (hits, len(expect)))
    rep["direction_hits"] = hits
    rep["n_expect"] = len(expect)
    if outp:
        with open(outp, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=1)
        print("WROTE", outp)


main()
