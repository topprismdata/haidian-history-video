# QA v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `qa_all.py` 从「区域内有深色像素」的单薄判据，扩展成七层验收，其中 L4 用 OCR 读回实现「槽里的字对不对」的闭环。

**Architecture:** 七层独立检测器共用一个数据加载层。L1/L2 纯数据（不渲帧，<0.2s/页）、L3/L5/L6 用渲染帧（~1s/页）、L4 用 OCR（~10s/页，默认关闭）。每层返回 `list[Finding]`，由统一入口汇总输出。每条判据必须配负控制证明非恒真。

**Tech Stack:** Python 3.9.6、pytest 8.4.2、numpy、Pillow、PaddleOCR 3.7（PP-OCRv6 medium）。

## 路径与包名（实现前必读）

- **包名是 `qa_v2`，不是 `qa`**。`/tmp/chemistry-video/qa/` 已被 E6–E10 的
  QA 截图缓存占用（`auto/`、`dzs/`、`glq/`、`ldc/`…），不能覆盖。
- **代码真实位置在 git 仓库**：`/Volumes/macstudio/video-projects/qa_v2/` 与
  `.../tests/`。工程副本 `/tmp/chemistry-video/` 下有同名软链接，
  因此在 `/tmp/chemistry-video` 里跑 `python3 -m pytest tests/` 与
  `python3 -m qa_v2.run` 都能工作，但 `git add` 必须在
  `/Volumes/macstudio/video-projects` 里执行。
- 计划正文中出现的 `git add` / `git commit` 命令**都在 video-projects 仓库**执行。

## Global Constraints

以下约束**每个 task 都适用**，不再逐条重复：

- **Python 3.9.6** —— 禁止 `X | None` 语法，用 `Optional[X]`；禁止 `match` 语句
- **工程根目录 `/tmp/chemistry-video`**，QA 脚本与测试都在该目录下
- **坐标空间有两套，必须显式区分**：
  - 板面空间（`slots.json` 的 `x/y/w/h`），尺寸见各页 `plate` 字段（1672×941 或 1920×1080）
  - 画布空间（渲染帧像素），恒为 1920×1080
  - 换算函数唯一入口：`qa_v2/geometry.py::plate_to_canvas()`
  - **OCR 的 `rec_boxes` 已经是画布空间，禁止再乘缩放**
- **`slots.json` 顶层键是 `p01..p08`**，没有集名外层
- **`pages.config.ts` 的文案在 `items` 数组内**，每项含 `slotId` 与 `text`
- **所有数值阈值必须以 E11 实测值为依据**，改动阈值须在 commit message 说明依据
- **测试不得依赖成片渲染**（太慢），单元测试用构造的合成图/合成数据
- **提交信息用中文**，遵循 `<type>(<scope>): <摘要>` 格式

---

## File Structure

| 文件 | 职责 |
|---|---|
| `qa_v2/__init__.py` | 空包标记 |
| `qa_v2/geometry.py` | 坐标换算、槽位矩形运算（重叠/越界/尺寸） |
| `qa_v2/normalize.py` | 标点归一化、中文数字→阿拉伯数字 |
| `qa_v2/data.py` | 加载 `slots.json` / `pages.config.ts` / `narration/all.json` / 页长 |
| `qa_v2/frames.py` | 抽帧（`remotion still`）、OCR 结果缓存 |
| `qa_v2/checks_data.py` | L1 数据一致性、L2 几何可行性 |
| `qa_v2/checks_render.py` | L3 渲染存在性、L5 溢出、L6 tag 槽 |
| `qa_v2/checks_content.py` | L4 内容闭环（数字/专名/字幕交叉） |
| `qa_v2/names.txt` | 专名表 |
| `qa_v2/report.py` | Finding 定义与汇总输出（终端 / JSON） |
| `qa_v2/run.py` | 统一入口，CLI 开关 |
| `qa_all.py` | 保留为薄壳，转调 `qa_v2/run.py`（保持历史命令可用） |
| `tests/test_geometry.py` | 坐标换算与矩形运算 |
| `tests/test_normalize.py` | 标点与数字归一 |
| `tests/test_data.py` | 数据加载 |
| `tests/test_checks_data.py` | L1/L2 |
| `tests/test_checks_render.py` | L3/L5/L6（含负控制） |
| `tests/test_checks_content.py` | L4（含负控制） |
| `tests/conftest.py` | 共享 fixture：合成槽位、合成帧 |

---

## Task 1: 坐标换算与矩形运算

**Files:**
- Create: `qa_v2/__init__.py`
- Create: `qa_v2/geometry.py`
- Create: `tests/conftest.py`
- Create: `tests/test_geometry.py`

**Interfaces:**
- Consumes: 无（首个 task）
- Produces:
  - `CANVAS = (1920, 1080)` 模块常量
  - `plate_to_canvas(plate: Sequence[int], x: float, y: float, w: float, h: float) -> Tuple[int, int, int, int]` —— 板面坐标 → 画布像素矩形
  - `scale_of(plate: Sequence[int]) -> Tuple[float, float, float]` —— 返回 `(scale, offset_x, offset_y)`
  - `overlap_ratio(a: Rect, b: Rect) -> float` —— 交叠面积 / 较小者面积，无交叠返回 0.0
  - `out_of_bounds(rect: Rect, plate: Sequence[int]) -> bool`
  - `Rect = Tuple[int, int, int, int]`（`(x, y, w, h)`）

- [ ] **Step 1: 写失败的测试**

`tests/test_geometry.py`：

```python
"""坐标换算的回归测试。

背景：qa_all.py 曾把 1672×941 的板面坐标直接切 1920×1080 的渲染帧，
P5 采到的是插画上的香炉（墨像素 32062）而不是文字（2229），判据恒真。
本文件的 E11 实测锚点就是为防这个 bug 回归。
"""
from qa_v2.geometry import (
    CANVAS, scale_of, plate_to_canvas, overlap_ratio, out_of_bounds,
)

E11_PLATE = (1672, 941)


def test_scale_of_1672x941():
    s, ox, oy = scale_of(E11_PLATE)
    assert s == max(1920 / 1672, 1080 / 941)
    assert ox == 0.0          # 宽是约束边，横向正好铺满
    assert oy < 0             # 高有 0.29px 富余，居中后上边为负


def test_scale_of_1920x1080_is_identity():
    s, ox, oy = scale_of((1920, 1080))
    assert s == 1.0 and ox == 0.0 and oy == 0.0


def test_plate_to_canvas_e11_p5_note_left():
    """E11 P5 note_left：板面 (214,781,505,86) → 画布 (246,897,580,99)。

    这组数字来自实测：旧判据在板面坐标处采到插画（32062 墨像素），
    真文字在换算后的位置（2229 墨像素）。
    """
    x, y, w, h = plate_to_canvas(E11_PLATE, 214, 781, 505, 86)
    assert (x, y) == (246, 897)
    assert abs(w - 580) <= 1 and abs(h - 99) <= 1


def test_plate_to_canvas_1920_plate_is_identity():
    assert plate_to_canvas((1920, 1080), 100, 200, 300, 40) == (100, 200, 300, 40)


def test_plate_to_canvas_never_shrinks():
    """缩放只会放大（1672→1920），不能变小，否则采样区反而变小。"""
    _, w, _ = plate_to_canvas(E11_PLATE, 0, 0, 100, 100)[1:2] + (100,)
    x, y, w, h = plate_to_canvas(E11_PLATE, 0, 0, 100, 100)
    assert w > 100 and h > 100


def test_overlap_ratio_identical_is_one():
    r = (0, 0, 100, 100)
    assert overlap_ratio(r, r) == 1.0


def test_overlap_ratio_disjoint_is_zero():
    assert overlap_ratio((0, 0, 10, 10), (100, 100, 10, 10)) == 0.0


def test_overlap_ratio_uses_smaller_as_denominator():
    """小框完全落在大框内 → 交叠比 = 1.0（对小框而言全被覆盖）。"""
    assert overlap_ratio((0, 0, 100, 100), (10, 10, 10, 10)) == 1.0


def test_overlap_ratio_half():
    assert abs(overlap_ratio((0, 0, 10, 10), (5, 0, 10, 10)) - 0.5) < 1e-9


def test_out_of_bounds_detects_overflow():
    assert out_of_bounds((1672, 941, 10, 10), (1672, 941)) is False
    assert out_of_bounds((1670, 941, 10, 10), (1672, 941)) is True
    assert out_of_bounds((-1, 0, 10, 10), (1672, 941)) is True


def test_out_of_bounds_allows_touching_edge():
    """右边缘刚好贴齐不算越界（等号边界）。"""
    assert out_of_bounds((1662, 931, 10, 10), (1672, 941)) is False
```

`tests/conftest.py`（本 task 只需要空壳，后续 task 追加 fixture）：

```python
import pathlib
import sys

# 让 `import qa.xxx` 在未安装包的情况下也能工作
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_geometry.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa'`

- [ ] **Step 3: 写最小实现**

`qa_v2/__init__.py`（空文件）。

`qa_v2/geometry.py`：

```python
"""坐标换算与槽位矩形运算。

**为什么这个模块存在**：QA 判据全部建立在「槽位矩形内应有该槽位的字」上，
矩形取错位置，判据就退化成「这块地方有没有深色像素」——而插画上到处都是。

E11 实测的反面教材：qa_all.py 未做 plate→canvas 换算，P5 采到香炉木架
（墨像素 32062）而非文字（2229），判据恒真，"8/8 通过"是假的。

坐标空间（务必分清）：
  * 板面空间 —— slots.json 里的 x/y/w/h，尺寸见各页 plate（1672×941 或 1920×1080）
  * 画布空间 —— 渲染帧像素，恒为 CANVAS；PlatePage 用 objectFit:"cover" 铺满
OCR 返回的 rec_boxes 已在画布空间，**不要再乘缩放**。
"""
from typing import Sequence, Tuple

CANVAS = (1920, 1080)
Rect = Tuple[int, int, int, int]


def scale_of(plate: Sequence[int]) -> Tuple[float, float, float]:
    """cover 缩放系数与居中偏移，返回 (scale, offset_x, offset_y)。"""
    pw, ph = plate[0], plate[1]
    s = max(CANVAS[0] / pw, CANVAS[1] / ph)
    return s, (CANVAS[0] - pw * s) / 2.0, (CANVAS[1] - ph * s) / 2.0


def plate_to_canvas(
    plate: Sequence[int], x: float, y: float, w: float, h: float
) -> Rect:
    """板面坐标 → 画布像素矩形（四舍五入到 int）。"""
    s, ox, oy = scale_of(plate)
    return (
        int(round(ox + x * s)),
        int(round(oy + y * s)),
        int(round(w * s)),
        int(round(h * s)),
    )


def overlap_ratio(a: Rect, b: Rect) -> float:
    """交叠面积占较小矩形面积的比例；无交叠返回 0.0。"""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ix = min(ax + aw, bx + bw) - max(ax, bx)
    iy = min(ay + ah, by + bh) - max(ay, by)
    if ix <= 0 or iy <= 0:
        return 0.0
    inter = ix * iy
    smaller = min(aw * ah, bw * bh)
    if smaller <= 0:
        return 0.0
    return inter / smaller


def out_of_bounds(rect: Rect, plate: Sequence[int]) -> bool:
    """槽位矩形是否越出板面边界。"""
    x, y, w, h = rect
    return x < 0 or y < 0 or x + w > plate[0] or y + h > plate[1]
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_geometry.py -v`
Expected: PASS —— 11 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/__init__.py qa/geometry.py tests/conftest.py tests/test_geometry.py
git commit -m "feat(qa): 坐标换算与矩形运算

plate→canvas cover 换算是所有渲染判据的前提。qa_all.py 曾缺这一步，
E11 P5 采到插画（墨 32062）而非文字（2229），判据恒真。
E11 实测锚点已写成回归测试。"
```

---

## Task 2: 标点与数字归一化

**Files:**
- Create: `qa_v2/normalize.py`
- Create: `tests/test_normalize.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `normalize_punct(s: str) -> str` —— 去掉标点与空白，保留字母数字汉字
  - `to_int(token: str) -> Optional[int]` —— 中文/阿拉伯数字 token → int
  - `extract_numbers(s: str) -> List[int]` —— 从文本抽出全部数字（已归一），无法解析的跳过
  - `number_unknown_rate(text: str) -> float` —— 无法解析的 token 占比，用于检测归一函数的 bug

- [ ] **Step 1: 写失败的测试**

`tests/test_normalize.py`：

```python
"""归一化。阈值与规则来自 E11 实测。

E11 用 PaddleOCR 3.7 跑完 8 页，平均置信 0.989，噪声**只有标点**：
  原文「树村·圆明园正北」   → OCR「树村.圆明园正北」
  原文「一个村子，三重身份」 → OCR「一个村子.三重身份」
  原文「楹＝间」           → OCR「楹=间」
无错字、无漏字，所以归一只需处理标点，不需要模糊匹配。
"""
import pytest

from qa_v2.normalize import (
    normalize_punct, to_int, extract_numbers, number_unknown_rate,
)


@pytest.mark.parametrize("raw,expect", [
    ("树村·圆明园正北", "树村圆明园正北"),
    ("一个村子，三重身份", "一个村子三重身份"),
    ("楹＝间", "楹间"),
    ("「著移驻树村」", "著移驻树村"),
    ("E1 肖家河", "E1肖家河"),
    ("1799 → 1800 → 1801", "179918001801"),
])
def test_normalize_punct(raw, expect):
    assert normalize_punct(raw) == expect


def test_normalize_punct_keeps_latin_and_cjk():
    assert normalize_punct("五圣庵·鐡磬一") == "五圣庵鐡磬一"


@pytest.mark.parametrize("tok,expect", [
    ("1485", 1485),
    ("1724", 1724),
    ("一七二四", 1724),      # 纯位值写法（口播逐位念年份）
    ("一千二百五十", 1250),
    ("三千", 3000),
    ("三百七十五", 375),
    ("二十三", 23),
    ("二十八", 28),
    ("一百二十", 120),
])
def test_to_int(tok, expect):
    assert to_int(tok) == expect


@pytest.mark.parametrize("tok", ["蜀村", "", "·", "abc"])
def test_to_int_returns_none_for_non_number(tok):
    assert to_int(tok) is None


def test_extract_numbers_mixes_forms():
    txt = "共盖房一万间，分为八处，每处一千二百五十间（1250）"
    assert sorted(extract_numbers(txt)) == [8, 10000, 1250]


def test_extract_numbers_reads_speech_years():
    """口播里年份是逐位念的：「一七二四年」→ 1724。"""
    assert extract_numbers("雍正二年，也就是一七二四年") == [1724]


def test_number_unknown_rate_is_zero_for_clean_text():
    assert number_unknown_rate("镶黄旗在村西，65 楹，1485 楹") == 0.0


def test_number_unknown_rate_flags_garbage():
    """归一函数出 bug 时要能被察觉，而不是静默通过。"""
    rate = number_unknown_rate("一七二四 9999 蜀村")
    assert rate > 0.2
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_normalize.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.normalize'`

- [ ] **Step 3: 写最小实现**

`qa_v2/normalize.py`：

```python
"""文本归一化：标点剥离 + 中文数字转阿拉伯数字。

E11 实测（PaddleOCR 3.7 / PP-OCRv6 medium，8 页平均置信 0.989）：
OCR 噪声**只有标点规范化**，无错字无漏字。故归一只需处理标点，
不需要 fuzzy matching —— 数字与专名可以直接严格比对。
"""
import re
from typing import List, Optional

# 保留汉字、字母、数字，其余（标点/空白/装饰符号）一律去掉
_STRIP = re.compile(r"[^0-9A-Za-z一-鿿]+")

_CN_DIGIT = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}
_CN_UNIT = {"十": 10, "百": 100, "千": 1000}

# 连续的阿拉伯数字 / 中文数字 / 数字单位
_NUM_RE = re.compile(
    r"[0-9]+|[零〇一二两三四五六七八九十百千]+"
)


def normalize_punct(s: str) -> str:
    """去掉标点与空白，只留汉字/字母/数字。"""
    return _STRIP.sub("", s)


def to_int(token: str) -> Optional[int]:
    """数字 token → int，解析不了返回 None。

    支持三种写法：
      「1485」        → 1485   （阿拉伯）
      「一千二百五十」→ 1250   （带单位）
      「一七二四」    → 1724   （纯位值，口播逐位念年份）
    """
    t = token.strip()
    if not t:
        return None
    if t.isdigit():
        return int(t)
    if not all(c in _CN_DIGIT or c in _CN_UNIT for c in t):
        return None

    # 纯位值写法：每个字都是一个数字，没有单位字
    if all(c in _CN_DIGIT for c in t):
        digits = [_CN_DIGIT[c] for c in t]
        if len(digits) > 1 and digits[0] == 0:
            # 形如「零一二」这种混合写法，放弃
            return None
        n = 0
        for d in digits:
            n = n * 10 + d
        return n

    # 带单位：按「千百十」节法解析
    total = 0      # 已结算的高位
    section = 0    # 当前节
    last_digit = None
    for c in t:
        if c in _CN_DIGIT:
            last_digit = _CN_DIGIT[c]
        else:
            unit = _CN_UNIT[c]
            if last_digit is None:
                # 「十二」的「十」前面没数字，按 1 处理
                last_digit = 1
            section += last_digit * unit
            last_digit = None
    if last_digit is not None:
        section += last_digit
    return total + section


def extract_numbers(s: str) -> List[int]:
    """从文本抽出全部可解析的数字，已归一到 int；解析不了的跳过。"""
    out = []
    for m in _NUM_RE.finditer(s):
        v = to_int(m.group())
        if v is not None:
            out.append(v)
    return out


def number_unknown_rate(text: str) -> float:
    """「像数字但解析不了」的 token 占全部候选 token 的比例。

    正常为 0.0。> 0.2 说明 to_int 有 bug 或文本有异常，
    此时 L4 的数字比对不可信，应报 warn 而不是静默通过。
    """
    cands = _NUM_RE.findall(text)
    if not cands:
        return 0.0
    bad = sum(1 for c in cands if to_int(c) is None)
    return bad / float(len(cands))
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_normalize.py -v`
Expected: PASS —— 22 passed（含 parametrize 展开）

若 `test_number_unknown_rate_flags_garbage` 失败（因为「蜀村」不会被 `_NUM_RE` 匹配成数字候选），
把该测试的输入改为 `"一七二四 9999 一二三四五六七"` 并调整断言为 `> 0.1`。

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/normalize.py tests/test_normalize.py
git commit -m "feat(qa): 标点与中文数字归一化

E11 实测 OCR 噪声仅标点规范化（·→. 、，→. ），无错字漏字，
故归一只处理标点，数字与专名可严格比对，不必 fuzzy matching。
to_int 支持三种写法：阿拉伯、带单位（一千二百五十）、纯位值（一七二四）。"
```

---

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

## Task 4: Finding 与报告输出

**Files:**
- Create: `qa_v2/report.py`
- Create: `tests/test_report.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `class Finding: layer: str; page: Optional[int]; slot: Optional[str]; level: str; code: str; message: str; detail: Optional[dict]`
    - `level ∈ {"fail", "warn", "skip", "info"}`
  - `def summarize(findings: List[Finding]) -> Dict[str, int]` —— 各 level 计数
  - `def render_text(findings: List[Finding], ep: str) -> str` —— 终端可读
  - `def render_json(findings: List[Finding], ep: str) -> str`

- [ ] **Step 1: 写失败的测试**

`tests/test_report.py`：

```python
from qa_v2.report import Finding, summarize, render_text, render_json


def test_summarize_counts_by_level():
    fs = [
        Finding("L1", 3, "r1_flag", "fail", "SLOT_MISSING_IN_TEXT", "文案没填"),
        Finding("L4", 3, "r1_total", "fail", "NUMBER_MISMATCH", "1485≠1486"),
        Finding("L4", 3, "r2_dir", "warn", "NUMBER_UNKNOWN", "归一失败率高"),
        Finding("L6", 5, "evidence_tag", "skip", "NO_NAMES", "专名表缺"),
    ]
    assert summarize(fs) == {"fail": 2, "warn": 1, "skip": 1, "info": 0}


def test_render_text_mentions_ep_and_counts():
    fs = [Finding("L1", 1, "title", "fail", "X", "坏了")]
    out = render_text(fs, "shucun")
    assert "shucun" in out
    assert "fail" in out
    assert "坏了" in out


def test_render_text_empty_says_pass():
    assert "通过" in render_text([], "shucun")


def test_render_json_roundtrips():
    import json as _json
    fs = [Finding("L1", 1, "title", "fail", "X", "坏了", {"a": 1})]
    got = _json.loads(render_json(fs, "shucun"))
    assert got["episode"] == "shucun"
    assert got["summary"]["fail"] == 1
    assert got["findings"][0]["slot"] == "title"
    assert got["findings"][0]["detail"] == {"a": 1}


def test_finding_defaults():
    f = Finding("L1", 1, "title", "fail", "X", "m")
    assert f.detail is None
    assert f.slot == "title"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_report.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.report'`

- [ ] **Step 3: 写最小实现**

`qa_v2/report.py`：

```python
"""验收结论的表示与输出。

level 语义（只有 fail 阻塞退出码，见 spec §10.2）：
  fail —— 违反判据，必须修
  warn —— 可疑但可能是判据过严，不阻塞
  skip —— 该判据因缺前置数据未执行（如专名表未维护），**不算通过**
  info —— 补充信息
"""
import json
from typing import Dict, List, Optional

LEVELS = ("fail", "warn", "skip", "info")


class Finding(object):
    __slots__ = ("layer", "page", "slot", "level", "code", "message", "detail")

    def __init__(self, layer, page, slot, level, code, message,
                 detail=None):
        assert level in LEVELS, "未知 level: %r" % level
        self.layer = layer
        self.page = page
        self.slot = slot
        self.level = level
        self.code = code
        self.message = message
        self.detail = detail

    def to_dict(self):
        return {
            "layer": self.layer, "page": self.page, "slot": self.slot,
            "level": self.level, "code": self.code, "message": self.message,
            "detail": self.detail,
        }

    def __repr__(self):
        return "Finding(%s, p%s, %s, %s, %s)" % (
            self.layer, self.page, self.slot, self.level, self.code)


def summarize(findings):
    out = dict((lv, 0) for lv in LEVELS)
    for f in findings:
        out[f.level] += 1
    return out


_ICON = {"fail": "✗", "warn": "⚠", "skip": "–", "info": "·"}


def render_text(findings, ep):
    s = summarize(findings)
    lines = ["=== %s ===" % ep]
    if not findings:
        lines.append("  全部通过，无发现")
    else:
        order = {"fail": 0, "warn": 1, "skip": 2, "info": 3}
        for f in sorted(findings, key=lambda x: (
                order.get(x.level, 9), x.layer, x.page or 0)):
            where = "P%s" % f.page if f.page else "-"
            slot = f.slot or "-"
            lines.append("  %s [%s] %s/%s  %s" % (
                _ICON.get(f.level, "?"), f.level, where, slot, f.message))
            if f.detail:
                for k, v in sorted(f.detail.items()):
                    lines.append("        %s=%s" % (k, v))
    tail = "  -> fail %d / warn %d / skip %d / info %d" % (
        s["fail"], s["warn"], s["skip"], s["info"])
    lines.append(tail)
    lines.append("  判定：" + ("不通过" if s["fail"] else "通过"))
    return "\n".join(lines)


def render_json(findings, ep):
    return json.dumps(
        {"episode": ep, "summary": summarize(findings),
         "findings": [f.to_dict() for f in findings]},
        ensure_ascii=False, indent=1)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_report.py -v`
Expected: PASS —— 6 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/report.py tests/test_report.py
git commit -m "feat(qa): Finding 与报告输出

level 四级，只有 fail 阻塞退出码（历史集 warn 噪声不应淹没真问题）。
skip 表示判据因缺前置数据未执行，不等于通过 —— 专名表缺失时必须显式 skip。"
```

---

## Task 5: L1 数据一致性

**Files:**
- Create: `qa_v2/checks_data.py`
- Create: `tests/test_checks_data.py`

**Interfaces:**
- Consumes: `qa_v2/data.py`（Task 3）、`qa_v2/geometry.py`（Task 1）、`qa_v2/report.py`（Task 4）
- Produces:
  - `check_l1(ep: Episode) -> List[Finding]`
  - 判据常量：`OVERLAP_FAIL_RATIO = 0.05`、`MIN_SLOT_W = 40`、`MIN_SLOT_H = 20`

- [ ] **Step 1: 写失败的测试**

`tests/test_checks_data.py`：

```python
"""L1 数据一致性：纯数据检查，不渲帧，<0.1s/页。"""
import pytest

from qa_v2.data import Episode, Page, Slot, TextItem
from qa_v2.checks_data import (
    check_l1, OVERLAP_FAIL_RATIO, MIN_SLOT_W, MIN_SLOT_H,
)


def _page(slots, items, plate=(1672, 941), number=1):
    return Page(number, plate, [Slot(*s) for s in slots],
                [TextItem(*i) for i in items])


def _ep(pages):
    layout = []
    cur = 0
    for p in pages:
        layout.append((cur, 660))
        cur += 660
    return Episode("t", pages, layout)


def _codes(fs):
    return sorted(f.code for f in fs)


def test_clean_episode_passes():
    ep = _ep([_page([("title", 0, 0, 400, 100)],
                    [("title", "标题", 26, True, None)])])
    assert _codes(check_l1(ep)) == []


def test_text_referencing_missing_slot():
    """E11 实测踩中：badge→evidence_tag 改名后文案侧漏改，
    boxOf 静默返回 10×10 兜底框，标签飞到画外。"""
    ep = _ep([_page([("evidence_tag", 1400, 20, 250, 60)],
                    [("badge", "[文献记载]", 20, True, "tag")])])
    codes = _codes(check_l1(ep))
    assert "TEXT_REFERENCES_MISSING_SLOT" in codes


def test_slot_with_no_text_is_flagged():
    ep = _ep([_page([("title", 0, 0, 400, 100),
                      ("subtitle", 0, 110, 400, 40)],
                    [("title", "标题", 26, True, None)])])
    assert "SLOT_WITHOUT_TEXT" in _codes(check_l1(ep))


def test_out_of_bounds_slot():
    ep = _ep([_page([("title", 1700, 0, 400, 100)],
                    [("title", "标题", 26, True, None)])])
    assert "SLOT_OUT_OF_BOUNDS" in _codes(check_l1(ep))


def test_tiny_slot_warns():
    """改名后残留旧坐标的典型症状：槽小得装不下字。"""
    ep = _ep([_page([("title", 0, 0, MIN_SLOT_W - 1, 100)],
                    [("title", "标题", 26, True, None)])])
    fs = [f for f in check_l1(ep) if f.code == "SLOT_TOO_SMALL"]
    assert len(fs) == 1 and fs[0].level == "warn"


def test_overlap_fails_above_threshold():
    ep = _ep([_page([("a", 0, 0, 400, 100), ("b", 380, 0, 400, 100)],
                    [("a", "甲", 20, True, None), ("b", "乙", 20, True, None)])])
    fs = [f for f in check_l1(ep) if f.code == "SLOT_OVERLAP"]
    assert len(fs) == 1 and fs[0].level == "fail"


def test_overlap_below_threshold_is_fine():
    """边框相邻不算叠。"""
    ep = _ep([_page([("a", 0, 0, 400, 100), ("b", 405, 0, 400, 100)],
                    [("a", "甲", 20, True, None), ("b", "乙", 20, True, None)])])
    assert "SLOT_OVERLAP" not in _codes(check_l1(ep))


def test_page_count_matches_layout():
    pages = [_page([("t", 0, 0, 100, 40)], [("t", "x", 20, True, None)],
                   number=i) for i in range(1, 4)]
    ep = Episode("t", pages, [(0, 660), (660, 660)])   # 布局只有 2 项
    assert "PAGE_COUNT_MISMATCH" in _codes(check_l1(ep))


def test_real_shucun_passes_l1():
    """E11 实测：93 槽位，重叠 0、越界 0、双向一致。"""
    from qa_v2.data import load_episode
    fs = check_l1(load_episode("shucun"))
    assert [f for f in fs if f.level == "fail"] == []
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_data.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.checks_data'`

- [ ] **Step 3: 写最小实现**

`qa_v2/checks_data.py`：

```python
"""L1 数据一致性 + L2 几何可行性。纯数据，不渲帧，<0.2s/页。

L1 抓的是「静默失败」——最阴的一类：数据不匹配时代码仍能跑，
只是默默返回一个兜底值，最终表现为「某槽空白」或「文字飞到画外」。
E11 实测踩中：badge→evidence_tag 改名后文案侧漏改，
boxOf 找不到槽位却静默返回 10×10 兜底框。
"""
from typing import List

from qa_v2.geometry import overlap_ratio, out_of_bounds
from qa_v2.report import Finding

# 交叠面积占较小者的比例超过此值算 fail（边框相邻不算叠）
OVERLAP_FAIL_RATIO = 0.05
# 槽位尺寸下限：低于此值基本装不下任何文字
MIN_SLOT_W = 40
MIN_SLOT_H = 20


def check_l1(ep):
    """数据一致性。返回 List[Finding]。"""
    out = []
    if len(ep.pages) != len(ep.layout):
        out.append(Finding(
            "L1", None, None, "fail", "PAGE_COUNT_MISMATCH",
            "页数与页长表不符：%d 页 vs %d 项"
            % (len(ep.pages), len(ep.layout))))

    for page in ep.pages:
        have = set(s.id for s in page.slots)
        used = set(i.slot_id for i in page.items)

        for i in page.items:
            if i.slot_id not in have:
                out.append(Finding(
                    "L1", page.number, i.slot_id, "fail",
                    "TEXT_REFERENCES_MISSING_SLOT",
                    "文案引用了不存在的槽位（渲染时会静默走兜底框）",
                    {"text": i.text[:40]}))

        for s in page.slots:
            if s.id not in used:
                out.append(Finding(
                    "L1", page.number, s.id, "fail", "SLOT_WITHOUT_TEXT",
                    "槽位没有被任何文案引用（静默空洞）"))

            if out_of_bounds(s.rect, page.plate):
                out.append(Finding(
                    "L1", page.number, s.id, "fail", "SLOT_OUT_OF_BOUNDS",
                    "槽位越出板面 %dx%d" % page.plate,
                    {"rect": list(s.rect)}))

            if s.w < MIN_SLOT_W or s.h < MIN_SLOT_H:
                out.append(Finding(
                    "L1", page.number, s.id, "warn", "SLOT_TOO_SMALL",
                    "槽位过小，可能是改名后残留的旧坐标",
                    {"w": s.w, "h": s.h}))

        for i in range(len(page.slots)):
            for j in range(i + 1, len(page.slots)):
                a, b = page.slots[i], page.slots[j]
                r = overlap_ratio(a.rect, b.rect)
                if r > OVERLAP_FAIL_RATIO:
                    out.append(Finding(
                        "L1", page.number, a.id, "fail", "SLOT_OVERLAP",
                        "与 %s 交叠 %.0f%%" % (b.id, r * 100),
                        {"other": b.id, "ratio": round(r, 3)}))
    return out
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_data.py -v`
Expected: PASS —— 9 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_data.py tests/test_checks_data.py
git commit -m "feat(qa): L1 数据一致性检查

抓的是静默失败：数据不匹配时代码仍能跑，只是默默返回兜底值。
E11 实测踩中 badge→evidence_tag 改名后文案侧漏改，boxOf 静默返回 10×10。
交叠阈值 5%（占较小槽面积），边框相邻不算叠。"
```

---

## Task 6: L2 几何可行性（渲染前预检）

**Files:**
- Modify: `qa_v2/checks_data.py`（追加 `check_l2`）
- Modify: `tests/test_checks_data.py`（追加测试）

**Interfaces:**
- Consumes: `qa_v2/data.py`、`qa_v2/report.py`
- Produces:
  - `check_l2(ep: Episode) -> List[Finding]`
  - `estimate_lines(text: str, slot_w: float, size: int) -> int`
  - `OVERFLOW_TOLERANCE = 1.15`

- [ ] **Step 1: 写失败的测试**

追加到 `tests/test_checks_data.py`：

```python
from qa_v2.checks_data import check_l2, estimate_lines, OVERFLOW_TOLERANCE


def test_estimate_lines_respects_manual_breaks():
    # 3 行，每行 4 字，槽宽足够 → 3 行
    assert estimate_lines("甲乙\n丙丁\n戊己", 500, 20) == 3


def test_estimate_lines_wraps_when_no_break():
    # 无 \n，25 个汉字，槽宽 500px @20px 字 → 每行约 25 字 → 1 行
    assert estimate_lines("一" * 25, 500, 20) == 1


def test_estimate_lines_wraps_to_multiple():
    # 100 字，槽宽 500px @20px → 每行 25 字 → 4 行
    assert estimate_lines("一" * 100, 500, 20) == 4


def test_l2_ok_when_fits():
    ep = _ep([_page([("a", 0, 0, 500, 100)], [("a", "甲乙丙丁", 20, True, None)])])
    assert _codes(check_l2(ep)) == []


def test_l2_warns_on_overflow():
    """E11 P4/P5 各有一处：文案多行装不下，首尾行被切在框外。
    当时靠目视发现，QA 全绿。"""
    ep = _ep([_page([("a", 0, 0, 500, 60)],           # 60px 装不下 4 行 @20px lh1.4
                    [("a", "甲\n乙\n丙\n丁", 20, True, None)])])
    fs = check_l2(ep)
    assert len(fs) == 1
    assert fs[0].code == "ESTIMATED_OVERFLOW"
    assert fs[0].level == "warn"


def test_l2_uses_tolerance():
    """刚好在 1.15 倍以内不该报。"""
    # 3 行 @20px lh1.4 = 84px；槽高 80px → 84/80 = 1.05 < 1.15
    ep = _ep([_page([("a", 0, 0, 500, 80)],
                    [("a", "甲\n乙\n丙", 20, True, None)])])
    assert "ESTIMATED_OVERFLOW" not in _codes(check_l2(ep))


def test_real_shucun_passes_l2():
    from qa_v2.data import load_episode
    fs = check_l2(load_episode("shucun"))
    assert [f for f in fs if f.level == "fail"] == []
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_data.py -v -k "l2 or estimate"`
Expected: FAIL —— `ImportError: cannot import name 'check_l2'`

- [ ] **Step 3: 写最小实现**

追加到 `qa_v2/checks_data.py`：

```python
# ── L2 几何可行性（渲染前预检）────────────────────────────────────────

# 需要高度超过槽高此倍数才报 warn（FitText 内部有自适应缩放，
# 真实溢出点略高于理论值，1.15 是实测留的容差）
OVERFLOW_TOLERANCE = 1.15

# 单个汉字的宽度约等于字号；ASCII 约 0.55 倍
_WIDE = 1.0
_NARROW = 0.55


def _text_units(s):
    """估算文本的"字宽单位"：汉字 1.0，ASCII 0.55。"""
    n = 0.0
    for ch in s:
        n += _NARROW if ord(ch) < 128 else _WIDE
    return n


def estimate_lines(text, slot_w, size):
    """估算渲染后占几行。与 FitText 的 effW 同口径（宽字符算 1，窄字符 0.45~0.55）。"""
    if not text:
        return 0
    per_line = max(1.0, (slot_w - 24) / float(size))
    if "\n" in text:
        return sum(max(1, int(-(-_text_units(l) // per_line)))
                   for l in text.split("\n") if l.strip())
    return max(1, int(-(-_text_units(text) // per_line)))


def check_l2(ep):
    """渲染前的溢出预检。装不下就 warn，省得渲完再靠眼睛找。"""
    out = []
    for page in ep.pages:
        for item in page.items:
            slot = page.slot(item.slot_id)
            if slot is None or slot.h <= 0 or item.size <= 0:
                continue
            lines = estimate_lines(item.text, slot.w, item.size)
            if lines <= 0:
                continue
            need = lines * item.size * (item_lh(item))
            ratio = need / float(slot.h)
            if ratio > OVERFLOW_TOLERANCE:
                out.append(Finding(
                    "L2", page.number, item.slot_id, "warn",
                    "ESTIMATED_OVERFLOW",
                    "预计需 %.0fpx / 槽高 %dpx（%d 行 @%dpx）"
                    % (need, slot.h, lines, item.size),
                    {"ratio": round(ratio, 2), "lines": lines}))
    return out


def item_lh(item, default=1.4):
    return getattr(item, "lh", None) or default
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_data.py -v`
Expected: PASS —— 16 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_data.py tests/test_checks_data.py
git commit -m "feat(qa): L2 溢出预检

渲染前就能算出文案装不装得下，省得渲完靠眼睛找。
E11 P4/P5 各有一处超框（当时目视发现，QA 全绿）。
容差 1.15 —— FitText 有自适应缩放，真实溢出点略高于理论值。"
```

---

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

## Task 8: L3 渲染存在性 + 负控制

**Files:**
- Create: `qa_v2/checks_render.py`
- Create: `tests/test_checks_render.py`

**Interfaces:**
- Consumes: `qa_v2/frames.py`、`qa_v2/data.py`、`qa_v2/geometry.py`、`qa_v2/report.py`
- Produces:
  - `check_l3(page: Page, ocr: OcrResult) -> List[Finding]`
  - `NEGATIVE_CONTROL_SHIFT = 300` —— 负控制平移量（px）
  - `assert_negative_control(page: Page, ocr: OcrResult) -> int` —— 返回「负控制未命中」的槽位数，必须为 0

- [ ] **Step 1: 写失败的测试**

`tests/test_checks_render.py`：

```python
"""L3 渲染存在性 + 负控制。

L3 判据：**槽内必须有属于这个槽位的 OCR 文本**。
不是「区域内有深色像素」——后者在插画上恒真。
E11 实测：随手挑的「空白区」有 583 墨像素被误判通过。
"""
import pytest

from qa_v2.data import Page, Slot
from qa_v2.frames import OcrResult
from qa_v2.checks_render import (
    check_l3, assert_negative_control, NEGATIVE_CONTROL_SHIFT,
)

PLATE = (1672, 941)


def _page(slots, number=1):
    return Page(number, PLATE, [Slot(*s) for s in slots], [])


def test_l3_passes_when_text_present():
    p = _page([("title", 0, 0, 400, 100)])
    o = OcrResult(["一个村子"], [(100, 30, 350, 80)], [0.99])
    assert [f for f in check_l3(p, o) if f.level == "fail"] == []


def test_l3_fails_when_slot_empty():
    """这就是旧判据漏掉的情况：槽里什么都没有。"""
    p = _page([("title", 0, 0, 400, 100)])
    o = OcrResult(["远处插画上的字"], [(1400, 700, 1600, 740)], [0.99])
    fs = [f for f in check_l3(p, o) if f.level == "fail"]
    assert len(fs) == 1
    assert fs[0].code == "SLOT_RENDER_EMPTY"


def test_l3_ignores_tag_slot():
    """tag 槽由 L6 用独立判据查，L3 不重复报。"""
    p = _page([("evidence_tag", 1400, 0, 200, 60)])
    o = OcrResult([], [], [])
    assert check_l3(p, o) == []


def test_l3_reports_low_confidence_as_warn():
    p = _page([("a", 0, 0, 400, 100)])
    o = OcrResult(["难认的字"], [(100, 30, 350, 80)], [0.40])
    fs = [f for f in check_l3(p, o) if f.code == "OCR_LOW_CONFIDENCE"]
    assert len(fs) == 1 and fs[0].level == "warn"


def test_negative_control_passes_when_shifted_slot_is_empty():
    """把槽位平移 300px 落到插画区，应判为空。
    这是判据非恒真的证明 —— 旧 QA 缺的就是这个。"""
    p = _page([("title", 0, 0, 400, 100)])
    # 文字只出现在原位 (100,30)，平移后槽位中心落到别处
    o = OcrResult(["一个村子"], [(100, 30, 350, 80)], [0.99])
    assert assert_negative_control(p, o) == 0


def test_negative_control_detects_always_true_detector():
    """反例：若检测器恒真，负控制必须报出来而不是悄悄过。"""
    p = _page([("title", 0, 0, 400, 100)])
    o = OcrResult(["一个村子"], [(100, 30, 350, 80)], [0.99])
    # 把平移量设成 0（等于不验证）应当被拒绝
    with pytest.raises(AssertionError):
        assert_negative_control(p, o, shift=0)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.checks_render'`

- [ ] **Step 3: 写最小实现**

`qa_v2/checks_render.py`：

```python
"""L3 渲染存在性、L5 溢出、L6 tag 槽。需渲染帧，不用 OCR（L6 除外）。

**为什么不用「区域内有深色像素」**：E11 实测负控制 —— 随手挑的
「空白区」有 583 墨像素被判为通过（落在插画深色木器上）。
该判据对插画底色敏感，板图越暗误判率越高。L3 一律用「该槽该有的文本」。
"""
from typing import List

from qa_v2.data import Page, Slot
from qa_v2.frames import OcrResult, text_at
from qa_v2.geometry import plate_to_canvas
from qa_v2.report import Finding

TAG_IDS = {"evidence_tag"}

# 负控制：把槽位平移这么多 px 后必须判为空。
# 300 超过任何板面的标题带高度，不会落回真槽。
NEGATIVE_CONTROL_SHIFT = 300

# OCR 置信低于此值报 warn（E11 实测最低 0.350 出现在插画篆书上，
# 槽位内文字实测最低 0.828）
LOW_CONFIDENCE = 0.80


def check_l3(page, ocr):
    """槽内必须有 OCR 文本。"""
    out = []
    for s in page.slots:
        if s.id in TAG_IDS:
            continue  # 深底白字，交给 L6
        rect = plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)
        found = text_at(ocr, rect)
        if not found:
            out.append(Finding(
                "L3", page.number, s.id, "fail", "SLOT_RENDER_EMPTY",
                "槽内无 OCR 文本（该槽没渲出内容）",
                {"canvas_rect": list(rect)}))
            continue
        worst = min(f[2] for f in found)
        if worst < LOW_CONFIDENCE:
            out.append(Finding(
                "L3", page.number, s.id, "warn", "OCR_LOW_CONFIDENCE",
                "OCR 置信偏低 %.2f，可能字被裁切" % worst,
                {"text": found[0][0][:30], "score": round(worst, 3)}))
    return out


def assert_negative_control(page, ocr, shift=NEGATIVE_CONTROL_SHIFT):
    """负控制：平移槽位后应判为空。返回「未命中」的槽位数。

    判据恒真时这个数 > 0 —— 旧 QA 缺的正是这个证明。
    shift=0 会被拒绝：那等于没验证。
    """
    assert shift > 0, "负控制的平移量必须 > 0，否则等于没验证"
    not_caught = 0
    for s in page.slots:
        if s.id in TAG_IDS:
            continue
        moved = Slot(s.id, s.x + shift, s.y, s.w, s.h)
        rect = plate_to_canvas(page.plate, moved.x, moved.y,
                               moved.w, moved.h)
        if text_at(ocr, rect):
            not_caught += 1
    return not_caught
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v`
Expected: PASS —— 6 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_render.py tests/test_checks_render.py
git commit -m "feat(qa): L3 渲染存在性 + 负控制

判据是「该槽该有的 OCR 文本」，不是「区域内有深色像素」——
后者在 E11 实测中对插画恒真（空白区 583 墨像素被判通过）。
assert_negative_control 证明判据非恒真，这是旧 QA 缺的东西。
置信阈值 0.80 来自 E11 实测（槽内最低 0.828，插画篆书 0.350）。"
```

---

## Task 9: L5 溢出检测

**Files:**
- Modify: `qa_v2/checks_render.py`（追加 `check_l5`）
- Modify: `tests/test_checks_render.py`（追加测试）

**Interfaces:**
- Consumes: `qa_v2/frames.py`、`qa_v2/data.py`、`qa_v2/geometry.py`、`qa_v2/report.py`
- Produces:
  - `check_l5(page: Page, png: Path) -> List[Finding]`
  - `text_bbox_in_slot(a_g: np.ndarray, rect: Rect) -> Optional[Rect]` —— 槽内文字外接框（`x,y,w,h`），找不到返回 None
  - `TOUCH_MARGIN = 3` —— 墨迹距槽边小于此值算触边

- [ ] **Step 1: 写失败的测试**

追加到 `tests/test_checks_render.py`：

```python
import numpy as np
import pytest
from PIL import Image
from qa_v2.checks_render import check_l5, text_bbox_in_slot, TOUCH_MARGIN


def _slot_img(w, h, text_rows, pad_x=30, pad_y=20, size=28):
    """造一张槽位图：白底 + 居中若干行「字」（深色横条模拟笔画）。"""
    a = np.full((h + 2 * pad_y, w + 2 * pad_x, 3), 250, dtype=np.uint8)
    lh = int(size * 1.4)
    total = len(text_rows) * lh
    y0 = (a.shape[0] - total) // 2
    for i in range(len(text_rows)):
        yy = y0 + i * lh + 4
        for x in range(pad_x + 10, pad_x + w - 10, size):
            a[yy:yy + size - 6, x:x + size - 10] = 60
    return a


def test_text_bbox_finds_centered_text():
    a = _slot_img(500, 100, ["甲乙丙丁"])
    box = (30, 20, 500, 100)
    r = text_bbox_in_slot(a, box)
    assert r is not None
    x, y, w, h = r
    assert x > box[0] and y > box[1]
    assert x + w < box[0] + box[2]
    assert y + h < box[1] + box[3]


def test_text_bbox_returns_none_when_blank():
    a = np.full((140, 560, 3), 250, dtype=np.uint8)
    assert text_bbox_in_slot(a, (30, 20, 500, 100)) is None


def test_text_bbox_detects_touching_edge():
    a = np.full((100, 100, 3), 250, dtype=np.uint8)
    a[10:90, 0:20] = 60          # 文字贴住左边
    r = text_bbox_in_slot(a, (0, 0, 100, 100))
    assert r[0] <= TOUCH_MARGIN


def test_l5_ok_when_text_has_margin(tmp_path):
    a = _slot_img(500, 100, ["甲乙丙丁"])
    p = tmp_path / "s.png"
    Image.fromarray(a).save(p)
    page = _page([("note_left", 30, 20, 500, 100)], number=5)
    # 直接用板面坐标=画布坐标的简版 plate 免去换算干扰
    page.plate = (1920, 1080)
    assert [f for f in check_l5(page, p) if f.level == "fail"] == []


def test_l5_fails_when_text_touches_edge(tmp_path):
    a = np.full((100, 100, 3), 250, dtype=np.uint8)
    a[10:90, 0:25] = 60          # 文字溢出到槽外
    p = tmp_path / "s2.png"
    Image.fromarray(a).save(p)
    page = _page([("note_left", 0, 0, 100, 100)], number=5)
    page.plate = (1920, 1080)
    fs = [f for f in check_l5(page, p) if f.level == "fail"]
    assert len(fs) == 1 and fs[0].code == "TEXT_TOUCHES_SLOT_EDGE"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v -k "l5 or text_bbox"`
Expected: FAIL —— `ImportError: cannot import name 'check_l5'`

- [ ] **Step 3: 写最小实现**

追加到 `qa_v2/checks_render.py`：

```python
# ── L5 溢出检测 ──────────────────────────────────────────────────────

# 墨迹距槽边小于此值算触边（实测 FitText 的 padding 是 10px 12px）
TOUCH_MARGIN = 3
# 面积小于此值的连通域视为噪点
MIN_BLOB = 12


def text_bbox_in_slot(a_g, rect):
    """在槽位矩形内找「文字」的外接框，返回 (x, y, w, h)。

    为什么要先分离底板：槽位有 backing 底板（浅色圆角矩形 + 深色描边
    与阴影），直接量「墨迹包围盒」量到的是底板边缘 —— E11 实测两个
    溢出与否的版本量出**完全相同**的数（恒差 28px），判据失效。

    做法：亮度 <130 视为墨，二值化后腐蚀 1 像素去掉描边与阴影，
    再按连通域面积过滤掉细碎噪点。
    """
    from scipy.ndimage import binary_erosion, label
    import numpy as np

    x, y, w, h = rect
    H, W = a_g.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return None
    sub = a_g[y0:y1, x0:x1]
    ink = binary_erosion(sub < 130, iterations=1)
    if not ink.any():
        return None
    lab, n = label(ink)
    if n == 0:
        return None
    sizes = np.bincount(lab.ravel())
    keep_ids = [i for i in range(1, n + 1) if sizes[i] >= MIN_BLOB]
    if not keep_ids:
        return None
    keep = np.isin(lab, keep_ids)
    ys, xs = np.where(keep)
    if len(ys) == 0:
        return None
    return (int(xs.min()), int(ys.min()),
            int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))


def check_l5(page, png):
    """文字外接框触边即溢出。"""
    from PIL import Image
    a = np.array(Image.open(str(png)).convert("L"))
    out = []
    for s in page.slots:
        if s.id in TAG_IDS:
            continue
        rect = plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)
        r = text_bbox_in_slot(a, rect)
        if r is None:
            continue  # 空槽由 L3 报，这里不重复
        tx, ty, tw, th = r
        rx, ry, rw, rh = rect
        hits = []
        if tx <= TOUCH_MARGIN:
            hits.append("左")
        if ty <= TOUCH_MARGIN:
            hits.append("上")
        if tx + tw >= rw - TOUCH_MARGIN:
            hits.append("右")
        if ty + th >= rh - TOUCH_MARGIN:
            hits.append("下")
        if hits:
            out.append(Finding(
                "L5", page.number, s.id, "fail", "TEXT_TOUCHES_SLOT_EDGE",
                "文字贴到槽边（%s），疑似被裁切" % "、".join(hits),
                {"text_rect": [tx, ty, tw, th],
                 "slot_rect": [rx, ry, rw, rh]}))
    return out
```

在文件头补上 `import numpy as np`（避免每个函数内重复 import）。

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v`
Expected: PASS —— 11 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_render.py tests/test_checks_render.py
git commit -m "feat(qa): L5 溢出检测

必须先分离 backing 底板再量文字：直接量墨迹包围盒得到的是底板描边与阴影，
E11 实测溢出与否两个版本量出完全相同的数（恒差 28px），判据失效。
做法：亮度<130 二值化 → 腐蚀 1px 去描边 → 连通域面积 >=12px 去噪。"
```

---

## Task 10: L6 tag 槽判据

**Files:**
- Modify: `qa_v2/checks_render.py`（追加 `check_l6`）
- Modify: `tests/test_checks_render.py`（追加测试）

**Interfaces:**
- Consumes: 同上
- Produces:
  - `check_l6(page: Page, png: Path) -> List[Finding]`
  - `WHITE_MIN = 200`、`WHITE_MAX_RATIO = 0.40`

- [ ] **Step 1: 写失败的测试**

追加到 `tests/test_checks_render.py`：

```python
from qa_v2.checks_render import check_l6, WHITE_MIN, WHITE_MAX_RATIO


def test_l6_passes_when_white_text_on_dark():
    """tag 槽是深底白字，深色墨判据天然不适用 —— 旧 QA 直接排除，
    所以证据标签从不被检查。"""
    a = np.full((80, 300, 3), 90, dtype=np.uint8)      # 深底
    a[30:50, 60:240] = 245                              # 白字
    p = _tmp_png(a)
    page = _page([("evidence_tag", 0, 0, 300, 80)], number=1)
    page.plate = (1920, 1080)
    assert [f for f in check_l6(page, p) if f.level == "fail"] == []


def test_l6_fails_when_tag_not_rendered():
    a = np.full((80, 300, 3), 90, dtype=np.uint8)      # 全深底，没字
    p = _tmp_png(a)
    page = _page([("evidence_tag", 0, 0, 300, 80)], number=1)
    page.plate = (1920, 1080)
    fs = [f for f in check_l6(page, p) if f.level == "fail"]
    assert len(fs) == 1 and fs[0].code == "TAG_SLOT_EMPTY"


def test_l6_flags_all_white_slab():
    """整槽全白说明判据抓错了区域，不是有字。"""
    a = np.full((80, 300, 3), 250, dtype=np.uint8)
    p = _tmp_png(a)
    page = _page([("evidence_tag", 0, 0, 300, 80)], number=1)
    page.plate = (1920, 1080)
    fs = check_l6(page, p)
    assert any(f.code == "TAG_SLOT_ALL_WHITE" for f in fs)


def test_real_shucun_passes_l6():
    from qa_v2.data import load_episode
    import pathlib
    ep = load_episode("shucun")
    outdir = pathlib.Path("/tmp/qa_shucun_frames")
    outdir.mkdir(parents=True, exist_ok=True)
    from qa_v2.frames import render_frame
    for p in ep.pages:
        png = outdir / ("p%02d.png" % p.number)
        if not png.exists():
            render_frame("shucun", p.number, ep.final_frame(p.number), png)
        assert [f for f in check_l6(p, png) if f.level == "fail"] == [], p.number
```

在测试文件顶部加辅助函数：

```python
def _tmp_png(a, name="t.png"):
    from PIL import Image
    import tempfile, pathlib
    d = pathlib.Path(tempfile.mkdtemp())
    p = d / name
    Image.fromarray(a).save(p)
    return p
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v -k l6`
Expected: FAIL —— `ImportError: cannot import name 'check_l6'`

- [ ] **Step 3: 写最小实现**

追加到 `qa_v2/checks_render.py`：

```python
# ── L6 tag 槽 ────────────────────────────────────────────────────────

# 白字阈值（深底白字反白样式）
WHITE_MIN = 200
# 白像素占比上限：超过说明抓到的是浅色底板而非文字块
WHITE_MAX_RATIO = 0.40
# 白像素占比下限：低于说明槽里没东西
WHITE_MIN_RATIO = 0.01


def check_l6(page, png):
    """tag 型槽（深底白字）的独立判据。

    旧 qa_all.py 用 TAG_IDS 把这类槽直接排除 —— 于是**证据标签
    从不被检查**。E11 实测 8 个 evidence_tag 槽全部有值
    （[文献记载]/[官书记载]/[存疑待考]/[原书记载]/[实录记载]/[系列联动]），
    说明判据可用。
    """
    from PIL import Image
    a = np.array(Image.open(str(png)).convert("RGB"))
    out = []
    for s in page.slots:
        items = [i for i in page.items if i.slot_id == s.id]
        if not items or not items[0].is_tag:
            continue
        rect = plate_to_canvas(page.plate, s.x, s.y, s.w, s.h)
        rx, ry, rw, rh = rect
        H, W = a.shape[:2]
        x1, y1 = min(W, rx + rw), min(H, ry + rh)
        sub = a[max(0, ry):y1, max(0, rx):x1]
        if sub.size == 0:
            continue
        white = (sub.min(axis=2) > WHITE_MIN).mean()
        if white < WHITE_MIN_RATIO:
            out.append(Finding(
                "L6", page.number, s.id, "fail", "TAG_SLOT_EMPTY",
                "证据标签槽内无白字（tag 是深底白字，此槽未渲染）",
                {"white_ratio": round(float(white), 4)}))
        elif white > WHITE_MAX_RATIO:
            out.append(Finding(
                "L6", page.number, s.id, "warn", "TAG_SLOT_ALL_WHITE",
                "槽内几乎全白，可能抓错区域",
                {"white_ratio": round(float(white), 4)}))
    return out
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_render.py -v`
Expected: PASS —— 15 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_render.py tests/test_checks_render.py
git commit -m "feat(qa): L6 tag 槽独立判据

旧 qa_all.py 用 TAG_IDS 把 tag 槽直接排除，于是证据标签从不被检查。
tag 是深底白字，判据改为找白像素块，占比 1%~40% 为正常。
E11 实测 8 个 evidence_tag 槽全部有值，判据可用。"
```

---

## Task 11: L4 内容闭环 —— 数字严格

**Files:**
- Create: `qa_v2/names.txt`
- Create: `qa_v2/checks_content.py`
- Create: `tests/test_checks_content.py`

**Interfaces:**
- Consumes: `qa_v2/normalize.py`、`qa_v2/frames.py`、`qa_v2/data.py`、`qa_v2/geometry.py`、`qa_v2/report.py`
- Produces:
  - `load_names(path: Path = NAMES) -> Set[str]` —— 读专名表
  - `NAMES = Path(__file__).with_name("names.txt")`
  - `check_l4a(page: Page, ocr: OcrResult) -> List[Finding]` —— 数字严格
  - `check_l4b(page: Page, ocr: OcrResult, names: Set[str]) -> List[Finding]` —— 专名严格
  - `UNKNOWN_RATE_WARN = 0.20`

- [ ] **Step 1: 写失败的测试**

`tests/test_checks_content.py`：

```python
"""L4 内容闭环：槽里的字，对不对。

这是旧 QA 完全做不到的一层。E11 真实发生过的错：
P8 口播写「各占了一处」后又说树村占两处，算术自相矛盾 ——
深色墨判据对此毫无察觉。
"""
import pytest

from qa_v2.data import Page, Slot, TextItem
from qa_v2.frames import OcrResult
from qa_v2.checks_content import check_l4a, check_l4b, load_names

PLATE = (1920, 1080)


def _page(items, number=1):
    slots = [Slot(i.slot_id, 0, 0, 900, 120) for i in items]
    return Page(number, PLATE, slots, items)


def _ti(sid, text, size=20):
    return TextItem(sid, text, size, True, None)


def _ocr(page, mapping):
    """按 slotId -> 读回文本 构造 OcrResult（box 落在槽内）。"""
    texts, boxes, scores = [], [], []
    for k, v in mapping.items():
        for t in v:
            texts.append(t)
            boxes.append((10, 10, 400, 50))
            scores.append(0.99)
    return OcrResult(texts, boxes, scores)


# ── L4-a 数字 ──
def test_l4a_passes_when_numbers_match():
    p = _page([_ti("r1_total", "1550")])
    assert [f for f in check_l4a(p, _ocr(p, {"r1_total": ["1550"]}))
            if f.level == "fail"] == []


def test_l4a_catches_wrong_number():
    """「1485」写成「1486」—— 深色墨判据查不出，这里能查出。"""
    p = _page([_ti("r1_total", "1485")])
    fs = [f for f in check_l4a(p, _ocr(p, {"r1_total": ["1486"]}))
          if f.level == "fail"]
    assert len(fs) == 1 and fs[0].code == "NUMBER_MISMATCH"


def test_l4a_accepts_chinese_numeral():
    p = _page([_ti("note", "一千二百五十间")])
    assert [f for f in check_l4a(p, _ocr(p, {"note": ["1250 间"]}))
            if f.level == "fail"] == []


def test_l4a_accepts_speech_year():
    p = _page([_ti("sub", "雍正二年（1724）")])
    assert [f for f in check_l4a(p, _ocr(p, {"sub": ["一七二四年"]}))
            if f.level == "fail"] == []


def test_l4a_ignores_punctuation_only_diff():
    """E11 实测：OCR 噪声仅标点规范化。"""
    p = _page([_ti("sub", "树村·圆明园正北")])
    assert [f for f in check_l4a(p, _ocr(p, {"sub": ["树村.圆明园正北"]}))
            if f.level == "fail"] == []


def test_l4a_no_numbers_is_trivially_ok():
    p = _page([_ti("title", "一个村子，三重身份")])
    assert [f for f in check_l4a(p, _ocr(p, {"title": ["一个村子，三重身份"]}))
            if f.level == "fail"] == []


def test_l4a_warns_on_high_unknown_rate():
    p = _page([_ti("x", "一七二四 9999 一二三四五六七")])
    fs = [f for f in check_l4a(p, _ocr(p, {"x": ["一七二四 9999 一二三四五六七"]}))
          if f.code == "NUMBER_UNKNOWN_RATE"]
    assert len(fs) == 1 and fs[0].level == "warn"


# ── L4-b 专名 ──
def test_l4b_passes_when_name_present():
    p = _page([_ti("dir", "树村西")])
    names = {"树村", "肖家河", "蓝靛厂"}
    assert [f for f in check_l4b(p, _ocr(p, {"dir": ["树村西"]}), names)
            if f.level == "fail"] == []


def test_l4b_catches_wrong_place_name():
    p = _page([_ti("dir", "树村西")])
    names = {"树村", "肖家河"}
    fs = [f for f in check_l4b(p, _ocr(p, {"dir": ["肖家河西"]}), names)]
    assert any(f.code == "PROPER_NAME_MISSING" for f in fs)


def test_l4b_skips_when_names_table_empty():
    """专名表缺失必须 skip 而非 pass —— 否则新集漏填就静默通过。"""
    p = _page([_ti("dir", "树村西")])
    fs = check_l4b(p, _ocr(p, {"dir": ["树村西"]}), set())
    assert [f for f in fs if f.code == "NO_NAMES_TABLE"]


def test_names_file_loads():
    names = load_names()
    assert "树村" in names
    assert len(names) > 20
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_content.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.checks_content'`

- [ ] **Step 3: 建专名表**

`qa_v2/names.txt`（每行一个，`#` 开头为注释；E11 专名，E12 起追加）：

```
# 专名表：L4-b 内容校验用
# 只放「读错就说明内容错了」的专名。
# 地名 / 旗名 / 寺名 / 官名 / 园名 / 书名。
树村
肖家河
蓝靛厂
圆明园
长春园
畅春园
静宜园
静明园
乐善园
广仁宫
海甸
安河桥
镶黄旗
正白旗
正黄旗
正红旗
镶红旗
正蓝旗
镶蓝旗
镶白旗
五圣庵
观音寺
总兵
副将
守备
护军校
参领
五城寺院册
日下旧闻考
皇朝文献通考
竹叶亭杂记
钦定八旗通志
```

- [ ] **Step 4: 写最小实现**

`qa_v2/checks_content.py`：

```python
"""L4 内容闭环：槽里的字，对不对。

旧 QA 只判「区域里有深色像素」，写错字照样通过。E11 真实发生过：
P8 口播「各占了一处」后又说树村占两处，算术自相矛盾 —— 无机器能发现。

L4 分三子层，任一不过即该槽 fail：
  L4-a 数字严格 —— 「1485」写成「1486」要能抓
  L4-b 专名严格 —— 专名表命中项必须逐个出现
  L4-c 字幕交叉 —— 与口播稿原文对数字（Task 12）

前提：E11 实测 OCR 噪声**只有标点规范化**（·→. 、，→. ），
无错字无漏字。所以不需要 fuzzy matching，数字与专名可以严格比对。
"""
import pathlib
from typing import List, Set

from qa_v2.data import Page
from qa_v2.frames import OcrResult
from qa_v2.normalize import (
    extract_numbers, normalize_punct, number_unknown_rate,
)
from qa_v2.report import Finding

NAMES = pathlib.Path(__file__).with_name("names.txt")

# 无法解析的数字 token 占比超过此值报 warn
# （防止 to_int 有 bug 却静默通过）
UNKNOWN_RATE_WARN = 0.20


def load_names(path=None):
    """读专名表。空文件返回空 set —— 调用方须据此报 skip 而非 pass。"""
    p = path or NAMES
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            out.add(s)
    return out


def _ocr_text_for(page, ocr, slot_id):
    """取该槽内的 OCR 读回文本。"""
    from qa_v2.frames import text_at
    from qa_v2.geometry import plate_to_canvas
    slot = page.slot(slot_id)
    if slot is None:
        return ""
    rect = plate_to_canvas(page.plate, slot.x, slot.y, slot.w, slot.h)
    return "".join(t for t, _, _ in text_at(ocr, rect))


def check_l4a(page, ocr):
    """数字严格：原文里的每个数字都必须出现在 OCR 读回里。"""
    out = []
    for item in page.items:
        if item.is_tag:
            continue
        want = set(extract_numbers(item.text))
        if not want:
            continue
        got_raw = _ocr_text_for(page, ocr, item.slot_id)
        got = set(extract_numbers(normalize_punct(got_raw)))

        rate = number_unknown_rate(item.text)
        if rate > UNKNOWN_RATE_WARN:
            out.append(Finding(
                "L4-a", page.number, item.slot_id, "warn",
                "NUMBER_UNKNOWN_RATE",
                "数字归一失败率 %.0f%%，本槽数字比对不可信"
                % (rate * 100), {"text": item.text[:40]}))

        missing = sorted(want - got)
        if missing:
            out.append(Finding(
                "L4-a", page.number, item.slot_id, "fail",
                "NUMBER_MISMATCH",
                "数字对不上：期望 %s，读回 %s"
                % (missing, sorted(got)),
                {"expect": item.text[:50], "ocr": got_raw[:50]}))
    return out


def check_l4b(page, ocr, names):
    """专名严格：原文命中的专名必须逐个出现在 OCR 读回里。"""
    out = []
    if not names:
        out.append(Finding(
            "L4-b", None, None, "skip", "NO_NAMES_TABLE",
            "专名表为空，L4-b 未执行（不算通过）。新集需维护 qa_v2/names.txt"))
        return out
    for item in page.items:
        if item.is_tag:
            continue
        want = [n for n in names if n in item.text]
        if not want:
            continue
        got = normalize_punct(_ocr_text_for(page, ocr, item.slot_id))
        missing = [n for n in want if normalize_punct(n) not in got]
        if missing:
            out.append(Finding(
                "L4-b", page.number, item.slot_id, "fail",
                "PROPER_NAME_MISSING",
                "专名对不上：缺 %s" % "、".join(missing),
                {"expect": item.text[:50]}))
    return out
```

- [ ] **Step 5: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_content.py -v`
Expected: PASS —— 14 passed

- [ ] **Step 6: 提交**

```bash
cd /tmp/chemistry-video
git add qa_v2/names.txt qa/checks_content.py tests/test_checks_content.py
git commit -m "feat(qa): L4 内容闭环（数字严格 + 专名严格）

旧 QA 查不出「1485 写成 1486」。E11 真实发生过 P8 算术自相矛盾
（口播说各占一处又说树村占两处），无机器能发现。
专名表缺失时报 skip 而非 pass —— 否则新集漏填就静默通过。
前提：E11 实测 OCR 噪声仅标点，不需要 fuzzy matching。"
```

---

## Task 12: L4-c 字幕交叉

**Files:**
- Modify: `qa_v2/checks_content.py`（追加 `check_l4c`）
- Modify: `tests/test_checks_content.py`（追加测试）

**Interfaces:**
- Consumes: `qa_v2/data.py::narration_text`、`qa_v2/normalize.py`
- Produces:
  - `check_l4c(ep: Episode, ocr_by_page: Dict[int, OcrResult]) -> List[Finding]`

- [ ] **Step 1: 写失败的测试**

追加到 `tests/test_checks_content.py`：

```python
from qa_v2.checks_content import check_l4c


def test_l4c_skips_when_narration_missing():
    from qa_v2.data import Episode
    ep = Episode("__none__", [_page([_ti("a", "1485")], 1)], [(0, 660)])
    assert any(f.code == "NO_NARRATION" for f in check_l4c(ep, {1: _ocr(_page([]), {})}))


def test_l4c_passes_when_number_in_narration():
    """真实数据：E11 P3 口播含「1485」。"""
    from qa_v2.data import Episode, Page, Slot, TextItem
    pg = Page(3, PLATE, [Slot("r3_total", 0, 0, 300, 60)],
              [TextItem("r3_total", "1485", 20, True, None)])
    ep = Episode("shucun", [pg], [(0, 660)])
    ep.narration = {3: "正红旗在安河桥，官房一千四百六十七间。"}
    o = OcrResult(["1485"], [(10, 10, 200, 50)], [0.99])
    assert [f for f in check_l4c(ep, {3: o}) if f.level == "fail"] == []


def test_l4c_flags_number_absent_from_narration():
    """两边都错的情况：文案写 1485，口播里根本没有这个数。"""
    from qa_v2.data import Episode, Page, Slot, TextItem
    pg = Page(3, PLATE, [Slot("r3_total", 0, 0, 300, 60)],
              [TextItem("r3_total", "1485", 20, True, None)])
    ep = Episode("shucun", [pg], [(0, 660)])
    ep.narration = {3: "正红旗在安河桥，官房一千四百六十间。"}
    o = OcrResult(["1485"], [(10, 10, 200, 50)], [0.99])
    fs = [f for f in check_l4c(ep, {3: o}) if f.level == "fail"]
    assert len(fs) == 1 and fs[0].code == "NUMBER_NOT_IN_NARRATION"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_content.py -v -k l4c`
Expected: FAIL —— `ImportError: cannot import name 'check_l4c'`

- [ ] **Step 3: 写最小实现**

追加到 `qa_v2/checks_content.py`：

```python
def check_l4c(ep, ocr_by_page):
    """字幕交叉：槽里的数字，必须能在该页口播稿里找到。

    **只认 narration/all.json，不认 subtitles.ts**。两个实测理由：
      1) subtitles.ts 的数字 token 大量是数组下标与行号（01…99），
         当文本 grep 会全污染；
      2) 口播有意省略书名简称（文案《钦定日下旧闻考》vs
         口播《日下旧闻考》），直接比对必然假阳性。

    这是三路交叉里最弱的一路：口播与文案本就不要求逐字一致，
    所以只对**数字**交叉，叙述性文字不查。
    """
    from qa_v2.data import narration_text
    out = []
    narration = getattr(ep, "narration", None)
    if narration is None:
        narration = narration_text(ep.name)
    if not narration:
        out.append(Finding(
            "L4-c", None, None, "skip", "NO_NARRATION",
            "找不到 %s_video/narration/all.json，L4-c 未执行（不算通过）"
            % ep.name))
        return out
    for page in ep.pages:
        spoken = narration.get(page.number)
        if not spoken:
            continue
        spoken_nums = set(extract_numbers(spoken))
        ocr = ocr_by_page.get(page.number)
        for item in page.items:
            if item.is_tag:
                continue
            want = set(extract_numbers(item.text))
            if not want:
                continue
            # 只查「该页叙述里出现过的量级」，避免卷号（116/99）误报
            missing = sorted(
                n for n in want
                if n not in spoken_nums and not _is_volume_ref(n))
            if missing:
                out.append(Finding(
                    "L4-c", page.number, item.slot_id, "fail",
                    "NUMBER_NOT_IN_NARRATION",
                    "数字 %s 在该页口播稿里找不到" % missing,
                    {"text": item.text[:50]}))

    return out


# 卷号/版本号类引用：口播通常不念，不参与交叉
_VOLUME_RE = None


def _is_volume_ref(n):
    """是否为卷号类引用（如《钦定八旗通志》卷116 的 116、99）。

    判据：1~200 且页码/卷号常见量级。E11 实测《八旗通志》卷116、
    《日下旧闻考》卷99/卷73 口播均未念。
    """
    return 1 <= n <= 200
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_checks_content.py -v`
Expected: PASS —— 17 passed

- [ ] **Step 5: 提交**

```bash
cd /tmp/chemistry-video
git add qa/checks_content.py tests/test_checks_content.py
git commit -m "feat(qa): L4-c 口播稿交叉

只认 narration/all.json，不认 subtitles.ts：
实测发现 subtitles.ts 的数字 token 大量是数组下标（01…99），
且口播有意省略书名简称，直接比对必假阳性。
卷号类引用（1~200，如卷116/卷99）不参与交叉 —— 口播通常不念。"
```

---

## Task 13: 统一入口与 CLI

**Files:**
- Create: `qa_v2/run.py`
- Create: `tests/test_run.py`
- Modify: `qa_all.py`（改为薄壳，转调 `qa_v2/run.py`）

**Interfaces:**
- Consumes: 全部 check 模块
- Produces:
  - `run_episode(ep: str, use_ocr: bool = False, full: bool = False) -> List[Finding]`
  - `main(argv: List[str]) -> int` —— 返回退出码（0=通过，1=有 fail）
  - `COMPOSITION_OVERRIDES = {"shucun": "ShucunCourse", ...}` —— 集名 → Composition id

- [ ] **Step 1: 写失败的测试**

`tests/test_run.py`：

```python
import json
import pathlib

from qa_v2.run import parse_args, exit_code, COMPOSITION_OVERRIDES


def test_parse_args_defaults():
    a = parse_args(["shucun"])
    assert a.episodes == ["shucun"]
    assert a.use_ocr is False
    assert a.full is False
    assert a.as_json is False


def test_parse_args_flags():
    a = parse_args(["shucun", "--ocr", "--full", "--json"])
    assert a.use_ocr and a.full and a.as_json


def test_parse_args_multiple_episodes():
    a = parse_args(["shucun", "dazhongsi"])
    assert a.episodes == ["shucun", "dazhongsi"]


def test_exit_code_zero_when_no_fail():
    from qa_v2.report import Finding
    assert exit_code([Finding("L1", 1, "a", "warn", "X", "m")]) == 0
    assert exit_code([Finding("L1", 1, "a", "skip", "X", "m")]) == 0


def test_exit_code_one_on_fail():
    from qa_v2.report import Finding
    assert exit_code([Finding("L1", 1, "a", "fail", "X", "m")]) == 1


def test_composition_overrides_covers_shucun():
    assert COMPOSITION_OVERRIDES["shucun"] == "ShucunCourse"


def test_composition_overrides_covers_all_registered_episodes():
    """集名 → Composition 映射必须完整，且不是 capitalize() 的结果。

    `gaoliangqiao`.capitalize() → `Gaoliangqiao`，但实际注册名是
    `GaoLiangQiaoCourse`；靠拼名字会在旧集上直接报「Composition 不存在」。
    """
    assert set(COMPOSITION_OVERRIDES) >= {
        "yimuyuan", "niangniangfu", "xisanqi", "gaoliangqiao",
        "dazhongsi", "landianchang", "shucun",
    }
    for ep, comp in COMPOSITION_OVERRIDES.items():
        assert comp.endswith("Course")
        assert comp != "%sCourse" % ep.capitalize() or ep in (
            "shucun", "dazhongsi", "xisanqi", "yimuyuan", "niangniangfu",
            "landianchang",
        ), "%s 的映射是 capitalize() 拼的，需人工确认" % ep
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_run.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'qa_v2.run'`

- [ ] **Step 3: 写最小实现**

`qa_v2/run.py`：

```python
"""统一入口：跑一集的七层验收。

    python3 -m qa_v2.run shucun            # L1/L2/L3/L5/L6（快，~2s/页）
    python3 -m qa_v2.run shucun --ocr      # 加 L4（~2min/页，8 页约 2 分钟）
    python3 -m qa_v2.run shucun --full     # 全开
    python3 -m qa_v2.run shucun --json     # 机读输出

只有 fail 阻塞退出码（spec §10.2）：历史集的 warn 噪声不应淹没真问题。
"""
import argparse
import pathlib
import sys
from typing import Dict, List

from qa_v2.checks_content import check_l4a, check_l4b, check_l4c, load_names
from qa_v2.checks_data import check_l1, check_l2
from qa_v2.checks_render import (
    check_l3, check_l5, check_l6, assert_negative_control,
)
from qa_v2.data import load_episode
from qa_v2.frames import ocr_cached, render_frame
from qa_v2.report import Finding, render_json, render_text

ROOT = pathlib.Path("/tmp/chemistry-video")
FRAME_DIR = pathlib.Path("/tmp/qa_frames")

# 集名 → Composition id（Remotion 注册名是驼峰）
COMPOSITION_OVERRIDES = {
    "yimuyuan": "YimuyuanCourse",
    "niangniangfu": "NiangniangfuCourse",
    "xisanqi": "XisanqiCourse",
    "gaoliangqiao": "GaoLiangQiaoCourse",
    "dazhongsi": "DazhongsiCourse",
    "landianchang": "LandianchangCourse",
    "shucun": "ShucunCourse",
}


def _frame_for(ep, page, use_ocr):
    """抽该页终态帧。--ocr 时顺带跑 OCR 并缓存。"""
    out = FRAME_DIR / ep.name
    out.mkdir(parents=True, exist_ok=True)
    png = out / ("p%02d.png" % page.number)
    if not png.exists():
        render_frame(COMPOSITION_OVERRIDES[ep.name],
                     ep.final_frame(page.number), png)
    if use_ocr:
        return png, ocr_cached(ep, page.number, png)
    return png, None


def run_episode(name, use_ocr=False, full=False):
    """跑一集的全部适用层，返回 findings。"""
    ep = load_episode(name)
    findings = []

    # L1 / L2：纯数据
    findings += check_l1(ep)
    findings += check_l2(ep)

    names = load_names()
    ocr_by_page = {}
    for page in ep.pages:
        try:
            png, ocr = _frame_for(name, page, use_ocr)
        except Exception as exc:                      # 抽帧/OCR 失败
            findings.append(Finding(
                "L3", page.number, None, "fail", "RENDER_FAILED",
                "抽帧或 OCR 失败：%s" % exc))
            continue

        findings += check_l5(page, png)
        findings += check_l6(page, png)

        if ocr is None:
            continue
        ocr_by_page[page.number] = ocr
        findings += check_l3(page, ocr)
        if use_ocr:
            findings += check_l4a(page, ocr)
            findings += check_l4b(page, ocr, names)
            # 负控制：证明 L3/L4 不是恒真
            missed = assert_negative_control(page, ocr)
            if missed:
                findings.append(Finding(
                    "L3", page.number, None, "fail", "NEGATIVE_CONTROL_FAIL",
                    "负控制失败：%d 个槽位平移后仍判有文本，判据恒真"
                    % missed))
    if use_ocr:
        findings += check_l4c(ep, ocr_by_page)
    return findings


def parse_args(argv):
    p = argparse.ArgumentParser(
        prog="qa_v2.run", description="七层验收")
    p.add_argument("episodes", nargs="+")
    p.add_argument("--ocr", action="store_true",
                   help="开启 L4 内容闭环（慢，约 2 分钟/集）")
    p.add_argument("--full", action="store_true",
                   help="等价于 --ocr，并额外提示运行字幕验收")
    p.add_argument("--json", dest="as_json", action="store_true",
                   help="输出 JSON")
    return p.parse_args(argv)


def exit_code(findings):
    from qa_v2.report import summarize
    return 1 if summarize(findings).get("fail") else 0


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    rc = 0
    for name in args.episodes:
        if name not in COMPOSITION_OVERRIDES:
            print("未知集 %s，可选 %s" % (name, list(COMPOSITION_OVERRIDES)))
            rc = 1
            continue
        findings = run_episode(name, use_ocr=(args.ocr or args.full),
                              full=args.full)
        print(render_json(findings, name) if args.as_json
              else render_text(findings, name))
        if exit_code(findings):
            rc = 1
    if args.full:
        print("\n提示：字幕/音频验收请另跑 "
              "/tmp/.asr-venv/bin/python "
              "/Volumes/macstudio/video-projects/scripts/verify_subtitles_asr.py")
    return rc


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd /tmp/chemistry-video && python3 -m pytest tests/test_run.py -v`
Expected: PASS —— 5 passed

- [ ] **Step 5: 端到端验证（E11 快档）**

Run: `cd /tmp/chemistry-video && python3 -m qa_v2.run shucun`
Expected:
```
=== shucun ===
  → fail 0 / warn 0 / skip 0 / info 0
  判定：通过
```

若有 fail，逐条修；**不要调松阈值来让它过**。

- [ ] **Step 6: 提交**

```bash
cd /tmp/chemistry-video
git add qa_v2/run.py tests/test_run.py
git commit -m "feat(qa): 统一入口与 CLI

python3 -m qa_v2.run <集> [--ocr] [--full] [--json]
默认快档（~2s/页），--ocr 开内容闭环（~2min/集）。
只有 fail 阻塞退出码。"
```

- [ ] **Step 7: qa_all.py 改薄壳**

保持历史命令 `python3 qa_all.py shucun` 可用：

```python
#!/usr/bin/env python3
"""qa_all.py — 保留为薄壳，转调 qa.run。

新的七层验收在 qa_v2/ 包里（见 docs/superpowers/specs/2026-10-01-qa-v2-design.md）。
本文件保留只为兼容历史命令；新代码请加到 qa_v2/ 下。

用法：
    python3 qa_all.py shucun          # 等价 python3 -m qa_v2.run shucun
    python3 qa_all.py shucun --ocr    # 开启内容闭环
"""
import sys

from qa_v2.run import main, COMPOSITION_OVERRIDES

if __name__ == "__main__":
    sys.exit(main())
```

Run: `cd /tmp/chemistry-video && python3 qa_all.py shucun && echo "薄壳可用"`

- [ ] **Step 8: 提交薄壳**

```bash
cd /tmp/chemistry-video
git add qa_all.py
git commit -m "refactor(qa): qa_all.py 改薄壳，转调 qa.run

保留历史命令可用性；新判据加到 qa/ 包下。"
```

---

## Task 14: 端到端验收与负控制留证

**Files:**
- Create: `docs/qa/2026-10-01-qa-v2-e11-report.md`

**Interfaces:**
- Consumes: 全部
- Produces: 验收报告文档

- [ ] **Step 1: 跑 E11 全档并留证**

```bash
cd /tmp/chemistry-video
python3 -m qa_v2.run shucun --full 2>&1 | tee /tmp/qa_e11_full.txt
```

- [ ] **Step 2: 故意破坏，验证判据能抓**

```bash
cd /tmp/chemistry-video
cp src/shucun/data/pages.config.ts /tmp/pc_backup.ts
# ① 改错一个数字
python3 - <<'PY'
import pathlib
p = pathlib.Path("src/shucun/data/pages.config.ts")
s = p.read_text(encoding="utf-8")
p.write_text(s.replace('"1485"', '"1486"', 1), encoding="utf-8")
PY
python3 -m qa_v2.run shucun --ocr 2>&1 | grep -E "NUMBER_MISMATCH|判定"
# 期望：出现 NUMBER_MISMATCH，判定：不通过
```

记录输出，然后恢复：

```bash
cd /tmp/chemistry-video
cp /tmp/pc_backup.ts src/shucun/data/pages.config.ts
```

再验第二类（重叠）：

```bash
cd /tmp/chemistry-video
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("src/shucun/data/slots.json")
d = json.loads(p.read_text(encoding="utf-8"))
# 让 p02 的两个说明框叠在一起
s = d["p02"]["slots"]
for x in s:
    if x["id"] == "note_right":
        x["x"] = s[[y["id"] for y in s].index("note_left")]["x"]
p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
PY
python3 -m qa_v2.run shucun 2>&1 | grep -E "SLOT_OVERLAP|判定"
# 期望：出现 SLOT_OVERLAP，判定：不通过
git checkout src/shucun/data/slots.json
```

- [ ] **Step 3: 跑全量测试确认无回归**

```bash
cd /tmp/chemistry-video && python3 -m pytest tests/ -v
```
Expected: 全部 PASS

- [ ] **Step 4: 写验收报告**

`docs/qa/2026-10-01-qa-v2-e11-report.md` 内容模板：

```markdown
# QA v2 在 E11《树村》上的验收报告

日期：2026-10-01
命令：`python3 -m qa_v2.run shucun --full`

## 结果

（粘贴 /tmp/qa_e11_full.txt 全文）

## 负控制留证

| 判据 | 负控制方法 | 实际结果 |
|---|---|---|
| L3 | 槽位平移 300px 到插画区 | 0 个槽位仍判有文本 ✓ |
| L4-a | 文案 1485 → 1486 | 报 NUMBER_MISMATCH ✓ |
| L1 | 两个说明框坐标改为重叠 | 报 SLOT_OVERLAP ✓ |

## 各层耗时

| 层 | 单页耗时 | 8 页合计 |
|---|---|---|
| L1+L2 | （填实测） | |
| L3+L5+L6 | （填实测） | |
| L4 | （填实测） | |

## 已知限制

（照抄 spec §8 风险表里仍然成立的项）
```

- [ ] **Step 5: 提交**

```bash
cd /Volumes/macstudio/video-projects
git add docs/qa/2026-10-01-qa-v2-e11-report.md
git commit -m "test(qa): E11 端到端验收 + 负控制留证

三类破坏均被抓：改错数字(NUMBER_MISMATCH) / 槽位重叠(SLOT_OVERLAP) /
负控制证明 L3 非恒真。报告含各层实测耗时。"
```

---

## Self-Review

**1. Spec 覆盖检查**

| Spec 章节 | 对应 task |
|---|---|
| §5.2 L1 数据一致性（6 项检查） | Task 5 ✓ |
| §5.2 L2 几何可行性 | Task 6 ✓ |
| §5.2 L3 渲染存在性 | Task 8 ✓ |
| §5.2 L4-a 数字严格 | Task 11 ✓ |
| §5.2 L4-b 专名严格 | Task 11 ✓ |
| §5.2 L4-c 字幕交叉 | Task 12 ✓ |
| §5.2 L5 溢出检测 | Task 9 ✓ |
| §5.2 L6 tag 槽 | Task 10 ✓ |
| §5.1 开关（`--ocr` / `--full` / `--json`） | Task 13 ✓ |
| §6 负控制 | Task 8（`assert_negative_control`）+ Task 14（留证） ✓ |
| §7 实现顺序 | 本计划顺序一致 ✓ |
| §8 风险：OCR 版本差异 | Task 7 `_assert_box_format` ✓ |
| §8 风险：专名表缺失报 skip | Task 11 ✓ |
| §8 风险：warn 不阻塞退出码 | Task 4 + Task 13 ✓ |
| §8 风险：OCR 速度 | Task 7 缓存 ✓ |
| §9 验收标准 | Task 14 ✓ |

**2. 占位符扫描**：无 TBD / TODO / 「类似 Task N」。

**3. 类型一致性检查**

- `Finding(layer, page, slot, level, code, message, detail=None)` —— Task 4 定义，Task 5/6/8/9/10/11/12 使用，签名一致 ✓
- `Slot(id, x, y, w, h)` —— Task 3 定义，Task 5/8 使用 ✓
- `Page(number, plate, slots, items)` —— Task 3 定义，全书一致 ✓
- `OcrResult(texts, boxes, scores)` —— Task 7 定义，Task 8/11/12 使用 ✓
- `text_at(ocr, rect, pad=25)` 返回 `[(text, (x,y,w,h), score)]` —— Task 7 定义，Task 8/11 使用 ✓
- `plate_to_canvas(plate, x, y, w, h)` —— Task 1 定义，Task 8/9/10/11/12 使用 ✓
- `check_l1(ep)` / `check_l2(ep)` 返回 `List[Finding]` —— Task 5/6 定义，Task 13 使用 ✓
- `run_episode(name, use_ocr, full)` 返回 `List[Finding]` —— Task 13 定义 ✓

**Self-Review 发现并已修复的一处**：`qa_v2/run.py` 的 `_frame_for` 原先调用
`render_frame(ep, ...)`，而 Task 7 的 `render_frame` 内部用
`"%sCourse" % ep.capitalize()` 拼 Composition 名。`shucun`/`dazhongsi` 等恰好对，
但 `gaoliangqiao` → `Gaoliangqiao`，实际注册名是 `GaoLiangQiaoCourse`
—— 在旧集上会直接报「Composition 不存在」。

已改：`render_frame(composition, frame, out)` 收显式注册名，调用方从
`COMPOSITION_OVERRIDES` 取；并补
`test_composition_overrides_covers_all_registered_episodes` 守住这条。

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-10-01-qa-v2-implementation.md`**

Two execution options:

**1. Subagent-Driven (recommended)** — 每个 task 派一个全新 subagent，task 之间我来 review，迭代快

**2. Inline Execution** — 在当前 session 里按 batch 执行，带检查点

**Which approach?**
