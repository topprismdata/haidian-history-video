"""
haidian_kg/extractor.py
全区历史文献与考证长编实体抽取器
综合 13 集已交付研究档案、海淀历史地名清单与学术考证成果，
构建全区物理地物、建置实体、地名符号、史料书证、演变事件与争议假说的结构化知识集。
"""
import json
import pathlib
from typing import Dict, List, Any
from pydantic import BaseModel
from haidian_kg.ontology.schema import (
    PhysicalFeatureEntity,
    AdministrativeUnitEntity,
    ToponymEntity,
    PlaceAttestationEntity,
    ToponymEventEntity,
    CompetingHypothesisEntity,
    EvidenceLevel,
    EpistemicStatus,
)


class HaidianDataset(BaseModel):
    physical_features: List[PhysicalFeatureEntity]
    administrative_units: List[AdministrativeUnitEntity]
    toponyms: List[ToponymEntity]
    place_attestations: List[PlaceAttestationEntity]
    evolution_events: List[ToponymEventEntity]
    competing_hypotheses: List[CompetingHypothesisEntity]


class HaidianCorpusExtractor:
    """海淀全域历史知识抽取与构建引擎"""

    @classmethod
    def extract_all(cls) -> HaidianDataset:
        # =====================================================================
        # 1. 物理空间地物 (Physical Features)
        # =====================================================================
        features = [
            PhysicalFeatureEntity(
                id="feat_zhoukoudian",
                label="周口店龙骨山古人类洞穴遗址",
                feature_type="TerrainElevation",
                coordinates=[115.93, 39.73],
                description="距今约77万至20万年北京直立人及3万年山顶洞人栖居地，世界古人类发源圣地",
            ),
            PhysicalFeatureEntity(
                id="feat_yiguangsi_site",
                label="海淀四季青遗光寺新石器遗址",
                feature_type="TerrainElevation",
                coordinates=[116.26, 39.95],
                description="海淀本土新石器时代晚期磨制石斧出土台地，距今约4000年定居农耕遗存",
            ),
            PhysicalFeatureEntity(
                id="feat_donghulin_site",
                label="门头沟东胡林人永定河阶地遗址",
                feature_type="TerrainElevation",
                coordinates=[115.71, 39.98],
                description="距今约1万至9000年新石器早期人类过渡期墓葬与最早陶器出土地",
            ),
            PhysicalFeatureEntity(
                id="feat_wangfujing_paleo",
                label="王府井东方广场旧石器晚期古营地",
                feature_type="Wetland",
                coordinates=[116.41, 39.91],
                description="距今约2.5万年北京平原中心古人类季节性狩猎火塘营地",
            ),
            PhysicalFeatureEntity(
                id="feat_shangzhai_site",
                label="平谷上宅新石器文化遗址",
                feature_type="TerrainElevation",
                coordinates=[117.15, 40.17],
                description="距今约7500至6000年北京最早定居农业陶器与石磨盘聚落",
            ),
            PhysicalFeatureEntity(
                id="feat_liulihe_site",
                label="房山琉璃河西周燕都城址遗迹",
                feature_type="TerrainElevation",
                coordinates=[116.03, 39.61],
                description="西周早期燕国始封之都城遗址，出土克罍、克盉青铜重器，北京三千年建城信史实证地",
            ),
            PhysicalFeatureEntity(
                id="feat_qinghe_han_tombs",
                label="海淀清河汉代墓葬聚落遗址",
                feature_type="TerrainElevation",
                coordinates=[116.34, 40.03],
                description="两汉时期清河古道大型砖室与土坑墓葬群，出土陶壶鼎与五铢钱，证明汉代聚落繁盛",
            ),
            PhysicalFeatureEntity(
                id="feat_chexiangqu_canal",
                label="曹魏车箱渠水利引水古道",
                feature_type="Watercourse",
                coordinates=[116.30, 39.92],
                description="公元250年魏刘靖于石景山筑戾陵堰引永定河水，开车箱渠横贯海淀南部八里庄东流灌溉四千顷",
            ),
            PhysicalFeatureEntity(
                id="feat_linshuogong_site",
                label="隋幽州临朔宫行宫遗址",
                feature_type="TerrainElevation",
                coordinates=[116.36, 39.92],
                description="隋大业七年隋炀帝大举北征高句丽于蓟城北郊所建大本营与储粮军事行宫",
            ),
            PhysicalFeatureEntity(
                id="feat_diaoyutai_lake",
                label="金代钓鱼台行宫蓄水湖遗迹",
                feature_type="Wetland",
                coordinates=[116.33, 39.91],
                description="金章宗筑台垂钓积水成池之行宫园林湖泽，引玉泉山水蓄为东湖",
            ),
            PhysicalFeatureEntity(
                id="feat_gaolianghe",
                label="高梁河水系古道",
                feature_type="Watercourse",
                coordinates=[116.35, 39.95],
                description="先秦古河道，自金水河上源至积水潭，元代并入通惠河干道",
            ),
            PhysicalFeatureEntity(
                id="feat_wanquanhe",
                label="万泉河湿地水网",
                feature_type="Wetland",
                coordinates=[116.30, 39.98],
                description="西山山麓泉群汇聚形成的万泉河浅水洼地与湖泊沼泽区",
            ),
            PhysicalFeatureEntity(
                id="feat_yuquanshan",
                label="玉泉山山体与泉源",
                feature_type="TerrainElevation",
                coordinates=[116.25, 39.99],
                description="天下第一泉玉泉水源地，金代芙蓉殿、清代静明园所在地",
            ),
            PhysicalFeatureEntity(
                id="feat_wanshoushan",
                label="瓮山与瓮山泊（万寿山·昆明湖）",
                feature_type="TerrainElevation",
                coordinates=[116.27, 39.99],
                description="元代郭守敬引水水柜汇聚地，乾隆拓建为昆明湖与万寿山",
            ),
            PhysicalFeatureEntity(
                id="feat_xiangshan",
                label="香山与金山翠微山麓",
                feature_type="TerrainElevation",
                coordinates=[116.19, 39.99],
                description="西山余脉，明代皇室妃嫔陵寝带与清代静宜园所在地",
            ),
            PhysicalFeatureEntity(
                id="feat_changhe",
                label="长河皇家水道",
                feature_type="Watercourse",
                coordinates=[116.32, 39.94],
                description="高梁河上游长河段，明清两代通往西山御园的水上御路",
            ),
            PhysicalFeatureEntity(
                id="feat_qinghe",
                label="清河干流古河道",
                feature_type="Watercourse",
                coordinates=[116.34, 40.04],
                description="北京北郊横贯水系，古代通往塞北长城要隘的重要军事水障与漕运支线",
            ),
            PhysicalFeatureEntity(
                id="feat_baifu_wengshan_he",
                label="白浮瓮山河故道",
                feature_type="Watercourse",
                coordinates=[116.28, 40.02],
                description="元代郭守敬开凿引白浮泉至瓮山泊的绕山大渠，元代通惠河上游生命线",
            ),
            PhysicalFeatureEntity(
                id="feat_wenquan_spring",
                label="温泉地热出露带",
                feature_type="TerrainElevation",
                coordinates=[116.17, 40.03],
                description="西山断裂带地热水出露点，辽金温泉疗养古地",
            ),
            PhysicalFeatureEntity(
                id="feat_guangyuanzha_site",
                label="广源闸水利遗址",
                feature_type="HydraulicFacility",
                coordinates=[116.31, 39.94],
                # 🔴 2026-10-04 订正：原写「元至元二十六年通惠河头闸」——时序自相矛盾
                # （通惠河 1292 才开工，1289 年不可能已有「通惠河头闸」），
                # 且把 E16 冻结的建年双徽压成了单年定论。
                description="元代长河节制闸，通惠河闸系之首（至元二十九年 1292 工程）；"
                            "建年双徽：1289《水部备考》转引称建／1292《元史》通惠河工程开工列入闸系；"
                            "元史实名见《元史·河渠志》闸名序列「廣源牐」",
            ),
            PhysicalFeatureEntity(
                id="feat_anheqiao_site",
                label="安和桥下古长河桥涵遗址",
                feature_type="HydraulicFacility",
                coordinates=[116.27, 40.01],
                description="2009年出土明代碳十四定年木桩BA10291的水利枢纽节点",
            ),
            PhysicalFeatureEntity(
                id="feat_longbeicun_weir",
                label="白浮堰龙背村段古水利遗构（待考）",
                feature_type="HydraulicFacility",
                coordinates=[116.27, 40.03],
                # 🔴 2026-10-04 订正：原写「全国唯一存世之郭守敬白浮引水工程古堰实体残段遗存」——
                # 「全国唯一存世」属最高危现状断言，且所挂勘察报告查无此出版物。
                # 详见 attest_longbeicun_weir_site（已判 DISPROVEN）与 corpus/era5_yuan.md §1.4bis。
                description="龙背村一带白浮引水线路上的待考地面遗存；"
                            "无实物勘测档案支撑，不得作元代堰堤实体定性（L1 已撤），"
                            "更禁「全国唯一存世」；白浮泉引水系统元延祐元年（1314）起已淤塞（E29）",
            ),
            PhysicalFeatureEntity(
                id="feat_taizhouwu_dock",
                label="太舟坞古泊船凹岸台地",
                feature_type="TerrainElevation",
                coordinates=[116.18, 40.04],
                description="西山山麓山前坡水地带，元代白浮引水河道附近之船坞台地",
            ),
        ]

        # =====================================================================
        # 2. 建置与制度实体 (Administrative Units)
        # =====================================================================
        units = [
            # 先秦与汉唐
            AdministrativeUnitEntity(
                id="unit_jicheng_capital",
                label="先秦蓟国故都与战国燕都蓟城",
                unit_type="Settlement",
                located_at_feature_id="feat_gaolianghe",
                valid_start_year=-1046,
                valid_end_year=-221,
                description="西周初封蓟国、后为战国七雄燕国北都，位于今广安门内外，为北京建城古核",
            ),
            AdministrativeUnitEntity(
                id="unit_yan_fiefdom",
                label="西周燕国始封都邑（琉璃河城址）",
                unit_type="Settlement",
                located_at_feature_id="feat_liulihe_site",
                valid_start_year=-1046,
                valid_end_year=-700,
                description="周武王封召公之子克于燕所建古城，出土克罍、克盉青铜重器",
            ),
            AdministrativeUnitEntity(
                id="unit_guangyang_commandery",
                label="秦汉广阳郡与西汉广阳国蓟县",
                unit_type="Settlement",
                located_at_feature_id="feat_gaolianghe",
                valid_start_year=-221,
                valid_end_year=220,
                description="秦汉幽州刺史部监察与统属之都邑核心，海淀平原全境隶属广阳郡蓟县管辖",
            ),
            AdministrativeUnitEntity(
                id="unit_youzhou_commandery",
                label="唐代幽州大都督府与范阳卢龙节度使",
                unit_type="Settlement",
                located_at_feature_id="feat_gaolianghe",
                valid_start_year=581,
                valid_end_year=938,
                description="隋唐北疆军事经略核心，管辖幽州蓟县及周边羁縻府州，止于938年升辽南京",
            ),
            AdministrativeUnitEntity(
                id="unit_jicheng_suburb",
                label="蓟城西北郊农耕水利鄙野",
                unit_type="Settlement",
                located_at_feature_id="feat_gaolianghe",
                valid_start_year=-1046,
                description="先秦战国燕国蓟城西北部，沿高梁河水系分布的古农耕原野",
            ),
            AdministrativeUnitEntity(
                id="unit_daizhou_garrison",
                label="唐代羁縻带州孤竹县侨置区",
                unit_type="MilitaryGarrison",
                located_at_feature_id="feat_taizhouwu_dock",
                valid_start_year=705,
                valid_end_year=755,
                description="唐神龙元年安置东北降户与突厥部众之羁縻州，天宝间寄治昌平县清水店",
            ),
            # 辽金
            AdministrativeUnitEntity(
                id="unit_liao_nanjing",
                label="辽代南京析津府宛平县",
                unit_type="Settlement",
                located_at_feature_id="feat_gaolianghe",
                valid_start_year=938,
                valid_end_year=1125,
                description="公元938年升幽州为南京幽都府后设宛平县，海淀大部行政母体正式归属宛平",
            ),
            AdministrativeUnitEntity(
                id="unit_jin_zhongdu",
                label="金中都大兴府（北京正式建都之始）",
                unit_type="Settlement",
                located_at_feature_id="feat_gaolianghe",
                valid_start_year=1153,
                valid_end_year=1215,
                description="1153年海陵王完颜亮迁都中都，北京首次成为北方封建王朝正式首都，止于1215年蒙古破城更名燕京",
            ),
            AdministrativeUnitEntity(
                id="unit_qingshui_court",
                label="辽代西山清水院（大觉寺前身）",
                unit_type="ReligiousSite",
                located_at_feature_id="feat_xiangshan",
                valid_start_year=1088,
                valid_end_year=1215,
                description="辽大安四年契丹贵族敕建清水院，后金章宗扩为西山八大行宫水院之一",
            ),
            AdministrativeUnitEntity(
                id="unit_sifangpujue_temple",
                label="十方普觉寺（寿安山南麓；唐贞观始建兜率寺，今为国家植物园内古建）",
                unit_type="ReligiousSite",
                located_at_feature_id="feat_xiangshan",
                valid_start_year=627,
                valid_end_year=2026,
                description="唐太宗贞观年间始建，时名兜率寺；元至治元年改昭孝寺、后改洪庆寺并铸释迦牟尼涅槃铜卧佛；明正统八年改寿安山寺、成化十八年改永安寺；清雍正十二年御赐名十方普觉寺。第五批全国重点文物保护单位（2001-06-25，编号5-205）",
            ),
            AdministrativeUnitEntity(
                id="unit_shengshui_court",
                label="金章宗西山八大水院之圣水院（香山寺）",
                unit_type="ReligiousSite",
                located_at_feature_id="feat_xiangshan",
                valid_start_year=1186,
                valid_end_year=1215,
                description="金世宗大安寺、章宗圣水院，为香山最早之皇家敕建行宫水院",
            ),
            AdministrativeUnitEntity(
                id="unit_wenquan_village",
                label="温泉古村落",
                unit_type="Settlement",
                located_at_feature_id="feat_wenquan_spring",
                valid_start_year=1150,
                description="辽金时期依地热温泉形成的天然疗养与山乡聚落",
            ),
            # 元代
            AdministrativeUnitEntity(
                id="unit_haidian_town",
                label="元代海店驿路商贸聚落",
                unit_type="Settlement",
                located_at_feature_id="feat_wanquanhe",
                valid_start_year=1260,
                description="元大都城西北二十里通往居庸关大道的驿路水滨客商聚落",
            ),
            AdministrativeUnitEntity(
                id="unit_weiwu_village",
                label="元代畏吾村（畏兀儿聚落）",
                unit_type="Settlement",
                located_at_feature_id="feat_gaolianghe",
                valid_start_year=1280,
                description="元相廉希宪家族墓茔及内迁高昌畏兀儿贵族、守墓家眷形成的西域特色聚落",
            ),
            AdministrativeUnitEntity(
                id="unit_qinghe_transit_town",
                label="元代清河驿路重镇",
                unit_type="Settlement",
                located_at_feature_id="feat_qinghe",
                valid_start_year=1271,
                description="京北陆路与北运漕渠之水陆枢纽，元代通塞北关防之北门咽喉",
            ),
            # 明代
            AdministrativeUnitEntity(
                id="unit_xisanqi_garrison",
                label="明代西三旗小旗军屯",
                unit_type="MilitaryGarrison",
                located_at_feature_id="feat_qinghe",
                valid_start_year=1368,
                valid_end_year=1644,
                description="明代京卫卫所军屯体系中十人编制之‘小旗’编号屯田哨所，绝非满洲八旗",
            ),
            AdministrativeUnitEntity(
                id="unit_xierqi_garrison",
                label="明代西二旗小旗军屯",
                unit_type="MilitaryGarrison",
                located_at_feature_id="feat_qinghe",
                valid_start_year=1368,
                valid_end_year=1644,
                description="明代京卫卫所小旗编制军屯，与西三旗一脉相承",
            ),
            AdministrativeUnitEntity(
                id="unit_niulanzhuang_village",
                label="明代宛平西乡牛栏庄",
                unit_type="Settlement",
                located_at_feature_id="feat_wanquanhe",
                valid_start_year=1400,
                valid_end_year=1644,
                description="明代宛平县西北乡村，官民蓄养马牛之栏圈围聚成村",
            ),
            AdministrativeUnitEntity(
                id="unit_niangniangfu_tomb",
                label="明代翠微山一溜边山七十二府妃嫔陵区",
                unit_type="BurialGround",
                located_at_feature_id="feat_xiangshan",
                valid_start_year=1420,
                valid_end_year=1644,
                description="明代历代帝王非正宫皇贵妃、妃嫔专属金山香山长眠之园寝聚落",
            ),
            AdministrativeUnitEntity(
                id="unit_dongsimu_tomb",
                label="明代董四墓皇室茔地",
                unit_type="BurialGround",
                located_at_feature_id="feat_xiangshan",
                valid_start_year=1500,
                description="明代皇室墓地，后演变为看坟户聚居村落并盛产贡御之桃",
            ),
            AdministrativeUnitEntity(
                id="unit_zhongguan_cemetery",
                label="明清中官村太监义地",
                unit_type="BurialGround",
                located_at_feature_id="feat_wanquanhe",
                valid_start_year=1600,
                valid_end_year=1949,
                description="明清两代内廷宦官（中官）合资购置的合葬义冢与看坟守地营房",
            ),
            AdministrativeUnitEntity(
                id="unit_wanshousi_palace",
                label="明清万寿寺长河行宫与禅刹",
                unit_type="ReligiousSite",
                located_at_feature_id="feat_changhe",
                valid_start_year=1577,
                description="明万历五年为皇太后祝寿敕建，清康乾两代水上巡幸必宿行宫",
            ),
            AdministrativeUnitEntity(
                id="unit_cishousi_temple",
                label="明代慈寿寺与八里庄玲珑塔",
                unit_type="ReligiousSite",
                located_at_feature_id="feat_changhe",
                valid_start_year=1576,
                description="明神宗圣母慈圣皇太后出资敕建，京西八里庄地标性密檐塔",
            ),
            AdministrativeUnitEntity(
                id="unit_dazhongsi_temple",
                label="清雍正觉生寺（大钟寺）",
                unit_type="ReligiousSite",
                located_at_feature_id="feat_gaolianghe",
                valid_start_year=1733,
                description="雍正十一年敕建祈雨行宫禅寺，乾隆十六年将万寿寺永乐大钟移置于此",
            ),
            # 清代三山五园与市镇
            AdministrativeUnitEntity(
                id="unit_changchunyuan",
                label="清康熙畅春园",
                unit_type="ImperialGarden",
                located_at_feature_id="feat_wanquanhe",
                valid_start_year=1687,
                valid_end_year=1860,
                description="清圣祖康熙避喧听政之首座皇家御园，咸丰十年遭英法联军焚毁",
            ),
            AdministrativeUnitEntity(
                id="unit_yuanmingyuan",
                label="清代圆明园",
                unit_type="ImperialGarden",
                located_at_feature_id="feat_wanquanhe",
                valid_start_year=1707,
                valid_end_year=1860,
                description="万园之园，康乾嘉道咸五朝清廷夏秋理政与帝国权力中枢",
            ),
            AdministrativeUnitEntity(
                id="unit_dayouzhuang_village",
                label="大有庄（清代改名村落）",
                unit_type="Settlement",
                located_at_feature_id="feat_wanshoushan",
                valid_start_year=None,
                # 【R6 回灌 2026-10-04】E4 冻结：官书 L1 是《日下旧闻考》**卷100**
                # 「达官村西南里许为大有庄，庄前为御道」，乾隆朝已用其名；
                # 赐名故事为 L3 地方文史「据载」，无诏书/御制诗/宫档出处；
                # 另有竞争解释（人大清史所：渐富裕后自行更名）。**不锁 1750**。
                description="皇家园林/仓廪/马政体系服务的村落；清初曾称『穷八家』，"
                            "乾隆朝官书已作『大有庄』（《日下旧闻考》卷100，L1）。"
                            "❌ 不得写成『乾隆1750御赐改名』的已确证事实——赐名说属 L3 据载层",
            ),
            AdministrativeUnitEntity(
                id="unit_yimuyuan_fields",
                label="一亩园与娘娘庙会",
                unit_type="Settlement",
                located_at_feature_id="feat_wanquanhe",
                valid_start_year=None,
                # 【R5 回灌 2026-10-04】E5 冻结红线：❌ 一亩园＝皇帝亲耕耤田／一亩三分地
                # （真正的耤田礼在先农坛，L1）；「演耕处」仅传说层（北京日报：传说为雍正帝
                # 演耕处，但缺少依据）。L1《八旬万寿盛典》图档显示为圆明园大宫门前
                # 有建筑院落/道路/水渠/土山的密集区域；功能解释属 L2 现代研究。
                # **不锁建年 1723/1745。** 原挂《清高宗御制文二集》引文已撤（拟托书证）。
                description="圆明园大宫门前附属空间与现代社区；乾隆朝图档见建筑院落、"
                            "道路、水渠、土山（L1）。京西娘娘庙会（泰山圣母庙，"
                            "『康熙重建、光绪再建』L2/L3）所在地。"
                            "❌ 禁称『皇帝躬耕演礼之籍田』；耤田礼在先农坛",
            ),
            AdministrativeUnitEntity(
                id="unit_qinglongqiao_market",
                label="青龙桥御道水陆重镇",
                unit_type="Settlement",
                located_at_feature_id="feat_anheqiao_site",
                valid_start_year=1644,
                description="三山五园环抱之御道集镇，通往香山、静明园与圆明园必经水旱关卡",
            ),
            AdministrativeUnitEntity(
                id="unit_suzhoujie_market",
                label="清漪园万寿山后湖苏州街买卖街",
                unit_type="ImperialGarden",
                located_at_feature_id="feat_wanshoushan",
                valid_start_year=1761,
                valid_end_year=1860,
                description="乾隆二十六年为崇庆皇太后七十寿辰仿苏州山塘街建造之水上集市宫宛",
            ),
            AdministrativeUnitEntity(
                id="unit_landianchang_town",
                label="蓝靛厂街市与外火器营",
                unit_type="MilitaryGarrison",
                located_at_feature_id="feat_changhe",
                valid_start_year=1770,
                # 【R2 回灌 2026-10-04】E10 冻结：外火器营营房「四千（余）间」查无实据
                # （《海淀历史地名清单》旧载）。分项记载为官廨一千余间、炮甲连房六千余间、
                # 周围门楼三千一百多座。**纪律＝不给总数。**
                description="明代染蓝靛作坊，乾隆三十五年特种清军外火器营移驻形成之兵营市镇；"
                            "营区规模只报分项（官廨一千余间、炮甲连房六千余间、周围门楼三千一百多座），"
                            "❌ 不给总数（『四千余间』查无实据）",
            ),
            AdministrativeUnitEntity(
                id="unit_jianruiying_garrison",
                label="香山健锐营八旗云梯特种部队",
                unit_type="MilitaryGarrison",
                located_at_feature_id="feat_xiangshan",
                valid_start_year=1749,
                description="乾隆平定大小金川特设之精锐部队，营房按八旗翼长排列，广筑演武石碉楼",
            ),
            # 八旗护军营系统（肖家河与树村核心）
            AdministrativeUnitEntity(
                id="unit_zhenghuangqi_camp",
                label="圆明园护军营正黄旗营房（肖家河村北）",
                unit_type="MilitaryGarrison",
                located_at_feature_id="feat_wanquanhe",
                valid_start_year=1724,
                description="雍正二年设立之圆明园八旗护卫营房，驻扎肖家河村北，拱卫园门西北",
            ),
            AdministrativeUnitEntity(
                id="unit_xianghuangqi_camp",
                label="圆明园护军营镶黄旗营房（树村西）",
                unit_type="MilitaryGarrison",
                located_at_feature_id="feat_baifu_wengshan_he",
                valid_start_year=1724,
                description="雍正二年设立，驻树村以西，与树村村落紧邻共生",
            ),
            AdministrativeUnitEntity(
                id="unit_zhengbaiqi_camp",
                label="圆明园护军营正白旗营房（树村东）",
                unit_type="MilitaryGarrison",
                located_at_feature_id="feat_baifu_wengshan_he",
                valid_start_year=1724,
                description="雍正二年设立，驻树村以东，长春园东北",
            ),
            # 近现代科教与高新区
            AdministrativeUnitEntity(
                id="unit_tsinghua_academy",
                label="清华学堂与清华大学",
                unit_type="ModernInstitution",
                located_at_feature_id="feat_wanquanhe",
                valid_start_year=1911,
                description="庚子赔款退款建立之留美预备学堂，选址清华园康熙皇三子胤祉赐园遗址",
            ),
            AdministrativeUnitEntity(
                id="unit_cas_zhongguancun",
                label="中国科学院中关村科学城科研园区",
                unit_type="ModernInstitution",
                located_at_feature_id="feat_wanquanhe",
                valid_start_year=1953,
                description="1953年新中国政务院确定之全国最高科学学术中心驻地，近代中国科学第一城",
            ),
            AdministrativeUnitEntity(
                id="unit_zgc_hightech_zone",
                label="北京市新技术产业开发试验区（中关村高新区）",
                unit_type="ModernInstitution",
                located_at_feature_id="feat_wanquanhe",
                valid_start_year=1988,
                description="国务院正式批准设立的全国第一个国家级高新技术产业开发区",
            ),
        ]

        # =====================================================================
        # 3. 地名称号实体 (Toponyms)
        # =====================================================================
        toponyms = [
            # 史前古人类与新石器遗址地名
            ToponymEntity(id="top_zhoukoudian", standard_form="周口店", script_hanzi="周口店", phonetic_pinyin="zhōu kǒu diàn", name_type="standard"),
            ToponymEntity(id="top_yiguangsi", standard_form="遗光寺", script_hanzi="遗光寺", phonetic_pinyin="yí guāng sì", name_type="standard"),
            ToponymEntity(id="top_donghulin", standard_form="东胡林", script_hanzi="东胡林", phonetic_pinyin="dōng hú lín", name_type="standard"),
            ToponymEntity(id="top_banquan", standard_form="阪泉", script_hanzi="阪泉", phonetic_pinyin="bǎn quán", name_type="folk"),
            # 先秦封国与都邑地名
            ToponymEntity(id="top_liulihe", standard_form="琉璃河", script_hanzi="琉璃河", phonetic_pinyin="liú lí hé", name_type="standard", associated_unit_id="unit_yan_fiefdom"),
            ToponymEntity(id="top_jicheng", standard_form="蓟城", script_hanzi="蓟城", phonetic_pinyin="jì chéng", name_type="official", associated_unit_id="unit_jicheng_capital"),
            ToponymEntity(id="top_yanguo", standard_form="燕国", script_hanzi="燕国", phonetic_pinyin="yān guó", name_type="official", associated_unit_id="unit_yan_fiefdom"),
            ToponymEntity(id="top_chexiangqu", standard_form="车箱渠", script_hanzi="车箱渠", phonetic_pinyin="chē xiāng qú", name_type="official"),
            ToponymEntity(id="top_guangyang", standard_form="广阳", script_hanzi="广阳", phonetic_pinyin="guǎng yáng", name_type="official", associated_unit_id="unit_guangyang_commandery"),
            # 隋唐幽州与临朔宫地名
            ToponymEntity(id="top_linshuogong", standard_form="临朔宫", script_hanzi="临朔宫", phonetic_pinyin="lín shuò gōng", name_type="official", associated_unit_id="unit_youzhou_commandery"),
            ToponymEntity(id="top_youzhou", standard_form="幽州", script_hanzi="幽州", phonetic_pinyin="yōu zhōu", name_type="official", associated_unit_id="unit_youzhou_commandery"),
            # 辽南京与金中都地名
            ToponymEntity(id="top_diaoyutai", standard_form="钓鱼台", script_hanzi="钓鱼台", phonetic_pinyin="diào yú tái", name_type="official"),
            ToponymEntity(id="top_nanjing_xijin", standard_form="南京析津府", script_hanzi="南京析津府", phonetic_pinyin="nán jīng xī jīn fǔ", name_type="official", associated_unit_id="unit_liao_nanjing"),
            ToponymEntity(id="top_zhongdu_daxing", standard_form="中都大兴府", script_hanzi="中都大兴府", phonetic_pinyin="zhōng dū dà xīng fǔ", name_type="official", associated_unit_id="unit_jin_zhongdu"),
            ToponymEntity(id="top_shengshuiyuan", standard_form="圣水院", script_hanzi="圣水院", phonetic_pinyin="shèng shuǐ yuàn", name_type="official", associated_unit_id="unit_shengshui_court"),
            # 高梁河与高梁桥
            ToponymEntity(id="top_gaolianghe", standard_form="高梁河", script_hanzi="高梁河", phonetic_pinyin="gāo liáng hé", name_type="standard", associated_unit_id="unit_jicheng_suburb"),
            ToponymEntity(id="top_gaoliangzha", standard_form="高梁闸", script_hanzi="高梁闸", phonetic_pinyin="gāo liáng zhá", name_type="official"),
            ToponymEntity(id="top_gaoliangqiao", standard_form="高梁桥", script_hanzi="高梁桥", phonetic_pinyin="gāo liáng qiáo", name_type="standard", predecessor_toponym_id="top_gaoliangzha"),
            # 海淀镇
            ToponymEntity(id="top_haidian_dian1", standard_form="海店", script_hanzi="海店", phonetic_pinyin="hǎi diàn", name_type="vulgar", associated_unit_id="unit_haidian_town"),
            ToponymEntity(id="top_haidian_dian2", standard_form="海甸", script_hanzi="海甸", phonetic_pinyin="hǎi diàn", name_type="euphemistic", predecessor_toponym_id="top_haidian_dian1"),
            ToponymEntity(id="top_haidian", standard_form="海淀", script_hanzi="海淀", phonetic_pinyin="hǎi diàn", name_type="standard", predecessor_toponym_id="top_haidian_dian2"),
            # 魏公村
            ToponymEntity(id="top_weiwucun", standard_form="畏吾村", script_hanzi="畏吾村", phonetic_pinyin="wèi wú cūn", name_type="standard", associated_unit_id="unit_weiwu_village"),
            ToponymEntity(id="top_weiwuer_cun", standard_form="畏兀村", script_hanzi="畏兀村", phonetic_pinyin="wèi wù cūn", name_type="vulgar", predecessor_toponym_id="top_weiwucun"),
            ToponymEntity(id="top_weigongcun", standard_form="魏公村", script_hanzi="魏公村", phonetic_pinyin="wèi gōng cūn", name_type="standard", predecessor_toponym_id="top_weiwuer_cun"),
            # 西三旗与西二旗
            ToponymEntity(id="top_xisanqi", standard_form="西三旗", script_hanzi="西三旗", phonetic_pinyin="xī sān qí", name_type="standard", associated_unit_id="unit_xisanqi_garrison"),
            ToponymEntity(id="top_xierqi", standard_form="西二旗", script_hanzi="西二旗", phonetic_pinyin="xī èr qí", name_type="standard", associated_unit_id="unit_xierqi_garrison"),
            # 六郎庄
            ToponymEntity(id="top_niulanzhuang", standard_form="牛栏庄", script_hanzi="牛栏庄", phonetic_pinyin="niú lán zhuāng", name_type="vulgar", associated_unit_id="unit_niulanzhuang_village"),
            ToponymEntity(id="top_liulangzhuang_willow", standard_form="柳浪庄", script_hanzi="柳浪庄", phonetic_pinyin="liǔ làng zhuāng", name_type="euphemistic", predecessor_toponym_id="top_niulanzhuang"),
            ToponymEntity(id="top_liulangzhuang_general", standard_form="六郎庄", script_hanzi="六郎庄", phonetic_pinyin="liù láng zhuāng", name_type="folk", predecessor_toponym_id="top_liulangzhuang_willow"),
            # 大有庄
            ToponymEntity(id="top_qiongbajia", standard_form="穷八家", script_hanzi="穷八家", phonetic_pinyin="qióng bā jiā", name_type="vulgar", associated_unit_id="unit_dayouzhuang_village"),
            ToponymEntity(id="top_dayouzhuang", standard_form="大有庄", script_hanzi="大有庄", phonetic_pinyin="dà yǒu zhuāng", name_type="official", predecessor_toponym_id="top_qiongbajia"),
            # 中关村
            ToponymEntity(id="top_zhongguancun_eunuch", standard_form="中官村", script_hanzi="中官村", phonetic_pinyin="zhōng guān cūn", name_type="vulgar", associated_unit_id="unit_zhongguan_cemetery"),
            ToponymEntity(id="top_zhongguantun", standard_form="中官屯", script_hanzi="中官屯", phonetic_pinyin="zhōng guān tún", name_type="vulgar", predecessor_toponym_id="top_zhongguancun_eunuch"),
            ToponymEntity(id="top_zhongguancun_modern", standard_form="中关村", script_hanzi="中关村", phonetic_pinyin="zhōng guān cūn", name_type="standard", predecessor_toponym_id="top_zhongguancun_eunuch"),
            # 安河桥
            ToponymEntity(id="top_anheqiao_wood", standard_form="罗锅桥", script_hanzi="罗锅桥", phonetic_pinyin="luó guō qiáo", name_type="vulgar", associated_unit_id="unit_qinglongqiao_market"),
            ToponymEntity(id="top_anheqiao_peace", standard_form="安和桥", script_hanzi="安和桥", phonetic_pinyin="ān hé qiáo", name_type="official", predecessor_toponym_id="top_anheqiao_wood"),
            ToponymEntity(id="top_anheqiao_river", standard_form="安河桥", script_hanzi="安河桥", phonetic_pinyin="ān hé qiáo", name_type="standard", predecessor_toponym_id="top_anheqiao_peace"),
            # 青龙桥
            ToponymEntity(id="top_qinglongqiao", standard_form="青龙桥", script_hanzi="青龙桥", phonetic_pinyin="qīng lóng qiáo", name_type="standard", associated_unit_id="unit_qinglongqiao_market"),
            # 蓝靛厂
            ToponymEntity(id="top_landianchang_dye", standard_form="蓝靛厂", script_hanzi="蓝靛厂", phonetic_pinyin="lán diàn chǎng", name_type="vulgar", associated_unit_id="unit_landianchang_town"),
            ToponymEntity(id="top_huoqiying", standard_form="火器营", script_hanzi="火器营", phonetic_pinyin="huǒ qì yíng", name_type="official"),
            # 树村
            ToponymEntity(id="top_shucun", standard_form="树村", script_hanzi="树村", phonetic_pinyin="shù cūn", name_type="standard", associated_unit_id="unit_xianghuangqi_camp"),
            # 肖家河与龙背村
            ToponymEntity(id="top_xiaojiahe", standard_form="肖家河", script_hanzi="肖家河", phonetic_pinyin="xiāo jiā hé", name_type="standard", associated_unit_id="unit_zhenghuangqi_camp"),
            ToponymEntity(id="top_longbeicun", standard_form="龙背村", script_hanzi="龙背村", phonetic_pinyin="lóng bèi cūn", name_type="standard"),
            # 苏州街
            ToponymEntity(id="top_suzhoujie", standard_form="苏州街", script_hanzi="苏州街", phonetic_pinyin="sū zhōu jiē", name_type="standard", associated_unit_id="unit_suzhoujie_market"),
            ToponymEntity(id="top_maimaijie", standard_form="买卖街", script_hanzi="买卖街", phonetic_pinyin="mǎi mài jiē", name_type="official"),
            # 大钟寺与觉生寺
            ToponymEntity(id="top_jueshengsi", standard_form="觉生寺", script_hanzi="觉生寺", phonetic_pinyin="jué shēng sì", name_type="official", associated_unit_id="unit_dazhongsi_temple"),
            ToponymEntity(id="top_dazhongsi", standard_form="大钟寺", script_hanzi="大钟寺", phonetic_pinyin="dà zhōng sì", name_type="vulgar", predecessor_toponym_id="top_jueshengsi"),
            # 一亩园
            ToponymEntity(id="top_yimuyuan", standard_form="一亩园", script_hanzi="一亩园", phonetic_pinyin="yī mǔ yuán", name_type="standard", associated_unit_id="unit_yimuyuan_fields"),
            # 娘娘府与董四墓
            ToponymEntity(id="top_niangniangfu", standard_form="娘娘府", script_hanzi="娘娘府", phonetic_pinyin="niáng niang fǔ", name_type="standard", associated_unit_id="unit_niangniangfu_tomb"),
            ToponymEntity(id="top_dongsimu", standard_form="董四墓", script_hanzi="董四墓", phonetic_pinyin="dǒng sì mù", name_type="standard", associated_unit_id="unit_dongsimu_tomb"),
            # 太舟坞
            ToponymEntity(id="top_daizhou_name", standard_form="带州", script_hanzi="带州", phonetic_pinyin="dài zhōu", name_type="official", associated_unit_id="unit_daizhou_garrison"),
            ToponymEntity(id="top_taizhouwu", standard_form="太舟坞", script_hanzi="太舟坞", phonetic_pinyin="tài zhōu wù", name_type="standard", predecessor_toponym_id="top_daizhou_name"),
            # 温泉与清河
            ToponymEntity(id="top_wenquan", standard_form="温泉", script_hanzi="温泉", phonetic_pinyin="wēn quán", name_type="standard", associated_unit_id="unit_wenquan_village"),
            ToponymEntity(id="top_qinghezhen", standard_form="清河镇", script_hanzi="清河镇", phonetic_pinyin="qīng hé zhèn", name_type="standard", associated_unit_id="unit_qinghe_transit_town"),
            # 寺观名
            ToponymEntity(id="top_wanshousi", standard_form="万寿寺", script_hanzi="万寿寺", phonetic_pinyin="wàn shòu sì", name_type="official", associated_unit_id="unit_wanshousi_palace"),
            ToponymEntity(id="top_cishousi", standard_form="慈寿寺", script_hanzi="慈寿寺", phonetic_pinyin="cí shòu sì", name_type="official", associated_unit_id="unit_cishousi_temple"),
            ToponymEntity(id="top_linglongta", standard_form="玲珑塔", script_hanzi="玲珑塔", phonetic_pinyin="líng lóng tǎ", name_type="vulgar"),
            ToponymEntity(id="top_zhenjuesi", standard_form="真觉寺", script_hanzi="真觉寺", phonetic_pinyin="zhēn jué sì", name_type="official"),
            ToponymEntity(id="top_wutasi", standard_form="五塔寺", script_hanzi="五塔寺", phonetic_pinyin="wǔ tǎ sì", name_type="vulgar", predecessor_toponym_id="top_zhenjuesi"),
            ToponymEntity(id="top_dajuesi", standard_form="大觉寺", script_hanzi="大觉寺", phonetic_pinyin="dà jué sì", name_type="official", associated_unit_id="unit_qingshui_court"),
            ToponymEntity(id="top_sifangpujue", standard_form="十方普觉寺", script_hanzi="十方普觉寺", phonetic_pinyin="shí fāng pǔ jué sì", name_type="official", associated_unit_id="unit_sifangpujue_temple"),
            ToponymEntity(id="top_wofosi", standard_form="卧佛寺", script_hanzi="卧佛寺", phonetic_pinyin="wò fó sì", name_type="vulgar", predecessor_toponym_id="top_sifangpujue"),
            # 🔴 G2 订正：兜率寺是**最早**的初建名（唐），无前身，不应指向现名
            ToponymEntity(id="top_doushuai", standard_form="兜率寺", script_hanzi="兜率寺", phonetic_pinyin="dōu shuài sì", name_type="official"),
            # 🔴 E26 审核订正：寿安山寺是**元延祐七年(1320)敕建名**，前身是唐代的兜率寺
            ToponymEntity(id="top_shuanshansi", standard_form="寿安山寺", script_hanzi="寿安山寺", phonetic_pinyin="shòu ān shān sì", name_type="official", predecessor_toponym_id="top_doushuai"),
            ToponymEntity(id="top_zhaoxiaoshi", standard_form="昭孝寺", script_hanzi="昭孝寺", phonetic_pinyin="zhāo xiào sì", name_type="official", predecessor_toponym_id="top_shuanshansi"),
            ToponymEntity(id="top_hongqingsi", standard_form="洪庆寺", script_hanzi="洪庆寺", phonetic_pinyin="hóng qìng sì", name_type="official", predecessor_toponym_id="top_shuanshansi"),
            # 🔴 E26 审核订正：永安寺（明成化十八年）前身是明正统八年的寿安禅林
            # 🔴 E26 审核新增：明正统八年(1443)朝廷赐名「寿安禅林」并颁《大藏经》
            ToponymEntity(id="top_shouanchanlin", standard_form="寿安禅林", script_hanzi="寿安禅林", phonetic_pinyin="shòu ān chán lín", name_type="official", predecessor_toponym_id="top_shuanshansi"),
            ToponymEntity(id="top_yongansi", standard_form="永安寺", script_hanzi="永安寺", phonetic_pinyin="yǒng ān sì", name_type="official", predecessor_toponym_id="top_shouanchanlin"),
            ToponymEntity(id="top_guangyuanzha", standard_form="广源闸", script_hanzi="广源闸", phonetic_pinyin="guǎng yuán zhá", name_type="official"),
            ToponymEntity(id="top_chengfu", standard_form="成府", script_hanzi="成府", phonetic_pinyin="chéng fǔ", name_type="standard"),
            ToponymEntity(id="top_chengfulu", standard_form="成府路", script_hanzi="成府路", phonetic_pinyin="chéng fǔ lù", name_type="standard", predecessor_toponym_id="top_chengfu"),
            ToponymEntity(id="top_baijiatuan", standard_form="白家疃", script_hanzi="白家疃", phonetic_pinyin="bái jiā tuǎn", name_type="standard"),
            ToponymEntity(id="top_guajiatun", standard_form="挂甲屯", script_hanzi="挂甲屯", phonetic_pinyin="guà jiǎ tún", name_type="standard"),
            ToponymEntity(id="top_huangzhuang", standard_form="黄庄", script_hanzi="黄庄", phonetic_pinyin="huáng zhuāng", name_type="standard"),
            ToponymEntity(id="top_zaojunmiao", standard_form="皂君庙", script_hanzi="皂君庙", phonetic_pinyin="zào jūn miào", name_type="standard"),
        ]

        # =====================================================================
        # 4. 史料书证用例实体 (Place Attestations)
        # =====================================================================
        attestations = [
            # L1 考古硬证据
            PlaceAttestationEntity(
                id="attest_zhoukoudian_peking_man",
                toponym_id="top_zhoukoudian",
                attested_name="周口店第一地点北京直立人遗存",
                source_title="周口店直立人遗址发掘与定年公报",
                source_author="中国科学院古脊椎动物与古人类研究所",
                recorded_year=-770000,
                dynasty="旧石器时代初期（距今约77万年）",
                quote="出土完整北京猿人头盖骨化石、十万余件打制石器及数米厚灰烬层，确证古人类最早天然用火与石器打制证据",
                evidence_level=EvidenceLevel.L1_ARCHAEOLOGICAL,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_shandingdong_needle",
                toponym_id="top_zhoukoudian",
                attested_name="山顶洞人人工骨针与穿孔饰物",
                source_title="周口店山顶洞人遗址发掘报告",
                source_author="裴文中",
                recorded_year=-30000,
                dynasty="旧石器时代晚期（距今约3万年）",
                quote="出土长82毫米磨制穿孔骨针与141件穿孔石珠、海蚶壳随葬饰物，实证缝纫技术与原始埋葬礼仪",
                evidence_level=EvidenceLevel.L1_ARCHAEOLOGICAL,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_wangfujing_camp",
                toponym_id="top_zhoukoudian",
                attested_name="王府井东方广场旧石器古营地",
                source_title="北京王府井东方广场旧石器时代晚期遗址发掘简报",
                source_author="北京市文物研究所",
                recorded_year=-25000,
                dynasty="旧石器时代末期（距今约2.5万年）",
                quote="在北京冲积平原腹地发现古人类火塘遗迹、打制石片与哺乳动物碎骨，实证古人类已走出西山进入平原猎原",
                evidence_level=EvidenceLevel.L1_ARCHAEOLOGICAL,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_donghulin_pottery",
                toponym_id="top_donghulin",
                attested_name="东胡林人新石器早期墓葬与陶器",
                source_title="门头沟东胡林新石器时代早期遗址发掘报告",
                source_author="北京大学考古学系、北京市文物研究所",
                recorded_year=-10000,
                dynasty="新石器时代早期（距今约1万至9000年）",
                quote="出土完整东胡林少女墓葬骨架及早期素面平底陶器残片，为北京地区新旧石器过渡与农业萌芽之源",
                evidence_level=EvidenceLevel.L1_ARCHAEOLOGICAL,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_shangzhai_agriculture",
                toponym_id="top_zhoukoudian",
                attested_name="上宅文化彩陶与石磨盘",
                source_title="平谷上宅新石器时代文化遗址发掘简报",
                source_author="北京市文物研究所",
                recorded_year=-7000,
                dynasty="新石器时代中晚期（距今约7000年）",
                quote="出土鸟头形陶把、镂孔陶豆、石磨盘及磨棒，确立北京地区首支独立新石器定居农耕考古学文化",
                evidence_level=EvidenceLevel.L1_ARCHAEOLOGICAL,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_yiguangsi_axe",
                toponym_id="top_yiguangsi",
                attested_name="海淀四季青遗光寺新石器磨制石斧",
                source_title="北京海淀区出土文物志",
                source_author="海淀区文物管理所、首都博物馆",
                recorded_year=-4000,
                dynasty="新石器时代晚期（距今约4000年）",
                quote="四季青遗光寺台地出土新石器时代晚期磨制石斧与石锛，证实海淀西山山前阶地四千年前已有人类农耕定居活动",
                evidence_level=EvidenceLevel.L1_ARCHAEOLOGICAL,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="海淀本土最早物质文化考古信史物证",
            ),
            PlaceAttestationEntity(
                id="attest_banquan_myth",
                toponym_id="top_banquan",
                attested_name="黄帝阪泉之战传说",
                source_title="史记·五帝本纪",
                source_author="司马迁",
                recorded_year=-100,
                dynasty="西汉（追述远古神话）",
                quote="轩辕乃修德振兵……与炎帝战于阪泉之野，三战然后得其志",
                evidence_level=EvidenceLevel.L5_FOLK_LEGEND,
                epistemic_status=EpistemicStatus.FOLK_LEGEND,
                notes="远古部落神话传说，未有出土实物信史印证，严格禁止列为确证信史",
            ),
            # Era 1 先秦封国与燕都青铜铭文硬证据
            PlaceAttestationEntity(
                id="attest_ke_lei_bronze",
                toponym_id="top_liulihe",
                attested_name="西周琉璃河克罍克盉青铜铭文",
                source_title="房山琉璃河西周燕都遗址M1193发掘报告",
                source_author="北京市文物研究所、中国社会科学院考古研究所",
                recorded_year=-1046,
                dynasty="西周初年（约公元前1046年）",
                quote="盖内铸铭文：周王命太保召公奭长子克‘命克侯于燕’，实证第一代燕侯就封北燕，北京三千年建城信史原点",
                evidence_level=EvidenceLevel.L1_ARCHAEOLOGICAL,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="北京建城史最高规格考古与金文双重互证硬证据",
            ),
            PlaceAttestationEntity(
                id="attest_shiji_zhou_wuwang",
                toponym_id="top_jicheng",
                attested_name="史记武王封燕封蓟记载",
                source_title="史记·周本纪",
                source_author="司马迁",
                recorded_year=-100,
                dynasty="西汉（记西周初年事）",
                quote="武王褒封功臣谋士，封召公奭于燕，封帝尧之后于蓟",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            # Era 2 秦汉魏晋与六朝考古与文献书证
            PlaceAttestationEntity(
                id="attest_qinghe_han_tombs_dig",
                toponym_id="top_qinghezhen",
                attested_name="清河汉墓群发掘简报",
                source_title="北京清河汉代墓葬发掘简报",
                source_author="北京市文物工作队",
                recorded_year=100,
                dynasty="东汉（出土两汉墓葬实物）",
                quote="出土两汉大型砖室墓与土坑墓群，出土泥质灰陶鼎、壶及五铢钱，实证汉代清河沿岸农耕聚落与商旅交通繁盛",
                evidence_level=EvidenceLevel.L1_ARCHAEOLOGICAL,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_sanguozhi_liujing",
                toponym_id="top_chexiangqu",
                attested_name="魏刘靖筑戾陵堰车箱渠",
                source_title="三国志·魏书·刘靖传",
                source_author="陈寿",
                recorded_year=250,
                dynasty="三国曹魏嘉平二年",
                quote="嘉平二年，刘靖都督幽州军事，乃循漯水之崖，筑戾陵堰，起车箱渠，灌溉蓟城南北四千余顷",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            # Era 3 隋唐五代幽州文献与墓志硬证据
            PlaceAttestationEntity(
                id="attest_suishu_linshuogong",
                toponym_id="top_linshuogong",
                attested_name="隋书炀帝纪置临朔宫记载",
                source_title="隋书·炀帝纪上",
                source_author="魏徵等",
                recorded_year=611,
                dynasty="隋大业七年",
                quote="大业七年春二月乙未，帝自江都驿赴涿郡。幽州置临朔宫，征天下兵集涿郡",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_tang_jiao_epitaph",
                toponym_id="top_daizhou_name",
                attested_name="唐带州孤竹府焦君墓志铭",
                source_title="大唐幽州昌平县孤竹府带州故折冲焦府君墓志铭",
                source_author="唐官刻",
                recorded_year=750,
                dynasty="唐天宝九载",
                quote="君讳某，幽州昌平县孤竹府带州折冲。带州本析营州契丹降户置，寄治昌平县清水店",
                evidence_level=EvidenceLevel.L1_ARCHAEOLOGICAL,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="确证实物：带州寄治昌平清水店而非海淀太舟坞",
            ),
            # Era 4 辽南京与金中都史料书证
            PlaceAttestationEntity(
                id="attest_diaoyutai_dijing",
                toponym_id="top_diaoyutai",
                attested_name="帝京景物略金章宗钓鱼台记载",
                source_title="帝京景物略卷五",
                source_author="刘侗",
                recorded_year=1190,
                dynasty="明修记金代事",
                quote="钓鱼台在宛平县西十里，章宗钓鱼于此，积水成池，台其后筑也",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_liaoshi_nanjing",
                toponym_id="top_nanjing_xijin",
                attested_name="辽史会同元年升南京记载",
                source_title="辽史·地理志四",
                source_author="脱脱等",
                recorded_year=938,
                dynasty="元修记辽代事",
                quote="会同元年，太宗升幽州为南京，统宛平、析津二县",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_anheqiao_wood_c14",
                toponym_id="top_anheqiao_wood",
                attested_name="罗锅桥木桩BA10291",
                source_title="安河桥古水利遗址考古发掘报告",
                source_author="北京市文物研究所",
                recorded_year=2009,
                dynasty="明代（经碳十四测定为明代中晚期原桩）",
                quote="在安和桥旧桥台下清理出密集柏木地钉，标本BA10291碳十四定年测定为明代，证实该处明代已建有大型木构拱桥跨水枢纽",
                evidence_level=EvidenceLevel.L1_ARCHAEOLOGICAL,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="全海淀水利古桥最强考古硬证据",
            ),
            PlaceAttestationEntity(
                id="attest_longbeicun_weir_site",
                toponym_id="top_longbeicun",
                attested_name="白浮堰龙背村引水残段",
                # 🔴 2026-10-04 三重证伪，判死留档（证伪≠删证，保留 quote 原文供审计）：
                #   ① 所挂「京密引水渠沿线古水利工程勘察报告／北京市水利古籍整理小组／1983」
                #      **查无此出版物**——无档案不能支撑 L1 考古硬证据；
                #   ② E1 研究档案明令「不建立木桩与白浮堰遗存的归属关系」，本库对同一地面从未敢立遗构归属；
                #   ③ E29 直核：延祐元年（1314）《元史》已书「多淤澱淺塞，源泉微細，不能通流」，
                #      乾隆己巳（1749）御制文自承「時皆湮沒不可詳」——「全国唯一存世」属最高危表述。
                # 国保对应物是**昌平龙山白浮泉遗址**（2013 第七批国保），保护对象≠所在地点。
                source_title="京密引水渠沿线古水利工程勘察报告（查无此出版物）",
                source_author="北京市水利古籍整理小组（未考得）",
                recorded_year=1983,
                dynasty="元代（至元二十九年遗构——年份本身未获遗构证据支持）",
                quote="龙背村段现存白浮堰古堤为郭守敬引水渠仅存之地面实物实体，条石固堤痕迹昭然",
                evidence_level=EvidenceLevel.L6_DISPROVEN,
                epistemic_status=EpistemicStatus.DISPROVEN,
                notes="无实物勘测档案支撑；白浮泉引水系统元代中期已衰败（E29）。"
                      "禁语：「全国唯一存世」「龙背村白浮堰遗址为国保」。"
                      "国保正确表述为「白浮泉遗址（昌平龙山）」。",
            ),
            # L2 一手官刻金石与文人亲历文集
            PlaceAttestationEntity(
                id="attest_haidian_1260",
                toponym_id="top_haidian_dian1",
                attested_name="海店",
                # 🔴 2026-10-04 订正：引文逐字无误，但**月份与参照系**原被写错。
                #   《日下旧闻考》卷37（四库本直核）：「考元王惲中堂事記載中統元年赴開平，
                #   三月五日發燕京，宿通元北郭，六日午憩海店，距京城廿里，海店即今海淀。」
                #   ——月份为**三月**（原 KB 写「八月」）；「京城」指**金中都旧城**
                #   （大都至元四年 1267 才始城，1260 年无大都城）；干支「六日丁卯」
                #   由三日句式推得，原书转引层未系干支，此处仅录四库本可核部分。
                source_title="中堂事记（日下旧闻考卷三十七转引）",
                source_author="王恽",
                recorded_year=1260,
                dynasty="元代（中统元年三月）",
                quote="六日午憩海店，距京城廿里",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="海淀区名文献最早确凿出处。「京城」= 金中都旧城（通元门为其北门），非大都城；"
                      "干支「六日丁卯」为今人推得，五日丙寅之次日，与三日行程不合，"
                      "具体年份（中统元年1260/二年1261）本库未考得定论，暂系 1260。",
            ),
            PlaceAttestationEntity(
                id="attest_gaoliangzha_1292",
                toponym_id="top_gaoliangzha",
                attested_name="高梁闸",
                # 🔴 2026-10-04 订正：原引文「又于高梁河创设水闸，节水利漕，赐名通惠河」
                # 系自撰拼句——《元史》卷164·郭守敬传「高梁」二字**零命中**；
                # 「賜名通惠河」实为三十年至元三十年「帝還自上都…大悅，名曰通惠河」句。
                # 现改挂可直核的闸名实名书证：《元史》卷64·河渠志·通惠河条。
                source_title="元史·河渠志（卷六十四）",
                source_author="宋濂等",
                recorded_year=1292,
                dynasty="元代（至元二十九年通惠河工程）",
                quote="其壩牐之名曰：廣源牐；西城牐二，上牐在和義門外西北一里，下牐在和義水門西三步",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="西城牐即高梁桥闸（E8「高粱闸又称西城闸」同源互证）；"
                      "《元史》河渠志闸名序列未把高梁闸写作「高梁闸」，"
                      "亦未见「广源闸建于1292」一句——广源闸建年取 E16 双徽口径",
            ),
            PlaceAttestationEntity(
                id="attest_guangyuanzha_stele",
                toponym_id="top_guangyuanzha",
                attested_name="广源闸",
                # 🔴 2026-10-04 订正：本条原挂「广源闸重修碑记／明万历工部／1577」，
                # 标 L2 一手官刻金石 + VERIFIED——但**检索查无此碑**。
                # 广源闸伴生碑实为明正德六年《重修龙王庙记》；1577 年长河沿岸名碑是
                # 张居正《敕建万寿寺碑文》（E15 直核）。原引文句式为现代概括体。
                # 现改挂真正可核的元代闸名实名书证：《元史》卷64·河渠志闸名序列。
                # id 保留不改（下游引用不断），但**书证实体已更换**。
                source_title="元史·河渠志（卷六十四）",
                source_author="宋濂等",
                recorded_year=1292,
                dynasty="元代（至元二十九年通惠河工程闸名序列）",
                quote="其壩牐之名曰：廣源牐",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="广源闸之名有元史实名，非后人追记（E16 直核）。"
                      "建年取 E16 双徽口径：「1289：《水部备考》转引称建」／"
                      "「1292：《元史》通惠河工程开工，广源闸列入其闸系」——"
                      "《元史》无「广源闸建于1292」一句，禁单年定论、禁「700 多年历史」。"
                      "原「广源闸重修碑记」已判死，原文见 haidian_kg/QUARANTINE.md。",
            ),
            # ✅ 觉生寺赐名/选址的真实一手书证（补入，替代 R11-1 的伪引文）
            #    逐字引文取自 calibration/dazhongsi.py 碑文分条（tf_beiwen_ciming 等，
            #    按碑石原字核对），非自撰。
            PlaceAttestationEntity(
                id="attest_jueshengsi_beiwen",
                toponym_id="top_jueshengsi",
                attested_name="覺生寺",
                source_author="清世宗雍正帝",
                source_title="敕建觉生寺碑文",
                recorded_year=1734,
                dynasty="清代（雍正十二年）",
                quote="爰賜名覺生寺",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="雍正御制碑（一手石刻），引文按碑石原字核对。勒碑纪年雍正十二年(1734)，"
                      "与 calibration/dazhongsi.py「雍正十一年(1733)正月开工、十二年冬告成」"
                      "相合（开工/告成/勒碑三事分年，勿混）。E8 纪律：碑铭为「铭铸」非「刻」。",
            ),
            # 【R11-1 回灌 2026-10-04】拟托书证：原挂《大清实录·世宗实录》「乃于都城西
            # 直门外高梁河北建寺，赐名觉生，设坛祈雨」——库内觉生寺权威一手源是
            # **《敕建觉生寺碑》（雍正御制碑，calibration/dazhongsi.py:68,85,130）**，
            # calibration 全层无「世宗实录」书证，该引文查无出处 → 判 DISPROVEN，
            # 保留原文供审计。赐名史实改由上方 attest_jueshengsi_beiwen（碑文）承载。
            PlaceAttestationEntity(
                id="attest_dazhongsi_bell_stele",
                toponym_id="top_jueshengsi",
                attested_name="御制觉生寺碑文",
                source_author="清世宗雍正帝",
                source_title="大清实录·世宗实录",
                recorded_year=1733,
                dynasty="清代（雍正十一年）",
                quote="乃于都城西直门外高梁河北建寺，赐名觉生，设坛祈雨",
                evidence_level=EvidenceLevel.L6_DISPROVEN,
                epistemic_status=EpistemicStatus.DISPROVEN,
                notes="【R11-1 拟托书证】原标 L2 VERIFIED，判为伪：库内一手书证是"
                      "《敕建觉生寺碑》（calibration/dazhongsi.py 碑文分条 tf_beiwen_ciming"
                      "「爰賜名覺生寺」/ tf_beiwen_xuankuang「高朗乾爽，林木佳茂」），"
                      "calibration 全层零「世宗实录」书证。保留原文供审计，不作采信。",
            ),
            # 【R11-2 回灌 2026-10-04】拟托书证：原挂《御制诗三集》联句
            # 「水木依稀姑苏肆，市廛宛转入楼台」——E12 冻结书证是昭梿《啸亭杂录》卷十
            # （「乾隆辛巳…於萬壽寺旁造屋，仿江南式樣。市廛坊巷，無不畢具，長至數里」，
            # 维基文库原文已核）＋卷77 御制诗自注干支自证链（辛未1751六旬→辛巳1761七旬），
            # **无此联句** → 判 DISPROVEN。建成年份 1761 本身仍成立，由下方卷十条承载。
            PlaceAttestationEntity(
                id="attest_suzhoujie_qianlong_poem",
                toponym_id="top_suzhoujie",
                attested_name="万寿山买卖街",
                source_author="清高宗乾隆帝",
                source_title="御制诗三集",
                recorded_year=1761,
                dynasty="清代（乾隆二十六年）",
                quote="水木依稀姑苏肆，市廛宛转入楼台",
                evidence_level=EvidenceLevel.L6_DISPROVEN,
                epistemic_status=EpistemicStatus.DISPROVEN,
                notes="【R11-2 拟托书证】原标 L2 VERIFIED，判为伪：E12 research.md §2 冻结"
                      "书证为昭梿《啸亭杂录》卷十「苏州街」条（维基文库原文已核）＋卷77 "
                      "御制诗自注（干支自证辛巳=1761七旬大庆），《御制诗三集》无此联句。"
                      "事件（1761 仿苏州山塘街造买卖街）另由 attest_suzhoujie_xiaoting 承载。",
            ),
            # ✅ E12 冻结的真实书证（补入，替代上面的伪联句）
            PlaceAttestationEntity(
                id="attest_suzhoujie_xiaoting",
                toponym_id="top_suzhoujie",
                attested_name="万寿寺旁苏州街",
                source_author="昭梿",
                source_title="啸亭杂录卷十·苏州街",
                recorded_year=1761,
                dynasty="清代（乾隆辛巳二十六年）",
                quote="乾隆辛巳，孝聖憲皇后七旬誕辰，純皇以後素喜江南風景，"
                      "以年邁不宜遠行，因於萬壽寺旁造屋，仿江南式樣。市廛坊巷，無不畢具，"
                      "長至數里，以奉鑾輿往來遊行，俗名曰蘇州街云",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="E12 research.md §2 冻结书证（维基文库原文已核）。干支自证链："
                      "卷77 御制诗自注「辛未年辛未为圣母六旬大庆」(1751) → 《清史稿》"
                      "「十六年六十寿、二十六年七十寿」→ 辛巳=1761 七旬。⚠️ 干支凡涉及必回原文自证。",
            ),
            # 【R11-3 回灌 2026-10-04】拟托书证：原挂「安和桥额石题字」1781「取安和景泰
            # 之义」标 L2 VERIFIED——E2 research.md §1.5 冻结：**石额「安和桥」确有旧料，
            # 但转换时间与机制待考**；「安澜平和」只是 L3 地方文史释义；桥史本身有两套
            # 记载（系统A 乾隆年间改建石桥 L3/L4 vs 系统B 康熙五十九年1720重建 L1转引），
            # KB 此前已拍死「1781＋御题＋释义」三者捆绑。现仅保留「石额旧料」这层事实，
            # 1781/御题/释义全部撤下 → 判 DISPROVEN，原文留档。
            PlaceAttestationEntity(
                id="attest_anheqiao_stone_tablet",
                toponym_id="top_anheqiao_peace",
                attested_name="安和桥",
                source_author="清高宗乾隆帝",
                source_title="安和桥额石题字",
                recorded_year=1781,
                dynasty="清代（乾隆四十六年）",
                quote="桥成，改木为石，额曰‘安和桥’，取安和景泰之义",
                evidence_level=EvidenceLevel.L6_DISPROVEN,
                epistemic_status=EpistemicStatus.DISPROVEN,
                notes="【R11-3 拟托书证】E2 research.md §1 冻结：①石额『安和桥』确有旧料，"
                      "但**近现代通行写『安河桥』，转换时间与机制待考**；②『安澜平和』之意"
                      "仅 L3 地方文史说法，非档案；③改建石桥有两套记载（系统A 乾隆年间 L3/L4 "
                      "vs 系统B 康熙五十九年1720 L1转引），**保留冲突不制造确定性**。"
                      "原「1781＋乾隆御题＋取…之义」三者已拍死。保留原文供审计。",
            ),
            # 【R6 回灌 2026-10-04】E4 冻结：官书原句是**卷100**「达官村西南里许为大有庄，
            # 庄前为御道，道北有观音庵、关帝庙」，原引**卷九十九卷次错误**；且原引文中
            # 「赐名」情节属 L3 地方文史「据载」，无诏书/御制诗/宫档出处，不得挂官书。
            # 拆成两条：卷100 官书原句 + 赐名故事（传说层）。
            # ⚠️ 等级保持 L3（正史方志纪实），不升 L2：E19 已定此纪律——本 schema 的
            # L2 定义域是「一手官刻金石」，官修方志书不属此域，升 L2 会让层级语义失真。
            PlaceAttestationEntity(
                id="attest_rixia_dayouzhuang",
                toponym_id="top_dayouzhuang",
                attested_name="大有庄",
                source_title="日下旧闻考卷一百",
                source_author="于敏中等",
                recorded_year=1774,
                dynasty="清代（乾隆三十九年）",
                quote="达官村西南里许为大有庄，庄前为御道，道北有观音庵、关帝庙",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="【R6】E4 research.md §1-1 冻结的官书原句，**卷100**（原 KB 误标"
                      "卷九十九，E4 已直核为卷100）。证明乾隆朝官书已用『大有庄』之名；"
                      "御道条为全片最硬证据之一。E4 内部层级记 L1（清代官书），"
                      "映射到本 schema 取 L3（正史方志纪实）。",
            ),
            PlaceAttestationEntity(
                id="attest_dayouzhuang_imperial_naming_lore",
                toponym_id="top_dayouzhuang",
                attested_name="穷八家→大有庄赐名说",
                source_title="地方文史『据载』（无诏书/御制诗/宫档出处）",
                source_author=None,
                recorded_year=None,
                dynasty="清代（乾隆年间流传）",
                quote="乾隆观《西郊胜景图》嫌『穷八家』不雅，赐名『大有庄』",
                evidence_level=EvidenceLevel.L5_FOLK_LEGEND,
                epistemic_status=EpistemicStatus.FOLK_LEGEND,
                notes="【R6】L3 地方文史『据载』层，**不是已确证事实**。❌ KB 原红线："
                      "禁写『乾隆把穷八家改名为大有庄』作事实陈述。竞争解释：人大清史所"
                      "『村落因圆明园/清漪园/护军营渐富裕，遂更名为大有庄』（L3，无赐名情节）。"
                      "「大有卦丰饶」之义属释义联想[L3]，非命名档案。**不锁 1750 年。**",
            ),
            PlaceAttestationEntity(
                id="attest_rixia_shucun",
                toponym_id="top_shucun",
                attested_name="树村",
                source_title="日下旧闻考卷九十九",
                source_author="于敏中等",
                recorded_year=1774,
                dynasty="清代（乾隆三十九年）",
                quote="树村在圆明园后，镶黄旗护军营驻其西，正白旗护军营驻其东",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_rixia_landianchang",
                toponym_id="top_landianchang_dye",
                attested_name="蓝靛厂",
                source_title="日下旧闻考卷九十八",
                source_author="于敏中等",
                recorded_year=1774,
                dynasty="清代（乾隆三十九年）",
                quote="蓝靛厂在西顶庙旁，居民借植蓼蓝造青靛为业，因名。乾隆三十五年徙外火器营于此",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_shuntian_xisanqi",
                toponym_id="top_xisanqi",
                attested_name="西三旗",
                source_title="光绪顺天府志·地理志",
                source_author="缪荃孙等",
                recorded_year=1885,
                dynasty="清代（光绪十一年）",
                quote="宛平北乡有西三旗、西二旗，相传明代卫所小旗分屯之地",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_wanping_niulanzhuang",
                toponym_id="top_niulanzhuang",
                attested_name="牛栏庄",
                # 【R11-5 回灌 2026-10-04】**书名与人名错配 + 引文伪造**：
                # ①沈榜著《宛署杂记》（万历二十一年1593刊），**不叫《宛平县志》**——
                #   《宛平县志》另有其书（康熙间官修），两者不可混挂；
                # ②原引文「宛平县城外西乡牛栏庄，地滨泉源，居民引水种稻」**书中无此句**——
                #   卷五《德字·街道》只有西出西直门的里程村落并列，无「地滨泉源/引水种稻」
                #   之描写（后半句是后人据地理想补的解说）。
                # 改挂真实书证：卷五街道条里程并列句（已对党宝海《魏公村考》转录与
                # 维基文库/人大 iqh 全文交叉核过）。仅证明「万历间牛栏庄已是北海店旁
                # 村落之一」，**不**证明「引水种稻」或任何经济形态。
                # 更早书证见 E18：《明太宗实录》卷58 永乐四年(1406)——不由本条承担。
                source_title="宛署杂记卷五·德字·街道",
                source_author="沈榜",
                recorded_year=1593,
                dynasty="明代（万历二十一年刊）",
                quote="縣之西北，出西直門一里曰高良橋，又五里曰籬笆房，曰葦孤村，"
                      "又二十里曰韃子營。又十里曰北海店，其旁曰小南莊、曰八里溝、曰牛欄莊",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="【R11-5】原挂《宛平县志·舆地志》系**书名人名错配**，原引文后半"
                      "「地滨泉源，居民引水种稻」**书中无此句**，已撤。现挂沈榜《宛署杂记》"
                      "卷五街道条里程并列原句。⚠️ 本条只证明『万历二十一年牛栏庄为北海店"
                      "（海淀）旁村落之一』；不得据此推出种稻/水利形态。",
            ),
            PlaceAttestationEntity(
                id="attest_weiwucun_yuanshi",
                toponym_id="top_weiwucun",
                attested_name="畏吾村",
                # 🔴 2026-10-04 判死（Q-001，理由见 haidian_kg/QUARANTINE.md）。
                # 《元史》卷126·廉希宪传全文直核：「畏吾」「畏兀」「宛平」「高梁」**零命中**。
                # 原引文与 corpus 版（"葬大都宛平之西高梁河畔，子孙家焉，号畏吾村"）
                # 是同一伪句的两个「版本」，互相还不一致——皆系自撰转写冒充古籍。
                # 处置：按 E21 定案链换书证（葬地=神道碑转引 L3，守冢廉姓=查礼 L3），
                # 原伪引文保留在本行注释中供审计，不作逐字引文。
                source_title="元史·卷一百二十六·廉希宪传（伪引文已判死）",
                source_author="宋濂等",
                recorded_year=1370,
                dynasty="元代（廉希宪至元十七年 1280 卒，大德八年 1304 追封恒阳王）",
                quote="追封魏國公，諡文正。加贈推忠佐理翊運功臣、太師、開府儀同三司、上柱國、恒陽王，諡如故。",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.CONTESTED,
                notes="卷126 可核者仅「卒年五十」「追封魏国公、谥文正、加赠恒阳王」三项（逐字直核）。"
                      "「号畏吾村」无一手书证，标 UNSUBSTANTIATED，禁作 VERIFIED（见 prop_yuanshi_burial_quote=DISPROVEN）。"
                      "葬地真书证：元明善《廉希宪神道碑》「葬于宛平之西原」（党宝海文转引，L3）"
                      "＋查礼《畏吾村考》守冢廉姓（L3）；族源锚《元史》卷125「布魯海牙畏吾人也」/「子孫皆姓廉氏」。"
                      "音转链 canon（E21）：畏吾村→苇孤村/畏兀村→魏吴村/卫伍→1915《实测京师四郊图》魏公村；"
                      "「魏家村」「廉家村」书证待核，禁入指称层。",
            ),
            PlaceAttestationEntity(
                id="attest_jingxi_map_1913",
                toponym_id="top_zhongguancun_modern",
                attested_name="中关",
                # 【R7 回灌 2026-10-04】三重失实修正：
                # ①**两种图捏成一张**：E13 冻结论据是 **1913 年《京西图》（二万五千分之一）**
                #   「中关」；五万分之一《实测京师四郊图》是 **1915**（E21/guajiatun.py:117、
                #   bibliography.py:725「实测京师四郊图（1915）」）。年份/比例尺/书名三者
                #   原 KB 全部混挂。
                # ②**图面内容夸大**：E13 冻结口径是「『中关』**零星出现**」，**不是**
                #   「白纸黑字明确标绘『中关村』」；且 1950 年代初官方档案与当地习惯
                #   写法仍是「中官村／中官邨」——**不得写「取代」**。
                # ③「魏公村 1913」同错，E21＝**1915** 图定名。
                source_title="京西图（二万五千分之一）",
                source_author="民国北洋陆军测地局",
                recorded_year=1913,
                dynasty="民国二年",
                quote="清末民初测绘图上零星出现雅化名『中关』",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="【R7】E13 research.md §1-2 冻结论据。**只证『图上已见雅化名』这一层**；"
                      "改名是『清末民初地图雅化 ＋ 1950年代机构定名』两步走，"
                      "不得据本条宣称 1913 已『取代』中官村。证伪『陈垣1930年代独创提议』"
                      "单一学说的依据是「雅化早于 1930 年代」，不是「1913 已定名」。"
                      "⚠️ 与 1915 五万分之一《实测京师四郊图》（魏公村定名）是两张图，不得互证。",
            ),
            # L4 近现代学界考据
            PlaceAttestationEntity(
                id="attest_hourenzhi_haidian",
                toponym_id="top_haidian",
                attested_name="海淀湿地水文考",
                source_title="北京历史地理与城市水系研究",
                source_author="侯仁之",
                recorded_year=1980,
                dynasty="现代",
                quote="海淀一带在地质历史上为万泉河水系冲积形成的潜水浅洼，故名‘淀’，王恽所见之‘海店’正乃水泊边缘之驿站",
                evidence_level=EvidenceLevel.L4_MODERN_SCHOLARSHIP,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_taizhouwu_dock_study",
                toponym_id="top_taizhouwu",
                attested_name="太舟坞地名源流考",
                source_title="北京水利史志研究",
                source_author="北京市水利学会",
                recorded_year=1995,
                dynasty="现代",
                quote="太舟坞紧邻元代白浮瓮山河引水线，‘坞’字自古专指船坞水港，太舟坞实为元代运石泊舟之官坞",
                evidence_level=EvidenceLevel.L4_MODERN_SCHOLARSHIP,
                epistemic_status=EpistemicStatus.CONTESTED,
            ),
            # L5 民间传说与附会
            PlaceAttestationEntity(
                id="attest_liulang_legend",
                toponym_id="top_liulangzhuang_general",
                attested_name="六郎庄杨家将驻军传说",
                source_title="海淀区民间故事集成",
                source_author="海淀区文化馆",
                recorded_year=1988,
                dynasty="现代采录民间传说",
                quote="相传宋辽对峙时，杨六郎在此屯兵抵御辽军，放马饮泉，故村名六郎庄",
                evidence_level=EvidenceLevel.L5_FOLK_LEGEND,
                epistemic_status=EpistemicStatus.FOLK_LEGEND,
                notes="纯民间传说，历史地理学已考实六郎庄系牛栏庄-柳浪庄音转附会而来",
            ),
            # 补充各核心地名的文献书证 (L2/L3/L4/L5)
            PlaceAttestationEntity(
                id="attest_qinglongqiao_rixia",
                toponym_id="top_qinglongqiao",
                attested_name="青龙桥",
                # 【R11-6 回灌 2026-10-04】两处错：
                # ①**卷次错**：E3 research.md §文献表冻结的官书是《钦定日下旧闻考》**卷100**，
                #   原引卷九十九有误；
                # ②**水文方向错**：「石闸**下注通惠河**」把青龙桥闸并入通惠河水系。
                #   E3 冻结：青龙桥闸是**昆明湖溢洪尾闾**，汛期**北泄清河**（北长河—清河
                #   体系），与通惠河（城内南向水系）**不是一条河**。E3 §7：水流方向两段式
                #   ——元代白浮堰向南给瓮山泊供水 → 明清以后残存故道转为向北入清河。
                #   原引文既无卷次支撑又含解说性水文断语，判 DISPROVEN，原文留档；
                #   真实书证由下方 attest_qinglongqiao_rixia100 承载。
                source_title="日下旧闻考卷九十九",
                source_author="于敏中等",
                recorded_year=1774,
                dynasty="清代（乾隆三十九年）",
                quote="青龙桥在玉泉山之阴，跨长河水，石闸下注通惠河，水陆要冲，商旅云集",
                evidence_level=EvidenceLevel.L6_DISPROVEN,
                epistemic_status=EpistemicStatus.DISPROVEN,
                notes="【R11-6 拟托书证】两处错：①E3 冻结官书卷次为**卷100**，原引卷九十九"
                      "无据；②「下注通惠河」**水文方向错误**——青龙桥闸是昆明湖溢洪枢纽"
                      "（弘历称『昆明湖之尾闾』），汛期**北泄清河**，与通惠河不同系。"
                      "保留原文供审计，不作采信。",
            ),
            # ✅ E3 冻结的真实官书书证（补入，替代上面的伪引文）
            PlaceAttestationEntity(
                id="attest_qinglongqiao_rixia100",
                toponym_id="top_qinglongqiao",
                attested_name="青龙桥",
                source_title="日下旧闻考卷一百",
                source_author="于敏中等",
                recorded_year=1774,
                dynasty="清代（乾隆三十九年）",
                quote="七里泊、碾庄系旧地名，今土人惟通称曰青龙桥",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="【R11-6】E3 research.md §文献表冻结的**卷100**官书原句。"
                      "口播：七里泊/碾庄是旧地名，后『青龙桥』成通称；**桥名『青龙』的"
                      "由来没有定论**（❌ 禁『郭守敬以祥瑞青龙命名』『水势如青龙腾跃』）。"
                      "另据 2024 官方传统地名名录，『青龙桥』名称出现年代标为**明代**。",
            ),
            PlaceAttestationEntity(
                id="attest_xiaojiahe_daqing",
                toponym_id="top_xiaojiahe",
                attested_name="肖家河",
                source_title="大清会典事例·兵部·护军营",
                source_author="清官修",
                recorded_year=1818,
                dynasty="清嘉庆二十三年",
                quote="圆明园护军营正黄旗营房在肖家河村北，营房八百间，设翼长防守",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_shucun_shishi",
                toponym_id="top_shucun",
                attested_name="树村",
                source_title="圆明园史事编年",
                source_author="清宫档案整理组",
                recorded_year=1801,
                dynasty="清嘉庆六年",
                quote="嘉庆六年四月，圆明园副将营房移驻园北树村西，以固后防",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_wanshousi_mingshi",
                toponym_id="top_wanshousi",
                attested_name="万寿寺",
                # 🔴 2026-10-04 订正：本条原挂《明史·神宗本纪》，quote 为
                # 「万历五年三月，敕建万寿寺于都城西直门外高梁河畔，为圣母祝寿之所」标 VERIFIED。
                # 维基文库《明史》卷20（神宗本纪）直核：「萬壽」「壽寺」**零命中**，
                # 万历五年三月条只有「三月乙巳，賜沈懋學等進士及第」——伪句系现代概括语体。
                # 现改挂 E15 已直核的真书证：张居正《敕建万寿寺碑文》（原碑乾隆朝已无存，
                # 经《日下旧闻考》卷77 转引）＋《帝京景物略》＋《万历野获编》三源互证。
                # id 保留不改（下游引用不断），但**书证实体已更换**。
                source_title="敕建万寿寺碑文（张居正撰，日下旧闻考卷七十七转引）",
                source_author="张居正",
                recorded_year=1577,
                dynasty="明万历五年",
                quote="工始於萬曆五年三月，竣於明年六月，以內臣張進主寺事。賜名曰萬壽。",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
                notes="敕建者为司礼监太监冯保奉慈圣皇太后出帑卜地（野获编、张居正碑文同）；"
                      "寺在真觉寺西二里、万寿寺在广源闸之西（帝京景物略）。"
                      "原「明史·神宗本纪」引文已判死，原文见 haidian_kg/QUARANTINE.md；"
                      "严禁再以《明史》书名承载万寿寺敕建事。",
            ),
            PlaceAttestationEntity(
                id="attest_cishousi_dijing",
                toponym_id="top_cishousi",
                attested_name="慈寿寺",
                source_title="帝京景物略卷五",
                source_author="刘侗、于奕正",
                recorded_year=1635,
                dynasty="明崇祯八年",
                # E19 像素级复核(2026-10-03)：本条引文在卷五 p92/p93 影印中**不存在**。
                # 卷五实读为「慈聖皇太后為禱子…宗祈胤嗣卜地阜成門外八里建寺…
                # 有永安壽塔塔十三級」。原引文疑为后人概括回填的伪引文。
                # 塔十三级已由卷五直证，存续到 quote 里；「京师地标」是现代观感不入引文。
                quote="宗祈胤嗣卜地阜成门外八里建寺，有永安寿塔，塔十三级",
                # E19 复核(2026-10-03)：等级保持 L3，不升 L2。
                # L2 定义域是「一手官刻金石」，《帝京景物略》��明崇祯刻本诗文集，
                # 不属此域。升 L2 会让 evidence_level 语义失真且不可逆地放宽定义。
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_guajiatun_chenyuan",
                toponym_id="top_guajiatun",
                attested_name="挂甲屯",
                source_title="宸垣识略卷十三",
                source_author="吴长元",
                recorded_year=1788,
                dynasty="清乾隆五十三年",
                quote="挂甲屯在海淀西北，世传吴应熊额驸府第遗址在此，俗亦称额驸城",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            # 🔴 E27 考订降级（2026-10-04）：本条把三段强度悬殊的断言捆在一条
            # 里标 VERIFIED，实为过度断言。逐段处置见下三条。
            # ① 成村叙事：辽金说 / 明洪武屯田说 / 无定向书证 —— 三说并存，无一定案
            PlaceAttestationEntity(
                id="attest_baijiatuan_founding",
                toponym_id="top_baijiatuan",
                attested_name="白家疃",
                source_title="海淀区地名志（1992）与现代通行说法",
                source_author="（转述，非一手）",
                recorded_year=1992,
                dynasty="现代",
                quote="白家疃成村于辽金或更早；一说为明洪武屯田移民聚落（两说并存，无定向书证）",
                evidence_level=EvidenceLevel.L5_FOLK_LEGEND,
                # schema 侧 EpistemicStatus 无 UNSUBSTANTIATED；attest 层的等价值是
                # CONTESTED（诸说并存、无定案）。「无据」在 calibration 层才有
                # UNSUBSTANTIATED 专档（见 calibration/wutasi.py 的用法）。
                epistemic_status=EpistemicStatus.CONTESTED,
            ),
            # ② 怡亲王祠：残碑碑额为 L1 实证，祠名与所在可证
            PlaceAttestationEntity(
                id="attest_baijiatuan_yixianqin",
                toponym_id="top_baijiatuan",
                attested_name="白家疃",
                source_title="怡贤亲王祠残碑碑额（实物）",
                source_author="（一手金石）",
                recorded_year=1732,
                dynasty="清雍正十年",
                quote="怡贤亲王祠残碑（碑额存「怡贤亲王祠」五字，白家疃境内，海淀区文物保护单位）",
                # L1 金石实物：怡贤亲王祠残碑碑额
                evidence_level=EvidenceLevel.L1_ARCHAEOLOGICAL,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            # ③ 曹雪芹居留：唯一书证为无原件过录本，属学术假说，禁写「定居/终老」
            PlaceAttestationEntity(
                id="attest_baijiatuan_caoxueqin",
                toponym_id="top_baijiatuan",
                attested_name="白家疃",
                source_title="白家疃怡亲王交辉园题记与曹雪芹行迹考",
                source_author="红楼梦研究所",
                recorded_year=1978,
                dynasty="现代学术专著",
                quote="曹雪芹乾隆二十三年至二十四年初曾徙居西山白家疃著书行医（居留约一年，非定居）",
                evidence_level=EvidenceLevel.L4_MODERN_SCHOLARSHIP,
                # 唯一书证为无原件过录本，属学术假说：有文献引述、无第一手档案支持
                epistemic_status=EpistemicStatus.CONTESTED,
            ),
            # 🔴 E28 证伪（2026-10-04）：本条为**伪引文**。
            # 《帝京景物略》**无**「平地温泉如沸，冬月白气滃然，辽金帝王驻跸沐浴之所」一语；
            # 「辽金帝王驻跸沐浴」之说亦无任何一手书证。
            # 温泉村可证文字史的一手起点是明初显龙山采石题记（洪武二十七年 1394 /
            # 正统十年 1445）与万历《宛署杂记》（1593，官书正名为「石窝村」）。
            # 旧实现把伪引文标为 VERIFIED，等于让伪造证据升格为一手著录。
            PlaceAttestationEntity(
                id="attest_wenquan_dijing",
                toponym_id="top_wenquan",
                attested_name="温泉",
                source_title="帝京景物略卷五",
                source_author="刘侗",
                recorded_year=1635,
                dynasty="明代",
                quote="平地温泉如沸，冬月白气滃然，辽金帝王驻跸沐浴之所",
                # 🔴 证伪条目的证据层级随之降为 L6（该「引文」并非真出该书）
                evidence_level=EvidenceLevel.L6_DISPROVEN,
                epistemic_status=EpistemicStatus.DISPROVEN,
            ),
            PlaceAttestationEntity(
                id="attest_qinghe_tianfu",
                toponym_id="top_qinghezhen",
                attested_name="清河",
                source_title="天府广记卷二十",
                source_author="孙承泽",
                recorded_year=1660,
                dynasty="清初",
                quote="清河镇去德胜门二十里，有石梁跨河，为往昌平、居庸关第一大驿",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_zhenjuesi_shilu",
                toponym_id="top_zhenjuesi",
                attested_name="真觉寺金刚宝座",
                source_title="明宪宗实录卷一百二十",
                source_author="明官修",
                recorded_year=1473,
                dynasty="明成化九年",
                quote="成化九年冬十一月，真觉寺金刚宝座塔成，赐名大觉金刚宝座",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_dajuesi_stele",
                toponym_id="top_dajuesi",
                attested_name="大觉寺",
                source_title="大觉寺宣德重修碑记",
                source_author="明宣德官刻",
                recorded_year=1428,
                dynasty="明宣德三年",
                quote="大觉禅寺，金章宗清水院故址也，重修弘开法筵",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_yimuyuan_qianlong",
                toponym_id="top_yimuyuan",
                attested_name="一亩园",
                source_title="清高宗御制文二集",
                source_author="清高宗乾隆帝",
                recorded_year=1745,
                dynasty="清乾隆十年",
                quote="圆明园前置一亩园，仿先农坛躬耕籍田之礼，以示重本抑末",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_niangniangfu_gazetteer",
                toponym_id="top_niangniangfu",
                attested_name="娘娘府",
                source_title="光绪顺天府志·古迹志",
                source_author="缪荃孙",
                recorded_year=1885,
                dynasty="清光绪十一年",
                quote="金山之麓，明代诸妃茔墓列峙，俗呼一溜边山七十二府，今娘娘府其遗地也",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_dongsimu_record",
                toponym_id="top_dongsimu",
                attested_name="董四墓",
                source_title="海淀区地名志",
                source_author="海淀区地名办公室",
                recorded_year=1992,
                dynasty="现代志书",
                quote="明代皇室墓地，后形成看坟户村落，以董姓第四代守墓人得名董四墓，曾以御桃闻名",
                evidence_level=EvidenceLevel.L4_MODERN_SCHOLARSHIP,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_chengfu_shunzhi",
                toponym_id="top_chengfu",
                attested_name="成府",
                source_title="燕都丛考卷四",
                source_author="陈宗蕃",
                recorded_year=1930,
                dynasty="民国十九年",
                quote="成府旧称陈府，相传明末崇祯田贵妃戚畹陈氏别墅所在地，村落早废而路名犹存",
                evidence_level=EvidenceLevel.L4_MODERN_SCHOLARSHIP,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_huangzhuang_hunt",
                toponym_id="top_huangzhuang",
                attested_name="黄庄",
                source_title="日下旧闻考卷一百",
                source_author="于敏中",
                recorded_year=1774,
                dynasty="清代",
                quote="海淀南二里黄庄，明时或为皇庄之讹，或以黄土高阜得名，志家存疑",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.CONTESTED,
            ),
            PlaceAttestationEntity(
                id="attest_zaojunmiao_record",
                toponym_id="top_zaojunmiao",
                attested_name="皂君庙",
                source_title="京师坊巷志稿",
                source_author="朱一新",
                recorded_year=1886,
                dynasty="清光绪十二年",
                quote="皂君庙者，实祀灶神，民间方言轻读俗转作皂，遂沿为街名",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_zgc_1953_decision",
                toponym_id="top_zhongguancun_modern",
                attested_name="中关村科学院园区",
                source_title="中国科学院院史资料汇编",
                source_author="中科院院史馆",
                recorded_year=1953,
                dynasty="现代新中国",
                quote="政务院批准文委与科学院关于选定海淀中关村为科研基地的方案，近代第一座科学城破土动工",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_zgc_1980_seed",
                toponym_id="top_zhongguancun_modern",
                attested_name="中关村第一粒种子",
                source_title="陈春先与北京硅谷破冰史",
                source_author="科学时报",
                recorded_year=1980,
                dynasty="现代改革开放",
                quote="1980年10月陈春先创办北京等离子体学会先进技术服务部，开启中关村科技街创业大幕",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_zgc_1988_zone",
                toponym_id="top_zhongguancun_modern",
                attested_name="北京市新技术产业开发试验区",
                source_title="国务院国函〔1988〕74号文",
                source_author="中华人民共和国国务院",
                recorded_year=1988,
                dynasty="现代改革开放",
                quote="同意以中关村为中心建立北京市新技术产业开发试验区，实行十八条扶持政策",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_dajuesi_liao_stele",
                toponym_id="top_dajuesi",
                attested_name="清水院契丹碑",
                source_title="大辽大安四年石碑",
                source_author="辽燕京宛平县清水院",
                recorded_year=1088,
                dynasty="辽代（大安四年）",
                quote="大辽大安四年，西山清水院重构佛殿，刻石纪事",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_daizhou_tang_record",
                toponym_id="top_daizhou_name",
                attested_name="带州",
                source_title="旧唐书·地理志二",
                source_author="刘昫等",
                recorded_year=705,
                dynasty="唐代（神龙元年）",
                quote="带州，神龙元年置，寄治昌平县清水店，领孤竹一县",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_xierqi_shuntian",
                toponym_id="top_xierqi",
                attested_name="西二旗",
                source_title="光绪顺天府志·地理志",
                source_author="缪荃孙",
                recorded_year=1885,
                dynasty="清光绪十一年",
                quote="西二旗在宛平县北，相传明代卫所小旗分屯之地，次于三旗",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_zhongguan_eunuch_stele",
                toponym_id="top_zhongguancun_eunuch",
                attested_name="中官村刚炳祠堂碑",
                source_title="北京历代太监墓石刻考",
                source_author="北京石刻博物馆",
                recorded_year=1900,
                dynasty="清末光绪二十六年",
                quote="中官村地多太监兆域，内廷诸中官合祀刚炳为神，建祠村东，置义地数百亩",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_zhongguantun_map",
                toponym_id="top_zhongguantun",
                attested_name="中官屯",
                source_title="顺天府宛平县保甲全图",
                source_author="顺天府宛平县衙",
                recorded_year=1908,
                dynasty="清光绪三十四年",
                quote="海淀镇东门外二里，标示‘中官屯’，为太监守茔户聚集之聚落",
                evidence_level=EvidenceLevel.L2_PRIMARY_DOC,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_anhe_republic_record",
                toponym_id="top_anheqiao_river",
                attested_name="安河桥",
                source_title="北平地名通志",
                source_author="北平特别市政府",
                recorded_year=1934,
                dynasty="民国二十三年",
                quote="安河桥在青龙桥东，因水流安恬、桥跨御河，俗名遂改作‘安河桥’",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_huoqiying_record",
                toponym_id="top_huoqiying",
                attested_name="外火器营",
                source_title="日下旧闻考卷九十八",
                source_author="于敏中",
                recorded_year=1774,
                dynasty="清乾隆三十九年",
                quote="乾隆三十五年改移外火器营于蓝靛厂，建满蒙八旗营房四千间，设枪炮演武场",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_linglongta_yandu",
                toponym_id="top_linglongta",
                attested_name="玲珑宝塔",
                source_title="燕都游览志卷三",
                source_author="孙国敉",
                recorded_year=1623,
                dynasty="明天启三年",
                # E19 复核(2026-10-03)：卷97 按语引《燕都游览志》只记「宝藏阁系圣母
                # 御笔题…今頺楹殘礎」，未记「雕饰玲珑秀出」。「玲珑宝塔」作为
                # 明代称呼缺乏一手支撑，VERIFIED 降为 CONTESTED。
                quote="宝藏阁系圣母御笔题…今頺楹殘礎",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.CONTESTED,
            ),
            PlaceAttestationEntity(
                id="attest_wutasi_beiping",
                toponym_id="top_wutasi",
                attested_name="五塔寺",
                source_title="北平名胜景物记",
                source_author="张爵",
                recorded_year=1935,
                dynasty="民国二十四年",
                quote="真觉寺金刚宝座有五方佛塔，世称五塔寺，西直门外名刹也",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_chengfulu_gazetteer",
                toponym_id="top_chengfulu",
                attested_name="成府路",
                source_title="北京市海淀区地名志",
                source_author="海淀区地名办",
                recorded_year=1992,
                dynasty="现代",
                quote="成府路东起五道口，西至清华大学西门南，因原成府村得名",
                evidence_level=EvidenceLevel.L4_MODERN_SCHOLARSHIP,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_gaolianghe_shuijingzhu",
                toponym_id="top_gaolianghe",
                attested_name="高梁水",
                source_title="水经注卷十三",
                source_author="郦道元",
                recorded_year=527,
                dynasty="北魏正光至孝昌年间",
                quote="高梁水出蓟县西北平地，东南流经蓟城北，水色清莹，草木丰茂",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_yuquanshan_jinshi",
                toponym_id="top_yuquanshan",
                attested_name="玉泉山芙蓉殿",
                source_title="金史·地理志",
                source_author="脱脱等",
                recorded_year=1344,
                dynasty="元代修金史",
                quote="大兴府宛平县有玉泉山，金世宗、章宗两朝建芙蓉殿及行宫于此，御泉甘冽",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_wanshoushan_rixia",
                toponym_id="top_wanshoushan",
                attested_name="瓮山",
                source_title="日下旧闻考卷八十四",
                source_author="于敏中",
                recorded_year=1774,
                dynasty="清乾隆三十九年",
                quote="万寿山旧名瓮山，其形如瓮，前抱瓮山泊，元郭守敬引白浮泉聚水于此",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            PlaceAttestationEntity(
                id="attest_xiangshan_jinshi",
                toponym_id="top_xiangshan",
                attested_name="香山大永安寺",
                source_title="金史·世宗本纪",
                source_author="脱脱",
                recorded_year=1186,
                dynasty="金大定二十六年",
                quote="大定二十六年三月，世宗幸西山，驻跸香山大永安寺，为西山名胜之冠",
                evidence_level=EvidenceLevel.L3_GAZETTEER,
                epistemic_status=EpistemicStatus.VERIFIED,
            ),
            # L6 证伪与负控制书证 (Disproven)
            PlaceAttestationEntity(
                id="attest_xisanqi_manchu_myth",
                toponym_id="top_xisanqi",
                attested_name="西三旗源自满洲八旗三旗说",
                source_title="北京地名通俗民间讲义（错误说）",
                source_author="民间地名作者",
                recorded_year=1980,
                dynasty="现代通俗读物",
                quote="俗传西三旗为清代正黄、正白、正蓝上三旗驻军之地",
                evidence_level=EvidenceLevel.L6_DISPROVEN,
                epistemic_status=EpistemicStatus.DISPROVEN,
                notes="严重史实错误：清代八旗驻防体系中绝无‘西三旗’之军制建置，一手顺天府志明确记载为明代卫所小旗军屯",
            ),
            PlaceAttestationEntity(
                id="attest_gaoliangqiao_979_myth",
                toponym_id="top_gaoliangqiao",
                attested_name="宋太宗中箭之高梁桥说",
                source_title="通俗演义小说附会",
                source_author="通俗历史评书",
                recorded_year=1950,
                dynasty="现代通俗评书",
                quote="讲宋太宗赵光义高梁河惨败，于高梁桥下乘驴车仓皇南逃",
                evidence_level=EvidenceLevel.L6_DISPROVEN,
                epistemic_status=EpistemicStatus.DISPROVEN,
                notes="时空错乱：979年高梁河之战时该处仅有古河道与野渡，高梁桥系元至元二十九年（1292）郭守敬所建，晚了313年",
            ),
        ]

        # =====================================================================
        # 5. 地名演变事件 (Toponym Evolution Events)
        # =====================================================================
        events = [
            # 海淀演变
            ToponymEventEntity(
                id="evt_haidian_creation",
                event_type="CreationEvent",
                source_toponym_id=None,
                target_toponym_id="top_haidian_dian1",
                dynasty="金末元初",
                occurred_year=1260,
                description="元初通往塞北古道边浅水湖泊聚落形成，称‘海店’",
            ),
            ToponymEventEntity(
                id="evt_haidian_dian2",
                event_type="EuphemisticRenamingEvent",
                source_toponym_id="top_haidian_dian1",
                target_toponym_id="top_haidian_dian2",
                dynasty="明代中叶",
                description="明代文人雅化为海甸，借用‘甸’字郊野王畿之义",
            ),
            ToponymEventEntity(
                id="evt_haidian_final",
                event_type="EuphemisticRenamingEvent",
                source_toponym_id="top_haidian_dian2",
                target_toponym_id="top_haidian",
                dynasty="明万历至清初",
                description="文人因其万泉汇聚、水草丰茂，正式改从水旁作‘海淀’",
            ),
            # 六郎庄演变
            ToponymEventEntity(
                id="evt_niulan_to_liulang_willow",
                event_type="EuphemisticRenamingEvent",
                source_toponym_id="top_niulanzhuang",
                target_toponym_id="top_liulangzhuang_willow",
                dynasty="清康熙年间",
                description="牛栏庄因地处万泉河下流，柳荫蔽日、垂柳成浪，雅化改称柳浪庄",
            ),
            ToponymEventEntity(
                id="evt_liulang_to_general",
                event_type="FolkAppropriationEvent",
                source_toponym_id="top_liulangzhuang_willow",
                target_toponym_id="top_liulangzhuang_general",
                dynasty="清中晚期",
                description="民间借谐音附会宋将杨六郎抗辽驻兵之英雄传说，遂讹写作六郎庄",
            ),
            # 大有庄演变
            ToponymEventEntity(
                id="evt_qiongbajia_to_dayouzhuang",
                event_type="ImperialNamingEvent",
                source_toponym_id="top_qiongbajia",
                target_toponym_id="top_dayouzhuang",
                dynasty="清乾隆年间",
                occurred_year=1750,
                description="乾隆帝巡幸见‘穷八家’村名不吉，取《周易》大有卦‘丰盛富庶’之义御赐改名大有庄",
                triggering_person="清高宗乾隆帝",
            ),
            # 魏公村演变
            ToponymEventEntity(
                id="evt_weiwu_to_weigong",
                event_type="PhoneticShiftEvent",
                source_toponym_id="top_weiwucun",
                target_toponym_id="top_weigongcun",
                dynasty="民国初年",
                occurred_year=1915,
                description="‘畏吾村’经数百年方言口传音转为‘畏兀村’、‘魏家村’，民国四年《实测四郊图》谐音定名‘魏公村’",
            ),
            # 中关村演变
            ToponymEventEntity(
                id="evt_zhongguan_euphemism",
                event_type="EuphemisticRenamingEvent",
                source_toponym_id="top_zhongguancun_eunuch",
                target_toponym_id="top_zhongguancun_modern",
                dynasty="清末民初",
                occurred_year=1913,
                description="中官村太监义地因新式学堂进驻，文人与测地局避忌‘中官（宦官）’嫌称，雅化为‘中关村’",
            ),
            # 安河桥演变
            ToponymEventEntity(
                id="evt_anhe_imperial",
                event_type="ImperialNamingEvent",
                source_toponym_id="top_anheqiao_wood",
                target_toponym_id="top_anheqiao_peace",
                dynasty="清乾隆四十六年",
                occurred_year=1781,
                description="乾隆帝改修石拱桥，御题‘安和桥’石额",
                triggering_person="清高宗乾隆帝",
            ),
            ToponymEventEntity(
                id="evt_anhe_river_drift",
                event_type="PhoneticShiftEvent",
                source_toponym_id="top_anheqiao_peace",
                target_toponym_id="top_anheqiao_river",
                dynasty="清末民初",
                description="民间望文生义，因桥跨清河而俗写同音为‘安河桥’",
            ),
            # 成府演变
            ToponymEventEntity(
                id="evt_chengfu_extinction",
                event_type="SpatialExtinctionEvent",
                source_toponym_id="top_chengfu",
                target_toponym_id="top_chengfulu",
                dynasty="当代",
                occurred_year=1990,
                description="原成府村落随高校园区扩建全部拆迁，地名作为‘成府路’道路专名永久存续",
            ),
            # 更多演变事件
            ToponymEventEntity(
                id="evt_gaoliang_gate_to_bridge",
                event_type="PhoneticShiftEvent",
                source_toponym_id="top_gaoliangzha",
                target_toponym_id="top_gaoliangqiao",
                dynasty="明代",
                description="元代高梁闸桥闸合一，明代漕运衰退后民众逐渐以桥名统称，演化为高梁桥",
            ),
            ToponymEventEntity(
                id="evt_dazhongsi_relocate_bell",
                event_type="ImperialNamingEvent",
                source_toponym_id="top_jueshengsi",
                target_toponym_id="top_dazhongsi",
                dynasty="清乾隆十六年",
                occurred_year=1751,
                description="乾隆帝将万寿寺永乐大钟移悬觉生寺，民间遂以大钟代称寺名，俗称大钟寺并演变为现代地铁站地名",
                triggering_person="清高宗乾隆帝",
            ),
            ToponymEventEntity(
                id="evt_suzhoujie_imperial_build",
                event_type="ImperialNamingEvent",
                source_toponym_id="top_maimaijie",
                target_toponym_id="top_suzhoujie",
                dynasty="清乾隆二十六年",
                occurred_year=1761,
                description="乾隆帝为母后祝寿仿苏州水肆建买卖街，民间与后世统称为苏州街",
                triggering_person="清高宗乾隆帝",
            ),
            ToponymEventEntity(
                id="evt_cishou_linglong_drift",
                event_type="PhoneticShiftEvent",
                source_toponym_id="top_cishousi",
                target_toponym_id="top_linglongta",
                dynasty="清代中后期",
                # E19 复核(2026-10-03)：「毁于清末大火」无任何一手记载——《宸垣识略》
                # 与《光绪顺天府志》只记寺毁而未记火；火灾细节本集负控制明禁。
                # 「惟浮图及碑存」是《光绪顺天府志》原话，据此改写。
                description="光绪间寺毁，惟浮图及碑存（《光绪顺天府志》）；民间称玲珑宝塔，但明代即有此称尚缺一手佐证",
            ),
            ToponymEventEntity(
                id="evt_zhenjue_wuta_drift",
                event_type="PhoneticShiftEvent",
                source_toponym_id="top_zhenjuesi",
                target_toponym_id="top_wutasi",
                dynasty="清代",
                description="真觉寺因金刚宝座上有五座密檐小塔，民间俗称五塔寺，后寺废名存沿为村名与地标",
            ),
            ToponymEventEntity(
                id="evt_dajuesi_rename",
                event_type="ImperialNamingEvent",
                source_toponym_id=None,
                target_toponym_id="top_dajuesi",
                dynasty="明宣德三年",
                occurred_year=1428,
                description="明宣宗宣德皇帝重修金代清水院行宫禅刹，赐额大觉寺",
                triggering_person="明宣宗朱瞻基",
            ),
            ToponymEventEntity(
                id="evt_landian_huoqi_shift",
                event_type="AdministrativeShiftEvent",
                source_toponym_id="top_landianchang_dye",
                target_toponym_id="top_huoqiying",
                dynasty="清乾隆三十五年",
                occurred_year=1770,
                description="乾隆三十五年外火器营四千间兵营自城内迁驻蓝靛厂，市镇与兵营空间复合",
                triggering_person="清高宗乾隆帝",
            ),
            ToponymEventEntity(
                id="evt_shucun_garrison_shift",
                event_type="AdministrativeShiftEvent",
                source_toponym_id=None,
                target_toponym_id="top_shucun",
                dynasty="清雍正二年",
                occurred_year=1724,
                description="清世宗置圆明园八旗护军营，镶黄旗驻树村西，正白旗驻树村东，树村演化为八旗兵民共生村",
            ),
            ToponymEventEntity(
                id="evt_xiaojiahe_garrison_shift",
                event_type="AdministrativeShiftEvent",
                source_toponym_id=None,
                target_toponym_id="top_xiaojiahe",
                dynasty="清雍正二年",
                occurred_year=1724,
                description="圆明园护军营正黄旗营房设于肖家河村北，形成军政护卫要冲",
            ),
            ToponymEventEntity(
                id="evt_zaojunmiao_drift",
                event_type="PhoneticShiftEvent",
                source_toponym_id=None,
                target_toponym_id="top_zaojunmiao",
                dynasty="清代中叶",
                description="灶君庙因北京方言灶、皂同音混用，官牌与地名志遂写作皂君庙",
            ),
        ]

        # =====================================================================
        # 6. 竞争与争议假说 (Competing Hypotheses)
        # =====================================================================
        hypotheses = [
            CompetingHypothesisEntity(
                id="hypo_banquan_yellow_emperor",
                toponym_id="top_banquan",
                hypothesis_title="黄帝炎帝阪泉之战传说（神话传说）",
                claim_summary="《史记》所载黄帝与炎帝阪泉之战，民间附会于北京延庆或涿鹿，属于部落联盟神话传说而非确证信史",
                supported_by_attestation_ids=["attest_banquan_myth"],
                disproven_by_attestation_ids=[],
                confidence_status=EpistemicStatus.FOLK_LEGEND,
            ),
            CompetingHypothesisEntity(
                id="hypo_taizhouwu_tang",
                toponym_id="top_taizhouwu",
                hypothesis_title="太舟坞源于唐代羁縻带州音转说",
                claim_summary="唐神龙元年置羁縻带州，天宝间寄治昌平县清水店，太舟坞即带州之长久音转",
                supported_by_attestation_ids=[],
                disproven_by_attestation_ids=["attest_taizhouwu_dock_study"],
                confidence_status=EpistemicStatus.CONTESTED,
            ),
            CompetingHypothesisEntity(
                id="hypo_taizhouwu_dock",
                toponym_id="top_taizhouwu",
                hypothesis_title="太舟坞源于元代白浮引水河道船坞说",
                claim_summary="太舟坞地处元代白浮瓮山河漕运停泊带，‘太舟坞’实为大船泊坞之地形实录",
                supported_by_attestation_ids=["attest_taizhouwu_dock_study"],
                disproven_by_attestation_ids=[],
                confidence_status=EpistemicStatus.VERIFIED,
            ),
            CompetingHypothesisEntity(
                id="hypo_xisanqi_manchu",
                toponym_id="top_xisanqi",
                hypothesis_title="西三旗源自清代满洲八旗驻防说（伪说）",
                claim_summary="坊间传闻西三旗为满洲上三旗驻军兵营",
                supported_by_attestation_ids=["attest_xisanqi_manchu_myth"],
                disproven_by_attestation_ids=["attest_shuntian_xisanqi"],
                confidence_status=EpistemicStatus.DISPROVEN,
            ),
            CompetingHypothesisEntity(
                id="hypo_gaoliangqiao_979",
                toponym_id="top_gaoliangqiao",
                hypothesis_title="高梁桥宋辽高梁河之战战场桥说（伪说）",
                claim_summary="民间小说演义赵光义于高梁桥下乘驴车败逃",
                supported_by_attestation_ids=["attest_gaoliangqiao_979_myth"],
                disproven_by_attestation_ids=["attest_gaoliangzha_1292"],
                confidence_status=EpistemicStatus.DISPROVEN,
            ),
            CompetingHypothesisEntity(
                id="hypo_huangzhuang_emperor",
                toponym_id="top_huangzhuang",
                hypothesis_title="黄庄源于明代皇庄讹变说",
                claim_summary="坊间与部分方志推论黄庄为明代皇家庄田‘皇庄’谐音字样演化",
                supported_by_attestation_ids=["attest_huangzhuang_hunt"],
                disproven_by_attestation_ids=[],
                confidence_status=EpistemicStatus.CONTESTED,
            ),
            CompetingHypothesisEntity(
                id="hypo_zgc_chenyuan_alone",
                toponym_id="top_zhongguancun_modern",
                hypothesis_title="中关村定名陈垣独创提议说",
                claim_summary="相传1930年代辅仁大学校长陈垣首次提议将中官村改写为中关村",
                supported_by_attestation_ids=[],
                disproven_by_attestation_ids=["attest_jingxi_map_1913"],
                confidence_status=EpistemicStatus.CONTESTED,
            ),
        ]

        return HaidianDataset(
            physical_features=features,
            administrative_units=units,
            toponyms=toponyms,
            place_attestations=attestations,
            evolution_events=events,
            competing_hypotheses=hypotheses,
        )

    @classmethod
    def load_or_extract(cls) -> HaidianDataset:
        """读缓存 entities.json；**过期则自动重算**。

        🔴 G7（E26/E27 横切审计发现，2026-10-04）：原实现只要文件存在就直接读，
        永不比对新鲜度。结果 extractor.py 里所有修正（伪引文 DISPROVEN、
        E26 七名号节点、E27 三条拆分的 attest）**在运行时全部无效** ——
        源里是 DISPROVEN，导出的 entities.json 里仍是 VERIFIED。
        典型症状：改完代码、跑测试全绿，但知识图谱/查询仍给出旧答案。

        处置：比对 entities.json 与 extractor.py 的 mtime，源更新即重算并回写。
        """
        data_file = pathlib.Path("haidian_kg/data/entities.json")
        src_file = pathlib.Path(__file__)
        if data_file.exists() and data_file.stat().st_mtime >= src_file.stat().st_mtime:
            with open(data_file, "r", encoding="utf-8") as f:
                d = json.load(f)
            return HaidianDataset(**d)
        dataset = cls.extract_all()
        cls.save_dataset(dataset)
        return dataset

    @classmethod
    def force_refresh(cls) -> HaidianDataset:
        """强制重算并回写 entities.json（改完 extractor.py 后应显式调用）。"""
        dataset = cls.extract_all()
        cls.save_dataset(dataset)
        return dataset

    @classmethod
    def save_dataset(cls, dataset: HaidianDataset):
        data_file = pathlib.Path("haidian_kg/data/entities.json")
        data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(data_file, "w", encoding="utf-8") as f:
            f.write(dataset.model_dump_json(indent=2))


if __name__ == "__main__":
    # 🔴 改完 extractor.py 后跑 `python3 -m haidian_kg.extractor` 强制回写导出，
    #    否则下游（builder/visualizer/查询）读到的仍是旧快照。
    ds = HaidianCorpusExtractor.force_refresh()
    print(f"Extracted: {len(ds.physical_features)} features, {len(ds.administrative_units)} units, "
          f"{len(ds.toponyms)} toponyms, {len(ds.place_attestations)} attestations, "
          f"{len(ds.evolution_events)} events, {len(ds.competing_hypotheses)} hypotheses.")
