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
_CN_UNIT = {"十": 10, "百": 100, "千": 1000, "万": 10000}

# 连续的阿拉伯数字 / 中文数字（中文数字首字必须是数词，不能直接以「百/千/万」开头）
_NUM_RE = re.compile(
    r"[0-9]+|[零〇一二两三四五六七八九十][零〇一二两三四五六七八九十百千万]*"
)

# 历史片常见朝代年号（如「雍正二年」「乾隆八年」「万历三十五年」）
# 年号纪年属于朝代历史表述，不作为定量数值参与 OCR 比对；随后的公历年份（如「1724」「一七二四」）才是比对对象
_REIGN_NAMES = (
    "顺治|康熙|雍正|乾隆|嘉庆|道光|咸丰|同治|光绪|宣统|"
    "洪武|建文|永乐|洪熙|宣德|正统|景泰|天顺|成化|弘治|正德|嘉靖|隆庆|万历|泰昌|天启|崇祯|"
    "大定|承安|泰和|贞祐|至元|乾亨|太平兴国"
)
_REIGN_YEAR_RE = re.compile(rf"(?:{_REIGN_NAMES})[零〇一二两三四五六七八九十]+年")
_PARALLEL_REIGN_YEAR = re.compile(r"(?<=[·、，,和与至到\s])([零〇一二两三四五六七八九十]{1,2}年)")


def clean_reign_years(s: str) -> str:
    """剥离帝号年号（如「乾隆四十六年」「嘉庆四年」）及紧随其后的简写年号（如「· 五年」）。

    注意：4 位数字的公历年份（如「一七八一年」）绝不是年号，必须保留。
    """
    has_reign = bool(_REIGN_YEAR_RE.search(s))
    s = _REIGN_YEAR_RE.sub("", s)
    if has_reign:
        s = _PARALLEL_REIGN_YEAR.sub("", s)
    return s

# 通用繁简字对照表：
# 移植自 scripts/verify_subtitles_asr.py，并扩充历史片/地名/常用规范汉字对照。
# 解决 OCR/ASR 产生的系统性繁简混淆（如「黃」↔「黄」、「鐵」↔「铁」等）。
TRAD_TO_SIMP = {
    # verify_subtitles_asr.py 原有条目
    "銅": "铜", "鑄": "铸", "銀": "银", "徑": "径", "園": "园", "裡": "里",
    "樹": "树", "臺": "台", "號": "号", "們": "们", "這": "这", "說": "说",
    "變": "变", "靈": "灵", "馬": "马", "體": "体", "飛": "飞", "後": "后",
    "東": "东", "長": "长", "萬": "万", "與": "与", "為": "为", "會": "会",

    # 颜色 / 八旗 / 方位 / 建筑 / 地名
    "黃": "黄", "藍": "蓝", "紅": "红", "綠": "绿", "鑲": "镶", "圓": "圆",
    "門": "门", "樓": "楼", "營": "营", "鄉": "乡", "莊": "庄", "橋": "桥",
    "開": "开", "關": "关", "廠": "厂", "廣": "广", "衛": "卫", "縣": "县",
    "區": "区", "線": "线", "邊": "边", "點": "点", "頭": "头",

    # 职官 / 军事
    "總": "总", "將": "将", "軍": "军", "處": "处", "參": "参", "領": "领",
    "備": "备", "護": "护",

    # 典籍 / 文献 / 宗教 / 器物
    "圖": "图", "書": "书", "記": "记", "誌": "志", "歷": "历",
    "觀": "观", "欽": "钦", "錄": "录", "鐵": "铁", "鐘": "钟",
    "寶": "宝", "聖": "圣", "廟": "庙", "閣": "阁",
    "舊": "旧", "冊": "册", "經": "经",

    # 常用字词
    "幾": "几", "兩": "两", "無": "无", "發": "发", "過": "过", "進": "进",
    "時": "时", "間": "间", "從": "从", "來": "来", "對": "对", "現": "现",
    "動": "动", "實": "实", "專": "专", "義": "义", "認": "认", "設": "设",
    "權": "权", "規": "规", "則": "则", "張": "张", "選": "选", "樣": "样",
    "種": "种", "類": "类", "個": "个", "準": "准", "確": "确", "稱": "称",
    "並": "并", "單": "单", "複": "复", "數": "数", "題": "题", "問": "问",
}


def normalize_script(s: str) -> str:
    """繁简归一：将繁体/异体字映射为通用规范简体字。"""
    for trad, simp in TRAD_TO_SIMP.items():
        if trad in s:
            s = s.replace(trad, simp)
    return s


def normalize_punct(s: str) -> str:
    """标点与繁简统一归一化：去掉标点空白并转为简体，只留规范汉字/字母/数字。"""
    s = _STRIP.sub("", s)
    return normalize_script(s)


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
        # 纯位值在口播中专用于逐位念年份（如「一七二四」）或单数字；
        # 超过 4 位的纯位值（如「一二三四五六七」）不是合法年份数字
        if len(digits) > 4:
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
            if unit == 10000:
                if last_digit is None and section == 0:
                    # 单独一个「万」不是定量数字（如「万寿山」）
                    return None
                section = (section + (last_digit if last_digit is not None else 0)) * unit
                total += section
                section = 0
                last_digit = None
            else:
                if last_digit is None:
                    # 只有「十」在开头可以省略「一」（「十二」-> 12）；「百」「千」不可省略（如「百年」「逾千年」）
                    if unit == 10:
                        last_digit = 1
                    else:
                        return None
                section += last_digit * unit
                last_digit = None
    if last_digit is not None:
        section += last_digit
    return total + section


def extract_numbers(s: str) -> List[int]:
    """从文本抽出全部可解析的数字，已归一到 int；解析不了的跳过。"""
    s_clean = clean_reign_years(s)
    out = []
    for m in _NUM_RE.finditer(s_clean):
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
