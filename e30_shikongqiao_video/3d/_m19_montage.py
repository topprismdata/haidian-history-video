# -*- coding: utf-8 -*-
"""M19 Δz 扫描 montage: 冬照 + 各 Δ 渲染 拼图(上: 冬照全幅, 下: 4 渲染 2x2)。
用法: python3 _m19_montage.py out.png render_prefix"""
import sys
from PIL import Image, ImageDraw

out = sys.argv[1]
prefix = sys.argv[2]
W = 1600

winter = Image.open("/tmp/e30_m19_zshift/3d/refs/balustrade_count/src/winter_20201221160537.jpg")
wr = winter.resize((W, int(winter.height * W / winter.width)), Image.LANCZOS)

tags = ["dz+0.0", "dz-1.0", "dz-1.4", "dz-1.8"]
cells = []
for t in tags:
    im = Image.open("%s_%s.png" % (prefix, t)).resize((W, 1067), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 340, 34), fill=(0, 0, 0))
    d.text((10, 8), "MODEL %s  (camera 92,-34,2 -> -20,0,3.2  38mm)" % t, fill=(255, 80, 80))
    cells.append(im)

d2 = ImageDraw.Draw(wr)
d2.rectangle((0, 0, 520, 34), fill=(0, 0, 0))
d2.text((10, 8), "REAL winter_20201221160537 (D810 38mm, frozen lake = normal water level)", fill=(255, 80, 80))

canvas = Image.new("RGB", (2 * W, wr.height + 2 * 1067 + 12), (20, 20, 20))
canvas.paste(wr, (0, 0))
canvas.paste(cells[0], (0, wr.height + 4))
canvas.paste(cells[1], (W, wr.height + 4))
canvas.paste(cells[2], (0, wr.height + 1067 + 8))
canvas.paste(cells[3], (W, wr.height + 1067 + 8))
canvas.save(out)
print("MONTAGE", out, canvas.size)
