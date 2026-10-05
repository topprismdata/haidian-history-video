# -*- coding: utf-8 -*-
"""A/B 桥体带 RGB 实测: 掩膜 = 两渲染逐像素差>阈值的区域(材质切换生效区=桥体)。
用法: python3 measure_ab.py  (在 ab_qingshi/ 目录)"""
import numpy as np
from PIL import Image, ImageFilter

A = np.asarray(Image.open("ab_hero_A_warm.png").convert("RGB"), dtype=np.int16)
B = np.asarray(Image.open("ab_hero_B_qingshi.png").convert("RGB"), dtype=np.int16)
assert A.shape == B.shape, (A.shape, B.shape)
H, W = A.shape[:2]

diff = np.abs(A - B).max(axis=2)
changed = diff > 8              # 材质生效区
tiny = (diff > 1) & (diff <= 8) # 噪声/间接光边缘
print("size %dx%d  changed %d px (%.2f%%)  tiny %d px (%.2f%%)"
      % (W, H, changed.sum(), 100.0 * changed.sum() / (W * H),
         tiny.sum(), 100.0 * tiny.sum() / (W * H)))

# 掩膜膨胀 3px(吞掉锯齿边), 用 PIL MaxFilter
m8 = Image.fromarray((changed * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(7))
mask = np.asarray(m8) > 0
ys, xs = np.nonzero(mask)
print("mask bbox x[%d..%d] y[%d..%d]  (W=%d H=%d)" % (xs.min(), xs.max(), ys.min(), ys.max(), W, H))

for tag, img in (("A_warm   ", A), ("B_qingshi", B)):
    r, g, b = img[mask].mean(axis=0)
    print("%s mask-mean RGB = (%.1f, %.1f, %.1f)  R-B=%+.1f  lum=%.1f"
          % (tag, r, g, b, r - b, 0.2126 * r + 0.7152 * g + 0.0722 * b))

# 参照组: 栏杆/狮/水/天 应不受影响 —— 用 diff==0 区验证两组图相同性
same = diff == 0
print("identical px %.2f%%  (栏杆/水/天侧应≈100%%)" % (100.0 * same.sum() / (W * H)))

# 并排图留证
imA = Image.open("ab_hero_A_warm.png"); imB = Image.open("ab_hero_B_qingshi.png")
side = Image.new("RGB", (imA.width * 2 + 8, imA.height), (30, 30, 30))
side.paste(imA, (0, 0)); side.paste(imB, (imA.width + 8, 0))
side.save("ab_hero_AB_side.png")
print("side-by-side -> ab_hero_AB_side.png")
