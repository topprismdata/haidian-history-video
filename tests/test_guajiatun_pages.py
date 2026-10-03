# -*- coding: utf-8 -*-
"""E23《挂甲屯·杨六郎传说与清初额驸城》Task 5: 页面与槽位系统测试.

验证:
1. slots.json 8 页完整, 与 pages.config.ts 槽位 id 1:1 双向一致;
2. 全部非 photo 槽位配置 backing: true (物理隔离红线);
3. 槽位坐标在 1920×1080 画布内, 宽高为正;
4. 屏显纪年数字（>=10）必须是当页口播数字的子集;
   逐字引文槽（slot_id 含 _quote）豁免——引文原样保留年号汉字，
   改写引文以迎合数字判据属篡改书证。红线改由 qa_v2 L4-c 承担。
5. remotion-template 与 /tmp/chemistry-video 副本一致性。
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from qa_v2.data import parse_pages_config
from qa_v2.normalize import extract_numbers

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE_DATA = ROOT / "remotion-template" / "src" / "guajiatun" / "data"
SYNC_DATA = pathlib.Path("/tmp/chemistry-video/src/guajiatun/data")
NARR_FILE = ROOT / "guajiatun_video" / "narration" / "all.json"

MIN_YEAR = 10  # 只对纪年量级数字做子集判据（<10 的「一/三/六」等会被普通词误抓）


def _slots_data():
    return json.loads((TEMPLATE_DATA / "slots.json").read_text(encoding="utf-8"))


def _cfg():
    return parse_pages_config((TEMPLATE_DATA / "pages.config.ts").read_text(encoding="utf-8"))


def _narration():
    return json.loads(NARR_FILE.read_text(encoding="utf-8"))


def test_slots_json_has_8_pages():
    data = _slots_data()
    assert len(data) == 8
    for i in range(1, 9):
        k = f"p{i:02d}"
        assert k in data, f"缺少 {k}"
        assert data[k]["plate"] == [1920, 1080]
        assert len(data[k]["slots"]) >= 5


def test_slots_and_pages_config_bidirectional_match():
    cfg = _cfg()
    slots = _slots_data()
    assert len(cfg) == 8, f"pages.config.ts 解析页数不为 8: {len(cfg)}"
    for i in range(1, 9):
        k = f"p{i:02d}"
        slot_ids = {s["id"] for s in slots[k]["slots"]}
        cfg_ids = {it.slot_id for it in cfg[i] if it.slot_id}
        assert not (slot_ids - cfg_ids), f"{k} slots.json 中的槽位未声明: {slot_ids - cfg_ids}"
        assert not (cfg_ids - slot_ids), f"{k} pages.config.ts 中的槽位未在 slots.json: {cfg_ids - slot_ids}"


def test_all_text_slots_have_backing():
    cfg = _cfg()
    for pno, items in cfg.items():
        for it in items:
            if it.kind == "photo":
                continue
            assert it.backing, f"P{pno} 槽位 {it.slot_id} 缺少 backing: true (物理隔离红线)"


def test_all_slots_within_canvas():
    for page_key, pdata in _slots_data().items():
        for s in pdata["slots"]:
            x, y, w, h = s["x"], s["y"], s["w"], s["h"]
            assert x >= 0 and y >= 0, f"{page_key}/{s['id']} 坐标为负"
            assert w > 0 and h > 0, f"{page_key}/{s['id']} 宽高必须正数"
            assert x + w <= 1920, f"{page_key}/{s['id']} 宽度越界: {x}+{w}"
            assert y + h <= 1080, f"{page_key}/{s['id']} 高度越界: {y}+{h}"


def test_screen_years_subset_of_spoken():
    cfg = _cfg()
    narr = _narration()
    for pno in range(1, 9):
        k = f"p{pno:02d}"
        spoken = {n for n in extract_numbers(narr[k]) if n >= MIN_YEAR}
        for it in cfg[pno]:
            if it.kind == "photo" or it.slot_id is None:
                continue
            if "quote" in it.slot_id:
                continue  # 逐字引文豁免
            screen = {n for n in extract_numbers(it.text) if n >= MIN_YEAR}
            excess = screen - spoken
            assert not excess, (
                f"P{pno} 槽位 {it.slot_id} 屏显纪年 {sorted(excess)} 未在当页口播念出 "
                f"(口播含 {sorted(spoken)})"
            )


def test_redline_no_fabricated_mansion_photo():
    """V-NC07：严禁 AI 生成额驸城大门或挂甲树伪造图景。"""
    cfg = _cfg()
    for pno, items in cfg.items():
        for it in items:
            if it.kind != "photo":
                continue
            assert "mansion" not in it.text.lower(), f"P{pno} photo 槽疑似伪造府第图景"
            assert "挂甲树" not in it.text, f"P{pno} photo 槽疑似伪造挂甲树图景"


def test_runtime_data_synced():
    assert SYNC_DATA.exists(), f"运行时目录不存在: {SYNC_DATA}"
    for filename in ["slots.json", "pages.config.ts", "pageMap.ts"]:
        src = TEMPLATE_DATA / filename
        dst = SYNC_DATA / filename
        assert dst.exists(), f"运行时未同步: {filename}"
        assert src.read_text(encoding="utf-8") == dst.read_text(encoding="utf-8"), (
            f"正本与副本不一致: {filename}"
        )
