#!/usr/bin/env python3
"""qa_all.py — 保留为薄壳，转调 qa_v2.run。

新的七层验收在 qa_v2/ 包里（见 docs/superpowers/specs/2026-10-01-qa-v2-design.md）。
本文件保留只为兼容历史命令；新代码请加到 qa_v2/ 下。

用法：
    python3 qa_all.py shucun          # 等价 python3 -m qa_v2.run shucun
    python3 qa_all.py shucun --ocr    # 开启内容闭环

## 历史经验与踩坑记录（从旧独立脚本保留）
1) 判据为什么不能是绝对色：
   E9 的 card 判据曾是「米色底板像素占比」，隐含"板面底色统一"。
   E10 板面偏黄绿（b 掉到 185–195），同一判据下所有槽位全判"缺"——8 页全缺，
   但帧里明明有字。（E10 实测踩中，一度以为是渲染坏了。）
   七层验收中 L3 用 OCR 文本判定，L5/L6 按连通域与反白独立判定，与底色解耦。

2) 必须排除的槽位类型：
   `kind: "tag"`（evidence_tag）是深底白字反白样式，没有深色墨像素，
   若按深色墨查会每页误报缺 1 项。L6 已为其建立独立白字判据。

3) plate→canvas 换算：
   slots.json 的坐标在**板面**空间（E5/E6/E11 是 1672×941，E7–E10 是 1920×1080），
   画布恒为 1920×1080 且 PlatePage 用 objectFit:"cover" 铺满 —— 不换算就是拿错位置去测。
   历史 bug：E11 上 8/8 全通过是假的，实际采到的是插画上的深色木纹
   （墨像素 32062 vs 真文字 2229），必然过阈值。
"""
import sys

from qa_v2.run import main, COMPOSITION_OVERRIDES

if __name__ == "__main__":
    sys.exit(main())
