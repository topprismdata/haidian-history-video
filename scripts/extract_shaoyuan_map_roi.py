#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E20《勺园·淑春园·未名湖》Task 1: 三山五园图海淀核心区地理切片.

从母版《清 佚名 三山五园图》(51x88cm 扫描, 10468x6072) 截取涵盖
海淀镇、巴沟水系、畅春园、圆明园南及未名湖湿地(勺园/淑春园故址带)的核心区域,
Lanczos 重采样至 4000x2400 (5:3), 作为 P3/P8 分层视口引擎 (2.2x 视口) 底图.

ROI 窗口 (x: 2880..8670, y: 2486..5960) 由逐区标签目视核验定界 (2026-10-03):
  - 巴溝村标签 ≈(2910,4140)、万泉庄泉宗庙/中营教场水网 ≈(1000-3700,3900-4800)
  - 西堤六桥(玉带桥/镜桥)、绣漪桥东北昆明湖水域 ≈(3200-5000,3200-4700)
  - 畅春园/西花园建筑群(集凤轩、虎城、娘娘殿、恩佑寺) ≈(4800-7800,4200-5100)
  - 海淀镇西市铺面街 ≈(4800-6500,4850-5700)
  - 圆明园大宫门(8244,4889)→正大光明(8460,4901)→勤政亲贤/九州清宴 ≈(8200-8660,4800-5150)
  - 畅春园东北与圆明园西南之间勺园/淑春园故址带 ≈(7500-8200,4200-4900)
计划原拟窗口 x:5000..9600, y:2700..5600 实测会整体错过巴沟水系(巴沟村 x≈2910)
并 overweight 颐和园长廊侧翼, 故按内容核验东移; 画幅严格保持 5:3 不变形.
y 下界 5960 以下为卷轴深色装裱边, 予以排除.

输出约束: 严格 4000x2400, PNG <= 15MB (防止 Remotion GPU 纹理 OOM).
颜色降档仅在超限时触发: 优先保留全彩 RGB, 超限则自适应 256 色 (抖动).

Python 3.9.6 兼容: 无 X | None, 无 match.
"""
import hashlib
import pathlib
import sys

from PIL import Image

MASTER_PATH = pathlib.Path("/Users/mac/Downloads/清 佚名 三山五园图51x88.tif")
OUT_DIR = pathlib.Path("assets/hist_shaoyuan")
OUT_PATH = OUT_DIR / "sanshanyuan_haidian_roi_4000.png"

# 计划约定 ROI (母版像素坐标) — 已按标签目视核验修订, 详见模块 docstring
ROI_X0, ROI_Y0, ROI_X1, ROI_Y1 = 2880, 2486, 8670, 5960
TARGET_SIZE = (4000, 2400)  # 严格 5:3
MAX_BYTES = 15 * 1024 * 1024


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def aspect_corrected_box(master_w, master_h):
    """按 5:3 收敛计划约定 ROI, 保持中心不动."""
    w = ROI_X1 - ROI_X0  # 4600
    h = round(w * TARGET_SIZE[1] / TARGET_SIZE[0])  # 4600 * 2400/4000 = 2760
    cx, cy = (ROI_X0 + ROI_X1) // 2, (ROI_Y0 + ROI_Y1) // 2
    x0, y0 = max(0, cx - w // 2), max(0, cy - h // 2)
    x1, y1 = min(master_w, x0 + w), min(master_h, y0 + h)
    return (x0, y0, x1, y1)


def save_under_budget(im, out_path):
    """全彩优先; 仅在超出 15MB 预算时降为自适应 256 色."""
    im.save(out_path, format="PNG", optimize=True)
    mode = "RGB-24bit"
    if out_path.stat().st_size > MAX_BYTES:
        sys.stderr.write("[warn] 全彩 PNG 超预算, 降级自适应 256 色 (Floyd-Steinberg 抖动)\n")
        try:
            pal = im.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
        except AttributeError:  # Pillow < 9.2 兜底
            pal = im.quantize(colors=256)
        pal.save(out_path, format="PNG", optimize=True)
        mode = "P-256color"
    size = out_path.stat().st_size
    if size > MAX_BYTES:
        out_path.unlink()
        raise RuntimeError("256 色仍超 15MB 预算, 需人工复核 ROI/压缩策略")
    return mode, size


def main():
    if not MASTER_PATH.exists():
        raise SystemExit("未找到母版: {}".format(MASTER_PATH))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    Image.MAX_IMAGE_PIXELS = None  # 10468x6072=63.6MP, 超默认上限, 母版已人工核验
    im = Image.open(MASTER_PATH)
    if im.mode != "RGB":
        im = im.convert("RGB")
    w, h = im.size

    box = aspect_corrected_box(w, h)
    print("母版: {}x{} | ROI box: {}".format(w, h, box))
    roi = im.crop(box)
    target = roi.resize(TARGET_SIZE, Image.LANCZOS)

    mode, size = save_under_budget(target, OUT_PATH)
    digest = sha256_of(OUT_PATH)
    print("输出: {} | {}x{} | {} | {:.2f} MB".format(
        OUT_PATH, TARGET_SIZE[0], TARGET_SIZE[1], mode, size / 1024 / 1024))
    print("sha256: {}".format(digest))


if __name__ == "__main__":
    main()
