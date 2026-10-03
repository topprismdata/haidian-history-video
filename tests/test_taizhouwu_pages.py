# -*- coding: utf-8 -*-
"""E22《太舟坞·唐代羁縻带州与元代船坞之谜》Task 5: 页面与槽位系统测试.

验证:
1. slots.json 8 页完整存在, 与 pages.config.ts 槽位 id 1:1 严格双向一致;
2. 全部文字槽位配置 backing: true (防古地图文字粘连负控制);
3. 槽位坐标在 1920x1080 画布内, 无非正宽高与越界;
4. 页面屏显数字必须是当页口播数字的子集 (L4-c);
5. remotion-template 与 /tmp/chemistry-video 副本一致性。
"""
import json
import pathlib
import pytest

from qa_v2.normalize import extract_numbers

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATE_DATA = ROOT / "remotion-template" / "src" / "taizhouwu" / "data"
SYNC_DATA = pathlib.Path("/tmp/chemistry-video/src/taizhouwu/data")
NARR_FILE = ROOT / "taizhouwu_video" / "narration" / "all.json"


def _slots_data():
    return json.loads((TEMPLATE_DATA / "slots.json").read_text(encoding="utf-8"))


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
    # 动态解析 pages.config.ts 中的 items
    import sys
    sys.path.insert(0, str(ROOT))
    from qa_v2.data import parse_pages_config

    config_text = (TEMPLATE_DATA / "pages.config.ts").read_text(encoding="utf-8")
    cfg_pages = parse_pages_config(config_text)
    slots_data = _slots_data()

    assert len(cfg_pages) == 8, f"pages.config.ts 解析页数不为8: {len(cfg_pages)}"

    for i in range(1, 9):
        k = f"p{i:02d}"
        slot_ids = {s["id"] for s in slots_data[k]["slots"]}
        cfg_items = cfg_pages[i]
        cfg_ids = {item.slot_id for item in cfg_items if item.slot_id}

        # 双向一致性
        missing_in_cfg = slot_ids - cfg_ids
        missing_in_slots = cfg_ids - slot_ids
        assert not missing_in_cfg, f"{k} slots.json 中的槽位未在 pages.config.ts 声明: {missing_in_cfg}"
        assert not missing_in_slots, f"{k} pages.config.ts 中的槽位未在 slots.json 声明: {missing_in_slots}"


def test_all_text_slots_have_backing():
    import sys
    sys.path.insert(0, str(ROOT))
    from qa_v2.data import parse_pages_config

    config_text = (TEMPLATE_DATA / "pages.config.ts").read_text(encoding="utf-8")
    cfg_pages = parse_pages_config(config_text)

    for page_no, items in cfg_pages.items():
        for item in items:
            if item.kind == "photo":
                continue
            assert item.backing, f"P{page_no} 槽位 {item.slot_id} 缺少 backing: true (物理隔离红线)"


def test_all_slots_within_canvas():
    slots_data = _slots_data()
    for page_key, pdata in slots_data.items():
        for s in pdata["slots"]:
            x, y, w, h = s["x"], s["y"], s["w"], s["h"]
            assert x >= 0 and y >= 0, f"{page_key}/{s['id']} 坐标为负: ({x}, {y})"
            assert w > 0 and h > 0, f"{page_key}/{s['id']} 宽高必须正数: ({w}, {h})"
            assert x + w <= 1920, f"{page_key}/{s['id']} 宽度越界: {x}+{w} > 1920"
            assert y + h <= 1080, f"{page_key}/{s['id']} 高度越界: {y}+{h} > 1080"


def test_screen_numbers_subset_of_spoken():
    import sys
    sys.path.insert(0, str(ROOT))
    from qa_v2.data import parse_pages_config

    config_text = (TEMPLATE_DATA / "pages.config.ts").read_text(encoding="utf-8")
    cfg_pages = parse_pages_config(config_text)
    narr = _narration()

    for page_no in range(1, 9):
        k = f"p{page_no:02d}"
        spoken_text = narr[k]
        spoken_nums = set(extract_numbers(spoken_text))

        screen_text = " ".join(item.text for item in cfg_pages[page_no] if item.kind != "photo")
        screen_nums = set(extract_numbers(screen_text))

        excess = screen_nums - spoken_nums
        assert not excess, f"P{page_no} 屏显数字 {excess} 未在当页口播中念出 (口播包含: {spoken_nums})"


def test_runtime_data_synced():
    assert SYNC_DATA.exists(), f"运行时目录不存在: {SYNC_DATA}"
    for filename in ["slots.json", "pages.config.ts", "pageMap.ts"]:
        src = TEMPLATE_DATA / filename
        dst = SYNC_DATA / filename
        assert dst.exists(), f"运行时未同步: {filename}"
        assert src.read_text(encoding="utf-8") == dst.read_text(encoding="utf-8"), (
            f"正本与副本不一致: {filename}"
        )
