## Task 7: 抽帧与 OCR 缓存

**Files:**
- Create: `qa_v2/frames.py`
- Create: `tests/test_frames.py`

**Interfaces:**
- Consumes: `qa_v2/data.py`、`qa_v2/geometry.py`
- Produces:
  - `class OcrResult: texts: List[str]; boxes: List[Rect]; scores: List[float]` —— `boxes` 是 `[x1,y1,x2,y2]` 画布坐标
  - `def render_frame(composition: str, frame: int, out: Path) -> Path` —— composition 传 Remotion 注册名（如 `ShucunCourse`），**不要从集名拼**（`gaoliangqiao`.capitalize() → `Gaoliangqiao`，与实际 `GaoLiangQiaoCourse` 不符）
  - `def ocr_page(png: Path, ocr=None) -> OcrResult` —— 惰性加载 PaddleOCR
  - `def ocr_cached(ep: str, page: int, png: Path, cache_dir: Path = CACHE) -> OcrResult`
  - `def load_ocr() -> Any` —— 构造 PaddleOCR
  - `CACHE = Path("/tmp/qa_cache")`
  - `def text_at(ocr: OcrResult, rect: Rect, pad: int = 25) -> List[Tuple[str, Tuple[int,int,int,int], float]]` —— 返回落在矩形内的 `(文本, box, 置信)`；`box` 归一为 `(x,y,w,h)`

- [ ] **Step 1: 写失败的测试**

`tests/test_frames.py`（**不调 PaddleOCR 与 remotion**，用合成 OcrResult 测几何部分）：

```python
from qa_v2.frames import OcrResult, text_at


def _r(x1, y1, x2, y2, t, s=0.99):
    return (t, (x1, y1, x2, y2), s)


def test_text_at_finds_box_inside():
    o = OcrResult(["标题"], [(800, 60, 1100, 100)], [0.99])
    got = text_at(o, (780, 40, 1140, 120))
    assert [g[0] for g in got] == ["标题"]


def test_text_at_converts_box_to_xywh():
    o = OcrResult(["标题"], [(800, 60, 1100, 100)], [0.99])
    got = text_at(o, (780, 40, 1140, 120))
    assert got[0][1] == (800, 60, 300, 40)


def test_text_at_rejects_outside():
    o = OcrResult(["别处"], [(100, 100, 300, 140)], [0.99])
    assert text_at(o, (800, 60, 1140, 120)) == []


def test_text_at_tolerates_small_pad():
    """E11 实测：容差须 >= 25px，槽位与文字框有细微错位。"""
    o = OcrResult(["边缘"], [(790, 50, 1090, 100)], [0.99])
    assert text_at(o, (815, 65, 300, 60)) == []      # 差 25px，超容差
    assert len(text_at(o, (812, 62, 300, 60))) == 1  # 差 23px，在容差内


def test_text_at_returns_scores():
    o = OcrResult(["低置信"], [(800, 60, 900, 100)], [0.35])
    assert text_at(o, (780, 40, 1140, 120))[0][2] == 0.35
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_frames.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.frames'`

- [ ] **Step 3: 写最小实现**

`qa_v2/frames.py`：

```python
"""抽帧与 OCR。

两处踩过的坑，写在这里免得再犯：

1) **rec_boxes 是 [x1,y1,x2,y2]，不是 [x,y,w,h]**。
   E11 实测：按前者解释 93/93 槽位命中，按后者 0/93。

2) **OCR 的 box 已在画布空间**（1920×1080），不要再乘 plate 缩放。
   多乘一次就会全部错位，且表现为"所有槽位都空"。

OCR 很慢（E11 实测 8.5~16.4s/页），故默认落盘缓存。
"""
import hashlib
import json
import pathlib
import subprocess
from typing import Any, List, Optional, Tuple

from qa_v2.data import Episode, Slot
from qa_v2.geometry import CANVAS, Rect

CACHE = pathlib.Path("/tmp/qa_cache")
ROOT = pathlib.Path("/tmp/chemistry-video")

_OCR = None


class OcrResult(object):
    """一页的 OCR 结果。

    texts / boxes / scores 一一对应。
    boxes 元素是 [x1,y1,x2,y2]（PaddleOCR 3.x 原样），画布空间。
    """
    __slots__ = ("texts", "boxes", "scores")

    def __init__(self, texts, boxes, scores):
        self.texts = list(texts)
        self.boxes = [tuple(int(v) for v in b) for b in boxes]
        self.scores = [float(s) for s in scores]

    def to_json(self):
        return {"texts": self.texts, "boxes": [list(b) for b in self.boxes],
                "scores": self.scores}

    @classmethod
    def from_json(cls, d):
        return cls(d["texts"], d["boxes"], d["scores"])


def load_ocr():
    """构造 PaddleOCR（进程内单例）。首次约 4.7s。"""
    global _OCR
    if _OCR is None:
        from paddleocr import PaddleOCR
        _OCR = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            lang="ch",
        )
    return _OCR


def render_frame(composition, frame, out):
    """用 remotion still 抽单帧。

    composition 是 Remotion 注册名，必须由调用方从 COMPOSITION_OVERRIDES 传入。
    集名到注册名的映射不是 capitalize() —— gaoliangqiao → GaoLiangQiaoCourse。
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["npx", "remotion", "still", "src/index.tsx", composition, str(out),
         "--frame=%d" % frame, "--log=error"],
        cwd=str(ROOT), check=True)
    return out


def ocr_page(png, ocr=None):
    """对一张图跑 OCR，返回 OcrResult。"""
    if ocr is None:
        ocr = load_ocr()
    r = ocr.predict(str(png))[0]
    boxes = r["rec_boxes"]
    boxes = boxes.tolist() if hasattr(boxes, "tolist") else boxes
    res = OcrResult(r["rec_texts"], boxes, r["rec_scores"])
    _assert_box_format(res)
    return res


def _assert_box_format(res):
    """断言 rec_boxes 是 [x1,y1,x2,y2]。

    PaddleOCR 版本间可能变格式，而错误格式的表现是"全部槽位都空"——
    静默且难以察觉。宁可报错。
    """
    if not res.boxes:
        return
    b = res.boxes[0]
    if not (b[2] > b[0] and b[3] > b[1]):
        raise ValueError(
            "rec_boxes 格式异常：首个框 %r 不满足 x2>x1 且 y2>y1。"
            "本 QA 依赖 [x1,y1,x2,y2] 格式（E11 实测 93/93）。" % (b,))


def ocr_cached(ep, page, png, cache_dir=None):
    """带落盘缓存的 OCR。同一帧重复跑不重复识别。"""
    cache_dir = cache_dir or CACHE
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = "%s_p%02d" % (ep, page)
    f = cache_dir / ("%s.json" % key)
    if f.exists():
        try:
            return OcrResult.from_json(json.loads(f.read_text(encoding="utf-8")))
        except (ValueError, KeyError):
            pass  # 缓存损坏，重算
    res = ocr_page(png)
    f.write_text(json.dumps(res.to_json(), ensure_ascii=False),
                 encoding="utf-8")
    return res


def text_at(ocr, rect, pad=25):
    """返回落在矩形（容差 pad）内的 (文本, (x,y,w,h), 置信)。

    判定用**box 中心点**而非四角全含——E11 实测槽位与文字框有细微错位，
    四角全含会漏掉贴着槽边的那几行。
    """
    rx, ry, rw, rh = rect
    out = []
    for t, b, s in zip(ocr.texts, ocr.boxes, ocr.scores):
        x1, y1, x2, y2 = b
        cx, cy = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        if (rx - pad <= cx <= rx + rw + pad
                and ry - pad <= cy <= ry + rh + pad):
            out.append((t, (x1, y1, x2 - x1, y2 - y1), s))
    return out
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_frames.py -v`
Expected: PASS —— 5 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/frames.py tests/test_frames.py
git commit -m "feat(qa): 抽帧与 OCR 缓存

两个坑写进 docstring：
1) rec_boxes 是 [x1,y1,x2,y2] 不是 [x,y,w,h]（E11 实测 93/93 vs 0/93）
2) OCR box 已在画布空间，不可再乘 plate 缩放
_assert_box_format 对格式做硬断言 —— 错格式的静默表现是「全部槽位空」。
text_at 用中心点判定而非四角全含，E11 实测槽与文字框有细微错位。"
```

---

