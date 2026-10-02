"""
haidian_kg/calibration/bridges.py
桥类词条（E8 高梁桥 + E2 安河桥）—— 海淀历史地名知识库入库模块

数据唯一来源（两份 v2 冻结研究档案，不凭印象补写）：
  - gaoliangqiao_video/research.md（E8，GPT 复查拦 16 条硬错误后的 v2 冻结版）
  - anheqiao_video/research.md（E2，ChatGPT 两轮复查后的 v2.1 冻结版）
与校准集 gaoliang.py 的关系：gaoliang.py 是本体 v2.1 的端到端校准数据集
（高梁水/西城闸/车箱渠视角）；本模块是 E8/E2 两集交付档案的正式词条入库，
按桥类实体分解（桥、闸、战场、行宫、新旧两桥、村、仓），实体 ID 各自独立。

证据分级映射（两档 research.md → 本体表达，绝不混级）：
  [文献记载]     → TextualFact（古籍繁体逐字引文）+ VERIFIED 采信
  [档案]/[L1转引] → 1929 北平工务局档案 facts + translator_note 标转引（原档未目验→暂按L2）
  [后世记载]     → 与 [文献记载] 分级并列，同挂一条 state 但写明层级
  [后世军事分析] → Proposition.alternative_explanations（不得写成史籍因果）
  [民间传说]     → FOLK_LEGEND 采信 + 指称 provenance（高亮赶水）
  [存疑待考]     → CONTESTED + alternative_relations（金元闸同址、现桥尺寸、木桩年代）
  [内部考据 L5]  → 一律不入库（木桩 1400—1475 区间禁入）

E8 红线落位（research.md §11 择要 → 机器判据）：
  - 979 战场在古高梁河畔（落点诸说并存），与 1292 年始建的高梁桥分属两个实体；
    「桥下即战场」在本库结构上不可通过（979 年桥无状态 → UNTESTABLE≠通过）
  - 闸已毁：ent_gaoliang_gate 状态止于 1911 断代边界，「2026 仍在服役」不可通过
  - 金承安三年(1198)已有闸记录；1292 是郭守敬重建系统化，金元同址不能画等号（UNCERTAIN）
  - 现桥尺寸/孔数/望柱数三源冲突 → 一律不入库，只写「历代重修，1980—1982 大改，非完整原状」
  - 字形：本库一律「高梁桥/高梁河」（木字底）；国保遗产点名「高粱闸」（米字底）单独建名并注明；
    「高亮桥」为传说名（FOLK_LEGEND），不建「高亮→高粱→高梁」得名链
  - 倚虹堂（桥西）与船坞（南岸）分列两建筑；长河/转河分界是今名，挂当代状态
E2 红线落位（research.md §八 → 机器判据）：
  - 桥史两套文献系统正面冲突（系统A 1724木桥 vs 系统B 1929档案元以前/1449/1720/1886）
    → CONTESTED 采信 + 身份断言列双方，不做裁决；1929 原档未目验不宣布「元以前始建」
  - 两河两桥严格分离：旧桥跨清河（名有效至 1964），1965 京密引水渠另址建新桥；
    「古桥一直跨京密引水渠」在本库为 DISPROVEN（附反驳事实）
  - 安河桥村地名出现年代＝明代（2025 名录），不证考古聚落形成；咸丰成村说撤稿
  - 丰益仓雍正七年(1729)八旗俸饷仓（官书）；「66300 石/八万兵丁」数字链撤稿不入库，
    审计层对混说数字直接 BLOCK
模块导出与现有词条同构：SOURCES / DIVISIONS / FACTS / ENTITIES / STATES /
IDENTITIES / APPELLATIONS / REFERENCES / TRANSFORMATIONS / PROPOSITIONS /
ADOPTIONS / AGGREGATES。
"""
from typing import List

from ..ontology.temporal import (
    CalibrationTable, DatePoint, Era, GregorianDate, ReignYear, TimeSpan,
)
from ..ontology.epistemic import (
    BeliefAdoption, EpistemicStatus, HistoricalSource, Proposition,
    SourceCategory, SourceDivision, TextualFact,
)
from ..ontology.spatiotemporal import (
    Appellation, AppellationKind, DiachronicIdentityAssertion,
    HistoricalFeatureState, IdentityRelation, PersistentSpatialEntity,
    PhysicalThingKind, PlaceAggregate, PlaceTransformation,
    PlaceTransformationEvent, ReferentialAssertion,
)
from .bibliography import source_by_title

CAL = CalibrationTable.CN_ASTRONOMICAL_ALMANAC


def _ry(era, title, n, verbatim, month=None, ganzhi=None):
    """文献纪年表达（「文献怎么写的」），不做换算——换算挂 DatePoint.gregorian"""
    return ReignYear(era=era, reign_title=title, year_within_reign=n,
                     lunar_month=month, ganzhi=ganzhi, verbatim=verbatim)


def _dt(y, tag, reign=None, precision="year"):
    return DatePoint(id=tag, label=str(y), precision=precision, reign_year=reign,
                     gregorian=GregorianDate(year=y, calibration=CAL))


def _ts(y1, y2, tag):
    return TimeSpan(id=tag, label="%d-%d" % (y1, y2),
                    begin=_dt(y1, tag + "_b"), end=_dt(y2, tag + "_e"))


# ==================================================================
# 1. 文献与篇卷（一律取自统一书目表，一书一条，禁止在此另建）
# ==================================================================

SOURCES: List[HistoricalSource] = [
    # E8 高梁桥侧
    source_by_title("金史"),
    source_by_title("元史"),
    source_by_title("袁中郎全集"),
    source_by_title("帝京景物略"),
    source_by_title("钦定日下旧闻考"),
    source_by_title("三山五园地区传统地名保护名录（第二批）"),
    source_by_title("北京市文物局公开文保资料"),
    source_by_title("海淀区人民政府公开史地沿革资料"),
    source_by_title("辽史"),
    source_by_title("宋史"),
    source_by_title("大金集礼"),
    # E2 安河桥侧
    source_by_title("钦定历代职官表"),
    source_by_title("北平市工务局郊区桥梁档案"),
    source_by_title("安河桥小史（老北京网）"),
    source_by_title("三山五园水系变迁"),
]

DIVISIONS: List[SourceDivision] = [
    # ---- 古籍篇卷（卷次待核者不得臆标） ----
    SourceDivision(id="div_jinshi_zhaguan", source_id="src_jinshi",
                   volume_number="卷次待核", section_title="河渠闸堰·高梁河闸条（承安三年）"),
    SourceDivision(id="div_yuanshi_hequ_gl", source_id="src_yuanshi",
                   volume_number="河渠志", section_title="通惠河（至元二十九年）"),
    SourceDivision(id="div_yhd_ylqj", source_id="src_yuanzhonglang",
                   volume_number="卷次待核", section_title="游高梁桥记"),
    SourceDivision(id="div_djjwl_glb", source_id="src_dijingjingwulue",
                   volume_number="卷次待核", section_title="高梁桥条（清明踏青）"),
    SourceDivision(id="div_rxjwkc_gl", source_id="src_rxjwkc",
                   volume_number="卷次待核", section_title="高梁桥条（南北牌坊题字）"),
    SourceDivision(id="div_liaoshi_84_gl", source_id="src_liaoshi",
                   volume_number="卷八十四", section_title="列传第十四·耶律休哥"),
    SourceDivision(id="div_songshi_tz_gl", source_id="src_songshi",
                   volume_number="本纪第四", section_title="太宗一"),
    SourceDivision(id="div_zhiguan_v8", source_id="src_lidaizhiguangbiao",
                   volume_number="卷八", section_title="户部仓场衙门表·丰益仓"),
    SourceDivision(id="div_dajinjili_daihe", source_id="src_dajinjili",
                   volume_number="卷次待核", section_title="金代漕渠闸堰相关条（待核）"),
    # ---- 政府名录（第二批） ----
    SourceDivision(id="div_minglu2_gl", source_id="src_minglu_2",
                   volume_number="第二批", section_title="高梁桥条（标准用字纠偏）"),
    SourceDivision(id="div_minglu2_ahc", source_id="src_minglu_2",
                   volume_number="第二批", section_title="安河桥村条（地名出现年代与村界四至）"),
    # ---- 机构公开资料（记录式陈述，与古籍引文分层） ----
    SourceDivision(id="div_wjbz_gl", source_id="src_wjbz_open",
                   volume_number="文保公开资料", section_title="高梁桥沿革与大运河遗产点"),
    SourceDivision(id="div_hd_yht", source_id="src_hd_gov_open",
                   volume_number="公开沿革", section_title="长河御道与倚虹堂条"),
    SourceDivision(id="div_hd_zhuanhe", source_id="src_hd_gov_open",
                   volume_number="公开沿革", section_title="长河转河今名分界"),
    SourceDivision(id="div_hd_anhe1965", source_id="src_hd_gov_open",
                   volume_number="公开沿革", section_title="京密引水渠与安河新桥条"),
    # ---- E2 档案与地方文史 ----
    SourceDivision(id="div_bma_anhe", source_id="src_bma_1929",
                   volume_number="郊区桥梁调查", section_title="安河桥条（1929）"),
    SourceDivision(id="div_anhe_xiaoshi", source_id="src_anheqiao_xiaoshi",
                   volume_number="全一卷", section_title="安河桥小史（系统A·地方文史）"),
    SourceDivision(id="div_sxwj_muzhuang", source_id="src_sxwj",
                   volume_number="出土实物图", section_title="安河桥下明代木桩（2009清河河底施工发现）"),
]


# ==================================================================
# 2. 文本事实（古籍繁体逐字引文；机构/档案为记录式陈述，分层不混）
# ==================================================================

FACTS: List[TextualFact] = [
    # ---- 金史：承安三年已有闸（堵「1292 第一道闸」） ----
    TextualFact(
        id="tf_jinshi_1198", division_id="div_jinshi_zhaguan",
        verbatim_quote="命勿毀高梁河閘，從民灌溉",
        attested_string="高梁河閘",
        source_year=_dt(1345, "dt_jinshi",
                        _ry(Era.YUAN, "至正", 5, "元至正五年前后成书")),
        translator_note="引文自研究档案v2（简体）转写为通行繁体；逐字核对以中华书局"
                        "点校本《金史》为准；志内篇次卷次待核",
    ),
    # ---- 元史：至元二十九年郭守敬引水工程（桥闸之始建锚年） ----
    TextualFact(
        id="tf_yuanshi_1292_tonghui", division_id="div_yuanshi_hequ_gl",
        verbatim_quote="至元二十九年，枢密院奏開通惠河，閘壩皆用木。",
        attested_string="至元二十九年",
        source_year=_dt(1345, "dt_yuanshi_gl"),
        translator_note="1292年为郭守敬引白浮、玉泉诸水汇瓮山泊—高梁河体系的工程纪年；"
                        "金代闸（1198）与元代闸是否同址同一构筑物不能画等号（见身份断言）",
    ),
    # ---- 袁宏道《游高梁桥记》：京师最胜地（篇名红线：不写《琼花斋集》） ----
    TextualFact(
        id="tf_yhd_ylqj", division_id="div_yhd_ylqj",
        verbatim_quote="高梁橋在西直門外，京師最勝地也。兩水夾堤，垂楊十餘里，"
                       "流急而清，魚之沉水底者，鱗鬣皆見。",
        attested_string="京師最勝地",
        translator_note="篇名《游高梁桥记》（收入《袁中郎全集》），不得写作《琼花斋集》；"
                        "引文自研究档案v2转写繁体，逐字核对以点校本为准",
    ),
    # ---- 帝京景物略：清明踏青（刘侗、于奕正同撰，周损编辑——不得说一人所撰） ----
    TextualFact(
        id="tf_djjwl_taqing", division_id="div_djjwl_glb",
        verbatim_quote="歲清明，桃柳當候，岸草遍矣，都人踏青高梁橋。",
        attested_string="踏青高梁橋",
        translator_note="《帝京景物略》为刘侗、于奕正同撰，周损编辑成书",
    ),
    # ---- 日下旧闻考：南北牌坊题字（北面是「資安」不是「姿安」） ----
    TextualFact(
        id="tf_rxjwkc_paifang", division_id="div_rxjwkc_gl",
        verbatim_quote="南牌坊南面曰長源，北面曰永澤；北牌坊北面曰資安，南面曰廣潤。",
        attested_string="資安",
        translator_note="据研究档案v2转述《日下旧闻考》；原典逐字句待核，"
                        "重点核对北面题字为「資安」不作「姿安」",
    ),
    # ---- 辽史/宋史：979 高梁河之战（乘驴车=[文献记载]；分级见命题层） ----
    TextualFact(
        id="tf_liaoshi_zhuozhou", division_id="div_liaoshi_84_gl",
        verbatim_quote="宋主僅以身免，至涿州，竊乘驢車遁去。",
        attested_string="乘驢車",
        source_year=_dt(1344, "dt_liaoshi_gl"),
        translator_note="地望是涿州，不是任何后世桥下；引文自研究档案转写繁体，"
                        "逐字核对以点校本为准",
    ),
    TextualFact(
        id="tf_songshi_979", division_id="div_songshi_tz_gl",
        verbatim_quote="太平興國四年，帝幸城南，圍幽州四十餘日。",
        attested_string="圍幽州",
        source_year=_dt(1345, "dt_songshi_gl"),
        translator_note="战役纪年：宋太平兴国四年＝辽景宗乾亨元年（不用「辽保宁十一年」）",
    ),
    # ---- 文物局公开资料：1980 大改 / 2003 公路桥 / 国保高粱闸 / 闸已毁 ----
    TextualFact(
        id="tf_wjbz_1980", division_id="div_wjbz_gl",
        verbatim_quote="桥历代重修，清代有重要重修；1980年代初展宽高梁桥路时重修高梁桥"
                       "（约1980—1982）；今天看到的不是完整的原状古桥。",
        attested_string="重修高梁桥",
        translator_note="现桥尺寸/孔数/望柱数三源冲突、缺文保测绘档，一律不入库不单列",
    ),
    TextualFact(
        id="tf_wjbz_2003", division_id="div_wjbz_gl",
        verbatim_quote="2003年，古桥南北各建公路桥，古桥被夹在两桥之间，不再供道路通行；"
                       "桥南归西城区展览路街道，桥北归海淀区北下关街道（界桥）。",
        attested_string="界桥",
    ),
    TextualFact(
        id="tf_wjbz_gjb_2013", division_id="div_wjbz_gl",
        verbatim_quote="2013年，「高粱闸」（该遗产点名称写作米字底「粱」）作为大运河北京段"
                       "的组成遗产点列入第七批全国重点文物保护单位；不是独立的国保单位，"
                       "不得表述为世界遗产点。",
        attested_string="高粱閘",
        translator_note="文保名录沿用米字底「高粱闸」；地名保护名录2024年纠偏为木字底——"
                        "两名录并存皆官方文件，不得互斥，也不得说三种写法互为错写",
    ),
    TextualFact(
        id="tf_wjbz_gate_destroyed", division_id="div_wjbz_gl",
        verbatim_quote="桥上置闸，称「高梁闸」，又称「西城闸」；该闸已毁（毁废年代无档）。",
        attested_string="高梁閘",
        translator_note="「现存闸板一件」之说缺文物登记或正式调查报告，不采用；"
                        "不得说古闸至今完整保存/仍在服役",
    ),
    # ---- 名录第二批（2024-11-13 公布）：字形纠偏 + 安河桥村明代 ----
    TextualFact(
        id="tf_minglu_gaoliang", division_id="div_minglu2_gl",
        verbatim_quote="2024年11月13日公布《三山五园地区传统地名保护名录》（第二批），"
                       "「高梁桥」列入，标准用字为木字底「梁」；文件落款2025年6月20日，"
                       "2025年10月由北京市规划自然资源委网站公开发布。",
        attested_string="高梁桥",
    ),
    TextualFact(
        id="tf_minglu_anhecun", division_id="div_minglu2_ahc",
        verbatim_quote="《三山五园地区传统地名保护名录（第二批）》将「安河桥村」村落地名的"
                       "出现年代列为明代；名录载其位置：东、南至清河，西至京密引水渠，"
                       "北至正红旗村。名录证明的是地名出现年代，不直接等同考古意义上的"
                       "聚落形成。",
        attested_string="安河桥村",
        translator_note="名录为桥跨清河的旁证（村界至清河），不直接证明桥史",
    ),
    # ---- 海淀区政府公开资料：倚虹堂 / 长河转河 / 1965新桥 ----
    TextualFact(
        id="tf_yihongtang_1751", division_id="div_hd_yht",
        verbatim_quote="乾隆十六年（1751年）在高梁桥西侧兴建倚虹堂，为长河皇家御道的"
                       "水陆换乘码头行宫；南岸另有船坞，两者是不同建筑；"
                       "慈禧赴颐和园时在附近登舟。",
        attested_string="倚虹堂",
        translator_note="倚虹堂（桥西）与船坞（南岸）分列两建筑，不得合并表述",
    ),
    TextualFact(
        id="tf_hd_changhe_zhuanhe", division_id="div_hd_zhuanhe",
        verbatim_quote="高梁桥是长河与转河两大河段的衔接点：桥以西至白石桥为长河，"
                       "桥以东往积水潭方向为转河。",
        attested_string="長河",
        translator_note="这是今天的水名分界；不得说「紫竹院湖到积水潭今统称南长河」",
    ),
    TextualFact(
        id="tf_anhe_1965", division_id="div_hd_anhe1965",
        verbatim_quote="1965年因修京密引水渠，于青龙桥东北约0.5公里另址新建安河桥新桥；"
                       "历史旧安河桥跨清河，新桥跨京密引水渠，两河两桥严格分离。",
        attested_string="京密引水渠",
    ),
    # ---- 1929 北平市工务局档案（转引）：系统B ----
    TextualFact(
        id="tf_bma_yuanyiqian", division_id="div_bma_anhe",
        verbatim_quote="安河桥始建于元代以前；明正统十四年(1449)重修；"
                       "康熙五十九年(1720)重建石拱桥；光绪十二年(1886)再修。",
        attested_string="安河桥",
        source_year=_dt(1929, "dt_bma1929"),
        translator_note="转引自研究论文（香港中文大学《历史人类学学刊》系），L1转引→暂按L2；"
                        "1929年原档扫描件未目验前，不得宣布「元以前始建」为新定论",
    ),
    TextualFact(
        id="tf_anhe_qinghe", division_id="div_bma_anhe",
        verbatim_quote="历史旧安河桥跨清河。",
        attested_string="清河",
        translator_note="1929档案所记；2025名录「安河桥村东南至清河」为旁证",
    ),
    # ---- 安河桥小史（地方文史）：系统A与兼容细节 ----
    TextualFact(
        id="tf_wenshi_1724", division_id="div_anhe_xiaoshi",
        verbatim_quote="地方文史记载：雍正二年(1724)始建木桥，乾隆年间改建单孔石拱。",
        attested_string="雍正二年",
        translator_note="「系统A」（L3/L4，口播须软化），与1929档案「系统B」正面冲突，"
                        "两说并存不裁决",
    ),
    TextualFact(
        id="tf_anhe_luoguo", division_id="div_anhe_xiaoshi",
        verbatim_quote="桥为单孔石拱，桥面隆起，俗称「罗锅桥」。",
        attested_string="羅鍋橋",
        translator_note="形态细节两系统兼容，可作兼容事实",
    ),
    TextualFact(
        id="tf_anhe_shie", division_id="div_anhe_xiaoshi",
        verbatim_quote="旧桥石额刻「安和桥」确有旧料；近现代通行写「安河桥」，"
                       "转换时间与机制待考；「安澜平和」之意为地方文史说法。",
        attested_string="安和橋",
    ),
    TextualFact(
        id="tf_anhe_zhaba", division_id="div_anhe_xiaoshi",
        verbatim_quote="安河桥一带设有控水闸坝，常水输瓮山泊、洪水泄清河（地方志支持）；"
                       "不说桥梁结构与闸体一体化。",
        attested_string="控水閘壩",
    ),
    TextualFact(
        id="tf_village_fade", division_id="div_anhe_xiaoshi",
        verbatim_quote="上世纪90年代到2000年代，安河桥一带经历京密引水渠、五环路、地铁等"
                       "多轮改造，村落逐渐消失；名字转移至安河桥大街、公交安河桥站、"
                       "地铁安河桥北站与官方名录——名字没有消失，而是转移到现代载体。",
        attested_string="安河橋",
        translator_note="「2004年整体因地铁腾退」缺一手征拆档案，不采用；此为软化表述（L2/L3）",
    ),
    TextualFact(
        id="tf_metro_anhebei", division_id="div_anhe_xiaoshi",
        verbatim_quote="地铁安河桥北站2009年9月28日随4号线开通（北端终点）；"
                       "规划阶段曾以「龙背村」命名，2008年定名安河桥北。",
        attested_string="安河橋北",
        translator_note="不说「龙背村的名字搬到了地铁站」——运营站名最终未保留龙背村",
    ),
    # ---- 三山五园水系变迁：明代木桩（L2实物图；L5内部年代不入库） ----
    TextualFact(
        id="tf_muzhuang_2009", division_id="div_sxwj_muzhuang",
        verbatim_quote="2009年清河河底施工时，安河桥下出土明代木桩；"
                       "《三山五园水系变迁》（2026年出版）刊布实物图。",
        attested_string="明代木樁",
        translator_note="木料年代区间属项目内部检测资料（L5，原始报告未公开），不入库、"
                        "口播禁用；木桩「桥基」身份存疑；与白浮堰遗存不建归属关系",
    ),
    # ---- 钦定历代职官表卷八：丰益仓（转述待核原典） ----
    TextualFact(
        id="tf_zhiguan_fengyicang", division_id="div_zhiguan_v8",
        verbatim_quote="丰益仓在德胜门外安河桥，雍正七年（1729）建，"
                       "供守卫圆明园八旗官军俸饷。",
        attested_string="丰益倉",
        translator_note="研究档案v2对卷八《户部仓场衙门表》的转述；原典逐字句待核"
                        "（维基文库/识典古籍载体）。v1「年需俸米六万六千三百余石」"
                        "「对应八万余兵丁」数字链无一手档案，已撤稿不入库",
    ),
]


# ==================================================================
# 3. 实体（桥、闸、战场、行宫、新旧两桥、村、仓——桥闸战场严格分体）
# ==================================================================

ENTITIES: List[PersistentSpatialEntity] = [
    PersistentSpatialEntity(id="ent_gaoliang_bridge",
                            kind=PhysicalThingKind.HYDRAULIC_STRUCTURE,
                            canonical_label="高梁桥（元代石闸桥；三山五园名录2024纠偏字形木字底）"),
    PersistentSpatialEntity(id="ent_gaoliang_gate",
                            kind=PhysicalThingKind.HYDRAULIC_STRUCTURE,
                            canonical_label="高梁闸（又称西城闸；1292郭守敬大都水系闸，已毁）"),
    PersistentSpatialEntity(id="ent_gaoliang_battlefield",
                            kind=PhysicalThingKind.HISTORIC_BATTLEFIELD,
                            canonical_label="高梁河古战场（979年宋辽战役，位于古高梁河畔，与元桥分属不同实体）"),
    PersistentSpatialEntity(id="ent_yihongtang",
                            kind=PhysicalThingKind.GARDEN_COMPLEX,
                            canonical_label="倚虹堂（1751年长河皇家御道水陆换乘码头行宫）"),
    PersistentSpatialEntity(id="ent_anhe_bridge",
                            kind=PhysicalThingKind.HYDRAULIC_STRUCTURE,
                            canonical_label="安河桥（历史旧桥，跨清河，罗锅桥；桥史两说并存）"),
    PersistentSpatialEntity(id="ent_anhe_new_bridge",
                            kind=PhysicalThingKind.HYDRAULIC_STRUCTURE,
                            canonical_label="安河新桥（1965年京密引水渠另址新建，与古桥分离）"),
    PersistentSpatialEntity(id="ent_anheqiao_village",
                            kind=PhysicalThingKind.SETTLEMENT_AREA,
                            canonical_label="安河桥村（官方名录：地名出现年代为明代）"),
    PersistentSpatialEntity(id="ent_fengyicang",
                            kind=PhysicalThingKind.STATE_GRANARY,
                            canonical_label="丰益仓（1729年德胜门外安河桥八旗俸饷仓）"),
]


# ==================================================================
# 4. 历时状态（每条状态：纪年挂靠 + evidence_fact_ids 溯源；
#    推断/争议的 epistemic status 落在 §7 命题与采信层）
# ==================================================================

STATES: List[HistoricalFeatureState] = [
    # ---- 高梁桥：1292 始建（明清延续）→ 1980 大改 → 2003 今状 ----
    HistoricalFeatureState(
        id="st_glb_1292", entity_id="ent_gaoliang_bridge",
        time_span=TimeSpan(id="ts_glb_a", label="1292-1911 元代石闸桥至清末",
                           begin=_dt(1292, "ts_glb_ab",
                                     _ry(Era.YUAN, "至元", 29, "元至元二十九年")),
                           end=_dt(1911, "ts_glb_ae")),
        geometry="石闸桥，桥上置闸（闸体另列实体 ent_gaoliang_gate）；跨古高梁水故道；"
                 "南北两端原各有牌坊：南「长源/永泽」、北「资安/广润」",
        material="石筑桥体（历代重修叠加）",
        function="郭守敬引白浮、玉泉诸水汇瓮山泊—高梁河体系的桥闸工程（通惠河上游水源段）；"
                 "明清出西直门向西北的主要通道、清明踏青胜地（「京师最胜地也」）；"
                 "1292年是否该河段第一道闸——不是：金承安三年(1198)已有闸记录",
        evidence_fact_ids=["tf_yuanshi_1292_tonghui", "tf_jinshi_1198",
                           "tf_yhd_ylqj", "tf_djjwl_taqing", "tf_rxjwkc_paifang"],
    ),
    HistoricalFeatureState(
        id="st_glb_1980", entity_id="ent_gaoliang_bridge",
        time_span=TimeSpan(id="ts_glb_b", label="1980-2002 大改后",
                           begin=_dt(1980, "ts_glb_bb", precision="approximate"),
                           end=_dt(2002, "ts_glb_be")),
        geometry="展宽高梁桥路时重修（约1980—1982）；无测绘档尺寸入库",
        material="石筑桥体（20世纪80年代大规模改造，非完整原状）",
        function="道路通行中的改建桥（历代重修、清代有重要重修、1980—1982大改——"
                 "今天看到的不是完整的原状古桥）",
        evidence_fact_ids=["tf_wjbz_1980"],
    ),
    HistoricalFeatureState(
        id="st_glb_2003", entity_id="ent_gaoliang_bridge",
        time_span=_ts(2003, 2026, "ts_glb_c"),
        geometry="古桥被南北两座公路桥夹于其间，不再供道路通行；界桥：桥南西城区展览路街道、"
                 "桥北海淀区北下关街道；今为长河（桥西至白石桥）与转河（桥东往积水潭）衔接点",
        function="文物保护与地名对象：2013年「高粱闸」（米字底）列大运河北京段第七批国保"
                 "遗产点（非独立国保、非世界遗产点）；2024年三山五园地名名录（第二批）"
                 "纠偏标准用字为木字底「高梁桥」",
        evidence_fact_ids=["tf_wjbz_2003", "tf_wjbz_gjb_2013",
                           "tf_minglu_gaoliang", "tf_hd_changhe_zhuanhe"],
    ),
    # ---- 高梁闸：金1198记录（不证同一构筑物）→ 元1292 置闸 → 已毁 ----
    HistoricalFeatureState(
        id="st_glz_jin_1198", entity_id="ent_gaoliang_gate",
        time_span=TimeSpan(id="ts_glz_a", label="1198 金代闸记录（不证连续存在）",
                           begin=_dt(1198, "ts_glz_ab",
                                     _ry(Era.LIAO_JIN, "承安", 3, "金承安三年")),
                           end=_dt(1198, "ts_glz_ae")),
        geometry="金代此河段已有人工水闸（记录年状态，不证桥闸连续存在）",
        function="「勿毁高梁河闸，从民灌溉」——农业灌溉用水闸；与元代闸是否同址、"
                 "是否同一构筑物不能画等号，只能并列说「金代已有，元代重建」"
                 "（见身份断言 dia_gate_jin_yuan）",
        evidence_fact_ids=["tf_jinshi_1198"],
    ),
    HistoricalFeatureState(
        id="st_glz_yuan_1292", entity_id="ent_gaoliang_gate",
        time_span=TimeSpan(id="ts_glz_b", label="1292-1911 元代闸至清代断代边界",
                           begin=_dt(1292, "ts_glz_bb",
                                     _ry(Era.YUAN, "至元", 29, "元至元二十九年")),
                           end=_dt(1911, "ts_glz_be")),
        geometry="桥上置闸，称高梁闸，又称西城闸",
        function="郭守敬大都引水体系的节制闸（通惠河上游水源段）；该闸已毁（毁废年代无档）——"
                 "本状态止于1911清代断代边界，非毁废之年；现代存续断言一律无状态支撑"
                 "（缺证据≠通过），「古闸至今仍在服役」不成立",
        evidence_fact_ids=["tf_yuanshi_1292_tonghui", "tf_wjbz_gate_destroyed"],
    ),
    # ---- 979 高梁河之战古战场（与桥分属不同实体） ----
    HistoricalFeatureState(
        id="st_battle_979", entity_id="ent_gaoliang_battlefield",
        time_span=TimeSpan(id="ts_b979", label="979 会战之年",
                           begin=_dt(979, "ts_b979_b",
                                     _ry(Era.LIAO_JIN, "乾亨", 1,
                                         "辽景宗乾亨元年（宋太平兴国四年）")),
                           end=_dt(979, "ts_b979_e")),
        geometry="古高梁河畔（具体战场位置至今有多种说法，不系于任何后世桥址）",
        function="宋辽会战：七月（农历）初六耶律沙部与宋军战于高梁河畔被击退，当晚耶律休哥"
                 "驰至（每人两支火把，宋军止追），与耶律斜轸左右夹攻、耶律学古出城，"
                 "宋军三面被围溃败；宋太宗乘驴车南逃至涿州一带脱身，辽军追至涿州而止"
                 "（乘驴车=[文献记载]《辽史》系；中箭=[后世记载]，两级分挂）。"
                 "宋军建国后第一次重大失败，重创首次收复幽燕的尝试",
        evidence_fact_ids=["tf_liaoshi_zhuozhou", "tf_songshi_979"],
    ),
    # ---- 倚虹堂：1751 建于桥西 ----
    HistoricalFeatureState(
        id="st_yht_1751", entity_id="ent_yihongtang",
        time_span=TimeSpan(id="ts_yht_a", label="1751-1911 皇家御道换乘行宫",
                           begin=_dt(1751, "ts_yht_ab",
                                     _ry(Era.QING, "乾隆", 16, "乾隆十六年")),
                           end=_dt(1911, "ts_yht_ae")),
        geometry="高梁桥西侧；南岸另有船坞（两建筑分列，勿合并）",
        function="长河皇家御道的水陆换乘码头行宫；慈禧赴颐和园时在附近登舟，"
                 "经白石桥、万寿寺、麦钟桥、长春桥达颐和园与玉泉山",
        evidence_fact_ids=["tf_yihongtang_1751"],
    ),
    # ---- 安河桥（旧桥）：始建两说并存 → 石拱罗锅桥 → 1886再修后沿用 ----
    HistoricalFeatureState(
        id="st_anh_origins", entity_id="ent_anhe_bridge",
        time_span=TimeSpan(id="ts_anh_a", label="始建年代两说并存（下限开放）",
                           open_begin=True, begin=None,
                           end=_dt(1719, "ts_anh_ae")),
        geometry="历史旧桥，跨清河（1929档案；2025名录村界至清河为旁证）",
        function="始建年代两套文献系统正面冲突，本状态不断言始建年代，仅录并存："
                 "系统A（地方文史L3/L4）雍正二年(1724)始建木桥；"
                 "系统B（1929工务局档案转引L1→暂按L2）元以前始建、正统十四年(1449)重修；"
                 "1929原档未目验前不宣布「元以前始建」为新定论",
        evidence_fact_ids=["tf_bma_yuanyiqian", "tf_wenshi_1724", "tf_anhe_qinghe"],
    ),
    HistoricalFeatureState(
        id="st_anh_shigong", entity_id="ent_anhe_bridge",
        time_span=TimeSpan(id="ts_anh_b", label="1720-1886 石拱罗锅桥时期",
                           begin=_dt(1720, "ts_anh_bb",
                                     _ry(Era.QING, "康熙", 59, "康熙五十九年")),
                           end=_dt(1886, "ts_anh_be")),
        geometry="单孔石拱、桥面隆起，俗称「罗锅桥」（两系统兼容）；跨清河",
        function="石拱形态形成期（重建/改建年代两说并存：系统B康熙五十九年(1720)重建石拱 "
                 "vs 系统A乾隆年间改建单孔石拱——不得写任一定论）",
        evidence_fact_ids=["tf_bma_yuanyiqian", "tf_wenshi_1724", "tf_anhe_luoguo"],
    ),
    HistoricalFeatureState(
        id="st_anh_1886", entity_id="ent_anhe_bridge",
        time_span=TimeSpan(id="ts_anh_c", label="1886-1964 再修后沿用",
                           begin=_dt(1886, "ts_anh_cb",
                                     _ry(Era.QING, "光绪", 12, "光绪十二年")),
                           end=_dt(1964, "ts_anh_ce")),
        geometry="旧桥沿用，跨清河；一带设有控水闸坝（常水输瓮山泊、洪水泄清河）",
        function="光绪十二年(1886)再修后的旧桥沿用期；1965年新桥另址建成，古桥时代终结"
                 "（1964为旧桥名有效性边界，非本体毁废之年——毁废年代无档）",
        evidence_fact_ids=["tf_bma_yuanyiqian", "tf_anhe_zhaba"],
    ),
    # ---- 安河新桥：1965 另址新建 ----
    HistoricalFeatureState(
        id="st_anhn_1965", entity_id="ent_anhe_new_bridge",
        time_span=_ts(1965, 2026, "ts_anhn_a"),
        geometry="青龙桥东北约0.5公里另址新建，跨京密引水渠",
        function="京密引水渠桥；与历史旧安河桥（跨清河）两河两桥严格分离，"
                 "不得说「古安河桥一直跨在今天的京密引水渠上」",
        evidence_fact_ids=["tf_anhe_1965"],
    ),
    # ---- 安河桥村：明代地名 → 近代聚落 → 消失与名字转移 ----
    HistoricalFeatureState(
        id="st_ahc_ming", entity_id="ent_anheqiao_village",
        time_span=TimeSpan(id="ts_ahc_a", label="明代起（官方法定地名年代）",
                           open_begin=True, begin=None,
                           end=_dt(1911, "ts_ahc_ae")),
        geometry="村界四至（名录载）：东、南至清河，西至京密引水渠，北至正红旗村",
        function="官方法定地名「安河桥村」出现年代为明代（2025名录）；名录证地名出现年代，"
                 "不直接等同考古意义上的聚落形成",
        evidence_fact_ids=["tf_minglu_anhecun"],
    ),
    HistoricalFeatureState(
        id="st_ahc_modern", entity_id="ent_anheqiao_village",
        time_span=_ts(1912, 2026, "ts_ahc_b"),
        geometry="民国时为青龙桥镇域内较大聚落（据地方文史）；20世纪90年代到2000年代多轮改造",
        function="村落逐渐消失（「2004年整体腾退」缺一手征拆档案不采用）；名字转移到"
                 "安河桥大街、公交安河桥站、地铁安河桥北站（2009-09-28随4号线开通，"
                 "规划阶段曾以龙背村命名）与官方2025名录",
        evidence_fact_ids=["tf_village_fade", "tf_metro_anhebei", "tf_minglu_anhecun"],
    ),
    # ---- 丰益仓：雍正七年八旗俸饷仓 ----
    HistoricalFeatureState(
        id="st_fyc_1729", entity_id="ent_fengyicang",
        time_span=TimeSpan(id="ts_fyc_a", label="1729-1911 八旗俸饷仓",
                           begin=_dt(1729, "ts_fyc_ab",
                                     _ry(Era.QING, "雍正", 7, "雍正七年")),
                           end=_dt(1911, "ts_fyc_ae")),
        geometry="德胜门外安河桥",
        function="八旗俸饷仓：供守卫圆明园八旗官军俸饷（雍正七年(1729)建，官书口径）；"
                 "不带任何石数/兵额换算（v1数字链已撤稿）",
        evidence_fact_ids=["tf_zhiguan_fengyicang"],
    ),
]


# ==================================================================
# 5. 身份断言：战场≠桥 / 金闸≠元闸 / 新旧两桥 / 桥史两系统
# ==================================================================

IDENTITIES: List[DiachronicIdentityAssertion] = [
    DiachronicIdentityAssertion(
        id="dia_battle_not_bridge",
        subject_entity_ids=["ent_gaoliang_battlefield", "ent_gaoliang_bridge"],
        relation=IdentityRelation.UNCERTAIN,
        time_span=TimeSpan(id="ts_dia_bnb", label="979战场与1292建桥的时间差",
                           begin=_dt(979, "ts_dia_bnb_b",
                                     _ry(Era.LIAO_JIN, "乾亨", 1,
                                         "辽景宗乾亨元年")),
                           end=_dt(1292, "ts_dia_bnb_e",
                                   _ry(Era.YUAN, "至元", 29, "元至元二十九年"))),
        evidence_fact_ids=["tf_liaoshi_zhuozhou", "tf_yuanshi_1292_tonghui"],
        status=EpistemicStatus.CONTESTED,
        alternative_relations=[
            "979年宋辽在古高梁河畔交战（落点诸说并存），1292年元代才在同名水系上建桥闸——"
            "两者分属不同实体，「桥下就是战场」不成立",
            "313年（1292−979）仅是时间跨度，不得表述为「同一地点相隔313年」的空间关系；"
            "979年高梁桥址是否已有固定桥梁无足够一手证据（存疑）",
        ],
    ),
    DiachronicIdentityAssertion(
        id="dia_gate_jin_yuan",
        subject_entity_ids=["ent_gaoliang_gate"],
        relation=IdentityRelation.UNCERTAIN,
        time_span=TimeSpan(id="ts_dia_gjy", label="金闸与元闸关系存疑",
                           begin=_dt(1198, "ts_dia_gjy_b",
                                     _ry(Era.LIAO_JIN, "承安", 3, "金承安三年")),
                           end=_dt(1292, "ts_dia_gjy_e",
                                   _ry(Era.YUAN, "至元", 29, "元至元二十九年"))),
        evidence_fact_ids=["tf_jinshi_1198", "tf_yuanshi_1292_tonghui"],
        status=EpistemicStatus.CONTESTED,
        alternative_relations=[
            "金承安三年(1198)高梁河闸与元至元二十九年(1292)郭守敬闸同址重建说",
            "金闸与元闸别址别闸说——是否同一构筑物不能画等号，只能并列说「金代已有，元代重建」",
        ],
    ),
    DiachronicIdentityAssertion(
        id="dia_anh_two_systems",
        subject_entity_ids=["ent_anhe_bridge"],
        relation=IdentityRelation.UNCERTAIN,
        time_span=TimeSpan(id="ts_dia_ats", label="桥史两套文献系统正面冲突",
                           open_begin=True, begin=None,
                           end=_dt(1964, "ts_dia_ats_e")),
        evidence_fact_ids=["tf_wenshi_1724", "tf_bma_yuanyiqian"],
        status=EpistemicStatus.CONTESTED,
        alternative_relations=[
            "系统A（地方文史L3/L4）：雍正二年(1724)始建木桥、乾隆年间改建单孔石拱",
            "系统B（1929工务局档案转引L1→暂按L2）：元以前始建、正统十四年(1449)重修、"
            "康熙五十九年(1720)重建石拱、光绪十二年(1886)再修",
            "1929原档扫描件未目验前不宣布「元以前始建」为新定论；两说并存不裁决",
        ],
    ),
    DiachronicIdentityAssertion(
        id="dia_anh_old_new_split",
        subject_entity_ids=["ent_anhe_bridge", "ent_anhe_new_bridge"],
        relation=IdentityRelation.REPLACED_BY,
        time_span=_ts(1965, 2026, "ts_dia_ons"),
        evidence_fact_ids=["tf_anhe_1965", "tf_anhe_qinghe"],
        status=EpistemicStatus.VERIFIED,
        alternative_relations=[
            "1965年另址新建（青龙桥东北约0.5公里），非原址改建；古桥未迁移至京密引水渠",
            "旧桥跨清河、新桥跨京密引水渠——两河两桥严格分离",
        ],
    ),
]


# ==================================================================
# 6. 名称与指称（「高粱闸/高梁闸」「安和桥/安河桥」字形皆显式建名，不靠字符串消歧）
# ==================================================================

APPELLATIONS: List[Appellation] = [
    Appellation(id="app_gaoliangqiao", label="高梁桥", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n_glq", label="元代建桥至今",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_glq_e")),
                attesting_fact_ids=["tf_yhd_ylqj", "tf_minglu_gaoliang"]),
    Appellation(id="app_gaoliangzha", label="高梁闸", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1292, 1911, "ts_n_glz"),
                attesting_fact_ids=["tf_wjbz_gate_destroyed"]),
    Appellation(id="app_xichengzha", label="西城闸", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1292, 1368, "ts_n_xcz"),
                attesting_fact_ids=["tf_yuanshi_1292_tonghui"]),
    Appellation(id="app_gaolianghezha", label="高梁河闸", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1198, 1198, "ts_n_glhz"),
                attesting_fact_ids=["tf_jinshi_1198"]),
    # 文保名录沿用米字底（2013国保遗产点名），与2024纠偏字形并存皆官方
    Appellation(id="app_sorghum_gate", label="高粱闸", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(2013, 2026, "ts_n_gb_gate"),
                attesting_fact_ids=["tf_wjbz_gjb_2013"]),
    # 传说名：高亮赶水（不建得名链）
    Appellation(id="app_gaoliang_legend", label="高亮桥", kind=AppellationKind.FOLK_LEGEND,
                valid_time_span=TimeSpan(id="ts_n_glc", label="传说流传期",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_glc_e")),
                attesting_fact_ids=[]),
    Appellation(id="app_yihongtang", label="倚虹堂", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1751, 2026, "ts_n_yht"),
                attesting_fact_ids=["tf_yihongtang_1751"]),
    Appellation(id="app_anheqiao", label="安河桥", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n_anh", label="旧桥名（至新桥另址建成前）",
                                         open_begin=True, begin=None,
                                         end=_dt(1964, "ts_n_anh_e")),
                attesting_fact_ids=["tf_bma_yuanyiqian", "tf_anhe_shie"]),
    Appellation(id="app_anheqiao_he", label="安和桥", kind=AppellationKind.OLD_NAME,
                valid_time_span=TimeSpan(id="ts_n_ahq", label="石额旧写",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_ahq_e")),
                attesting_fact_ids=["tf_anhe_shie"]),
    Appellation(id="app_luoguoqiao", label="罗锅桥", kind=AppellationKind.VULGAR,
                valid_time_span=TimeSpan(id="ts_n_lgq", label="俗称流传期",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_lgq_e")),
                attesting_fact_ids=["tf_anhe_luoguo"]),
    Appellation(id="app_anheqiao_village", label="安河桥村", kind=AppellationKind.OFFICIAL,
                valid_time_span=TimeSpan(id="ts_n_ahc", label="明代起（名录）",
                                         open_begin=True, begin=None,
                                         end=_dt(2026, "ts_n_ahc_e")),
                attesting_fact_ids=["tf_minglu_anhecun"]),
    Appellation(id="app_anhe_new_bridge", label="安河新桥", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1965, 2026, "ts_n_anhn"),
                attesting_fact_ids=["tf_anhe_1965"]),
    Appellation(id="app_fengyicang", label="丰益仓", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(1729, 1911, "ts_n_fyc"),
                attesting_fact_ids=["tf_zhiguan_fengyicang"]),
    Appellation(id="app_gaoliang_battle", label="高梁河之战", kind=AppellationKind.OFFICIAL,
                valid_time_span=_ts(979, 979, "ts_n_gl_battle"),
                attesting_fact_ids=["tf_liaoshi_zhuozhou"]),
]

REFERENCES: List[ReferentialAssertion] = [
    ReferentialAssertion(id="rr_gaoliangqiao", appellation_id="app_gaoliangqiao",
                         referent_entity_id="ent_gaoliang_bridge",
                         time_span=TimeSpan(id="ts_r_glq", label="元代建桥至今",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_glq_e")),
                         evidence_fact_ids=["tf_yhd_ylqj", "tf_minglu_gaoliang"]),
    ReferentialAssertion(id="rr_gaoliangzha", appellation_id="app_gaoliangzha",
                         referent_entity_id="ent_gaoliang_gate",
                         time_span=_ts(1292, 1911, "ts_r_glz"),
                         evidence_fact_ids=["tf_wjbz_gate_destroyed"]),
    ReferentialAssertion(id="rr_xichengzha", appellation_id="app_xichengzha",
                         referent_entity_id="ent_gaoliang_gate",
                         time_span=_ts(1292, 1368, "ts_r_xcz"),
                         evidence_fact_ids=["tf_yuanshi_1292_tonghui"]),
    ReferentialAssertion(id="rr_gaolianghezha", appellation_id="app_gaolianghezha",
                         referent_entity_id="ent_gaoliang_gate",
                         time_span=_ts(1198, 1198, "ts_r_glhz"),
                         evidence_fact_ids=["tf_jinshi_1198"],
                         status=EpistemicStatus.CONTESTED,
                         provenance="金代「高梁河闸」与元代闸是否同一构筑物存疑"
                                    "（见 dia_gate_jin_yuan）；名称先挂闸实体，"
                                    "同址问题由身份断言承载"),
    ReferentialAssertion(id="rr_sorghum_gate", appellation_id="app_sorghum_gate",
                         referent_entity_id="ent_gaoliang_gate",
                         time_span=_ts(2013, 2026, "ts_r_gb_gate"),
                         evidence_fact_ids=["tf_wjbz_gjb_2013"],
                         provenance="国保名录沿用米字底「高粱闸」（大运河遗产点名）；"
                                    "2024地名名录纠偏为木字底「高梁桥/高梁闸」——"
                                    "两名录并存皆官方文件，不得互斥，"
                                    "也不得说三种写法互为错写"),
    ReferentialAssertion(id="rr_gaoliang_legend", appellation_id="app_gaoliang_legend",
                         referent_entity_id="ent_gaoliang_bridge",
                         time_span=TimeSpan(id="ts_r_glc", label="传说流传期",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_glc_e")),
                         evidence_fact_ids=[],
                         status=EpistemicStatus.FOLK_LEGEND,
                         provenance="民间传说「高亮赶水」之名（关学曾北京琴书、"
                                    "郭德纲铁片大鼓改编）：高亮追水被吞没处建桥得名。"
                                    "高梁之名远早于传说背景（金1198已有高梁河闸记录、"
                                    "《水经注》已记高梁水），不得建立"
                                    "「高亮→高粱→高梁」得名演变链"),
    ReferentialAssertion(id="rr_yihongtang", appellation_id="app_yihongtang",
                         referent_entity_id="ent_yihongtang",
                         time_span=_ts(1751, 2026, "ts_r_yht"),
                         evidence_fact_ids=["tf_yihongtang_1751"]),
    ReferentialAssertion(id="rr_anheqiao", appellation_id="app_anheqiao",
                         referent_entity_id="ent_anhe_bridge",
                         time_span=TimeSpan(id="ts_r_anh", label="旧桥名",
                                            open_begin=True, begin=None,
                                            end=_dt(1964, "ts_r_anh_e")),
                         evidence_fact_ids=["tf_bma_yuanyiqian", "tf_anhe_qinghe"]),
    ReferentialAssertion(id="rr_anheqiao_he", appellation_id="app_anheqiao_he",
                         referent_entity_id="ent_anhe_bridge",
                         time_span=TimeSpan(id="ts_r_ahq", label="石额旧写",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_ahq_e")),
                         evidence_fact_ids=["tf_anhe_shie"],
                         provenance="石额刻「安和桥」确有旧料；近现代通行写「安河桥」；"
                                    "转换时间与机制待考，不写「和/河通写」的确定性解释"),
    ReferentialAssertion(id="rr_luoguoqiao", appellation_id="app_luoguoqiao",
                         referent_entity_id="ent_anhe_bridge",
                         time_span=TimeSpan(id="ts_r_lgq", label="俗称流传期",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_lgq_e")),
                         evidence_fact_ids=["tf_anhe_luoguo"]),
    ReferentialAssertion(id="rr_anheqiao_village", appellation_id="app_anheqiao_village",
                         referent_entity_id="ent_anheqiao_village",
                         time_span=TimeSpan(id="ts_r_ahc", label="明代起（名录）",
                                            open_begin=True, begin=None,
                                            end=_dt(2026, "ts_r_ahc_e")),
                         evidence_fact_ids=["tf_minglu_anhecun"]),
    ReferentialAssertion(id="rr_anhe_new_bridge", appellation_id="app_anhe_new_bridge",
                         referent_entity_id="ent_anhe_new_bridge",
                         time_span=_ts(1965, 2026, "ts_r_anhn"),
                         evidence_fact_ids=["tf_anhe_1965"]),
    ReferentialAssertion(id="rr_fengyicang", appellation_id="app_fengyicang",
                         referent_entity_id="ent_fengyicang",
                         time_span=_ts(1729, 1911, "ts_r_fyc"),
                         evidence_fact_ids=["tf_zhiguan_fengyicang"]),
    ReferentialAssertion(id="rr_gaoliang_battle", appellation_id="app_gaoliang_battle",
                         referent_entity_id="ent_gaoliang_battlefield",
                         time_span=_ts(979, 979, "ts_r_gl_battle"),
                         evidence_fact_ids=["tf_liaoshi_zhuozhou"],
                         status=EpistemicStatus.CONTESTED,
                         provenance="战役绑定的是「高梁河畔」这一水系地望；具体战场落点"
                                    "诸说并存（北望甸等），不系于任何后世桥址"),
]


# ==================================================================
# 7. 断言与采信：把两份冻结档案的降格结论固化（推断/传说/现代观点绝不混级为史实）
# ==================================================================

PROPOSITIONS: List[Proposition] = [
    Proposition(
        id="prop_battle_979_fenji",
        statement="979年（宋太平兴国四年/辽景宗乾亨元年）高梁河之战：宋太宗乘驴车南逃"
                  "=[文献记载]（《辽史》系）；中箭=[后世记载]，两级分挂不得同级并列；"
                  "「围三缺一」等战败归因=[后世军事分析]不得写成史籍因果；影响软化为"
                  "「重创首次收复幽燕的尝试」，不得说「攻守易势」「三百年和平」"
                  "（当年满城之战辽军败于宋、986年宋仍发动雍熙北伐）",
        derived_from_fact_ids=["tf_liaoshi_zhuozhou", "tf_songshi_979"],
        inferred_subject_id="ent_gaoliang_battlefield",
        inference_method="《辽史》与《宋史》互证战役骨架；证据分级逐条挂靠——"
                         "驴车出自《辽史》明文，中箭仅后世记载；"
                         "不得说宋太宗被俘或差点被俘，不得用「两个致命决策」暗示单一战因",
        alternative_explanations=[
            "宋太宗中箭说（[后世记载]，非一级文献）",
            "「攻守易势/三百年和平」说——被满城之战与雍熙北伐证伪，不采",
        ],
    ),
    Proposition(
        id="prop_battle_location_hepan",
        statement="战场位于古高梁河畔，具体落点至今诸说并存；与1292年始建的高梁桥"
                  "分属不同实体，「桥下就是战场」不成立——313年只是时间跨度",
        derived_from_fact_ids=["tf_liaoshi_zhuozhou", "tf_yuanshi_1292_tonghui"],
        inferred_subject_id="ent_gaoliang_battlefield",
        inference_method="空间关系自证：979年时桥尚未建（桥最早状态1292年），"
                         "979年桥址是否有固定桥梁无一手证据——空间绑定必须落在水系地望",
        alternative_explanations=[
            "北望甸等战场落点诸说（并存不裁决）",
            "「同一地点相隔313年」说——把时间差偷换为空间同一，不采",
        ],
    ),
    Proposition(
        id="prop_gate_jin_yuan_relation",
        statement="金承安三年(1198)已有「高梁河闸」用于民灌溉；元至元二十九年(1292)"
                  "郭守敬引水工程重置闸桥——金元闸是否同址同一构筑物不能画等号，"
                  "不得说「1292年是这条河第一道闸」，也不得说郭守敬凭空造出这条河的水利"
                  "（他是重构与系统化）",
        derived_from_fact_ids=["tf_jinshi_1198", "tf_yuanshi_1292_tonghui"],
        inferred_subject_id="ent_gaoliang_gate",
        inference_method="《金史》明文在先，《元史》工程在后；两级文献并列，"
                         "同址问题无同时代测绘档案，只能存疑并列",
        alternative_explanations=[
            "金元同址重建说（无逐闸档案确证）",
            "金元别址别闸说（无挖掘调查确证）",
        ],
    ),
    Proposition(
        id="prop_gate_destroyed",
        statement="高梁闸（西城闸）已毁，毁废年代无档；「现存闸板一件」缺文物登记不采用；"
                  "「古闸至今完整保存/仍在服役」不成立",
        derived_from_fact_ids=["tf_wjbz_gate_destroyed"],
        inferred_subject_id="ent_gaoliang_gate",
        inference_method="文保公开口径明言闸已毁；无任何现代在役状态与测绘支撑",
        alternative_explanations=[
            "古闸尚存说——无文保登记或调查报告支撑，不采",
        ],
    ),
    Proposition(
        id="prop_bridge_not_original",
        statement="今桥非完整原状古桥：历代重修、清代有重要重修、1980—1982大规模改造；"
                  "现桥尺寸/孔数/望柱数三源冲突且缺文保测绘档，一律不列",
        derived_from_fact_ids=["tf_wjbz_1980"],
        inferred_subject_id="ent_gaoliang_bridge",
        inference_method="「长16米宽10米、16对石柱」等数据来源互斥，按纪律宁缺毋滥",
        alternative_explanations=[
            "1982年桥体北移约1米重建拓宽说——[存疑待考]，不采",
        ],
    ),
    Proposition(
        id="prop_minglu_correction",
        statement="桥名标准用字为木字底「高梁桥/高梁河」（2024-11-13三山五园名录第二批"
                  "纠偏）；2013年国保遗产点名沿用米字底「高粱闸」——两名录并存皆官方，"
                  "不得互斥，不得说「高粱桥/高亮桥/高梁桥是同一东西的三种错写」",
        derived_from_fact_ids=["tf_minglu_gaoliang", "tf_wjbz_gjb_2013"],
        inferred_subject_id="ent_gaoliang_bridge",
        inference_method="两份官方文件并置：地名名录管地名用字、文保名录管遗产点名，"
                         "职能不同故字形并存",
        alternative_explanations=[
            "「三种写法皆错写」说——违反两名录并存的官方事实，不采",
        ],
    ),
    Proposition(
        id="prop_changhe_zhuanhe_bound",
        statement="高梁桥是今长河与转河的衔接点（桥西至白石桥为长河、桥东往积水潭为转河）；"
                  "不得说「紫竹院湖到积水潭这一段今天统称南长河」；古代水源链"
                  "（白浮堰—瓮山泊）不得说成今天实际水源链（1966年京密引水渠后已改变）",
        derived_from_fact_ids=["tf_hd_changhe_zhuanhe"],
        inferred_subject_id="ent_gaoliang_bridge",
        inference_method="今名与古名分层：古高梁河河道遗存被今天不同名称的河段继承",
        alternative_explanations=[
            "「今统称南长河」说——与现行河名分界不符，不采",
        ],
    ),
    Proposition(
        id="prop_yihongtang_not_dock",
        statement="倚虹堂（1751，桥西）是长河皇家御道的水陆换乘码头行宫；南岸另有船坞——"
                  "两建筑分列，不得把倚虹堂说成船坞",
        derived_from_fact_ids=["tf_yihongtang_1751"],
        inferred_subject_id="ent_yihongtang",
        inference_method="公开沿革明载两建筑分列；「功能与所在场所的功能分开验证」纪律",
        alternative_explanations=[
            "倚虹堂即船坞说——两建筑混一，不采",
        ],
    ),
    Proposition(
        id="prop_anhe_dual_system",
        statement="安河桥桥史存在两套不同记载，同时呈现、不做裁决：系统A（地方文史）"
                  "1724年始建木桥、乾隆年间改建单孔石拱；系统B（1929工务局档案转引）"
                  "元以前始建、1449重修、1720重建石拱、1886再修",
        derived_from_fact_ids=["tf_wenshi_1724", "tf_bma_yuanyiqian"],
        inferred_subject_id="ent_anhe_bridge",
        inference_method="两源正面冲突且互不隶属；1929原档扫描件未目验前不宣布任一"
                         "单一年代定论——「始建于1724年」与「元以前始建」均不得作定论口播",
        alternative_explanations=[
            "系统A单采说（1929档案在先，不能无视）",
            "系统B单采说（原档未目验，不能宣布为新定论）",
        ],
    ),
    Proposition(
        id="prop_anhe_jingmi_confusion",
        statement="「古安河桥一直跨在今天的京密引水渠上」为时空混说：历史旧桥跨清河，"
                  "1965年才因修京密引水渠另址新建新桥（青龙桥东北约0.5公里）",
        derived_from_fact_ids=["tf_anhe_qinghe", "tf_anhe_1965"],
        inferred_subject_id="ent_anhe_bridge",
        inference_method="两河两桥严格分离：旧桥的河道与年份均不支持渠上混说；"
                         "2025名录村界四至（东、南至清河，西至京密引水渠）为地理旁证",
        alternative_explanations=[
            "古桥迁移跨渠说——无迁移档案，不采",
        ],
    ),
    Proposition(
        id="prop_fengyicang_official",
        statement="丰益仓在德胜门外安河桥，雍正七年(1729)建，供守卫圆明园八旗官军俸饷"
                  "（《钦定历代职官表》卷八《户部仓场衙门表》，官书口径）；"
                  "不带任何石数/兵额换算",
        derived_from_fact_ids=["tf_zhiguan_fengyicang"],
        inferred_subject_id="ent_fengyicang",
        inference_method="L1官书直证；v1「年需俸米六万六千三百余石」「对应八万余兵丁」"
                         "系二手循环引用且与护军编制不匹配，已撤稿",
        alternative_explanations=[
            "俸米66300石/八万兵丁换算说——无一手档案，撤稿不采",
        ],
    ),
    Proposition(
        id="prop_village_ming_dating",
        statement="「安河桥村」这一村落地名的出现年代为明代（官方名录）；名录证地名年代，"
                  "不直接等同考古聚落形成；「咸丰年间才成村」已撤稿",
        derived_from_fact_ids=["tf_minglu_anhecun"],
        inferred_subject_id="ent_anheqiao_village",
        inference_method="政府名录是地名年代的权威载体；v1「咸丰成村」与名录冲突，撤稿",
        alternative_explanations=[
            "咸丰成村说——与官方法定名录冲突，已撤稿",
            "考古聚落形成年代说——无发掘资料，不入库",
        ],
    ),
    Proposition(
        id="prop_longbei_naming",
        statement="地铁安河桥北站规划阶段曾以「龙背村」命名，2008年定名安河桥北，"
                  "2009-09-28随4号线开通；不说「龙背村的名字搬到了地铁站」"
                  "（运营站名最终未保留龙背村）",
        derived_from_fact_ids=["tf_metro_anhebei"],
        inferred_subject_id="ent_anheqiao_village",
        inference_method="命名沿革公开资料；规划名与运营名分属两个阶段",
        alternative_explanations=[
            "「站名继承村名」说——运营名未保留龙背村，不成立",
        ],
    ),
    Proposition(
        id="prop_gaoliang_legend",
        statement="「高亮赶水」（高亮追水被吞没处建「高亮桥」、河改名「高亮河」）是"
                  "民间传说，后附会于早已有之的河名：金1198已有「高梁河闸」记录、"
                  "《水经注》已记高梁水——不得建立「高亮→高粱→高梁」得名演变链；"
                  "该传说被改编为关学曾北京琴书、郭德纲铁片大鼓《高亮赶水》",
        derived_from_fact_ids=["tf_jinshi_1198"],
        inferred_subject_id="ent_gaoliang_bridge",
        inference_method="文献年代夹逼：河名早于传说背景数百年，得名链不成立；"
                         "传说本身单列民间传说层",
        alternative_explanations=[
            "高梁得名于高亮赶水说——年代倒置，不采",
            "作物说/津梁说/梁山说等词源诸说——均无定论（见校准集gaoliang.py）",
        ],
    ),
    Proposition(
        id="prop_muzhuang_two_layers",
        statement="「安河桥下出土的明代木桩」为公开出版研究层（实物图，2009年清河河底"
                  "施工发现）；木料年代区间属项目内部检测资料（L5，原始报告未公开）——"
                  "口播禁用具体数据，年代如提只说「据研究可上溯至明代前期」；"
                  "木桩「桥基」身份存疑，与白浮堰遗存不建归属关系",
        derived_from_fact_ids=["tf_muzhuang_2009"],
        inferred_subject_id="ent_anhe_bridge",
        inference_method="公开刊布与内部检测分两层；「出土木桩」≠「桥基」，不做推断跳接",
        alternative_explanations=[
            "木桩即古桥桥基说——身份存疑，不采",
            "木桩属白浮堰体系说——无归属证据，不采",
        ],
    ),
]

ADOPTIONS: List[BeliefAdoption] = [
    BeliefAdoption(proposition_id="prop_battle_979_fenji",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E8交付档案v2",
                   rationale="两史互证战役骨架；分级（驴车/中箭/军事分析）是档案纪律本身"),
    BeliefAdoption(proposition_id="prop_battle_location_hepan",
                   status=EpistemicStatus.CONTESTED, confidence=0.7,
                   adopted_by="E8交付档案v2",
                   rationale="河畔交战可证，落点诸说并存；「桥下即战场」在结构上"
                             "不可通过（979年桥无状态）"),
    BeliefAdoption(proposition_id="prop_gate_jin_yuan_relation",
                   status=EpistemicStatus.CONTESTED, confidence=0.6,
                   adopted_by="E8交付档案v2",
                   rationale="两级文献并列，同址无档案确证；只说「金代已有，元代重建」"),
    BeliefAdoption(proposition_id="prop_gate_destroyed",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E8交付档案v2",
                   rationale="文保口径明言闸已毁；在役说无任何支撑"),
    BeliefAdoption(proposition_id="prop_bridge_not_original",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E8交付档案v2",
                   rationale="重修链清晰；冲突尺寸按纪律不入库"),
    BeliefAdoption(proposition_id="prop_minglu_correction",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E8交付档案v2",
                   rationale="两份官方名录文件俱在，字形并存是职能差异不是对错"),
    BeliefAdoption(proposition_id="prop_changhe_zhuanhe_bound",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E8交付档案v2",
                   rationale="今名分界为政府公开口径；古名今名分层"),
    BeliefAdoption(proposition_id="prop_yihongtang_not_dock",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E8交付档案v2",
                   rationale="公开沿革明载两建筑分列"),
    BeliefAdoption(proposition_id="prop_anhe_dual_system",
                   status=EpistemicStatus.CONTESTED, confidence=0.5,
                   adopted_by="E2交付档案v2.1",
                   rationale="两套文献系统正面冲突且互不隶属；1929原档未目验前"
                             "不制造确定性——保留冲突即结论"),
    BeliefAdoption(proposition_id="prop_anhe_jingmi_confusion",
                   status=EpistemicStatus.DISPROVEN, confidence=0.85,
                   adopted_by="E2交付档案v2.1",
                   rationale="旧桥跨清河（1929档案）与1965另址建新桥（公开沿革）"
                             "双重反驳渠上混说",
                   refuting_fact_ids=["tf_anhe_qinghe", "tf_anhe_1965"]),
    BeliefAdoption(proposition_id="prop_fengyicang_official",
                   status=EpistemicStatus.VERIFIED, confidence=0.9,
                   adopted_by="E2交付档案v2.1",
                   rationale="官书直证俸饷功能；数字链无档已撤稿"),
    BeliefAdoption(proposition_id="prop_village_ming_dating",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E2交付档案v2.1",
                   rationale="官方法定名录为地名年代权威；咸丰说撤稿"),
    BeliefAdoption(proposition_id="prop_longbei_naming",
                   status=EpistemicStatus.VERIFIED, confidence=0.85,
                   adopted_by="E2交付档案v2.1",
                   rationale="命名沿革公开；规划名≠运营名"),
    BeliefAdoption(proposition_id="prop_gaoliang_legend",
                   status=EpistemicStatus.FOLK_LEGEND, confidence=0.3,
                   adopted_by="E8交付档案v2",
                   rationale="传说单列民间层；得名链被文献年代夹逼否决"),
    BeliefAdoption(proposition_id="prop_muzhuang_two_layers",
                   status=EpistemicStatus.CONTESTED, confidence=0.55,
                   adopted_by="E2交付档案v2.1",
                   rationale="公开实物图层可述；内部检测层（L5）不入库口播禁用；"
                             "桥基身份存疑"),
]


# ==================================================================
# 8. 空间变化事件（只收有明确纪年的变化；「已毁/渐废」无档不建事件）
# ==================================================================

TRANSFORMATIONS: List[PlaceTransformation] = [
    PlaceTransformation(
        id="pte_glb_1292_built", entity_id="ent_gaoliang_bridge",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1292, 1292, "ts_pte_glb1"),
        resulting_state_id="st_glb_1292",
        resulting_condition="元至元二十九年(1292)郭守敬引水工程建石闸桥"
                            "（金代已有闸记录，1292非第一道闸）",
        evidence_fact_ids=["tf_yuanshi_1292_tonghui"],
    ),
    PlaceTransformation(
        id="pte_glb_1980_rebuilt", entity_id="ent_gaoliang_bridge",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=TimeSpan(id="ts_pte_glb2", label="1980-1982 大规模改造",
                           begin=_dt(1980, "ts_pte_glb2b", precision="approximate"),
                           end=_dt(1982, "ts_pte_glb2e")),
        resulting_state_id="st_glb_1980",
        resulting_condition="展宽高梁桥路时重修（约1980—1982），非完整原状",
        evidence_fact_ids=["tf_wjbz_1980"],
    ),
    PlaceTransformation(
        id="pte_glz_1292_built", entity_id="ent_gaoliang_gate",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1292, 1292, "ts_pte_glz1"),
        resulting_state_id="st_glz_yuan_1292",
        resulting_condition="郭守敬工程置闸，称高梁闸（又称西城闸）；后已毁（毁废年代无档）",
        evidence_fact_ids=["tf_yuanshi_1292_tonghui", "tf_wjbz_gate_destroyed"],
    ),
    PlaceTransformation(
        id="pte_yht_1751_built", entity_id="ent_yihongtang",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1751, 1751, "ts_pte_yht1"),
        resulting_state_id="st_yht_1751",
        resulting_condition="乾隆十六年(1751)建于高梁桥西侧，南岸另有船坞（分列）",
        evidence_fact_ids=["tf_yihongtang_1751"],
    ),
    PlaceTransformation(
        id="pte_anh_1720_rebuilt", entity_id="ent_anhe_bridge",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1720, 1720, "ts_pte_anh1"),
        resulting_state_id="st_anh_shigong",
        resulting_condition="系统B：康熙五十九年(1720)重建石拱；系统A：乾隆年间改建单孔"
                            "石拱——两说并存，不得写定论",
        evidence_fact_ids=["tf_bma_yuanyiqian", "tf_wenshi_1724"],
    ),
    PlaceTransformation(
        id="pte_anh_1886_repaired", entity_id="ent_anhe_bridge",
        transformation=PlaceTransformationEvent.REBUILT,
        time_span=_ts(1886, 1886, "ts_pte_anh2"),
        resulting_state_id="st_anh_1886",
        resulting_condition="光绪十二年(1886)再修（系统B），旧桥沿用至1964年名效边界",
        evidence_fact_ids=["tf_bma_yuanyiqian"],
    ),
    PlaceTransformation(
        id="pte_anhn_1965_built", entity_id="ent_anhe_new_bridge",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1965, 1965, "ts_pte_anhn1"),
        resulting_state_id="st_anhn_1965",
        resulting_condition="因修京密引水渠另址新建（青龙桥东北约0.5公里），两河两桥分离",
        evidence_fact_ids=["tf_anhe_1965"],
    ),
    PlaceTransformation(
        id="pte_fyc_1729_built", entity_id="ent_fengyicang",
        transformation=PlaceTransformationEvent.CONSTRUCTED,
        time_span=_ts(1729, 1729, "ts_pte_fyc1"),
        resulting_state_id="st_fyc_1729",
        resulting_condition="雍正七年(1729)建丰益仓于德胜门外安河桥，供八旗俸饷",
        evidence_fact_ids=["tf_zhiguan_fengyicang"],
    ),
]

AGGREGATES: List[PlaceAggregate] = []
