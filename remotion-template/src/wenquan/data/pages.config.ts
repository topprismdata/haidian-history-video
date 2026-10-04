// pages.config.ts — E28《温泉·「温泉」之前叫「石窝」》逐页槽位文案与样式.
// 唯一规格书：docs/superpowers/specs/2026-10-04-e28-wenquan-design.md（APPROVED）
// ＋ wenquan_video/research.md v1.0.
// 板型：P1–P5/P7/P8 MixedPage；P6 证伪页待补对照卡期间为 TextOnly（右槽留空）。
// 槽位几何见 slots.json（plate 全部 1920×1080 设计空间 = 画布 1:1）。
// 屏显纪年一律年号或全字形汉字；禁 U+3007 圆圈数字、禁阿拉伯公历年上屏。
// V-NC01 改名年代无书证，严禁「某年由石窝村改称温泉村」；
// V-NC02 一手起点是明初采石题记，禁提前到辽金；
// V-NC03 伪引文只以「伪引」身份上屏（灰化底＋虚线框），原文卡实底实线框；
// V-NC04 香水院断碑在妙高峰，严禁系于温泉后山；
// V-NC05 国保编号 6-886 / 6-810 / 7-1973-3-009 必须同卡附批次与公布年；
// V-NC06 泉眼现状双禁：不写仍在涌流，不写早已干涸。
const INK = "#3a3226";
// 存疑/伪引一律灰化底 rgba(213,208,198,0.94)；档案卡卡纸底 rgba(247,240,223,0.95)。
// backing 必须写字面量（qa_v2.parse_pages_config 只认 "..." 与 true，不认常量引用）。

export interface TextItem {
  slotId?: string;
  text: string;
  size?: number;
  color?: string;
  weight?: number;
  lh?: number;
  align?: "center" | "left";
  backing?: boolean | string;
  kind?: string;
  sub?: string;
  delay?: number;
  pad?: string;
  /** V-NC03：伪引卡 "dashed"，原文卡 "solid"；其余卡不设边框。 */
  borderStyle?: "dashed" | "solid";
}

export const PAGE_CONFIG: Record<number, { design: number; bounds: number[]; items: TextItem[] }> = {
  // ── p01 地图上两个字的地名 ──────────────────────────────────────
  1: {
    design: 1,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p1_title", text: "温泉 · 「温泉」之前叫「石窝」", size: 38, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p1_sub", text: "一口泉的名字 · 活了五百年", size: 24, color: INK, weight: 700, lh: 1.3, backing: true },
      { slotId: "p1_hook", text: "北京的地图上，地名多是庙、桥、营、坟。\n只有西北这一角，端端正正写着两个字：\n温泉。\n可要问一句——\n这口泉，今天还在冒热水吗？", size: 26, color: INK, weight: 800, lh: 1.45, backing: true, delay: 120 },
      { slotId: "p1_index", text: "图幅注记索引：石窝 · 白家疃 · 杨家村 · 黑龙潭 · 福山 · 昌平界\n——村名注记见于图幅西缘县界之上", size: 22, color: INK, weight: 700, lh: 1.5, backing: true, delay: 260 },
      { slotId: "p1_foot", text: "右图：民国四年《實測京師四郊地圖》切片。本幅未见可确读的「溫泉」注记，\n村名注记见于图幅西缘县界之上。图幅有非线性畸变，\n与今坐标仅作趋势比对，不作点位断言。", size: 20, color: "#5a4f3c", weight: 700, lh: 1.5, backing: true, delay: 380 },
      { slotId: "p1_tag_mec", kind: "tag", text: "一手实测档案 · 民国四年", backing: true, delay: 480 },
      { slotId: "p1_close", text: "右下：《清 佚名 三山五园图》香山北坡带切片——\n清代官绘本图的北界到碧云寺一线为止，\n温泉村在图幅之外。", size: 22, color: INK, weight: 700, lh: 1.5, backing: true, delay: 560 },
      { slotId: "p1_tag_hook", kind: "tag", text: "名字比水活得久 · 本集追问", backing: true, delay: 660 },
      { slotId: "p1_photo_1915", kind: "photo", text: "1915 实测图切片（Page01 提供 PhotoSpec）" },
      { slotId: "p1_photo_sanshan", kind: "photo", text: "三山五园图切片（Page01 提供 PhotoSpec）" },
      { slotId: "p1_cap_sanshan", text: "《清 佚名 三山五园图》香山北坡带切片（公有领域）· 温泉村在图幅之外", size: 17, color: "#5a4f3c", weight: 700, lh: 1.3, backing: true, delay: 700 },
    ],
  },
  // ── p02 明末文献里的第一眼温泉 ────────────────────────────────
  2: {
    design: 2,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p2_title", text: "明崇祯八年的第一眼", size: 38, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p2_tag_source", kind: "tag", text: "明末笔记所记 · 非原刊扫描", backing: true, delay: 100 },
      { slotId: "p2_quote1", text: "「山北十里，平疇良苗，溫泉出焉。\n泉如湯未至沸時，甃而為池，以待浴者。」", size: 26, color: INK, weight: 800, lh: 1.55, backing: true, delay: 180 },
      { slotId: "p2_quote2", text: "「資泉之民，無苦瘍躄。\n泉前數武，有碧霞殿，單楹板扉。」", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 300 },
      { slotId: "p2_geo", text: "「泉而東六十里，大湯山，又一溫泉。\n再東三里，小湯山，又一溫泉。」", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 420 },
      { slotId: "p2_verdict", text: "「泉如湯未至沸時」——水温写得很准。\n「甃而為池，以待浴者」——泉被砌成浴池，对公众开放。\n这是一口民间的汤池，不是皇家禁地。", size: 23, color: INK, weight: 800, lh: 1.55, backing: true, delay: 540 },
      { slotId: "p2_doubt1", text: "存疑 · 「山北十里」之「山」，原文未指明。通行比定于诸山，\n但与今里程不合——本片只引原文，不断言山名。", size: 21, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 660 },
      { slotId: "p2_doubt2", text: "存疑 · 碧霞殿（今无存世记录）、堂前陈天祥撰记碑（无拓本与实物），\n本片只作文献所见，不作今地实证。", size: 21, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 760 },
      { slotId: "p2_tag_zhou", kind: "tag", text: "甃池剖面 · 制作组绘制示意", backing: true, delay: 860 },
      { slotId: "p2_photo_folio", kind: "photo", text: "帝京景物略书影（Page02 提供 PhotoSpec）" },
      { slotId: "p2_photo_zhou", kind: "photo", text: "甃池剖面示意（Page02 提供 PhotoSpec）" },
    ],
  },
  // ── p03 比书更早的石头 ────────────────────────────────────────
  3: {
    design: 3,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p3_title", text: "比书更早的石头", size: 40, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p3_tag_source", kind: "tag", text: "一手实物 · 明代采石题记", backing: true, delay: 100 },
      { slotId: "p3_archive", text: "显龙山，又名堂子山：石灰岩，海拔约九十米，在温泉村南。\n石壁存明洪武二十七年（一三九四）与\n正统十年（一四四五）采石匠刻字。", size: 24, color: INK, weight: 800, lh: 1.55, backing: true, delay: 180 },
      { slotId: "p3_archive2", text: "两条纪年相隔五十一年——\n采石跨明代前中期持续进行。", size: 23, color: INK, weight: 700, lh: 1.55, backing: true, delay: 320 },
      { slotId: "p3_verdict", text: "这是温泉村一带可证历史的最早一手实物——\n比《宛署杂记》早约两百年。\n「石窝」二字，就是采石场留下的名字。", size: 24, color: INK, weight: 800, lh: 1.55, backing: true, delay: 440 },
      { slotId: "p3_doubt1", text: "存疑 · 「明代故宫石料取自此地」仅见通俗文章，无档案依据——本片不采。", size: 21, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 560 },
      { slotId: "p3_doubt2", text: "存疑 · 本片只说「京西采石场村」，不外推石料用途。", size: 21, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 660 },
      { slotId: "p3_tag_mec", kind: "tag", text: "地名置换时间轴 · 无书证段以虚线明示", backing: true, delay: 760 },
      { slotId: "p3_photo_timeline", kind: "photo", text: "地名置换时间轴（Page03 提供 PhotoSpec）" },
      { slotId: "p3_photo_caishi", kind: "photo", text: "采石题记摩崖示意（Page03 提供 PhotoSpec）" },
    ],
  },
  // ── p04 正德九年：一座堂改写了山与村（核心证据页）──────────────
  4: {
    design: 4,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p4_title", text: "正德九年：一座堂，改写了山与村", size: 36, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p4_tag_source", kind: "tag", text: "明代官修志书所记 · 泉名成堂名", backing: true, delay: 100 },
      { slotId: "p4_quote", text: "「溫泉堂，在石窩村，離城五十里。\n本村有山，曰堂子山，下有溫泉，\n正德甲戌谷太監建堂於其上，因名。\n右僉都御史陳天祥記。」", size: 25, color: INK, weight: 800, lh: 1.6, backing: true, delay: 180 },
      { slotId: "p4_kao", text: "逐字考订——\n「石窩村」：万历官书里的正式村名，不叫温泉。\n「下有溫泉」：山下确有温泉出露，得名的实物前提。\n「正德甲戌」：干支即正德九年，一五一四年。\n「因名」：官书自己说——堂因泉得名。", size: 22, color: INK, weight: 700, lh: 1.55, backing: true, delay: 340 },
      { slotId: "p4_verdict", text: "泉有名字，是水给的；\n堂有名字，是人给的——正德九年，一位谷姓太监。\n山因堂得名叫堂子山，村慢慢跟着堂改口。\n名字是一层层传下来的。", size: 23, color: INK, weight: 800, lh: 1.55, backing: true, delay: 500 },
      { slotId: "p4_doubt1", text: "存疑 · 山名得自山上之「堂」是通行考释，原文未明言——本片标存疑。", size: 21, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 620 },
      { slotId: "p4_doubt2", text: "存疑 · 谷太监仅存姓氏，名未考得；温泉堂与陈天祥碑今无存世记录。\n存疑 · 《宛署杂记》成书年份通行作万历二十一年，另有万历二十年说；本片只说「明万历年间」。", size: 20, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 720 },
      { slotId: "p4_photo_wanshu", kind: "photo", text: "宛署杂记书影（Page04 提供 PhotoSpec）" },
      { slotId: "p4_photo_chain", kind: "photo", text: "命名链拓扑（Page04 提供 PhotoSpec）" },
    ],
  },
  // ── p05 一冷一热：黑龙潭与温泉 ────────────────────────────────
  5: {
    design: 5,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p5_title", text: "一冷一热，两眼泉，两座庙", size: 38, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p5_tag_source", kind: "tag", text: "姊妹地名 · 祈与浴分层", backing: true, delay: 100 },
      { slotId: "p5_quote_hlt", text: "依岗有龙王庙，碧殿丹垣，廊前为潭。\n土人云有黑龙潜其中，\n故名黑龙潭。\n——[明末笔记所记]", size: 21, color: INK, weight: 700, lh: 1.55, backing: true, delay: 180 },
      { slotId: "p5_quote_wq", text: "泉如湯未至沸時，\n甃而為池，以待浴者。\n——[明末笔记所记]", size: 21, color: INK, weight: 700, lh: 1.55, backing: true, delay: 300 },
      { slotId: "p5_shiyou", text: "山门石额题「敕建黑龙王庙」，未书年款。\n明成化二十二年（一四八六）建庙碑、清康熙二十年（一六八一）重建。\n清乾隆三年（一七三八）封龙神为「昭靈沛澤龍王之神」。\n殿顶覆黄琉璃筒瓦（实物在）。", size: 21, color: INK, weight: 700, lh: 1.55, backing: true, delay: 420 },
      { slotId: "p5_verdict", text: "龙王庙求雨，温泉堂沐浴。\n一个「祈」，一个「浴」，分属两眼泉、两座庙。\n把它们合成一句「皇帝常来温泉洗澡」，是错的。", size: 24, color: INK, weight: 800, lh: 1.55, backing: true, delay: 560 },
      { slotId: "p5_doubt1", text: "存疑 · 「土人云」三字表明「黑龙潜其中」系采俗说，刘侗本人只记庙与潭。", size: 20, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 680 },
      { slotId: "p5_doubt2", text: "存疑 · 「乾隆八十八岁亲叩龙王庙」为传说，不入史实层（黄琉璃瓦是实物，另说）。\n存疑 · 龙王庙「始建年代不详」与成化二十二年建庙碑并存——本片表述为「始建不详，成化二十二年建庙碑为现存最早纪年」。", size: 20, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 780 },
      { slotId: "p5_photo_hlt", kind: "photo", text: "黑龙潭龙王庙示意（Page05 提供 PhotoSpec）" },
      { slotId: "p5_card_qi", text: "祈 · 求雨\n黑龙潭龙王庙\n冷泉", size: 26, color: INK, weight: 800, lh: 1.6, backing: true, delay: 880 },
      { slotId: "p5_card_yu", text: "浴 · 沐浴\n温泉堂\n热泉", size: 26, color: INK, weight: 800, lh: 1.6, backing: true, delay: 960 },
    ],
  },
  // ── p06 伪引文 · 原文（证伪页；对照卡待补期间 TextOnly，右槽留空）──
  6: {
    design: 6,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p6_title", text: "伪引文 · 原文", size: 38, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p6_tag_kao", kind: "tag", text: "逐字对勘 · 本集核心证伪", backing: true, delay: 100 },
      { slotId: "p6_fake", text: "伪引 · 已证伪 · 出处标注不实\n\n「平地温泉如沸，冬月白气滃然，\n辽金帝王驻跸沐浴之所」\n——旧注称出自《帝京景物略》卷五", size: 22, color: INK, weight: 700, lh: 1.55, backing: "rgba(213,208,198,0.94)", borderStyle: "dashed", delay: 180 },
      { slotId: "p6_vs", text: "VS", size: 26, color: "#8a5a2c", weight: 800, lh: 1.2, backing: true, delay: 300 },
      { slotId: "p6_orig", text: "原文 · 《帝京景物略》「温泉」条\n\n「山北十里，平疇良苗，溫泉出焉。\n泉如湯未至沸時，甃而為池，以待浴者。」", size: 22, color: INK, weight: 800, lh: 1.55, backing: "rgba(247,240,223,0.95)", borderStyle: "solid", delay: 380 },
      { slotId: "p6_fake2", text: "伪说：西山八大水院之香水院＝温泉后山\n原文：「金章宗設六院遊覽，此其一院。\n草際斷碑，『香水院』三字存焉。」\n——断碑在妙高峰法云寺，不在温泉后山", size: 22, color: INK, weight: 700, lh: 1.55, backing: "rgba(213,208,198,0.94)", borderStyle: "dashed", delay: 520 },
      { slotId: "p6_verdict", text: "《帝京景物略》里没有那句话。\n香水院的断碑在妙高峰，不在温泉后山。\n本村可证的文字史，从明代开始。\n辽金那一层，是后人的想象叠上去的。", size: 24, color: INK, weight: 800, lh: 1.55, backing: true, delay: 660 },
      { slotId: "p6_doubt1", text: "存疑 · 诸本对八院名目与今地对应互异，《帝京景物略》且作「六院」；\n除清水院＝大觉寺有辽碑直证外，其余均为后世考释。", size: 20, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 780 },
      { slotId: "p6_doubt2", text: "存疑 · 温泉与金章宗的关联无据，本片不作断言。", size: 20, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 880 },
    ],
  },
  // ── p07 民国的显龙山：一面山壁的三层字 ────────────────────────
  7: {
    design: 7,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p7_title", text: "一面山壁，三层字", size: 38, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p7_tag_source", kind: "tag", text: "一手实物 · 摩崖与纪念建筑", backing: true, delay: 100 },
      { slotId: "p7_l1", text: "崖刻「水流云在」四字——英敛之民国二年正月手书，\n每字高约一点六米。", size: 23, color: INK, weight: 800, lh: 1.55, backing: true, delay: 180 },
      { slotId: "p7_l1q", text: "「英斂之偕內子淑仲小兒千里遊此，偶取杜句寄意，\n時宣統退位之次年正月也。」", size: 21, color: INK, weight: 700, lh: 1.55, backing: true, delay: 300 },
      { slotId: "p7_l1v", text: "取杜甫《江亭》「水流心不競，雲在意俱遲」之意。\n清帝退位次年，一位报人把心事刻进了山壁。", size: 22, color: INK, weight: 700, lh: 1.55, backing: true, delay: 420 },
      { slotId: "p7_l2", text: "纪念坊落款「民國二十五年十一月馮玉祥」，锁定题刻年代。\n八角七级密檐式白石塔，通高十二点二米；\n塔台南「精神不死」，北「浩氣長存」；\n塔身嵌邹鲁、居正、冯玉祥、于右任等塔铭。", size: 21, color: INK, weight: 700, lh: 1.55, backing: true, delay: 540 },
      { slotId: "p7_l3", text: "孙岳，滦州起义共谋者，\n一九三一年葬显龙山。六年后，\n冯玉祥在同一座山上建滦州起义纪念园。", size: 21, color: INK, weight: 700, lh: 1.55, backing: true, delay: 660 },
      { slotId: "p7_doubt1", text: "存疑 · 「选址因孙岳墓而来」属合理推断，本片不作断言。\n存疑 · 「英敛之为北京地区最大摩崖石刻」之说与凤凰岭民国石刻口径冲突——本片不取「最大之最」，只写每字高约一点六米的实测描述。", size: 20, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 780 },
      { slotId: "p7_doubt2", text: "存疑 · 孙岳墓方位（南侧山环中／东脉山麓下）区保条目内部两说并存——本片只说「显龙山麓」。", size: 20, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 880 },
      { slotId: "p7_photo_shuiliu", kind: "photo", text: "水流云在摩崖示意（Page07 提供 PhotoSpec）" },
      { slotId: "p7_photo_luanzhou", kind: "photo", text: "滦州纪念塔示意（Page07 提供 PhotoSpec）" },
    ],
  },
  // ── p08 泉去名存：一个地名的水文遗嘱 ──────────────────────────
  8: {
    design: 8,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p8_title", text: "泉去名存：一个地名的水文遗嘱", size: 36, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p8_tag_chain", kind: "tag", text: "五段接力 · 泉→堂→山→村→镇", backing: true, delay: 100 },
      { slotId: "p8_chain", text: "泉 · 温泉——山下温泉出露（《宛署杂记》「下有溫泉」）\n堂 · 温泉堂——正德九年谷太监建于堂子山上\n山 · 堂子山——山因堂得名（通行考释，存疑）；今名显龙山\n村 · 温泉村——明末文献已用；此前官书作「石窝村」\n镇 · 温泉镇——今海淀区温泉镇，下辖七行政村", size: 21, color: INK, weight: 700, lh: 1.5, backing: true, delay: 180 },
      { slotId: "p8_guobao", text: "辛亥滦州起义纪念园——第六批全国重点文物保护单位，\n二零零六年五月二十五日公布，编号 6-886\n（近现代重要史迹及代表性建筑类）。\n黑龙潭及龙王庙——大运河国保子项：二零零六年列第六批（6-810），\n二零一三年并入第七批「大运河」（7-1973-3-009）；\n另为一九八四年第三批北京市文物保护单位。", size: 20, color: INK, weight: 700, lh: 1.45, backing: true, delay: 340 },
      { slotId: "p8_doubt_status", text: "存疑 · 天然温泉眼的今日存续状态未考得——本片既不写「至今仍在涌流」，\n也不写「早已干涸」。\n已证旁例：黑龙潭于二十一世纪初因超采地下水，水深不盈尺。", size: 21, color: INK, weight: 700, lh: 1.5, backing: "rgba(213,208,198,0.94)", delay: 500 },
      { slotId: "p8_end_l", text: "水会隐没，名字不会。\n村、镇、路、医院、水厂，\n都还姓「温泉」。", size: 22, color: INK, weight: 800, lh: 1.6, backing: true, delay: 640 },
      { slotId: "p8_end_r", text: "疗养这件事六百年没断，\n只是换了主人。", size: 22, color: INK, weight: 800, lh: 1.6, backing: true, delay: 760 },
      { slotId: "p8_duizhen", text: "同属今温泉镇的西邻白家疃，讲的是祠堂与碑的故事——\n同一条山前带，别样地名生成机制。", size: 21, color: INK, weight: 700, lh: 1.5, backing: true, delay: 880 },
      { slotId: "p8_doubt_guobao", text: "存疑 · 编号与批次据名录口径，须与国务院公布名单原件复核。", size: 19, color: INK, weight: 700, lh: 1.4, backing: "rgba(213,208,198,0.94)", delay: 980 },
      { slotId: "p8_photo_chain", kind: "photo", text: "命名链拓扑（Page08 提供 PhotoSpec）" },
      { slotId: "p8_photo_timeline", kind: "photo", text: "地名置换时间轴（Page08 提供 PhotoSpec）" },
    ],
  },
};
