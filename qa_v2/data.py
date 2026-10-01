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

    def __init__(self, sid: str, x: int, y: int, w: int, h: int):
        self.id = sid
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)

    @property
    def rect(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.w, self.h)

    def __repr__(self) -> str:
        return "Slot(%r, %d, %d, %d, %d)" % (
            self.id, self.x, self.y, self.w, self.h)


class TextItem(object):
    __slots__ = ("slot_id", "text", "size", "backing", "kind")

    def __init__(
        self,
        slot_id: str,
        text: str,
        size: int,
        backing: Any,
        kind: Optional[str],
    ):
        self.slot_id = slot_id
        self.text = text
        self.size = size
        self.backing = backing
        self.kind = kind

    @property
    def is_tag(self) -> bool:
        return self.kind == "tag"

    def __repr__(self) -> str:
        return "TextItem(%r, %r)" % (self.slot_id, self.text)


class Page(object):
    def __init__(
        self,
        number: int,
        plate: Tuple[int, int],
        slots: List[Slot],
        items: List[TextItem],
    ):
        self.number = number
        self.plate = plate
        self.slots = slots
        self.items = items

    def slot(self, sid: str) -> Optional[Slot]:
        for s in self.slots:
            if s.id == sid:
                return s
        return None


class Episode(object):
    def __init__(
        self,
        name: str,
        pages: List[Page],
        layout: List[Tuple[int, int]],
        data_dir: Optional[pathlib.Path] = None,
    ):
        self.name = name
        self.pages = pages
        self.layout = layout
        if data_dir is not None:
            self.data_dir = pathlib.Path(data_dir)
        else:
            default_dir = ROOT / "src" / name / "data"
            self.data_dir = default_dir if default_dir.exists() else None
    def page(self, number: int) -> Optional[Page]:
        for p in self.pages:
            if p.number == number:
                return p
        return None

    def final_frame(self, number: int) -> int:
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


def parse_pages_config(text: str) -> Dict[int, List[TextItem]]:
    """从 pages.config.ts 源码解析出 {页码: [TextItem, ...]}。

    只取顶层 `N: {` 块（避免匹配到嵌套），块内逐条抽 slotId。
    """
    out: Dict[int, List[TextItem]] = {}
    blocks = list(re.finditer(r"^  (\d+):\s*\{", text, re.M))
    for idx, bm in enumerate(blocks):
        end = blocks[idx + 1].start() if idx + 1 < len(blocks) else len(text)
        body = text[bm.end():end]
        page_no = int(bm.group(1))
        items: List[TextItem] = []
        for im in _ITEM_RE.finditer(body):
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


def _nums(block: str) -> List[float]:
    """只取数值字面量，先剥掉 // 与 /* */ 注释。"""
    block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
    block = re.sub(r"//[^\n]*", "", block)
    return [float(x) for x in _NUMS.findall(block)]


def _page_layout(ep_dir: pathlib.Path) -> List[Tuple[int, int]]:
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
            out: List[Tuple[int, int]] = []
            cur = 0
            for sec in _nums(m.group(1)):
                n = int(round(sec * FPS))
                out.append((cur, n))
                cur += n
            return out
    nj = ep_dir / "data" / "narration.json"
    if nj.exists():
        d = json.load(open(nj, encoding="utf-8"))
        fps = d.get("fps") or FPS
        out = []
        cur = 0
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
            out = []
            cur = 0
            for a in _nums(m.group(1)):
                n = int(round((a + 1.6) * FPS))
                out.append((cur, n))
                cur += n
            return out
    raise SystemExit("%s: 找不到页长数据" % ep_dir)


def load_episode(ep: str, root: Optional[pathlib.Path] = None) -> Episode:
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
    return Episode(ep, pages, layout, data_dir=ep_dir / "data")


def narration_text(ep: str, root: Optional[pathlib.Path] = None) -> Dict[int, str]:
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
