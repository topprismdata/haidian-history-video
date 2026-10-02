"""
haidian_kg/expansion.py
地名 ⇄ 古书 闭包扩展引擎 v3（人工门控的增量图扩展）

本系统不是自动跑到 fixpoint 的 closure loop（spec §0）：循环由人工
admission 事件推进，引擎只做每轮的「发现与登记」。禁止实现
`while graph_changed: ...` 式自动迭代。

身份三层（spec §2.1，P0-1）——字符串名不承担实体身份：
  ToponymOccurrence         文本事实层（机器可自动产生）
  CandidatePlaceHypothesis  实体假说层（保守聚类：每 normalized_form 一假说）
  CanonicalPlaceEntity      正式词条（只有人工闸门能产生，本引擎永不写入）

去重单位是 SourceVisitKey（spec §2.2，P0-3），不是裸 (source_id, division_id)；
遍历严格「先查后加，再挖掘」。

纪律（spec §2.5，不可妥协）：
  1. 引擎只发现，不入库——admitted 恒 []
  2. 机器观察记录不是事实
  3. 每个 occurrence 带 evidence_fact_id / source_id，可溯源
  4. 词表/规则档繁简双字形（G6/G7/挖掘器三次教训，硬性规定）
  5. miner_version / rule_profile_version 进 SourceVisitKey

spec 伪代码名 → 本模块实现名对照（m4）：
  SourceVisitKey       → 同名类型别名（六元组）
  ToponymOccurrence    → 同名 dataclass
  candidates.offer()   → CandidatePlaceHypothesis 聚类（expand 内联保守实现）
  store_observation()  → ExpansionReport.candidates_found 携带 occurrence（落库留给 P1）
"""
from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional, Protocol, Set, Tuple

from .production_exports import KnowledgeBase
from .ontology.epistemic import TextualFact


#: 挖掘器版本 / 规则档版本——两者其一升级即视为「篇卷没挖过」（spec §2.5.5）
#: v4（2026-10-02，holdout run1 闸门裁决）：
#:   1) KnownMention 通道——已知名命中降级记录为 mention 事件，不再静默丢弃
#:      （不进 CandidatePlaceHypothesis 的纪律不变，变的是 mention 层可见性）；
#:   2) rp-v4 句读/回溯边界表扩 Markdown 记号（* - #、书名号《》【】）与
#:      单字边界（今/名/记）——holdout run1 逐条归因的 P0 修复；
#:   3) 纯地名条目（圆明园/万寿山/昆明湖等）移出 _STOPWORDS：它们是地点不
#:      是噪声，「已知名不冒充新发现」改由 expander 的 known 集合路由保证。
#: v5（2026-10-02，holdout run3 闸门裁决）：
#:   1) 通名后缀 +墓/街/房（复合 营房/營房 走旗名穿越）——run3 R 侧 8 条
#:      FN（董四墓×3 / 苏州街×2 / 三旗营房×3）的直接病因：通名不在表，
#:      「专名+通名」双通道同时不可达（suffix-and-cue-missing）；
#:   2) 边界垃圾前缀表 LEADING_STOP_PREFIXES：提取面以非地名成分开头
#:      （的/将/按/建/刹/俗呼/讹写作/俗称/居民/皇家/十处/后世/枪炮/
#:      香山公园/海淀…）→ 剥离前缀后重验证「专名+通名」，剥后不合格
#:      整面拒绝——run3 P 侧 ~10 条垃圾 coverage-gap FP 的共同面头
#:      （的金代行宫园/刹碧云寺/讹写作六郎庄/按八旗/十处天然泉…）；
#:   3) 回溯边界字 +的将將按建依刹（长编层现代汉语功能词；文言官书
#:      低频，回溯不许越过）；旗制集合噪声词 +八旗（建满蒙八旗/按八旗
#:      类子串拦截，整词防不住——正黄旗营房 必须放行）。
MINER_VERSION = "v5"
RULE_PROFILE_VERSION = "rp-v5"


# ---------------------------------------------------------------------------
# 繁简归一（身份归一的地基：官书引文是繁体，档案是简体）
# ---------------------------------------------------------------------------

#: opencc 式字符映射子集——只收本项目语料出现过的异体字；
#: 未收录字符原样保留（生僻字如「礳」繁简同形）
_TRAD_TO_SIMP = {
    "樹": "树", "蕭": "萧", "橋": "桥", "龍": "龙", "莊": "庄",
    # 2026-10-02 run7(v2冻结基线)FN归因:髙 为《日下旧闻考》四库本高频异写,
    # 引擎缺键致 ent_gaoliang_bridge 全漏——冻结后第一道被测题(run8 验收)
    "髙": "高",
    "藍": "蓝", "廠": "厂", "場": "场", "聖": "圣", "菴": "庵",
    "觀": "观", "關": "关", "廟": "庙", "達": "达", "馬": "马",
    "總": "总", "圓": "圆", "園": "园", "內": "内", "務": "务",
    "倉": "仓", "鐵": "铁", "爐": "炉", "鐘": "钟", "磚": "砖",
    "鑲": "镶", "黃": "黄", "紅": "红", "間": "间", "處": "处",
    "萬": "万", "壽": "寿", "護": "护", "軍": "军", "將": "将",
    "營": "营", "門": "门", "陽": "阳", "稱": "称", "舊": "旧",
    "係": "系", "駐": "驻", "鎮": "镇", "廣": "广", "歲": "岁",
    "頃": "顷", "驢": "驴", "車": "车", "樞": "枢", "開": "开",
    "壩": "坝", "議": "议", "參": "参", "領": "领", "備": "备",
    "暢": "畅", "靜": "静", "兩": "两", "個": "个", "點": "点",
    "綺": "绮", "側": "侧", "圍": "围", "竊": "窃", "罷": "罢",
    "賜": "赐", "謂": "谓", "從": "从", "與": "与", "並": "并",
    "則": "则", "數": "数", "築": "筑", "設": "设", "為": "为",
    "於": "于", "諸": "诸",
    "蘇": "苏",   # v5：苏州街（E12）入 KB 后的繁体引文字形
}


def normalize_form(surface: str) -> str:
    """繁体字形 → 简体规范形（逐字映射，未收录字符原样保留）"""
    return "".join(_TRAD_TO_SIMP.get(ch, ch) for ch in surface)


#: 已知「非地名」的干扰词：出现在引文里但不是我们要的地名
#: 繁简双字形——官书引文是繁体，档案是简体（G6/G7/挖掘器三次教训，硬性规定）
#:
#: v4 迁移：纯地名字形（圆明园/清漪园/畅春园/静宜园/静明园/万寿山/昆明湖/
#: 玉泉山/稻田厂 及其繁体）不再是「噪声」——它们是真实地点。G6 时代把它们
#: 停在这里是为了防「已建词条字形冒充新发现」，v4 起该职责由
#: ClosureExpander 的 known 集合路由（KnownMention 通道）承担，miner 层
#: 不再吞掉地名。机构/旗制复合词（圆明园八旗、圆明园副将）与旗名、职官、
#: 纪年仍留本表——它们不是地点。
_STOPWORDS = {
    # 简体
    "皇帝", "天子", "朝廷", "官书", "内务府", "中科院", "考古所",
    "护军", "参领", "护军校", "副将", "总兵", "守备", "千总", "把总",
    "康熙", "雍正", "乾隆", "嘉庆", "万历", "天启", "嘉靖", "成化",
    "正统", "景泰", "天顺", "弘治", "正德", "隆庆", "泰定", "至元",
    "至大", "太平兴国", "昭文馆", "太史院", "翰林",
    "八处", "仓署",
    "两个小旗驻点", "三个小旗驻点", "圆明园副将", "都督河北诸军事",
    "一万间", "一千二百五十间",
    # 繁体（官书引文用字）
    "護軍", "參領", "護軍校", "副將", "總兵", "守備", "千總", "把總",
    "內務府",
    # 泛指词（模式命中但非专名）
    "八處", "八旗", "御道", "倉署", "兩個小旗駐點", "三個小旗駐點",
    "圓明園副將", "都督河北諸軍事", "圓明園八旗", "圆明园八旗",
    # 八旗满洲旗分（旗名有通名形状但是旗籍不是地点）
    "正黄旗", "正黃旗", "鑲黄旗", "鑲黃旗", "正白旗", "鑲白旗",
    "正红旗", "正紅旗", "鑲红旗", "鑲紅旗", "正蓝旗", "正藍旗",
    "鑲蓝旗", "鑲藍旗",
    "镶黄旗", "镶白旗", "镶红旗", "镶蓝旗",
    # 旗制职级/器物/泛称（通名形状但非地点）
    "總旗", "总旗", "小旗", "鐵爐", "铁炉", "牧馬場", "牧马场",
    "北牧馬場", "北牧马场",
    # 文言虚词/量词短语（模式误切的典型产物）
    "一萬間", "一千二百五十間", "四丁未", "六年", "十年",
    # v5 泛指建筑/街市词（「房/街」通道负控制）：正房/厢房/营房/步行街
    # 单独出现是建筑称谓或现代街市，不是地名；复合地名「正黄旗营房」
    # 不受影响——_is_noise 是整词成员判定，不是子串
    "营房", "營房", "正房", "廂房", "厢房", "步行街",
}


# ---------------------------------------------------------------------------
# 身份三层（spec §2.1，P0-1）
# ---------------------------------------------------------------------------

@dataclass
class ToponymOccurrence(object):
    """
    文本事实层：「某文献某位置出现了形状为 X 的字串，上下文像地名」。
    机器可自动产生，但它不是事实（spec §2.5.2）。
    """
    occurrence_id: str
    surface_form: str              # 原样字串（繁体引文保留繁体）
    normalized_form: str           # 归一形（繁→简），聚类的唯一键
    source_id: str                 # 哪部书（M1：mine() 必须写入）
    evidence_fact_id: str          # 哪条引文里出现了它
    extractor_method: str          # cue:坐落 / cue:為 / suffix_scan
    extractor_version: str
    edition_id: Optional[str] = None   # 哪个版本（转录本≠校勘本，由引擎盖章）
    division_id: Optional[str] = None
    text_span: str = ""            # 命中所在的上下文片段
    confidence: str = "low"        # high: 提示词+通名双证 / mid: 单证 / low: 仅模式
    stripped_suffix: Optional[str] = None  # 被剥离的方位后缀
    note: str = ""


@dataclass
class KnownMention(object):
    """
    v4 已知名命中事件（mention 层降级记录，spec §2.5 v4 语义）。

    v3 及以前：已建词条字形（KB label / script_variants / known_forms）
    在引擎层被**静默丢弃**（known_form_hits 只计数）——「已知名不冒充新
    发现」的纪律顺带杀死了 mention 层对已知实体的可见性，holdout v1
    首轮闸门的 recall 因此测不了（6 条 FN 直接来源于此）。

    v4：命中已知名产出 KnownMention——**仍不进 CandidatePlaceHypothesis**
    （「不重复膨胀候选」的纪律原样保留），但事件本身带完整溯源字段，
    供 mention 层评估与后续人工挂接复核。
    """
    surface_form: str              # 原样字串
    normalized_form: str           # 归一形
    source_id: str
    evidence_fact_id: str
    division_id: Optional[str] = None
    edition_id: Optional[str] = None
    extractor_method: str = ""
    extractor_version: str = ""
    text_span: str = ""
    confidence: str = "known"      # 恒为 known：已知名不参与置信竞争

    @classmethod
    def from_occurrence(cls, occ: "ToponymOccurrence") -> "KnownMention":
        return cls(
            surface_form=occ.surface_form,
            normalized_form=occ.normalized_form,
            source_id=occ.source_id,
            evidence_fact_id=occ.evidence_fact_id,
            division_id=occ.division_id,
            edition_id=occ.edition_id,
            extractor_method=occ.extractor_method,
            extractor_version=occ.extractor_version,
            text_span=occ.text_span,
        )


@dataclass
class CandidatePlaceHypothesis(object):
    """
    实体假说层（spec §2.1）：「这批 occurrence 可能指向同一个历史地点」。
    保守聚类：每个 normalized_form 一假说，下挂全部 occurrences——
    一名多书互证保留为 occurrence 列表（修 M2 证据塌缩）。
    """
    normalized_form: str
    occurrences: List[ToponymOccurrence] = field(default_factory=list)
    confidence: str = "low"        # 取成员 occurrence 的最高置信

    @property
    def name(self) -> str:
        return self.normalized_form

    def add_occurrence(self, occ: ToponymOccurrence) -> None:
        self.occurrences.append(occ)
        if _CONF_RANK.get(occ.confidence, 0) > _CONF_RANK.get(self.confidence, 0):
            self.confidence = occ.confidence


_CONF_RANK = {"low": 0, "mid": 1, "high": 2}

#: 去重单位（spec §2.2，P0-3）：(书, 版本, 篇卷, 挖掘器版本, 规则档版本, 所属KB)
#: kb_id 防 M5——每个 KB deep-copy 各自 facts，两词条共引同卷不同切片时
#: 第二个 KB 的独有引文不是「环」，是必须保留的书证
SourceVisitKey = Tuple[str, str, str, str, str, str]


# ---------------------------------------------------------------------------
# 挖书器（spec §2.4 SourceMiner；实现 ToponymMiner，FullTextMiner 留接口）
# ---------------------------------------------------------------------------

#: 中文地名通名后缀表（专名+通名结构：树「村」、安河「桥」、七里「泊」）
#: 繁简双字形——官书引文是繁体，档案是简体（G6/G7/挖掘器三次教训）
#:
#: v5（holdout run3）：+墓（董四墓）/街（苏州街）/房（通用，复合结构走
#: 营房/營房 二字形）——墓/街/房 繁简同形，无需双写；营房/營房 是
#: 「旗名+营房」八旗驻防建置的复合通名，走 _walk_back 的旗名穿越通道
#: （正黄旗营房 整体成词），单字 房 仍受旗边界约束（「X旗房」不裂）。
PLACE_SUFFIXES = (
    # 聚落
    "村", "莊", "庄", "屯", "營", "营", "旗", "府", "坊", "胡同",
    # 聚落·v5 通名补收（holdout run3 R 侧 8 条 FN 的直接病因）
    "墓", "街", "房", "营房", "營房",
    # 水利
    "河", "橋", "桥", "泊", "泉", "閘", "闸", "堰", "渠", "湖", "海",
    # 宗教
    "寺", "菴", "庵", "觀", "观", "廟", "庙", "塔", "殿",
    # 其他
    "山", "墳", "坟", "園", "园", "廠", "厂", "場", "场", "倉", "仓",
    "窯", "窑", "店", "口", "關", "关", "嶺", "岭", "峪", "澱", "淀",
)
_SUFFIX_SET = frozenset(PLACE_SUFFIXES)

#: 复合建筑通名（旗名穿越通道，v5）：这些二字后缀命中时允许回溯越过
#: 「旗」边界——「正黄旗营房」是八旗驻防建置地名，旗名是专名头的一部分；
#: rp-v3 的旗边界只保护单字 营/旗 通名（「鑲黄旗營」不许裂成 X旗營）
_CROSS_FLAG_SUFFIXES = frozenset(("营房", "營房"))

#: 方位后缀（「樹村西邊」须剥离为「樹村」）
DIRECTION_SUFFIXES = ("西邊", "東邊", "南邊", "北邊",
                      "西边", "东边", "南边", "北边",
                      "之西", "之東", "之东", "之南", "之北",
                      "西北", "東北", "东北", "西南", "東南", "东南")

#: v5 边界垃圾前缀表（holdout run3 P 侧归因）：提取面以这些成分开头 =
#: 句法杂缀/俗语引导/通用集合名词，不是地名头。规则：剥离前缀后重验证
#: 「专名+通名」，剥后不合格整面拒绝（strip_leading_stop_prefix）。
#: run3 实证垃圾面：的金代行宫园 / 俗呼一溜边山 / 建满蒙八旗（建 在
#: 边界字表，此处兜 cue 窗口）/ 按八旗 / 十处天然泉 / 皇家宫廷内湖 /
#: 讹写作六郎庄 / 刹碧云寺 / 海淀温泉 / 海淀区三里河 / 海淀凤凰岭 /
#: 后世三山五园 / 枪炮演武场 / 香山公园香山。
#: 繁简双字形（將）——G6/G7 硬性规定；最长前缀优先排序
#: （海淀公园/海淀区 → 海淀：先剥短的会产出「公园香山」「区三里河」
#: 类二次垃圾）。剥后余量 <2 字不剥：真名「海淀」「海淀镇」不误伤
#: （「步行街」类整词通用词走 _STOPWORDS 整词拦截）。
LEADING_STOP_PREFIXES = (
    # 通用名词/区划前缀
    "香山公园", "海淀公园", "海淀区", "海淀",
    # 俗语/讹写引导
    "讹写作", "俗称", "俗呼",
    # 通用集合名词开头
    "居民", "皇家", "十处", "后世", "枪炮",
    # 结构助词/动词/介词（与 _STOP_CHARS 同源；此处兜 cue 窗口路径的面头）
    "的", "将", "將", "按", "建", "依", "刹",
)
_LEADING_PREFIXES_SORTED = tuple(
    sorted(LEADING_STOP_PREFIXES, key=len, reverse=True))


def strip_leading_stop_prefix(name):
    """剥面头的非地名前缀并重验证；返回 (剥离后名, 剥离链)。

    - 无前缀命中：原样返回（「剥不动」≠「拒绝」，交还调用方噪声判定）。
    - 剥离余量必须 ≥2 字：余量不足不剥（「海淀」「海淀镇」类真名不误伤）。
    - 剥过 → 重验证：长度 2–6、仍以通名后缀收尾、头不得是回溯边界字
      （「居民依墓」剥出「依墓」，头 依 是动词边界 → 整面拒绝）；
      任一不过返回 (None, peeled)，调用方整面拒绝。
    """
    cur = name
    peeled = []
    while True:
        for p in _LEADING_PREFIXES_SORTED:
            if cur.startswith(p) and len(cur) - len(p) >= 2:
                peeled.append(p)
                cur = cur[len(p):]
                break
        else:
            break
    if not peeled:
        return name, peeled
    if not (2 <= len(cur) <= 6):
        return None, peeled
    if not any(cur.endswith(s) for s in PLACE_SUFFIXES):
        return None, peeled
    if cur[0] in _STOP_CHARS:
        return None, peeled
    return cur, peeled

#: 繁简双字形的机构/建筑通名单字（单独成词时不是专名，但作为后缀合法）
GENERIC_SINGLE = set("村莊庄屯營营府河橋桥泊泉閘闸堰渠湖山園园廠厂場场倉仓窯窑店铺關关嶺岭峪")

#: 句读（切短语/截窗口用）
#: rp-v4：扩 Markdown 记号（* - #）与书名号/方头括号（《》【】）——
#: holdout run1 逐条归因：**蓝靛厂/《圆明园/- 牛栏庄 类记号渗入与
#: walkback 越界（「- **外火器营」8 字）同源于此表缺失
_PUNCT_CHARS = "，。、；：！？「」『』（）《》【】*-#"
#: 短语切分（单一来源，_phrase_hits 与归因镜像共用同一张表）
_PHRASE_SPLIT_RE = re.compile("[%s]" % re.escape(_PUNCT_CHARS))

#: 提示词锚点（A 法线索词）
_CUE_MARKERS = ("為", "曰", "有", "坐落", "跨其上", "即")

#: 回溯边界字（M3）：介词/虚词/连词/限定词/动词——专名头不可能越过它们。
#: 繁简并收；注意「通」不在表内（通惠河/通稱共用），「三」「北」不在表内
#: （西三旗/北安河桥是专名头）——lexicalized 方位词误伤面见 spec §四.3
_STOP_CHARS = set(
    # 介词/虚词/连词/助词
    "於于在自從从往到為为之其與与及和並并而則则皆即乃且等者們们因中"
    # 限定词/量词
    "每各諸诸數数兩两个個此這这那"
    # 动词（含提示词锚点本身）
    "出入至築筑開开引灌設设駐驻紮扎移改奏議议始有曰謂谓幸圍围遁竊窃"
    "跨存增添罷罢賜赐禁理以著稱称惟落坐葬轄辖"
    # 旗籍通名：旗名内部不可回溯穿越（鑲黄旗營 不许裂成 X旗營/旗營）
    "旗"
)
#: rp-v4 单字边界（holdout run1 归因）：今（今大觉寺/今海淀温泉）、
#: 名（名娘娘府/名健锐营）、记（卷九十八记外火器营）——专名头不可能
#: 越过它们；不收 北/三/西（lexicalized 方位头：西三旗/北安河 先例）
_STOP_CHARS |= set("今名记")
#: rp-v5 单字边界（holdout run3 归因）：长编层现代汉语功能词——
#: 的（的金代行宫园）、将（将万寿山后湖）、按（按八旗）、建（建满蒙八旗，
#: 兼保「敕建泉宗庙」类被截断书证的干净回溯）、依（居民依墓成村）、
#: 刹（名刹碧云寺）。文言官书低频（將 并收），回溯不许越过它们
_STOP_CHARS |= set("的将將按建依刹")


class SourceMiner(Protocol):
    """挖书器接口（spec §2.4）。实现：ToponymMiner；FullTextMiner 预留。"""

    def mine(self, source_id: str, division_id: str,
             facts: List[TextualFact]) -> List[ToponymOccurrence]:
        ...


#: 纪年/帝号模式（繁简）——_is_noise 与评估器归因镜像共用
_REIGN_PREFIXES = ("康熙", "雍正", "乾隆", "嘉庆", "萬曆", "万历", "天啟", "天启",
                   "嘉靖", "成化", "至元", "至大", "泰定", "太平興國", "太平兴国")
#: 官职/机构模式（繁简）——同上共用
#: v5：+八旗（旗制集合词）：「建满蒙八旗」「按八旗」类回溯产物整词不在
#: 停用词表，只能子串拦；「正黄旗营房」不含 八旗 子串，不受影响
_NOISE_KEYWORDS = ("護軍", "护军", "副將", "副将", "總兵", "总兵", "內務府", "内务府",
                   "御道", "倉署", "仓署", "碾房", "都督", "八旗")


class ToponymMiner(object):
    """
    混合策略地名挖掘器 v3：
      A. 提示词模式（為/曰/有/坐落…）——锚点后开窗
      B. 通名后缀扫描——召回无线索词但符合「专名+通名」结构的
      C. 方位后缀剥离——樹村西邊 → 樹村
      D. 置信度分级 high（双证）/ mid（单证）/ low，人工审阅从高往低

    M3 核心修复：命中通名后缀后，从后缀向前回溯到标点/提示词锚点/
    虚词边界，取出干净专名头——
      「水流自永定河入西山」→ 永定河（而非「永定河入西山」）
      「內務府於青龍橋設稻田廠」→ 青龍橋、稻田廠（绝不产出「龍橋設稻田廠」）

    为什么不直接上 jieba/HanLP：
      文言文分词/NER 在现代语料模型上误切率高（实测风险），
      而「专名+通名」是中文地名强结构，后缀词典便宜、可解释、可控。
    """

    def __init__(self, known_names: Optional[Set[str]] = None):
        self.known_names = set(known_names or [])
        self._stopwords = set(_STOPWORDS)
        self._seq = 0

    # ---------- 接口 ----------

    def mine(self, source_id: str, division_id: str,
             facts: List[TextualFact]) -> List[ToponymOccurrence]:
        """挖一个篇卷。同一 fact 内同形只发一次；跨 fact/跨卷保留（互证）"""
        out: List[ToponymOccurrence] = []
        self._seq = 0
        emitted: Set[Tuple[str, str]] = set()   # (fact_id, surface_form)
        for f in facts:
            if f.division_id != division_id:
                continue
            text = f.verbatim_quote
            # A. 提示词锚点：锚点后开窗，窗内找通名后缀并回溯
            for marker in _CUE_MARKERS:
                start = 0
                while True:
                    i = text.find(marker, start)
                    if i < 0:
                        break
                    start = i + len(marker)
                    for occ in self._cue_hits(text, i, marker, f, source_id):
                        self._collect(out, emitted, occ)
            # B. 通名后缀扫描（无线索词也能召回）
            for occ in self._phrase_hits(text, f, source_id):
                self._collect(out, emitted, occ)
        return out

    # ---------- 内部 ----------

    def _collect(self, out: List[ToponymOccurrence], emitted: Set[Tuple[str, str]],
                 occ: ToponymOccurrence) -> None:
        key = (occ.evidence_fact_id, occ.surface_form)
        if key in emitted:
            return
        emitted.add(key)
        out.append(occ)

    def _cue_hits(self, text: str, marker_pos: int, marker: str,
                  fact: TextualFact, source_id: str) -> List[ToponymOccurrence]:
        """锚点后开窗（截句读、12 字窗），窗内后缀回溯；无后缀则退回窗口截取"""
        window = text[marker_pos + len(marker):]
        cut = len(window)
        for j, ch in enumerate(window):
            if ch in _PUNCT_CHARS:
                cut = j
                break
        window = window[:cut][:12].strip()
        if not window:
            return []
        hits = self._suffix_hits(window, fact, source_id,
                                 method="cue:%s" % marker, cue=True)
        if hits:
            return hits
        # 无通名后缀的线索词命名：生僻通名（水礳）靠这条保住（spec §2.4）
        name, stripped = self._strip_direction(window)
        # v5：面头非地名前缀剥离 + 重验证（剥后不合格整面拒绝）
        name, peeled = strip_leading_stop_prefix(name)
        if name is None or not (2 <= len(name) <= 6) or self._is_noise(name):
            return []
        note = "提示词「%s」窗口「%s」" % (marker, window)
        if peeled:
            note += "←剥前缀「%s」" % "+".join(peeled)
        return [self._emit(name, fact, source_id, method="cue:%s" % marker,
                           note=note,
                           conf="mid", span=marker + window, stripped=stripped)]

    def _phrase_hits(self, text: str, fact: TextualFact,
                     source_id: str) -> List[ToponymOccurrence]:
        """B 法：按句读切短语，短语内每个通名后缀命中都回溯取专名头"""
        out: List[ToponymOccurrence] = []
        for phrase in _PHRASE_SPLIT_RE.split(text):
            phrase = phrase.strip()
            if phrase:
                out.extend(self._suffix_hits(phrase, fact, source_id,
                                             method="suffix_scan", cue=False))
        return out

    def _suffix_hits(self, window: str, fact: TextualFact, source_id: str,
                     method: str, cue: bool) -> List[ToponymOccurrence]:
        """窗口内每个通名后缀命中 → 回溯专名头 → 干净名（M3 核心路径）。
        从右往左扫：已采纳的命中区间不再接受重叠命中——
        「安河橋」不许裂出子词「安河」（子串让位于更长的干净名）"""
        out: List[ToponymOccurrence] = []
        taken: List[Tuple[int, int]] = []       # 已采纳 (head, end) 区间
        for k in range(len(window) - 1, -1, -1):
            for size in (2, 1):        # 多字后缀（胡同）优先
                start = k - size + 1
                if start < 0:
                    continue
                suffix = window[start:k + 1]
                if len(suffix) != size or suffix not in _SUFFIX_SET:
                    continue
                head = self._walk_back(
                    window, start,
                    cross_flags=suffix in _CROSS_FLAG_SUFFIXES)
                name = window[head:k + 1]   # 专名头 + 通名后缀本身
                if not (2 <= len(name) <= 6):
                    break               # 该命中作废，扫下一个后缀字
                if self._is_noise(name):
                    break
                # v5：面头非地名前缀剥离 + 重验证（剥后不合格整面拒绝）
                cleaned, peeled = strip_leading_stop_prefix(name)
                if cleaned is None:
                    break
                if any(head < e and k + 1 > s for s, e in taken):
                    break               # 与已采纳命中重叠（子词命中）
                taken.append((head, k + 1))
                note = "%s「%s」" % ("提示词回溯" if cue else "后缀扫描",
                                    window[max(0, head - 2):k + 1])
                if peeled:
                    note += "←剥前缀「%s」" % "+".join(peeled)
                out.append(self._emit(
                    cleaned, fact, source_id, method=method,
                    note=note,
                    conf="high" if cue else "mid",
                    span=window, stripped=None))
                break
        out.reverse()   # 恢复从左到右的出现顺序
        return out

    @staticmethod
    def _walk_back(window: str, suffix_start: int,
                   cross_flags: bool = False) -> int:
        """从后缀起点向左回溯到标点/锚点词/虚词边界，返回专名头下标（M3）。

        cross_flags（v5）：营房类复合建筑通名允许穿越「旗」边界——
        「正黄旗营房」是八旗驻防建置地名，旗名是专名头的一部分；穿越后
        继续按边界字回溯（「建满蒙八旗营房」在建 处截停 → 7 字超长作废）。
        rp-v3 的旗边界语义不变：单字 营/旗 通名仍不许穿越（「鑲黄旗營」
        不得裂出 X旗營/旗營）。
        """
        j = suffix_start
        while j > 0 and window[j - 1] not in _STOP_CHARS:
            j -= 1
        if cross_flags:
            while j > 0 and window[j - 1] == "旗":
                j -= 1
                while j > 0 and window[j - 1] not in _STOP_CHARS:
                    j -= 1
        return j

    def _clip(self, seg: str) -> Optional[str]:
        for j, ch in enumerate(seg):
            if ch in _PUNCT_CHARS:
                seg = seg[:j]
                break
        return seg.strip() or None

    def _strip_direction(self, name: str) -> Tuple[str, Optional[str]]:
        for suf in DIRECTION_SUFFIXES:
            if name.endswith(suf) and len(name) > len(suf):
                return name[:-len(suf)], suf
        return name, None

    def _has_place_suffix(self, name: str) -> bool:
        return any(name.endswith(s) for s in PLACE_SUFFIXES)

    def _emit(self, name: str, fact: TextualFact, source_id: str, method: str,
              note: str, conf: str, span: str,
              stripped: Optional[str] = None) -> ToponymOccurrence:
        self._seq += 1
        return ToponymOccurrence(
            occurrence_id="occ:%s:%s:%d" % (fact.id, method, self._seq),
            surface_form=name,
            normalized_form=normalize_form(name),
            source_id=source_id,                     # M1：溯源必填
            evidence_fact_id=fact.id,
            extractor_method=method,
            extractor_version=MINER_VERSION,
            division_id=fact.division_id,
            text_span=span,
            confidence=conf,
            stripped_suffix=stripped,
            note=note,
        )

    def _is_noise(self, name: str) -> bool:
        """繁体、简体两个字形都要过一遍（G6/G7 硬性规定）"""
        forms = (name, normalize_form(name))
        if any(f in self._stopwords for f in forms):
            return True
        if any(f in self.known_names for f in forms):
            return True
        if any(ch.isdigit() for ch in name):
            return True
        for form in forms:
            for reign in _REIGN_PREFIXES:
                if form.startswith(reign):
                    return True
            for kw in _NOISE_KEYWORDS:
                if kw in form:
                    return True
        return False


# ---------------------------------------------------------------------------
# 闭包引擎
# ---------------------------------------------------------------------------

@dataclass
class ExpansionReport(object):
    seeds: List[str] = field(default_factory=list)
    entries_visited: List[str] = field(default_factory=list)
    sources_mined: List[str] = field(default_factory=list)
    candidates_found: List[CandidatePlaceHypothesis] = field(default_factory=list)
    admitted: List[str] = field(default_factory=list)
    rejected: List[Tuple[str, str]] = field(default_factory=list)  # (name, reason)
    #: 「没重复挖」三类事件分账（原 cycles_avoided 混计不可归因，M2/M5）
    revisited_visits: int = 0       # SourceVisitKey 已登记 → 跳过
    known_form_hits: int = 0        # 命中已建词条字形 → 仅计数
    duplicate_candidates: int = 0   # 同名同证重复观察 → 并入已有假说
    #: v4：已知名命中事件（known_form_hits 的明细版），不进 candidates_found
    known_mentions: List[KnownMention] = field(default_factory=list)

    def render(self) -> str:
        lines = ["闭包扩展报告 v3（miner=%s / rule_profile=%s）"
                 % (MINER_VERSION, RULE_PROFILE_VERSION)]
        lines.append("  种子词条: %s" % "、".join(self.seeds))
        lines.append("  遍历词条: %d" % len(self.entries_visited))
        lines.append("  挖过的篇卷: %d 个（%s）" % (
            len(self.sources_mined), "、".join(self.sources_mined)))
        lines.append("  发现候选假说: %d 个" % len(self.candidates_found))
        for h in self.candidates_found:
            srcs = "、".join(sorted({o.source_id for o in h.occurrences}))
            lines.append("    - %-8s [%s] 书证 %d 处《%s》"
                         % (h.normalized_form, h.confidence,
                            len(h.occurrences), srcs))
            for o in h.occurrences:
                lines.append("        · 「%s」 %s @%s（引文 %s）%s"
                             % (o.surface_form, o.extractor_method,
                                o.division_id, o.evidence_fact_id, o.note))
        lines.append("  重访篇卷（VisitKey 已登记）: %d" % self.revisited_visits)
        lines.append("  命中已建词条字形（跳过）: %d" % self.known_form_hits)
        lines.append("  已知实体 mention（v4 降级记录）: %d" % len(self.known_mentions))
        lines.append("  重复候选观察（并入假说）: %d" % self.duplicate_candidates)
        lines.append("  收录: %d / 拒绝: %d"
                     % (len(self.admitted), len(self.rejected)))
        for n, why in self.rejected:
            lines.append("    × %s：%s" % (n, why))
        return "\n".join(lines)


class ClosureExpander(object):
    """
    地名 ⇄ 古书 闭包遍历（人工门控的增量扩展，spec §0/§2.2）。

    用法：
        expander = ClosureExpander(seed_kbs=[kb1, kb2, kb3, kb4])
        report = expander.expand()
        print(report.render())

    关键纪律：
    - 新候选只是「假说」，不自动入库；入库必须过人工九维闸门
    - SourceVisitKey 先查后加，再挖掘（spec §2.2 遍历伪代码）
    - expand() 无跨调用状态：同一 expander 重复 expand 结果恒等
    """

    def __init__(self, seed_kbs: List[KnowledgeBase],
                 miner: Optional[SourceMiner] = None,
                 known_forms: Optional[Set[str]] = None,
                 adversarial: Optional[Tuple[str, str]] = None):
        self.seeds = list(seed_kbs)
        self.miner = miner if miner is not None else ToponymMiner()
        self.known_forms: Set[str] = set(known_forms or [])
        self.adversarial = adversarial
        #: kb 身份进 VisitKey（M5）：同一 (书,卷) 在不同 KB 里各挖各的
        self._kb_ids: Dict[int, str] = {
            id(kb): "kb%d" % i for i, kb in enumerate(self.seeds)}

    def expand(self) -> ExpansionReport:
        rep = ExpansionReport()

        # 1) 已知字形表 = 调用方 known_forms + 全部种子的 label + script_variants
        #    （C2：Appellation.script_variants 是异体/讹字，必须一并算「已知晓」，
        #     否则已建词条的繁体字形会以高置信冒充新发现）
        known: Set[str] = {normalize_form(f) for f in self.known_forms}
        for kb in self.seeds:
            for a in kb.appellations.values():
                rep.seeds.append(a.label)
                rep.entries_visited.append(a.label)
                known.add(normalize_form(a.label))
                for v in a.script_variants:
                    known.add(normalize_form(v))

        # 2) 登记种子引用的篇卷：先查后加，再挖掘（spec §2.2）
        seen_visits: Set[SourceVisitKey] = set()
        queue: List[Tuple[str, str, str, KnowledgeBase]] = []
        for kb in self.seeds:
            kb_id = self._kb_ids[id(kb)]
            for d in kb.divisions.values():
                work_id = d.source_id
                src = kb.sources.get(work_id)
                edition_id = getattr(src, "base_edition", None) or "未标注"
                key: SourceVisitKey = (work_id, edition_id, d.id,
                                       MINER_VERSION, RULE_PROFILE_VERSION,
                                       kb_id)
                if key in seen_visits:
                    rep.revisited_visits += 1
                    continue
                seen_visits.add(key)            # 立即登记，再挖
                queue.append((work_id, edition_id, d.id, kb))
                rep.sources_mined.append(d.id)

        # 3) 挖书 → 聚类（保守：每 normalized_form 一假说，全 occurrences 下挂）
        hypo_by_form: Dict[str, CandidatePlaceHypothesis] = {}
        seen_sigs: Dict[str, Set[Tuple[str, str]]] = {}
        for work_id, edition_id, division_id, kb in queue:
            occs = self.miner.mine(work_id, division_id, list(kb.facts.values()))
            for occ in occs:
                if occ.edition_id is None:
                    occ.edition_id = edition_id
                if occ.normalized_form in known:
                    # v4：降级记录为 KnownMention（mention 层可见），
                    # 不再静默丢弃；计数器语义保持不变
                    rep.known_form_hits += 1
                    rep.known_mentions.append(
                        KnownMention.from_occurrence(occ))
                    continue
                hyp = hypo_by_form.get(occ.normalized_form)
                if hyp is None:
                    hyp = CandidatePlaceHypothesis(normalized_form=occ.normalized_form)
                    hypo_by_form[occ.normalized_form] = hyp
                    rep.candidates_found.append(hyp)
                    seen_sigs[occ.normalized_form] = set()
                sig = (occ.evidence_fact_id, occ.surface_form)
                if sig in seen_sigs[occ.normalized_form]:
                    rep.duplicate_candidates += 1
                    continue
                seen_sigs[occ.normalized_form].add(sig)
                hyp.add_occurrence(occ)

        # 4) 候选不自动入库——只登记为假说，等人工/闸门裁决
        rep.admitted = []           # 引擎只负责发现；入库由闸门+人工
        rep.rejected = []
        return rep
