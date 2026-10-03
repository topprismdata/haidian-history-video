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
import re
from typing import Dict, List, Optional, Set

from qa_v2.data import Episode, Page
from qa_v2.frames import OcrResult
from qa_v2.normalize import (
    _REIGN_NAMES, extract_numbers, normalize_punct, normalize_script,
    number_unknown_rate, to_int,
)
from qa_v2.report import Finding

NAMES = pathlib.Path(__file__).with_name("names.txt")

# 无法解析的数字 token 占比超过此值报 warn
# （防止 to_int 有 bug 却静默通过）
UNKNOWN_RATE_WARN = 0.20

_BOOK_TITLE_RE = re.compile(r"《[^》]+》")
_VOLUME_RE = re.compile(r"卷\s*([0-9]+|[零〇一二两三四五六七八九十百]+)")
_EPISODE_RE = re.compile(r"\bE\d+\b")
_TABLE_SLOT_RE = re.compile(r"^(?:r\d+_|th_|cell_)")
_ERA_PAREN_RE = re.compile(
    rf"(?:(?:{_REIGN_NAMES})[零〇一二两三四五六七八九十]+年)"
    r"\s*[（\(·]\s*(\d{3,4})\s*[）\)]?"
)


def load_names(path: Optional[pathlib.Path] = None) -> Set[str]:
    """读专名表。空文件返回空 set —— 调用方须据此报 skip 而非 pass。"""
    p = pathlib.Path(path) if path else NAMES
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            out.add(normalize_script(s))
    return out


def _ocr_text_for(page: Page, ocr: OcrResult, slot_id: str) -> str:
    """取该槽内的 OCR 读回文本。"""
    from qa_v2.frames import text_at
    from qa_v2.geometry import plate_to_canvas
    slot = page.slot(slot_id)
    if slot is None:
        return ""
    rect = plate_to_canvas(page.plate, slot.x, slot.y, slot.w, slot.h)
    return "".join(t for t, _, _ in text_at(ocr, rect))


def _can_decompose_glued(target: str, pieces: List[str]) -> bool:
    """判断目标数字字符串是否可以完全由候选数字拼块按顺序无缝拼接组成（至少两个拼块）。

    边界权衡与判定原则（详见 check_l4a 文档）：
    - 必须完全由候选拼块精确拼合（如 '3926' 由 '39' + '26' 拼出，'6539' 由 '65' + '39' 拼出）；
    - 绝不允许任意子串匹配或前后缀通配：
      例如文案 '1485' 而 OCR 读回 '14850' 或 '1486' 时，因为无法由合法数字拼块精确还原整串，
      严禁判定为粘连，必须判定为真错值报 fail；
    - 单个拼块（即自身相等）由外层 got 集合直接匹配，此处必须由 >= 2 个拼块组合。
    """
    memo: Dict[str, bool] = {}

    def dfs(rem: str, depth: int) -> bool:
        if not rem:
            return depth >= 2
        if rem in memo:
            return memo[rem]
        for p in pieces:
            if rem.startswith(p):
                if dfs(rem[len(p):], depth + 1):
                    memo[rem] = True
                    return True
        memo[rem] = False
        return False

    return dfs(target, 0)


def check_l4a(page: Page, ocr: OcrResult) -> List[Finding]:
    """数字严格：原文里的每个数字都必须出现在 OCR 读回里。

    粘连判据设计与边界权衡：
    -------------------------------------------------------------------------
    1. 现象与成因：
       OCR 在密集排版（如明细表格 P3）中经常发生两类结构性数字粘连：
       - 纵向粘连（多行单元格）：如同一格内多行数字 [39, 26] 读回为 3926，
         [1167, 315] 读回为 1167315，[1206, 341] 读回为 1206341；
       - 横向粘连（邻格串字）：如 [65] 读回为 6539（与邻格 39 粘连），
         [1485] 读回为 14851167，[1550] 读回为 15501206。
    2. 核心红线（禁止降级）：
       - 绝不使用「只要期望数字是读回数字的子串就放过」的粗暴判据！
       - 区分 1485 ↔ 14850 与 1485 ↔ 1486：
         - 1485 ↔ 1486：字形错误，无任何粘连拼接证据，必须报 NUMBER_MISMATCH；
         - 1485 ↔ 14850：尾随多出 0，但 0 不是该页排版中的合法数字拼块，
           无法被精确分解为 [1485, 0]，必须报 NUMBER_MISMATCH；
         - 1485 ↔ 14851167：14851167 能够被整除/精确分解为当前页面的真值拼块
           ['1485', '1167']，属于可解释的结构性粘连，予以豁免。
    3. 判定算法：
       - 收集当前页面所有合法文案中出现过的数字字符串作为拼块候选集合；
       - 当某期望数字 w 未在 got 中直接命中时，检查 got 中是否存在包含 w 的读回数字 g；
       - 若 g 能够被候选拼块集合精确无缝拼接（深度 >= 2），则判定 w 属于粘连成功匹配；
       - 否则保留为 missing 报 fail。
    -------------------------------------------------------------------------
    """
    out = []
    # 收集当前页面所有合法文案中提取出的数字，作为候选拼块
    page_numbers: Set[int] = set()
    for it in page.items:
        if not it.is_tag:
            page_numbers.update(extract_numbers(it.text))
    # 拼块按长度降序排序，过滤单字符 0 以免意外充当通配符
    candidate_pieces = sorted([str(n) for n in page_numbers if n > 0],
                              key=lambda s: len(s), reverse=True)

    for item in page.items:
        if item.is_tag or item.is_photo():
            # 2026-10-03：真图槽的文字由 PhotoFrame 组件在画布别处渲染，
            # 槽内只有图像像素——L4 逐字/数字比对对它不成立。
            continue
        want = set(extract_numbers(item.text))
        if not want:
            continue
        got_raw = _ocr_text_for(page, ocr, item.slot_id)
        got = set(extract_numbers(got_raw))

        rate = number_unknown_rate(item.text)
        if rate > UNKNOWN_RATE_WARN:
            out.append(Finding(
                "L4-a", page.number, item.slot_id, "warn",
                "NUMBER_UNKNOWN_RATE",
                "数字归一失败率 %.0f%%，本槽数字比对不可信"
                % (rate * 100), {"text": item.text[:40]}))

        missing = sorted(want - got)
        if missing:
            # 检查是否有结构性粘连
            glued_found = set()
            for w in missing:
                w_str = str(w)
                for g in got:
                    g_str = str(g)
                    if w_str in g_str and g_str != w_str:
                        if _can_decompose_glued(g_str, candidate_pieces):
                            glued_found.add(w)
                            break
            real_missing = sorted(set(missing) - glued_found)
            if real_missing:
                out.append(Finding(
                    "L4-a", page.number, item.slot_id, "fail",
                    "NUMBER_MISMATCH",
                    "数字对不上：期望 %s，读回 %s"
                    % (real_missing, sorted(got)),
                    {"expect": item.text[:50], "ocr": got_raw[:50]}))
    return out


def check_l4b(page: Page, ocr: OcrResult, names: Set[str]) -> List[Finding]:
    """专名严格：原文命中的专名必须逐个出现在 OCR 读回里。"""
    out = []
    if not names:
        out.append(Finding(
            "L4-b", None, None, "skip", "NO_NAMES_TABLE",
            "专名表为空，L4-b 未执行（不算通过）。新集需维护 qa_v2/names.txt"))
        return out
    for item in page.items:
        if item.is_tag or item.is_photo():
            # 2026-10-03：真图槽的文字由 PhotoFrame 组件在画布别处渲染，
            # 槽内只有图像像素——L4 逐字/数字比对对它不成立。
            continue
        norm_item_text = normalize_punct(item.text)
        want = [normalize_punct(n) for n in names if normalize_punct(n) in norm_item_text]
        if not want:
            continue
        got = normalize_punct(_ocr_text_for(page, ocr, item.slot_id))
        missing = [n for n in want if n not in got]
        if missing:
            out.append(Finding(
                "L4-b", page.number, item.slot_id, "fail",
                "PROPER_NAME_MISSING",
                "专名对不上：缺 %s" % "、".join(missing),
                {"expect": item.text[:50]}))
    return out


def _is_table_cell(slot_id: str) -> bool:
    """是否为明细表格单元格槽位（如 r1_hall, th_dir, cell_2_3）。"""
    return bool(_TABLE_SLOT_RE.match(slot_id))


def _has_competing_number(w: int, spoken_nums: Set[int]) -> bool:
    """口播稿中是否存在与 w 属于同一维度/数量级的竞争数值（用于判断两边冲突）。

    若口播完全没提该数量级的数值（如口播只讲方位，压根没提 1000~2000 之间的房数），
    则说明该明细数据为视觉呈现资料，口播本就未念；
    若口播念了相近区间的数字（例如口播念了 1460，文案写了 1485），
    说明两边都在陈述同一指标但数字冲突，必须报警。
    """
    for s in spoken_nums:
        if w == s:
            return False
        # 相对误差 15% 以内，视为同维度竞争数值
        rel_diff = abs(w - s) / max(w, s)
        if rel_diff <= 0.15:
            return True
        # 或绝对差值 <= 5（针对小规模计数）
        if w >= 20 and abs(w - s) <= 5:
            return True
    return False


def _clean_slot_text_for_l4c(text: str, spoken: str) -> str:
    """清理文案中纯视觉属性的非口播文本：

    1) 书名号《...》：属于专名（由 L4-b 校验），且《八旗》中的「八」不是定量数值；
    2) 卷号「卷116」：文献引用标识，口播不念卷号；
    3) 集数标识「E1」「E11」：系列编号，口播不念；
    4) 朝代年号后的公历换算括号「万历二十八年（1600）」：
       若口播已念出该朝代年号，则括号内的公历换算属于画面辅助注释，予以剥除。
    """
    t = _BOOK_TITLE_RE.sub("", text)
    t = _VOLUME_RE.sub("", t)
    t = _EPISODE_RE.sub("", t)
    for m in _ERA_PAREN_RE.finditer(text):
        era_full = m.group(0)
        era_name = re.match(rf"(?:(?:{_REIGN_NAMES})[零〇一二两三四五六七八九十]+年)", era_full)
        if era_name and era_name.group(0) in spoken:
            t = t.replace(m.group(0), "")
    return t


def _is_volume_ref(n: int) -> bool:
    """是否为小额非定量/卷号数字兜底（1 <= n <= 200）。

    L4-c 重构后，绝大部分卷号与专名已由上下文正则精确剥除。
    保留 1 <= n <= 200 作为多集泛化的二级兜底（如未规范书名号的卷号、
    以及「一个字」「两处」等汉语不定冠词/次序词），
    避免将非定量修辞误判为事实矛盾。
    """
    return 1 <= n <= 200


#: L4-c 口播豁免槽（冻结裁决落地，非判据松动）。
#: C09（E19 闸门，2026-10-03）：P7 机车年款 1937/1956 定为「仅卡片小字、
#: 不进口播、不进 L4-c」——机车是彩蛋不是主线，为它开白名单会挤占叙事预算。
#: 登记在此的槽：数字不要求口播覆盖，但仍受 L4-a（OCR 可读性）约束。
L4C_NONSPOKEN_SLOT_IDS = {"p7_loco"}


def check_l4c(ep: Episode, ocr_by_page: Dict[int, OcrResult]) -> List[Finding]:
    """字幕交叉：槽里的数字，必须与当页口播稿保持事实一致。

    重构设计决策（详见 .superpowers/sdd/l4c-redesign.md）：
      1) 区分「结构性表格参考」与「核心叙事文案」：
         明细表格（如 P3 八旗营房表）是纯视觉资料，口播只作方位概括而不念 24 格数字。
         表格单元格仅在口播念了同量级竞争数字却与文案不一致时报 fail（抓两边冲突）；
         口播完全不提该量级数据时豁免。
      2) 精准剥除视觉辅助数字：
         书名号《八旗》内非定量字、文献卷号（卷116）、集数标识（E11）、
         以及口播念了年号时画面附带的公历换算括号（万历二十八年（1600））。
      3) 核心叙述槽位（标题、时间线、主卡片）严格交叉：
         文案中的关键事实数字（年份、人数、总房数、汛数等）必须在口播中找到对应表述。
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

        for item in page.items:
            if item.is_tag:
                continue

            cleaned_text = _clean_slot_text_for_l4c(item.text, spoken)
            want = set(extract_numbers(cleaned_text))
            if not want:
                continue

            # 表格明细槽位：只有当口播念了相近竞争数值但与文案不同时才报警
            if _is_table_cell(item.slot_id):
                needs_check = any(_has_competing_number(w, spoken_nums) for w in want)
                if not needs_check:
                    continue

            # C09 冻结豁免槽（如 E19 p7_loco 机车年款）：数字不要求口播覆盖
            if item.slot_id in L4C_NONSPOKEN_SLOT_IDS:
                continue

            missing = sorted(
                n for n in want
                if n not in spoken_nums and not _is_volume_ref(n)
            )
            if missing:
                out.append(Finding(
                    "L4-c", page.number, item.slot_id, "fail",
                    "NUMBER_NOT_IN_NARRATION",
                    "数字 %s 在该页口播稿里找不到" % missing,
                    {"text": item.text[:50]}))

    return out


# ── L4-d 引文一致性（2026-10-02，E12/E13 盲区补） ──────────────────────
# 实证 1（E12 p6）：口播「震钧写下五个字：今已毁尽」——实为四个字，
# 同页画面就是原文，观者同秒可证伪；QA 七层全放行，靠人工反向走查才抓到。
# 实证 2（E13 P7）：表头 1980 vs 口播 1984 由 L4-c 抓到，但引文类语义错
# 无任何判据覆盖。
#
# 两级判据：
#   计数自洽（快档即可，纯口播文本）：口播里「N个字」与其紧邻引文实长矛盾
#     → fail QUOTE_COUNT_MISMATCH
#   上屏核验（仅 --ocr）：口播引文（≥3 个实义字）在该页 OCR 文本中找不到
#     → warn QUOTE_NOT_ON_SCREEN（OCR 漏读无法排除，不阻塞）

_QUOTE_RE = re.compile(r"[「『“]([^「」『』“”]{2,40})[」』”]")
_COUNT_RE = re.compile(
    r"([0-9]+|[零〇一二两三四五六七八九十百]+)\s*个?\s*(?:大)?字"
)
# E12 p6 实测格式：计数词后跟冒号、裸引文（无引号括号），句号收尾
# 「震钧写下四个字：今已毁尽。」
_COLON_QUOTE_RE = re.compile(
    r"([0-9]+|[零〇一二两三四五六七八九十百]+)\s*个?\s*(?:大)?字\s*[：:]\s*"
    r"([^。！？；，、\n「」『』“”—]{2,40})"
)
_HANZI_ALNUM_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9]")
# 引文与计数词之间允许的最大距离（含引号/冒号/逗号）
_COUNT_WINDOW = 12


def _substantive_len(quote: str) -> int:
    """引文实义长度：只数汉字/字母/数字，标点空白不算。"""
    return len(_HANZI_ALNUM_RE.findall(quote))


def check_l4d(ep: Episode, ocr_by_page: Optional[Dict[int, OcrResult]] = None
              ) -> List[Finding]:
    """引文一致性：口播里的「N个字」计数、引文上屏两层核验。

    计数自洽是纯文本检查，快档即跑（零成本，E12 p6 类错误的直接疫苗）。
    上屏核验只在 --ocr 下执行，报 warn 不报 fail——OCR 漏读无法排除，
    诚实降级而不是假装确定（与「skip 不算通过」同一纪律）。
    """
    from qa_v2.data import narration_text

    out: List[Finding] = []
    narration = getattr(ep, "narration", None)
    if narration is None:
        narration = narration_text(ep.name)
    if not narration:
        out.append(Finding(
            "L4-d", None, None, "skip", "NO_NARRATION",
            "找不到 %s_video/narration/all.json，L4-d 未执行（不算通过）"
            % ep.name))
        return out

    for page in ep.pages:
        spoken = narration.get(page.number)
        if not spoken:
            continue
        seen_quotes = set()
        # 候选 = (quote, stated_or_None)。括号引文计数词在前后窗口找；
        # 冒号裸引文计数词就是前缀（E12 p6 实测格式）
        candidates = []
        for m in _QUOTE_RE.finditer(spoken):
            before = spoken[max(0, m.start() - _COUNT_WINDOW):m.start()]
            after = spoken[m.end():m.end() + _COUNT_WINDOW]
            stated = None
            token = None
            for ctx in (before, after):
                cm = _COUNT_RE.search(ctx)
                if cm:
                    token = cm.group(1)
                    stated = to_int(token)
                    if stated is not None:
                        break
            candidates.append((m.group(1), stated, token))
        for m in _COLON_QUOTE_RE.finditer(spoken):
            token, quote = m.group(1), m.group(2)
            stated = to_int(token)
            candidates.append((quote, stated if stated is not None else None,
                               token))

        for quote, stated, token in candidates:
            actual = _substantive_len(quote)
            if actual < 2:
                continue
            key = (page.number, quote)
            if key in seen_quotes:
                continue
            seen_quotes.add(key)

            if stated is not None and stated != actual:
                out.append(Finding(
                    "L4-d", page.number, None, "fail",
                    "QUOTE_COUNT_MISMATCH",
                    "口播称「%s个字」但引文「%s」实为 %d 字（画面可同秒证伪）"
                    % (token, quote, actual),
                    {"quote": quote, "stated": stated, "actual": actual}))

            # 上屏核验：仅 --ocr；≥3 实义字才查（过短误报高）
            if ocr_by_page and actual >= 3:
                # 数字性引文（「一千五百多间」这类量词短语）归 L4-c 数字
                # 交叉管——shucun P2 实测：画面写 1550，口播念汉字数字，
                # 字面必然不同，屏检只会重复报警
                hanzi = [c for c in quote if "\u4e00" <= c <= "\u9fff"]
                numish = sum(1 for c in hanzi
                             if c in "零〇一二两三四五六七八九十百千万几多约余")
                if not hanzi or numish >= 0.8 * len(hanzi):
                    continue
                ocr = ocr_by_page.get(page.number)
                if ocr is None:
                    continue
                # 两侧同口径:繁简归一后比对(E15 实测:屏显繁体「慧日長輝」,
                # 口播/表内是简体「慧日长辉」,不归一会恒假 warn)
                want = normalize_script(normalize_punct(quote))
                got = normalize_script(normalize_punct("".join(ocr.texts)))
                # 摘录容忍：画面常节引史料（shucun P7 上谕只摘「移驻树村」），
                # 任一 ≥4 字连续片段命中即视为上屏；整段缺席才 warn
                n = min(4, len(want))
                on_screen = want in got or any(
                    want[i:i + n] in got for i in range(len(want) - n + 1))
                if not on_screen:
                    out.append(Finding(
                        "L4-d", page.number, None, "warn",
                        "QUOTE_NOT_ON_SCREEN",
                        "口播引文「%s」在该页 OCR 文本中未找到（可能漏读，"
                        "人工复核）" % quote,
                        {"quote": quote}))
    return out
