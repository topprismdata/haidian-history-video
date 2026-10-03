# -*- coding: utf-8 -*-
"""E22《太舟坞·唐代羁縻带州与元代船坞之谜》Task 1 资产测试.

断言 assets/hist_taizhouwu/ 全套地理切片与视觉资产真实存在,
分辨率/色彩通道符合工程约束, sources.csv 的 sha256 完整性与 VEC 分级留痕一致,
且全部资产已同步至 /tmp/chemistry-video/public/taizhouwu/。

证据分级依据 docs/superpowers/specs/2026-10-03-e22-taizhouwu-design.md:
MEC-1~4 / VEC-1~4。
"""
import csv
import hashlib
import pathlib

from PIL import Image

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSET_DIR = REPO_ROOT / "assets" / "hist_taizhouwu"
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/taizhouwu")

REQUIRED_ASSETS = {
    "sanshanyuan_xishan_roi_4000.png": ("西山山麓太舟坞段高清切片", 3000, 1800, None, {"RGB", "RGBA"}),
    "beijing_1915_taizhouwu_roi.png": ("1915 实测京师四郊图太舟坞切片", 1920, 1080, (1920, 1080), {"RGB", "RGBA"}),
    "tang_daizhou_jiu_tangshu_folio.png": ("旧唐书·地理志带州条目书影", 800, 600, None, {"RGB", "L", "LA"}),
    "tang_jiaofujun_epitaph_folio.png": ("唐焦府君墓志铭拓本书影", 800, 600, None, {"RGB", "L", "LA"}),
    "heilongtan_longwangmiao_hall.png": ("黑龙潭龙王庙大殿遗存照", 800, 500, None, {"RGB", "L", "LA"}),
    "modern_taizhouwu_street.png": ("现代太舟坞街区/京密引水渠实拍", 800, 500, None, {"RGB", "L", "LA"}),
    "mec4_composite_eras.png": ("MEC-4 四时代叠合图", 1920, 1080, (1920, 1080), {"RGB", "RGBA"}),
}

SOURCE_CSV_HEADER = {"file", "title", "sha256", "vec"}


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
            mode = img.mode
            assert mode in modes, f"{filename} mode={mode} 不在允许集合 {modes}"
            assert w >= min_w and h >= min_h, (
                f"{filename} 尺寸 ({w}x{h}) 小于最小约束 ({min_w}x{min_h})"
            )
            if exact is not None:
                assert (w, h) == exact, f"{filename} 必须精确为 {exact}, 实际 ({w}x{h})"


def test_sources_csv_integrity():
    csv_path = ASSET_DIR / "sources.csv"
    assert csv_path.exists(), "缺少 sources.csv 留痕文件"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        assert SOURCE_CSV_HEADER.issubset(fields), (
            f"sources.csv 缺少必要列: {SOURCE_CSV_HEADER - fields}"
        )
        rows = list(reader)

    files_in_csv = set()
    for row in rows:
        fn = row["file"]
        files_in_csv.add(fn)
        asset_file = ASSET_DIR / fn
        assert asset_file.exists(), f"sources.csv 登记了不存在的文件: {fn}"
        actual_sha = _sha256_of(asset_file)
        assert actual_sha.lower() == row["sha256"].lower(), (
            f"{fn} sha256 不匹配: 实际 {actual_sha} vs csv {row['sha256']}"
        )
        assert row["vec"].startswith(("MEC-", "VEC-")), (
            f"{fn} 证据分级非法: {row['vec']}"
        )

    required_filenames = set(REQUIRED_ASSETS.keys())
    missing_in_csv = required_filenames - files_in_csv
    assert not missing_in_csv, f"以下必要资产未在 sources.csv 登记: {missing_in_csv}"


def test_public_sync_matches():
    assert PUBLIC_DIR.exists(), f"公共静态目录不存在: {PUBLIC_DIR}"
    for filename in REQUIRED_ASSETS.keys():
        src = ASSET_DIR / filename
        dst = PUBLIC_DIR / filename
        assert dst.exists(), f"未同步至 public: {filename}"
        assert _sha256_of(src) == _sha256_of(dst), f"同步内容与源不一致: {filename}"
