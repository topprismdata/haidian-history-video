# -*- coding: utf-8 -*-
"""E24《五塔寺·阳台山麓的千年清水院》Task 1 资产测试.

断言 assets/hist_wutasi/ 全套资产真实存在, 分辨率/色彩通道符合工程约束,
sources.csv 的 sha256 完整性与证据分级留痕一致, 且已同步 public/。

🔴 E23 事故防线（本集特有）:
1915 切片曾因「拼接窗口宽 1792px < 裁切窗口 ox+1920=2410px」被 PIL 黑色补齐,
成片右侧 1/3 纯黑。测试必须量化断言右侧 260px 带的黑像素占比。
"""
import csv
import hashlib
import pathlib

from PIL import Image

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSET_DIR = REPO_ROOT / "assets" / "hist_wutasi"
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/wutasi")

REQUIRED_ASSETS = {
    "sanshanyuan_changhe_north_roi_4000.png": ("长河北岸白石桥段切片", 3000, 1200, None, {"RGB", "RGBA"}),
    "beijing_1915_changhe_anchor_roi.png": ("1915 实测京师四郊图长河北岸切片", 1920, 1080, (1920, 1080), {"RGB", "RGBA"}),
    "mingxianzong_shilu_folio.png": ("明宪宗实录卷一百二十书影", 800, 600, None, {"RGB", "L", "LA"}),
    "quanmen_shibei_folio.png": ("帝京景物略五塔寺条书影", 800, 600, None, {"RGB", "L", "LA"}),
    "dijingjingwulue_folio.png": ("钦定日下旧闻考卷一百六五塔寺条书影", 800, 600, None, {"RGB", "L", "LA"}),
    "wutasi_pagoda_photo.png": ("五塔寺无量寿佛殿实拍", 900, 500, None, {"RGB", "L", "LA"}),
    "mec4_composite_eras.png": ("MEC-4 四时代叠合图", 1920, 1080, (1920, 1080), {"RGB", "RGBA"}),
}

SOURCE_CSV_HEADER = {"file", "title", "sha256", "vec"}

#: 1915 切片右侧 260px 带的黑像素占比上限（E23 事故值: 实测 0.0058 合格 / 补齐时接近 1.0）
BLACK_RATIO_MAX = 0.02


def _sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_asset_files_exist_and_specs_valid():
    assert ASSET_DIR.exists(), f"资产目录不存在: {ASSET_DIR}"
    for filename, (desc, min_w, min_h, exact, modes) in REQUIRED_ASSETS.items():
        p = ASSET_DIR / filename
        assert p.exists(), f"缺少资产文件 [{desc}]: {filename}"
        assert p.stat().st_size > 1024, f"文件过小可能损坏: {filename}"
        with Image.open(p) as img:
            w, h = img.size
            assert img.mode in modes, f"{filename} mode={img.mode} 不在允许集合 {modes}"
            assert w >= min_w and h >= min_h, f"{filename} 尺寸 ({w}x{h}) 小于约束 ({min_w}x{min_h})"
            if exact is not None:
                assert (w, h) == exact, f"{filename} 必须精确为 {exact}, 实际 ({w}x{h})"


def test_1915_slice_has_no_black_border():
    """E23 事故防线：拼接窗口必须 >= 裁切窗口，否则 PIL 黑色补齐。"""
    p = ASSET_DIR / "beijing_1915_changhe_anchor_roi.png"
    if not p.exists():
        pytest_skip = "资产尚未生成"
        raise AssertionError(pytest_skip)
    with Image.open(p) as img:
        w, h = img.size
        right = img.crop((w - 260, 0, w, h))
        colors = right.getcolors(maxcolors=1 << 24)
        black = sum(c for c, rgb in colors if sum(rgb) < 60)
        ratio = black / float(260 * h)
        assert ratio < BLACK_RATIO_MAX, (
            f"1915 切片右侧 260px 黑像素占比 {ratio:.4f} >= {BLACK_RATIO_MAX}, "
            f"疑似拼接窗口小于裁切窗口导致 PIL 黑色补齐（E23 事故）"
        )


def test_sources_csv_integrity():
    csv_path = ASSET_DIR / "sources.csv"
    assert csv_path.exists(), "缺少 sources.csv 留痕文件"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert SOURCE_CSV_HEADER.issubset(set(reader.fieldnames or []))
        rows = list(reader)

    files_in_csv = set()
    for row in rows:
        fn = row["file"]
        files_in_csv.add(fn)
        f_path = ASSET_DIR / fn
        assert f_path.exists(), f"sources.csv 登记了不存在的文件: {fn}"
        assert _sha256_of(f_path).lower() == row["sha256"].lower(), f"{fn} sha256 不匹配"
        assert row["vec"].startswith(("MEC-", "VEC-")), f"{fn} 证据分级非法: {row['vec']}"

    missing = set(REQUIRED_ASSETS) - files_in_csv
    assert not missing, f"以下必要资产未在 sources.csv 登记: {missing}"


def test_public_sync_matches():
    assert PUBLIC_DIR.exists(), f"公共静态目录不存在: {PUBLIC_DIR}"
    for filename in REQUIRED_ASSETS:
        src = ASSET_DIR / filename
        dst = PUBLIC_DIR / filename
        assert dst.exists(), f"未同步至 public: {filename}"
        assert _sha256_of(src) == _sha256_of(dst), f"同步内容与源不一致: {filename}"
