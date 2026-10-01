"""抽帧与 OCR。

两处踩过的坑，写在这里免得再犯：

1) **rec_boxes 是 [x1,y1,x2,y2]，不是 [x,y,w,h]**。
   PaddleOCR 3.x 的 rec_boxes 是右下角坐标格式。
   E11 实测：按前者解释 93/93 槽位命中，按后者 0/93。
   错误格式的静默表现是「所有槽位都空」——极难察觉。
   故通过 _assert_box_format 做硬断言，宁可报错。

2) **OCR 的 box 已在画布空间**（1920×1080），不要再乘 plate 缩放。
   slots.json 的 x/y/w/h 是板面空间（1672×941 或 1920×1080）；
   而 OCR 返回的 rec_boxes 是画布空间，输入就是渲染帧。
   多乘一次缩放就会全部错位，且表现为"所有槽位都空"。

OCR 很慢（E11 实测 8.5~16.4s/页），故默认落盘缓存。
"""
import json
import pathlib
import subprocess
from typing import Any, List, Optional, Tuple

from qa_v2.geometry import Rect

# OCR 结果落盘缓存目录。
# 注意：缓存文件名以 "%s_p%02d.json" % (ep, page) 命名，并未计算帧图像内容哈希（MD5）。
# 若修改了文案、排版或样式并重新渲染帧，旧缓存不会自动失效！
# 此时必须手动清空此缓存目录（rm -rf /tmp/qa_cache），否则 QA 会继续读取旧缓存。
CACHE = pathlib.Path("/tmp/qa_cache")
ROOT = pathlib.Path("/tmp/chemistry-video")

_OCR = None


class OcrResult(object):
    """一页的 OCR 结果。

    texts / boxes / scores 一一对应。
    boxes 元素是 [x1,y1,x2,y2]（PaddleOCR 3.x 原样），画布空间。
    """
    __slots__ = ("texts", "boxes", "scores")

    def __init__(
        self,
        texts: List[str],
        boxes: List[Tuple[int, int, int, int]],
        scores: List[float],
    ):
        self.texts = list(texts)
        self.boxes = [tuple(int(v) for v in b) for b in boxes]
        self.scores = [float(s) for s in scores]

    def to_json(self) -> dict:
        return {
            "texts": self.texts,
            "boxes": [list(b) for b in self.boxes],
            "scores": self.scores,
        }

    @classmethod
    def from_json(cls, d: dict) -> "OcrResult":
        return cls(d["texts"], d["boxes"], d["scores"])


def load_ocr() -> Any:
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


def render_frame(composition: str, frame: int, out: pathlib.Path) -> pathlib.Path:
    """用 remotion still 抽单帧。

    composition 是 Remotion 注册名，必须由调用方从 COMPOSITION_OVERRIDES 传入。
    集名到注册名的映射不是 capitalize() —— gaoliangqiao → GaoLiangQiaoCourse。
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "npx", "remotion", "still", "src/index.tsx", composition, str(out),
            "--frame=%d" % frame, "--log=error"
        ],
        cwd=str(ROOT),
        check=True,
    )
    return out


def ocr_page(png: pathlib.Path, ocr: Any = None) -> OcrResult:
    """对一张图跑 OCR，返回 OcrResult。"""
    if ocr is None:
        ocr = load_ocr()
    r = ocr.predict(str(png))[0]
    boxes = r["rec_boxes"]
    boxes = boxes.tolist() if hasattr(boxes, "tolist") else boxes
    res = OcrResult(r["rec_texts"], boxes, r["rec_scores"])
    _assert_box_format(res)
    return res


def _assert_box_format(res: OcrResult) -> None:
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
            "本 QA 依赖 [x1,y1,x2,y2] 格式（E11 实测 93/93）。" % (b,)
        )


def ocr_cached(
    ep: str,
    page: int,
    png: pathlib.Path,
    cache_dir: Optional[pathlib.Path] = None,
) -> OcrResult:
    """带落盘缓存的 OCR。同一帧重复跑不重复识别。

    注意：缓存键仅由 (ep, page) 构成，未绑定图像内容哈希。
    如果视频工程重新渲染帧（如修改文案/排版后），必须手动清理缓存目录（如 rm -rf /tmp/qa_cache），
    否则会继续读取旧的 OCR 缓存。
    """
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
    f.write_text(json.dumps(res.to_json(), ensure_ascii=False), encoding="utf-8")
    return res


def text_at(
    ocr: OcrResult, rect: Rect, pad: int = 25
) -> List[Tuple[str, Tuple[int, int, int, int], float]]:
    """返回落在矩形（容差 pad）内的 (文本, (x,y,w,h), 置信)。

    判定用**box 中心点**而非四角全含——E11 实测槽位与文字框有细微错位，
    四角全含会漏掉贴着槽边的那几行。
    box 归一为 (x, y, w, h)。
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
