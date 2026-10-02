"""
haidian_kg.evaluation.holdout_sampler
=====================================

Holdout 基准语料分层随机抽样器（spec docs/superpowers/specs/
2026-10-02-closure-expansion-design.md §5.3）。

纪律（spec §七 P0-3）：holdout 冻结语料必须在接入《日下旧闻考》原文
**之前**完成——抽样框架、分层轴、判定标准、验收阈值全部先行冻结，
使闭包规则迭代从未接触评测集，杜绝「在考卷上调参」。

当前实现只读 haidian_kg/corpus/era*.md 现有考据长编；抽样总体 =
与《日下旧闻考》存在引用线索（direct / section / file）的段。
原文 160 卷全文尚未接入，抽样只覆盖长编转述层——缺口清单见
.superpowers/sdd/holdout-design.md §7，接入原文后用同一脚本换
--corpus-dir 重抽，分层轴与段 schema 不变（冻结的是框架不是快照）。

设计原则：
1. 抽样器与挖掘器词表**故意不共享**（不用 expansion.PLACE_SUFFIXES）：
   holdout 判据若复用被测系统的启发式，就测不出系统自身的盲区。
2. 一切输出路径禁用 set 迭代 / 时间戳 / 随机器全局态：
   固定 seed + 全序化 ⇒ 两次运行字节级一致。
3. 段（segment）= 顶层列表项及其嵌套续行，标注最小自洽单元。

用法：
    python3 -m haidian_kg.evaluation.holdout_sampler \
        --n 120 --seed 20261002 --out holdout.jsonl [--report r.json]

输出 JSONL 每行一个段：segment_id / source_file / line_start /
line_end / heading_path / text / strata{dynasty,doc_type,script,
toponym_type} / rxjwkc_cue_scope / rxjwkc_juan / text_sha1 / n_chars。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple

DEFAULT_SEED = 20261002
DEFAULT_N = 120

# ---------------------------------------------------------------------------
# 《日下旧闻考》识别（书名变体 + 相关篇卷号抽取）
# ---------------------------------------------------------------------------

#: 简体 / 新旧繁体混排都收；语料实际以简体为主，变体表防转录漂移
RXJWK_VARIANTS: Tuple[str, ...] = (
    "日下旧闻考", "日下旧聞考", "日下舊聞考", "日下旧舊聞考",
)

#: 「卷」号捕获：简繁数字或阿拉伯数字（卷72 / 卷九十八 / 卷一百零四）
_JUAN_TOKEN_RE = re.compile(r"[零一二两三四五六七八九十百千\d]{1,12}")

#: 书名与「卷」之间允许出现的字（书名号收尾、空格、括号、「第」）
_ALLOWED_BETWEEN = frozenset("》」』）)（( 　\t\n第")
#: 区间分隔（「卷七十六至卷一百零四」两端都算相关篇卷）
_RANGE_SEPARATORS = frozenset("至—～~-－")


def extract_rxjwkc_juan(text: str) -> List[int]:
    """抽取文本中《日下旧闻考》书名后紧邻的相关篇卷号（升序去重）。

    实现纪律：**禁止窗口截取**。曾经用「书名后 40 字窗口 + 正则」，
    窗口边界会把「一百零一」拦腰截成「一百」→100，产出看似合法的
    错卷号（实测踩中）。改为全文扫描：每个书名出现点向后只越过
    白名单字符（书名号/括号/空白/第）即须遇到「卷」，再取完整
    数字 token；区间分隔符（至/—/～）后读第二端点。
    """
    juans: set = set()
    ends: set = set()
    for variant in RXJWK_VARIANTS:
        start = 0
        while True:
            idx = text.find(variant, start)
            if idx < 0:
                break
            start = idx + len(variant)
            ends.add(start)
    for end in sorted(ends):
        juans.update(_juan_after(text, end))
    return sorted(juans)


def _juan_after(text: str, pos: int) -> List[int]:
    """从书名结束位置向后解析卷号（含一个区间的第二端点）。"""
    i = pos
    while i < len(text) and text[i] in _ALLOWED_BETWEEN:
        i += 1
    if i >= len(text) or text[i] != "卷":
        return []
    j = i + 1
    if j < len(text) and text[j] == "第":  # 「卷第九十八」
        j += 1
    m = _JUAN_TOKEN_RE.match(text, j)
    if not m:
        return []
    first = chinese_num_to_int(m.group(0))
    if first is None or not 1 <= first <= 300:
        return []
    juans = [first]
    # 区间第二端点：「至卷一百零四」「至一百零四」
    k = m.end()
    saw_separator = False
    while k < len(text) and (text[k] in _ALLOWED_BETWEEN
                             or text[k] in _RANGE_SEPARATORS):
        if text[k] in _RANGE_SEPARATORS:
            saw_separator = True
        k += 1
    if saw_separator:
        second = _number_at(text, k)
        if second is not None:
            juans.append(second)
    return juans


def _number_at(text: str, pos: int) -> Optional[int]:
    """pos 处起取「[第][卷]数字」的完整数字 token；无则 None。"""
    if pos < len(text) and text[pos] == "第":
        pos += 1
    if pos < len(text) and text[pos] == "卷":
        pos += 1
    m = _JUAN_TOKEN_RE.match(text, pos)
    if not m:
        return None
    value = chinese_num_to_int(m.group(0))
    if value is None or not 1 <= value <= 300:
        return None
    return value

_CN_DIGIT = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
             "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def chinese_num_to_int(token: str) -> Optional[int]:
    """「九十八」→98、「104」→104；含无法解析字符时返回 None。

    支持至多千位、繁简数字混写；数字解析错误的 token 恒返回 None，
    绝不「尽力猜测」——篇卷号错一位就是错层。
    """
    if not token:
        return None
    if token.isdigit():
        return int(token)
    total, num = 0, 0
    for ch in token:
        if ch in _CN_DIGIT:
            num = _CN_DIGIT[ch]
        elif ch == "十":
            total += (num or 1) * 10
            num = 0
        elif ch == "百":
            total += (num or 1) * 100
            num = 0
        elif ch == "千":
            total += (num or 1) * 1000
            num = 0
        else:
            return None
    return total + num


# ---------------------------------------------------------------------------
# 分层轴一：朝代（era 文件名 → 朝代标签）
# ---------------------------------------------------------------------------

ERA_DYNASTY: Dict[str, str] = {
    "era0": "史前",
    "era1": "先秦",
    "era2": "秦汉魏晋南北朝",
    "era3": "隋唐五代",
    "era4": "辽金",
    "era5": "元",
    "era6": "明",
    "era7": "清",
    "era8_9": "近现代",
}


def dynasty_of(filename: str) -> str:
    stem = filename.rsplit(".", 1)[0]
    if stem in ERA_DYNASTY:
        return ERA_DYNASTY[stem]
    for key in sorted(ERA_DYNASTY, key=len, reverse=True):  # era8_9 先于 era8
        if stem.startswith(key + "_"):
            return ERA_DYNASTY[key]
    return stem  # 未知 era 文件以词干兜底，不静默丢层


# ---------------------------------------------------------------------------
# 分层轴二：文献类型（证据等级 Level 1-6，段内优先、节内兜底）
# ---------------------------------------------------------------------------

_LEVEL_RE = re.compile(r"Level\s*([1-6])")

LEVEL_LABEL: Dict[str, str] = {
    "1": "L1_考古实物",
    "2": "L2_一手官书档案文集",
    "3": "L3_正史方志纪实",
    "4": "L4_现代学界考订",
    "5": "L5_民间传说",
    "6": "L6_证伪伪说",
}


def doc_type_of(levels: Sequence[str]) -> str:
    """证据等级 → 文献类型层。多级并存取**最强证据**（数字最小者）。

    era5 §1.2 同段标「Level 1 + Level 2」，层值必须唯一，取 L1。
    """
    if not levels:
        return "unattributed"
    return LEVEL_LABEL[min(levels)]


# ---------------------------------------------------------------------------
# 分层轴三：繁简/异体（单字符集粗判：trad / simp / mixed）
# ---------------------------------------------------------------------------

#: 只出现于繁体的常用字（与简体字形不同），按语料实际用字冻结
_TRAD_ONLY = frozenset(
    "舊聞萬壽圓護軍東橋莊廟觀閘廠長記錄經與則從為歷顯豐興廢復門縣歲"
    "際兩書體靈氣風雲電陰陽國圖時語說證處營倉窯嶺澱闕壇磚樓臺館"
    "樹駐龍鳳齋軒"
)
#: 只出现于简体的对应常用字
_SIMP_ONLY = frozenset(
    "旧闻万寿圆护军东桥庄庙观闸厂长记录经与则从为历显丰兴废复门县岁"
    "际两书体灵气风云电阴阳国图时语说证处营仓窑岭淀阙坛砖楼台馆"
    "树驻龙凤斋轩"
)


def script_of(text: str) -> str:
    n_trad = sum(1 for ch in text if ch in _TRAD_ONLY)
    n_simp = sum(1 for ch in text if ch in _SIMP_ONLY)
    if n_trad and n_simp:
        return "mixed"
    if n_trad:
        return "trad"
    return "simp"  # 含中性字-only 文本；粗判粒度见设计文档 §3.3


# ---------------------------------------------------------------------------
# 分层轴四：地名类型（通名后缀 → 类。词表独立冻结，不 import expansion）
# ---------------------------------------------------------------------------

#: 类 → 通名后缀表（冻结副本；与 expansion.PLACE_SUFFIXES 语义对齐但
#: 独立维护——见模块 docstring 设计原则 1）
TOPO_SUFFIXES: Dict[str, Tuple[str, ...]] = {
    "settlement": ("村", "莊", "庄", "屯", "店", "坊", "市", "镇", "鎮"),
    "hydraulic": ("河", "泊", "泉", "閘", "闸", "堰", "渠", "湖", "海",
                  "澱", "淀", "橋", "桥"),
    "garden": ("園", "园", "苑", "宮", "宫", "殿", "囿"),
    "temple": ("寺", "菴", "庵", "觀", "观", "廟", "庙", "塔", "祠"),
    "military": ("營", "营", "旗", "廠", "厂", "場", "场", "倉", "仓",
                 "署", "局"),
    "landscape": ("山", "嶺", "岭", "峪", "墳", "坟", "崗", "岗", "崖"),
    "pass": ("關", "关", "口", "隘"),
}

#: 全部后缀均为单字 ⇒ 收进一个字符类（严禁用 "|".join 拼多字字面串：
#: 那会把整类字符当成一个 9 字字面量，永不命中）
_ALL_SUFFIX_CHARS = "".join(
    "".join(sufs) for sufs in (TOPO_SUFFIXES[k] for k in sorted(TOPO_SUFFIXES)))
_TOPO_RE = re.compile("([\u4e00-\u9fff]{1,6}?)([%s])" % _ALL_SUFFIX_CHARS)


def toponym_type_of(text: str) -> str:
    """段内最先命中的通名后缀决定地名类型层（确定性：按文本位置，
    finditer 自左向右，首个命中即最早位置）。"""
    suffix_to_class = {}
    for cls in sorted(TOPO_SUFFIXES):
        for suf in TOPO_SUFFIXES[cls]:
            suffix_to_class[suf] = cls
    for m in _TOPO_RE.finditer(text):
        cls = suffix_to_class.get(m.group(2))
        if cls is not None:
            return cls
    return "none"


# ---------------------------------------------------------------------------
# 语料解析：era*.md → 段
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_QUOTE_RE = re.compile(r"^\s*>")
_HR_RE = re.compile(r"^\s*-{3,}\s*$")
_TOP_ITEM_RE = re.compile(r"^(?:[-*]|\d+[.)、])\s+")


class Segment(object):
    """一个可标注段：顶层列表项/散文块及其嵌套续行。"""

    __slots__ = ("source_file", "heading_path", "line_start", "line_end",
                 "text", "section_key", "levels")

    def __init__(self, source_file: str, heading_path: str,
                 line_start: int, line_end: int, text: str,
                 section_key: str, levels: List[str]) -> None:
        self.source_file = source_file
        self.heading_path = heading_path
        self.line_start = line_start
        self.line_end = line_end
        self.text = text
        self.section_key = section_key
        self.levels = levels

    @property
    def segment_id(self) -> str:
        return "%s:L%d-L%d" % (self.source_file, self.line_start, self.line_end)


def parse_segments(path: Sequence[str], filename: str) -> List[Segment]:
    """把一个 era*.md 解析成段列表。

    规则：
    - 标题（#/##/###...）与水平线闭合当前段，并更新节作用域；
    - 顶层列表项（`- ` / `1. `）开启新段；
    - 缩进行为当前段的嵌套续行；
    - 引用块（`> ...`）不入段，只作为文件级引用线索（file cue）；
    - 空行闭合当前段；
    - 顶层散文行并入当前段，无段则开启散文段。
    """
    segments: List[Segment] = []
    cur_lines: List[str] = []
    cur_start = 0
    cur_levels: List[str] = []   # 段内已见的 Level 标记（仅本段自身）
    heading_l1 = ""
    heading_l2 = ""
    heading_l3 = ""
    section_levels_seen: Dict[str, List[str]] = {}  # 节 → 节内全部 Level 标记

    def current_section() -> str:
        """节作用域：### 优先，缺 ### 时回退 ##，再回退 #。
        era7 §2 负控制判据直接挂在 ## 下，不能因无 ### 被整节丢弃。"""
        return heading_l3 or heading_l2 or heading_l1

    def flush() -> None:
        nonlocal cur_lines, cur_start, cur_levels
        text = "\n".join(cur_lines).strip()
        section = current_section()
        if text and section:
            hp = " > ".join(p for p in (heading_l1, heading_l2, heading_l3) if p)
            segments.append(Segment(
                source_file=filename, heading_path=hp,
                line_start=cur_start, line_end=cur_start + len(cur_lines) - 1,
                text=text, section_key=section, levels=list(cur_levels)))
        cur_lines, cur_start, cur_levels = [], 0, []

    for lineno, raw in enumerate(path, start=1):
        line = raw.rstrip("\n")
        if not line.strip():
            flush()
            continue
        if _HR_RE.match(line):
            flush()
            continue
        hm = _HEADING_RE.match(line)
        if hm:
            flush()
            level, title = len(hm.group(1)), hm.group(2)
            if level == 1:
                heading_l1, heading_l2, heading_l3 = title, "", ""
            elif level == 2:
                heading_l2, heading_l3 = title, ""
            else:
                heading_l3 = title
            section_levels_seen.setdefault(current_section(), [])
            continue
        if _QUOTE_RE.match(line):
            flush()  # 文件前导引用块不入段（cue 由调用方单独收集）
            continue
        for m in _LEVEL_RE.finditer(line):
            cur_levels.append(m.group(1))
            section_levels_seen.setdefault(current_section(), []).append(m.group(1))
        if _TOP_ITEM_RE.match(line):
            flush()
            cur_start = lineno
            cur_lines = [line]
            continue
        if cur_lines:
            cur_lines.append(line)
        else:
            cur_start = lineno
            cur_lines = [line]
    flush()

    # 节级兜底：段自身无 Level 标记时，继承所在 ### 节的**全部**标记。
    # 必须全文解析完再兜底——「证据等级」bullet 常列在节末，
    # 位置依赖的继承会漏掉它（先出现后标记同样生效）。
    for seg in segments:
        if not seg.levels:
            seen = section_levels_seen.get(seg.section_key, [])
            deduped = sorted(set(seen))
            if deduped:
                seg.levels = deduped
    return segments


def _section_cue_text(segments: List[Segment]) -> str:
    return "\n".join(s.heading_path + "\n" + s.text for s in segments)


# ---------------------------------------------------------------------------
# 相关性：direct / section / file / none（spec 纪律：线索必须可追溯）
# ---------------------------------------------------------------------------

def _first_variant(text: str) -> Optional[str]:
    positions = [(text.find(v), v) for v in RXJWK_VARIANTS if text.find(v) >= 0]
    if not positions:
        return None
    positions.sort()
    return positions[0][1]


def assign_relevance(segments: List[Segment],
                     file_preamble: str) -> List[Tuple[Segment, str, str]]:
    """返回 (segment, cue_scope, cue_context)。

    cue_context = 建立「《日下旧闻考》相关」的证据文本：direct=段自身，
    section=所在 ### 节全文，file=文件前导引用块。篇卷号从
    cue_context ∪ 段文本中抽取（节内「文献出处」bullet 是兄弟段，
    兄弟段携带的卷号同样适用于同节各段）。
    """
    direct = _first_variant(file_preamble or "")
    sections: Dict[str, List[Segment]] = {}
    for seg in segments:
        sections.setdefault(seg.section_key, []).append(seg)
    section_cue: Dict[str, str] = {}
    for key in sorted(sections):
        hit = _first_variant(_section_cue_text(sections[key]))
        if hit:
            section_cue[key] = hit
    out: List[Tuple[Segment, str, str]] = []
    for seg in segments:
        if _first_variant(seg.text):
            out.append((seg, "direct", seg.text))
        elif seg.section_key in section_cue:
            out.append((seg, "section", _section_cue_text(sections[seg.section_key])))
        elif direct:
            out.append((seg, "file", file_preamble))
        else:
            out.append((seg, "none", ""))
    return out


# ---------------------------------------------------------------------------
# 分层与配额
# ---------------------------------------------------------------------------

def strata_of(seg: Segment, levels: Sequence[str]) -> Dict[str, str]:
    return {
        "dynasty": dynasty_of(seg.source_file),
        "doc_type": doc_type_of(levels),
        "script": script_of(seg.text),
        "toponym_type": toponym_type_of(seg.text),
    }


def strata_key(strata: Dict[str, str]) -> str:
    return "|".join(strata[k] for k in ("dynasty", "doc_type", "script",
                                        "toponym_type"))


def allocate(universe_by_key: Dict[str, int], n: int) -> Dict[str, int]:
    """比例分配 + 最大余数法；非空层 ≤ n 时每层保底 1。"""
    keys = sorted(universe_by_key)
    total = sum(universe_by_key[k] for k in keys)
    quota = min(n, total)
    floor_one = len(keys) <= quota and quota > 0
    alloc: Dict[str, int] = {}
    base_total = 0
    for k in keys:
        exact = universe_by_key[k] * quota / total
        base = int(exact)
        if floor_one and base < 1:
            base = 1
        base = min(base, universe_by_key[k])
        alloc[k] = base
        base_total += base
    # 最大余数法补足（余数并列按层名字典序，保证确定性）
    remainders = sorted(
        ((universe_by_key[k] * quota / total - int(universe_by_key[k] * quota / total), k)
         for k in keys),
        key=lambda t: (-t[0], t[1]))
    i = 0
    while base_total < quota and keys:
        k = remainders[i % len(remainders)][1]
        if alloc[k] < universe_by_key[k]:
            alloc[k] += 1
            base_total += 1
        i += 1
        if i > 100 * len(remainders) + 10:  # 全层顶满仍补不足（理论不可达）
            break
    return alloc


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def load_frame(corpus_dir: str) -> Tuple[List[Tuple[Segment, str, str]], Dict[str, str]]:
    """读 corpus 目录，返回（全部段+线索, 语料 SHA256 摘要字典）。"""
    import os
    names = sorted(fn for fn in os.listdir(corpus_dir)
                   if fn.startswith("era") and fn.endswith(".md"))
    if not names:
        raise SystemExit("corpus 目录无 era*.md：%s" % corpus_dir)
    frame: List[Tuple[Segment, str, str]] = []
    digests: Dict[str, str] = {}
    for fn in names:
        with open(os.path.join(corpus_dir, fn), "r", encoding="utf-8") as fh:
            content = fh.read()
        digests[fn] = hashlib.sha256(content.encode("utf-8")).hexdigest()
        lines = content.split("\n")
        preamble = "\n".join(l for l in lines if _QUOTE_RE.match(l))
        segs = parse_segments(lines, fn)
        frame.extend(assign_relevance(segs, preamble))
    return frame, digests


def build_record(seg: Segment, cue_scope: str, cue_context: str,
                 strata: Dict[str, str]) -> Dict[str, object]:
    levels = sorted(set(seg.levels))
    return {
        "segment_id": seg.segment_id,
        "source_file": seg.source_file,
        "line_start": seg.line_start,
        "line_end": seg.line_end,
        "heading_path": seg.heading_path,
        "text": seg.text,
        "strata": strata,
        "rxjwkc_cue_scope": cue_scope,
        "rxjwkc_juan": extract_rxjwkc_juan(cue_context + "\n" + seg.text),
        "text_sha1": hashlib.sha1(seg.text.encode("utf-8")).hexdigest(),
        "n_chars": len(seg.text),
    }


def sample_holdout(corpus_dir: str, n: int = DEFAULT_N,
                   seed: int = DEFAULT_SEED) -> Tuple[List[Dict[str, object]], Dict[str, object]]:
    """主入口：返回（JSONL 记录列表, 报告字典）。完全确定：同参同果。"""
    frame, digests = load_frame(corpus_dir)
    related = [(s, scope, ctx) for (s, scope, ctx) in frame if scope != "none"]

    universe: Dict[str, List[Tuple[Segment, str, str]]] = {}
    for seg, scope, ctx in related:
        universe.setdefault(strata_key(strata_of(seg, seg.levels)), []).append(
            (seg, scope, ctx))
    for key in universe:
        universe[key].sort(key=lambda t: t[0].segment_id)

    alloc = allocate({k: len(v) for k, v in universe.items()}, n)
    rng = random.Random(seed)
    picked: List[Tuple[Segment, str, str]] = []
    for key in sorted(alloc):  # 先收集再统一洗牌，避免层序影响抽样
        pool = universe[key]
        take = min(alloc[key], len(pool))
        picked.extend(rng.sample(pool, take))
    picked.sort(key=lambda t: t[0].segment_id)

    records = [build_record(seg, scope, ctx, strata_of(seg, seg.levels))
               for seg, scope, ctx in picked]
    report = {
        "seed": seed,
        "n_requested": n,
        "corpus_files": sorted(digests),
        "corpus_sha256": digests,
        "universe_segments_total": len(frame),
        "frame_segments_total": len(related),
        "frame_shortfall": max(0, n - len(related)),
        "strata_universe": {k: len(v) for k, v in sorted(universe.items())},
        "strata_allocation": dict(sorted(alloc.items())),
        "strata_sampled": {},
        "cue_scope_sampled": {},
        "sampled": len(records),
    }
    for rec in records:
        key = strata_key(rec["strata"])  # type: ignore[arg-type]
        report["strata_sampled"][key] = report["strata_sampled"].get(key, 0) + 1
        scope = rec["rxjwkc_cue_scope"]
        report["cue_scope_sampled"][scope] = report["cue_scope_sampled"].get(scope, 0) + 1
    return records, report


def dumps_jsonl(records: Sequence[Dict[str, object]]) -> str:
    return "".join(
        json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n"
        for r in records)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="holdout 基准分层随机抽样器（spec §5.3，冻结框架）")
    parser.add_argument("--corpus-dir", default=None,
                        help="corpus 目录（默认 <repo>/haidian_kg/corpus）")
    parser.add_argument("--n", type=int, default=DEFAULT_N,
                        help="目标抽样段数（默认 %d；不足时抽满总体并报告缺口）"
                             % DEFAULT_N)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                        help="随机种子（默认 %d，冻结）" % DEFAULT_SEED)
    parser.add_argument("--out", required=True, help="输出 JSONL 路径")
    parser.add_argument("--report", default=None,
                        help="可选：抽样报告 JSON 路径")
    args = parser.parse_args(argv)

    repo_root = __file__.rsplit("/haidian_kg/", 1)[0]
    corpus_dir = args.corpus_dir or repo_root + "/haidian_kg/corpus"
    records, report = sample_holdout(corpus_dir, n=args.n, seed=args.seed)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(dumps_jsonl(records))
    if args.report:
        with open(args.report, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
    sys.stderr.write(
        "抽样 %d/%d（请求 %d，缺口 %d）→ %s\n"
        % (report["sampled"], report["frame_segments_total"],
           report["n_requested"], report["frame_shortfall"], args.out))
    if report["frame_shortfall"]:
        sys.stderr.write("⚠ 总体不足请求量：分层覆盖缺口见 "
                         ".superpowers/sdd/holdout-design.md §7\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
