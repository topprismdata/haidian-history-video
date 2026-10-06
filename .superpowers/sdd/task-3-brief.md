## Task 3: 数据加载层

**Files:**
- Create: `qa_v2/data.py`
- Create: `tests/test_data.py`

**Interfaces:**
- Consumes: `qa_v2/geometry.py`（Task 1）
- Produces:
  - `class Slot: id: str; x: int; y: int; w: int; h: int`
  - `class TextItem: slot_id: str; text: str; size: int; backing: Any; kind: Optional[str]`
  - `class Page: number: int; plate: Tuple[int, int]; slots: List[Slot]; items: List[TextItem]`
  - `class Episode: name: str; pages: List[Page]; layout: List[Tuple[int, int]]` —— `layout[i] = (起始帧, 页长帧)`
  - `load_episode(ep: str, root: Path = ROOT) -> Episode`
  - `parse_pages_config(text: str) -> Dict[int, List[TextItem]]` —— 从 `pages.config.ts` 源码解析
  - `ROOT = Path("/tmp/chemistry-video")`
  - `narration_text(ep: str, root: Path = ROOT) -> Dict[int, str]` —— 读 `narration/all.json`；E5–E10 若无则返回 `{}`

- [ ] **Step 1: 写失败的测试**

`tests/test_data.py`：

```python
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
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_data.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.data'`

- [ ] **Step 3: 写最小实现**

`qa_v2/data.py`：

```python
"""加载每集的槽位几何、文案、页长与口播稿。

数据源（七个集结构一致）：
  src/<ep>/data/slots.json        槽位几何（板面空间）
  src/<ep>/data/pages.config.ts   文案（TypeScript 源码，正则解析）
  src/<ep>/data/pageMap.ts        页长（PAGE_DURATIONS_SEC，含 1.6s 留白）
  <ep>_video/narration/all.json   口播稿（L4-c 专用，勿用 subtitles.ts）
"""
import json
import pathlib
import re
from typing import Any, Dict, List, Optional, Tuple

ROOT = pathlib.Path("/tmp/chemistry-video")
VIDEO_ROOT = pathlib.Path("/Volumes/macstudio/video-projects")
FPS = 30


class Slot(object):
    __slots__ = ("id", "x", "y", "w", "h")

    def __init__(self, sid, x, y, w, h):
        self.id = sid
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)

    @property
    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def __repr__(self):
        return "Slot(%r, %d, %d, %d, %d)" % (
            self.id, self.x, self.y, self.w, self.h)


class TextItem(object):
    __slots__ = ("slot_id", "text", "size", "backing", "kind")

    def __init__(self, slot_id, text, size, backing, kind):
        self.slot_id = slot_id
        self.text = text
        self.size = size
        self.backing = backing
        self.kind = kind

    @property
    def is_tag(self):
        return self.kind == "tag"

    def __repr__(self):
        return "TextItem(%r, %r)" % (self.slot_id, self.text)


class Page(object):
    def __init__(self, number, plate, slots, items):
        self.number = number
        self.plate = plate
        self.slots = slots
        self.items = items

    def slot(self, sid):
        for s in self.slots:
            if s.id == sid:
                return s
        return None


class Episode(object):
    def __init__(self, name, pages, layout):
        self.name = name
        self.pages = pages
        self.layout = layout

    def page(self, number):
        for p in self.pages:
            if p.number == number:
                return p
        return None

    def final_frame(self, number):
        """该页终态帧：页尾前 3 帧。

        取终态帧而非中途帧：槽位是逐项入场的，中途帧看着像"缺内容"
        （E11 P3 有 49 项，中途只填了 3 行，一度误判为渲染失败）。
        """
        start, length = self.layout[number - 1]
        return start + length - 3


# ── pages.config.ts 解析 ──────────────────────────────────────────────
_ITEM_RE = re.compile(
    r"\{\s*slotId:\s*\"(?P<sid>[^\"]+)\"(?P<rest>[^}]*)\}"
)
_TEXT_RE = re.compile(r"text:\s*(\"(?:[^\"\\]|\\.)*\")")
_SIZE_RE = re.compile(r"size:\s*(\d+)")
_BACKING_RE = re.compile(
    r"backing:\s*(\"(?:[^\"\\]|\\.)*\"|true)"
)


def parse_pages_config(text):
    """从 pages.config.ts 源码解析出 {页码: [TextItem, ...]}。

    只取顶层 `N: {` 块（避免匹配到嵌套），块内逐条抽 slotId。
    """
    out = {}
    blocks = list(re.finditer(r"^  (\d+):\s*\{", text, re.M))
    for idx, bm in enumerate(blocks):
        end = blocks[idx + 1].start() if idx + 1 < len(blocks) else len(text)
        body = text[bm.end():end]
        page_no = int(bm.group(1))
        items = []
        for im in _ITEM_RE.finditer(body):
            raw = im.group(0)
            sid = im.group("sid")
            rest = im.group("rest")
            tm = _TEXT_RE.search(rest)
            if not tm:
                continue
            txt = json.loads(tm.group(1))
            sm = _SIZE_RE.search(rest)
            km = re.search(r"kind:\s*\"tag\"", rest)
            bm2 = _BACKING_RE.search(rest)
            if bm2:
                backing = (True if bm2.group(1) == "true"
                           else json.loads(bm2.group(1)))
            else:
                backing = True
            items.append(TextItem(
                sid, txt, int(sm.group(1)) if sm else 20, backing,
                "tag" if km else None))
        out[page_no] = items
    return out


# ── 页长 ──────────────────────────────────────────────────────────────
_NUMS = re.compile(r"\d+\.?\d*")


def _nums(block):
    """只取数值字面量，先剥掉 // 与 /* */ 注释。"""
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
    block = re.sub(r"//[^\n]*", "", block)
    return [float(x) for x in _NUMS.findall(block)]


def _page_layout(ep_dir):
    """返回 [(起始帧, 页长帧), ...]。

    优先级必须是 pageMap > narration.json，**不能反**：
      pageMap.ts 的 PAGE_DURATIONS_SEC = 纯音频 + 1.6s 页尾留白（真实页长）
      narration.json 的 pageLenSec       = 纯音频（不含留白）
    E9 两份都有，累积到 P4 差 144 帧，抽帧落到前一页尾巴 → 误报 3 个槽位缺失。
    """
    pm = ep_dir / "data" / "pageMap.ts"
    if pm.exists():
        m = re.search(r"PAGE_DURATIONS_SEC[^=]*=\s*\[([^\]]+)\]",
                      pm.read_text(encoding="utf-8"))
        if m:
            out, cur = [], 0
            for sec in _nums(m.group(1)):
                n = int(round(sec * FPS))
                out.append((cur, n))
                cur += n
            return out
    nj = ep_dir / "data" / "narration.json"
    if nj.exists():
        d = json.load(open(nj, encoding="utf-8"))
        fps = d.get("fps") or FPS
        out, cur = [], 0
        for p in d["pages"]:
            n = int(round(p["pageLenSec"] * fps))
            out.append((cur, n))
            cur += n
        return out
    ts = ep_dir / "data" / "narration.ts"
    if ts.exists():
        m = re.search(
            r"(?:PAGE_AUDIO_SEC|AUDIO_SEC|AUDIO|DUR_SEC)\s*=\s*\[([^\]]+)\]",
            ts.read_text(encoding="utf-8"))
        if m:
            out, cur = [], 0
            for a in _nums(m.group(1)):
                n = int(round((a + 1.6) * FPS))
                out.append((cur, n))
                cur += n
            return out
    raise SystemExit("%s: 找不到页长数据" % ep_dir)


def load_episode(ep, root=None):
    """加载一集的完整验收数据。"""
    root = root or ROOT
    ep_dir = root / "src" / ep
    raw = json.load(open(ep_dir / "data" / "slots.json", encoding="utf-8"))
    cfg = parse_pages_config(
        (ep_dir / "data" / "pages.config.ts").read_text(encoding="utf-8"))
    layout = _page_layout(ep_dir)

    pages = []
    for key in sorted(raw):
        num = int(key[1:])
        det = raw[key]
        plate = tuple(det["plate"])
        slots = [Slot(s["id"], s["x"], s["y"], s["w"], s["h"])
                 for s in det["slots"]]
        pages.append(Page(num, plate, slots, cfg.get(num, [])))
    return Episode(ep, pages, layout)


def narration_text(ep, root=None):
    """读 <ep>_video/narration/all.json，返回 {页码: 口播原文}。

    **只认口播稿原文，不认 subtitles.ts**。两个实测理由：
      1) subtitles.ts 里的数字 token 大量是数组下标与行号（01…99），
         当文本 grep 会全污染；
      2) 口播有意省略书名简称（文案写《钦定日下旧闻考》，口播说《日下旧闻考》），
         直接比对必然假阳性。
    """
    p = VIDEO_ROOT / ("%s_video" % ep) / "narration" / "all.json"
    if not p.exists():
        return {}
    raw = json.load(open(p, encoding="utf-8"))
    out = {}
    for k, v in raw.items():
        m = re.match(r"p?(\d+)", str(k))
        if m:
            out[int(m.group(1))] = v
    return out
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_data.py -v`
Expected: PASS —— 9 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/data.py tests/test_data.py
git commit -m "feat(qa): 数据加载层（槽位/文案/页长/口播稿）

口播稿只认 narration/all.json，不认 subtitles.ts：
实测发现 subtitles.ts 的数字 token 大量是数组下标（01…99），
且口播有意省略书名简称，直接比对必假阳性。
页长优先级 pageMap > narration.json 不可反（E9 踩过，差 144 帧）。"
```

---

