"""从 pages.config.ts 源码解析文案。

注意 pages.config.ts 是 TypeScript，无法 import，只能正则解析。
E10 与 E11 的导出类型不同（any vs TextItem），但 items 结构一致。
"""
import json
import pathlib

from qa_v2.data import parse_pages_config, load_episode, narration_text

E11_PC = '''
const INK = "#3a3226";
export const PAGE_CONFIG: Record<number, any> = {
  1: {
      { slotId: "badge", kind: "tag", text: "[文献记载]" },
      { slotId: "title", text: "一个村子，三重身份", size: 26, backing: true },
  },
  2: {
      { slotId: "title", text: "有\\n换行", size: 20, backing: "rgba(232,214,178,0.95)" },
  },
};
'''


def test_parse_pages_config_basic():
    got = parse_pages_config(E11_PC)
    assert set(got) == {1, 2}
    assert got[1][0].slot_id == "badge"
    assert got[1][0].kind == "tag"
    assert got[1][1].text == "一个村子，三重身份"
    assert got[1][1].size == 26
    assert got[1][1].backing is True


def test_parse_pages_config_unescapes_newline():
    got = parse_pages_config(E11_PC)
    assert got[2][0].text == "有\n换行"
    assert "\n" in got[2][0].text


def test_parse_pages_config_string_backing():
    got = parse_pages_config(E11_PC)
    assert got[2][0].backing == "rgba(232,214,178,0.95)"


def test_parse_pages_config_default_size():
    got = parse_pages_config(E11_PC)
    assert got[1][0].size == 20      # 无 size 时默认 20


def test_load_episode_shucun_has_eight_pages():
    ep = load_episode("shucun")
    assert len(ep.pages) == 8
    assert ep.pages[0].number == 1
    assert ep.pages[0].plate == (1672, 941)


def test_load_episode_layout_accumulates():
    ep = load_episode("shucun")
    assert len(ep.layout) == 8
    # 页起点必须累加，第 2 页起点 = 第 1 页长度
    assert ep.layout[1][0] == ep.layout[0][1]
    assert ep.layout[1][0] > 0


def test_load_episode_slot_and_item_counts_match_slots_json():
    ep = load_episode("shucun")
    # 93 个槽位、93 条文案（E11 实测）
    n_slots = sum(len(p.slots) for p in ep.pages)
    n_items = sum(len(p.items) for p in ep.pages)
    assert n_slots == 93
    assert n_items == 93


def test_narration_text_reads_all_json():
    got = narration_text("shucun")
    assert set(got) == set(range(1, 9))
    assert "雍正二年" in got[2]


def test_narration_text_missing_returns_empty():
    got = narration_text("__no_such_episode__")
    assert got == {}
