// pages.config.ts — E27《白家疃·纸上的疃，嘴里的滩》逐页槽位文案与样式.
// 唯一规格书：docs/superpowers/specs/2026-10-04-e27-baijiatuan-design.md（APPROVED）
// ＋ baijiatuan_video/research.md v1.0.
// 板型：全片八页皆为 MixedPage（纸底＋装裱真图＋HTML 卡）；P6 无 photo 槽（纯文字页）。
// 槽位几何见 slots.json（plate 全部 1920×1080 设计空间 = 画布 1:1，只读勿改）。
// 🔴 E24/E25 教训：屏显纪年一律全字形（四位阿拉伯数字不上屏），禁 U+3007 圆圈数字。
// V-NC01 蒙古语说只作被裁决错说（口播 p04），屏显零命中；
// V-NC02 三副面孔等权并存，禁单线演变（未考得≠证伪）；
// V-NC03 允祥（生前避讳）／胤祥（身后复名）仅 P4 同页分期出现；
// V-NC04 1915 图上村名字形不可断言，严禁「图上作白家滩」；
// V-NC05 只写海淀区文物保护单位，全片无「X-YYY」编号；
// V-NC06 成村年代与曹雪芹居留双双存疑化，禁「晚年定居／终老」断言（仅裁决卡引述）；
// V-NC07 纪年白名单：年号／全字形／相对量；V-NC08 内审标记零上屏；
// V-NC09 示意图 caption 限定语逐字（非原刊扫描／非原石拓片／非测绘拓扑…）；
// V-NC10 存疑清单逐条落位（每条带「存疑」前缀），禁写清单零命中。
const INK = "#3a3226";
// 浅红底：亮度高于墨迹阈值，L5 检测器只见深红文字（见 172 行注释）
const RED_BANNER_TINT = "rgba(168, 69, 44, 0.14)";

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
}

// 存疑标注：灰化底（规格 §二：不得与档案卡同底色）。
const GRAY_BACKING = "rgba(107,90,68,0.16)";
const GRAY_INK = "#5a5044";
// P5 证据状态横幅：全片唯一红底警示条（规格 §二 Page05）。
// 🔴 E27 实测：深红底(#8c2f24)+浅字会让 L5 溢出检测器把整块垫板判成墨迹
//    （检测器以亮度<130 为墨），四面贴边误报。改为浅红底＋深红字：
//    警示语义不变，检测器假设（浅底深字）不破。

export const PAGE_CONFIG: Record<number, { design: number; bounds: number[]; items: TextItem[] }> = {
  // ── p01 连红学家都要查字典的村名 ──────────────────────────────
  1: {
    design: 1,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p1_title", text: "白家疃 · 纸上的疃，嘴里的滩", size: 38, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p1_sub", text: "一个字 · 一条村 · 五个时代", size: 24, color: INK, weight: 700, lh: 1.3, backing: true },
      { slotId: "p1_tag_index", kind: "tag", text: "白家疃 · 杨家村 · 黑龙潭 · 香山山脊 · 温泉镇界", backing: true },
      {
        slotId: "p1_hook",
        text: "一九七二年，红学家要找白家疃。\n两个人，都不知道它在京郊哪个方向。\n借来一本派出所管界手册，查到三个字：\n「疃」——得翻字典。\n到了村里才知道：这里人念「滩」。",
        size: 27, color: INK, weight: 800, lh: 1.45, backing: true, delay: 300,
      },
      {
        slotId: "p1_note",
        text: "［据吴恩裕晚年回忆，转引自樊志斌考证文章］",
        size: 16, color: GRAY_INK, weight: 500, lh: 1.5, backing: GRAY_BACKING, delay: 460,
      },
      { slotId: "p1_tag_foot", kind: "tag", text: "纸上一个音 · 嘴里一个音 · 从名字开始就不简单", backing: true, delay: 560 },
      {
        slotId: "p1_photo_main", kind: "photo",
        text: "民国四年实测图（Page01 提供 PhotoSpec）",
      },
    ],
  },
  // ── p02 疃字的两千年档案 ─────────────────────────────────────
  2: {
    design: 2,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p2_title", text: "疃字的两千年档案", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      {
        slotId: "p2_quote_shuowen",
        text: "《说文解字·田部》\n疃：禽獸所踐處也。\n《詩》曰：「町疃鹿場。」\n從田，童聲。土短切。",
        size: 26, color: INK, weight: 800, lh: 1.45, backing: true, delay: 120,
      },
      {
        slotId: "p2_quote_shijing",
        text: "《诗经·豳风·东山》\n町疃鹿場，熠耀宵行。",
        size: 26, color: INK, weight: 800, lh: 1.45, backing: true, delay: 260,
      },
      { slotId: "p2_tag_src", kind: "tag", text: "传世经典原刊录文 · 底本可靠", backing: true, delay: 380 },
      {
        slotId: "p2_verdict",
        text: "「从田，童声」——字的骨架是「田」。\n「土短切」——韵书读音链完整。\n本义是野兽践踏出的空场，与村庄无关。",
        size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 480,
      },
      { slotId: "p2_tag_verdict", kind: "tag", text: "字义一脉相承 · 本义≠村庄", backing: true, delay: 580 },
      { slotId: "p2_photo_folio", kind: "photo", text: "《说文》书影（Page02 提供 PhotoSpec）" },
    ],
  },
  // ── p03 从鹿场到村疃：三副面孔 ───────────────────────────────
  3: {
    design: 3,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p3_title", text: "从鹿场到村疃", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      {
        slotId: "p3_quote_luyou",
        text: "宋·陆游《入蜀记》：\n「自出城，即黄茅弥望，每十余里，\n有村疃数家而已。」",
        size: 25, color: INK, weight: 800, lh: 1.45, backing: true, delay: 120,
      },
      {
        slotId: "p3_quote_mohe",
        text: "元·孟汉卿《魔合罗》：「怎把走村串疃货郎儿」\n存疑：《康熙字典》按语注意到今本《诗经》异体作「畽」——仍为同字。",
        size: 22, color: INK, weight: 700, lh: 1.5, backing: true, delay: 260,
      },
      {
        slotId: "p3_faces",
        text: "嘴里的「白家滩」（tān）· 俗名记录，二十世纪七十年代实地\n纸上的「白家疃」（tuǎn）· 清前期官立碑额已用此字\n册子上的「白家瞳」（tóng）· 二十世纪三四十年代教区堂口记录\n存疑：「滩白」代指白家疃——弘晓《明善堂诗集》，转引自樊志斌文，卷次未核",
        size: 21, color: INK, weight: 700, lh: 1.5, backing: true, delay: 380,
      },
      {
        slotId: "p3_verdict",
        text: "两个读音长期并存。\n是「滩」雅化成了「疃」，还是「疃」的白读本就是「滩」？\n——未考得，本片不定案。\n存疑：「白」之所指两说（白姓聚居／滩地地形）皆无早期书证。",
        size: 22, color: INK, weight: 800, lh: 1.45, backing: true, delay: 500,
      },
      { slotId: "p3_tag_verdict", kind: "tag", text: "三副面孔 · 并存不定案", backing: true, delay: 620 },
      { slotId: "p3_photo_card", kind: "photo", text: "疃字释义卡（Page03 提供 PhotoSpec）" },
    ],
  },
  // ── p04 敕建的祠：残碑上的「敕」字 ──────────────────────────────
  4: {
    design: 4,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p4_title", text: "敕建白家疃和硕怡贤亲王祠", size: 38, color: INK, weight: 800, lh: 1.3, backing: true },
      {
        slotId: "p4_names",
        text: "怡亲王允祥——生前避雍正帝讳称「允祥」；\n雍正八年卒，谥「贤」，配享太庙，\n特旨复名「胤祥」。",
        size: 24, color: INK, weight: 800, lh: 1.5, backing: true, delay: 120,
      },
      {
        slotId: "p4_chain",
        text: "雍正初年在此造别业 → 雍正八年身故 →\n当地百姓呈请作祠、奉旨批准、以附近官田为祭田 →\n雍正十年（一七三二）建成怡贤亲王祠\n（海淀区文保名录口径）",
        size: 23, color: INK, weight: 700, lh: 1.5, backing: true, delay: 260,
      },
      {
        slotId: "p4_beibei",
        text: "残碑四通 · 碑额著录\n「敕賜白家疃賢王祠祭田碑記」／「敕建白家疃和□怡親王祠碑記」\n「羅夫人紀念碑」／「千載不朽碑」",
        size: 24, color: INK, weight: 800, lh: 1.5, backing: true, delay: 400,
      },
      { slotId: "p4_tag_src", kind: "tag", text: "一手实物层：残碑碑额 · 官建官祀", backing: true, delay: 520 },
      {
        slotId: "p4_caveat",
        text: "存疑：别业建年两说并存（造园／设行营），清代原始档案未核，本片不系年。\n存疑：「行营设白家疃」系现代媒体口径，非清代档案事实。\n存疑：祠宇朝向采海淀区文保名录「坐南向北」说，另有著录作「坐北朝南」。",
        size: 21, color: GRAY_INK, weight: 600, lh: 1.45, backing: GRAY_BACKING, delay: 620,
      },
      { slotId: "p4_photo_beibi", kind: "photo", text: "碑额拓影（Page04 提供 PhotoSpec）" },
    ],
  },
  // ── p05 一桩书证，写着一个村名 ───────────────────────────────
  // 🔴 delay 单位是帧（SlotPage: at = 8 + min(idx,30)*14 + delay）。p05 旁白重录后
  // 仅 16.96s，QA 抽帧在音频结束−0.2s ≈ 帧 502——delay 压到 ≤200 帧，最晚入场 ≈ 帧 278。
  5: {
    design: 5,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p5_title", text: "一桩书证，写着一个村名", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      {
        slotId: "p5_quote1",
        text: "敦敏《瓶湖懋斋记盛》：\n「（乾隆二十三年）春間，芹圃曾過舍以告，\n將徙居白家疃，值余赴通州迓過公，未能相遇。」",
        size: 24, color: INK, weight: 800, lh: 1.45, backing: true, delay: 40,
      },
      {
        slotId: "p5_quote2",
        text: "「乃訪其居……其地有小溪阻路，\n隔岸望之，土屋四間……」",
        size: 24, color: INK, weight: 800, lh: 1.45, backing: true, delay: 80,
      },
      {
        slotId: "p5_banner",
        text: "原件不存 · 今存过录本 · 真伪存争",
        size: 26, color: "#8c2f24", weight: 800, lh: 1.4, backing: RED_BANNER_TINT, delay: 120,
      },
      { slotId: "p5_tag", kind: "tag", text: "过录本 · 真伪存争", backing: true, delay: 160 },
      {
        slotId: "p5_caveat",
        text: "存疑：据传缘起——乾隆二十二年冬其姨母目盲，雪芹为之医治至春方愈，白氏请以祖茔土地树木筑室。\n存疑：「曹雪芹小道」为媒体报道口径的旅游叙事，步道与红枫林现状未核——本片不写「至今开放」。",
        size: 21, color: GRAY_INK, weight: 600, lh: 1.45, backing: GRAY_BACKING, delay: 200,
      },
      { slotId: "p5_photo_trail", kind: "photo", text: "小道拓扑（Page05 提供 PhotoSpec）" },
    ],
  },
  // ── p06 没有原件的公案（纯文字页，无 photo）────────────────────
  6: {
    design: 6,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p6_title", text: "没有原件的公案", size: 42, color: INK, weight: 800, lh: 1.3, backing: true },
      {
        slotId: "p6_chain",
        text: "《废艺斋集稿》八卷（署「芹圃曹霑」）→ 一九四三年孔祥泽经日本教员短暂过手抄录 → 原件旋佚，从未公开 → 上世纪七十年代吴恩裕于《文物》撰文公布残文 → 学界两派至今未决",
        size: 24, color: INK, weight: 700, lh: 1.4, backing: true, delay: 120,
      },
      {
        slotId: "p6_left",
        text: "主真派\n吴恩裕 · 冯其庸\n胡文彬 · 胡德平",
        size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 260,
      },
      {
        slotId: "p6_right",
        text: "质疑派\n陈毓罴 · 刘世德（孤证、文风、节气难对证）\n郭若愚（比对以为过录书法出自近人之手）\n邓云乡（旗人精手艺者托名可能）",
        size: 23, color: INK, weight: 700, lh: 1.5, backing: true, delay: 380,
      },
      {
        slotId: "p6_verdict",
        text: "既有文献引述，无第一手档案支持。\n这不是结论，是证据状态本身。\n「晚年定居」「终老于此」——本片不写。",
        size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 500,
      },
      { slotId: "p6_tag_verdict", kind: "tag", text: "孤本过录 · 两派未决 · 不定案", backing: true, delay: 620 },
      {
        slotId: "p6_caveat",
        text: "存疑：「土屋四间」无遗存报告；故居位置与形制未考得，本片不画复原图。",
        size: 22, color: GRAY_INK, weight: 600, lh: 1.45, backing: GRAY_BACKING, delay: 700,
      },
    ],
  },
  // ── p07 山后的科学心跳 ───────────────────────────────────────
  7: {
    design: 7,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p7_title", text: "山后的科学心跳", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      {
        slotId: "p7_jiufeng",
        text: "鹫峰地震台：中国人自行设计建设和管理的第一座地震台。\n一九三零年建于西山鹫峰山麓；一九三七年因抗战停测。",
        size: 22, color: INK, weight: 800, lh: 1.5, backing: true, delay: 120,
      },
      {
        slotId: "p7_baijiatuan",
        text: "一九五五年决定易地重建于白家疃；\n一九五七年正式恢复观测（适逢国际地球物理年），\n台站名「北京地震基准台、地磁台」；\n后来更名北京国家地球观象台。",
        size: 23, color: INK, weight: 800, lh: 1.5, backing: true, delay: 260,
      },
      {
        slotId: "p7_miles",
        text: "我国第一台自主研制的地震仪\n我国第一个地震遥测台网\n我国第一个数字化地震台",
        size: 22, color: INK, weight: 700, lh: 1.5, backing: true, delay: 400,
      },
      {
        slotId: "p7_road",
        text: "台址登记地址为「北京市海淀区白家疃路」——村名进了路名。",
        size: 22, color: INK, weight: 800, lh: 1.5, backing: true, delay: 520,
      },
      {
        slotId: "p7_caveat",
        text: "存疑：鹫峰台在今苏家坨镇北安河村西，与白家疃分属两处；「鹫峰台迁此」是职能迁移，不是原地延续。\n存疑：鹫峰台运行年数与记录地震总数，本片不列（来源为机构口径，非官方统计档）。",
        size: 21, color: GRAY_INK, weight: 600, lh: 1.45, backing: GRAY_BACKING, delay: 620,
      },
      { slotId: "p7_photo_1915", kind: "photo", text: "民国四年实测图（Page07 提供 PhotoSpec）" },
    ],
  },
  // ── p08 一个字，一条村，五个时代 ─────────────────────────────
  8: {
    design: 8,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p8_title", text: "一个字，一条村，五个时代", size: 42, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p8_eras", kind: "photo", text: "六段时代叠合（Page08 提供 PhotoSpec）" },
      {
        slotId: "p8_left",
        text: "一个字要翻字典才认得，\n一个村子有三个名字。\n名相的层累不是错误——\n是历史本身。",
        size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 260,
      },
      {
        slotId: "p8_right",
        text: "村还在，名字还挂在路牌上。\n「至今仍在」的，只有那座台。",
        size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 380,
      },
      { slotId: "p8_wenbao", kind: "tag", text: "怡贤亲王祠 · 海淀区文物保护单位（批次存疑） · 境内无全国重点文物保护单位", backing: true, delay: 500 },
      { slotId: "p8_photo_biane", kind: "photo", text: "门额拓影（Page08 提供 PhotoSpec）" },
    ],
  },
};
