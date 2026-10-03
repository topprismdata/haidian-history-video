import pathlib
from PIL import Image

ASSET_DIR = pathlib.Path("assets/hist_shaoyuan")
PUBLIC_DIR = pathlib.Path("/tmp/chemistry-video/public/shaoyuan")


def test_sanshanyuan_roi_4000_exists_and_dimensions():
    p = ASSET_DIR / "sanshanyuan_haidian_roi_4000.png"
    assert p.exists(), "切片地图必须存在于 assets/hist_shaoyuan"
    im = Image.open(p)
    assert im.size == (4000, 2400), "切片必须严格为 4000x2400 像素以适配 1080p 2.2x 视口"
    assert p.stat().st_size <= 15 * 1024 * 1024, "切片文件大小必须受控防止 OOM"


def test_public_shaoyuan_synced():
    p = PUBLIC_DIR / "sanshanyuan_haidian_roi_4000.png"
    assert p.exists(), "切片地图必须已同步到 public/shaoyuan"


def test_sources_csv_contains_mec_and_vec_fields():
    csv_file = ASSET_DIR / "sources.csv"
    assert csv_file.exists(), "sources.csv 必须存在"
    content = csv_file.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    header = lines[0].split(",")
    lower_headers = [h.lower() for h in header]
    assert "mec" in lower_headers and "vec" in lower_headers, "sources.csv 表头必须同时包含 mec 和 vec 两列"
    data_rows = [l for l in lines[1:] if not l.startswith("#")]
    assert all("MEC-" in r or "VEC-" in r for r in data_rows), "每条有效资产数据行必须包含 MEC 或 VEC 证据分级"
