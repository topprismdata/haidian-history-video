// pages.config.ts — E20《勺园·淑春园·未名湖》逐页槽位文案与样式。
// 唯一规格书：docs/superpowers/specs/2026-10-03-e20-map-documentary-design.md（APPROVED）
// ＋ shaoyuan_video/research.md v1.1（引文一律繁体照录附录A，异体字照录）。
// 板型：MapPage 4（P1 索引图 / P2 长卷释读 / P3 三山五园 PanZoom / P8 四时代 CrossFade）
//      ＋ MixedPage 4（P4 抄档 / P5 物证 / P6 燕大 / P7 定名）。
// 槽位几何见 slots.json（plate 全部 1920×1080 设计空间 = 画布 1:1）。
// 红线：浮在地图/长卷/照片上方的文字项一律 backing: true（卡纸垫 rgba(247,240,223,0.95)）；
// 屏显数字 ⊆ 当页口播（1615/1799/1801/1860/1920/1924/1925/1928/1931/1952/1982/2001/1003/42/64）；
// 标记圈/点位纯 SVG 叠加，不入槽表；全幅视口由页面打底，不占槽位。
const INK = "#3a3226";
const SOFT = "#6b5a44";

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

export const PAGE_CONFIG: Record<number, { design: number; bounds: number[]; items: TextItem[] }> = {
  // ── p01 今天这一湖（era_today 索引图打底 + 未名湖实拍镜框）──────
  1: {
    design: 1,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p1_title", text: "勺园·淑春园·未名湖", size: 46, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p1_sub", text: "一桩地名公案 · 一块土地的三个名字", size: 24, color: INK, weight: 700, lh: 1.3, backing: true },
      { slotId: "p1_index_tag", kind: "tag", text: "研究索引示意 · MEC-4 制作组示意", backing: true },
      { slotId: "p1_tag_lake", kind: "tag", text: "未名湖", backing: true },
      { slotId: "p1_tag_ship", kind: "tag", text: "石舫底座", backing: true },
      { slotId: "p1_tag_shao", kind: "tag", text: "勺园故址 · 西南隅一带", backing: true },
      { slotId: "p1_case", text: "这片湖，悬着一桩地名公案：\n它到底是不是明代米万钟勺园的湖？", size: 30, color: INK, weight: 800, lh: 1.45, backing: true, delay: 320 },
      { slotId: "p1_tower", text: "「一塔湖图」\n塔 · 湖 · 图书馆", size: 26, color: INK, weight: 700, lh: 1.5, backing: true },
      { slotId: "p1_photo", kind: "photo", text: "未名湖实拍镜框（Page01 提供 PhotoSpec）" },
    ],
  },
  // ── p02 1615：我们看见过勺园（ScrollPan 长卷释读带 + 文献卡）────
  2: {
    design: 2,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p2_title", text: "1615：我们看见过勺园", size: 34, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p2_honesty", text: "吴彬原卷影像未授权 · 本段以同时代文献释读卷中景致（非复制品）", size: 17, color: SOFT, weight: 700, lh: 1.3, backing: true },
      { slotId: "p2_q1", text: "淀之水濫觴一勺，\n都人米仲詔濬之，築為勺園。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 200 },
      { slotId: "p2_q1_badge", kind: "tag", text: "文献记载 · 长安客话", backing: true },
      { slotId: "p2_ye", text: "李園壯麗，米園曲折。\n米園不俗，李園不酸。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 410 },
      { slotId: "p2_ye_badge", kind: "tag", text: "文献记载 · 帝京景物略", backing: true },
      { slotId: "p2_route", text: "風煙里 → 纓雲橋 → 勺海堂\n太乙葉 → 翠葆樓 → 林於澨 → 稻畦千頃", size: 19, color: INK, weight: 700, lh: 1.6, backing: true, delay: 300 },
      { slotId: "p2_route_badge", kind: "tag", text: "文献记载 · 燕都游览志", backing: true },
      { slotId: "p2_lamp", text: "他把园景画成灯，人称「米家燈」", size: 22, color: INK, weight: 700, lh: 1.4, backing: true, delay: 260 },
      { slotId: "p2_lamp_badge", kind: "tag", text: "文献记载 · 长安客话", backing: true },
      { slotId: "p2_wubin", text: "吴彬《勺園祓禊圖》· 乙卯（1615）· 卷藏北京大学图书馆", size: 22, color: INK, weight: 800, lh: 1.4, backing: true, delay: 560 },
      { slotId: "p2_wubin_badge", kind: "tag", text: "一手题跋 · 翁氏旧藏今归北大图书馆", backing: true },
    ],
  },
  // ── p03 两套园址系统（三山五园图 PanZoom 中央大地图）──────────
  3: {
    design: 3,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p3_title", text: "两套园址系统 · 先看西南，再看东北", size: 30, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p3_map_tag", kind: "tag", text: "《三山五园图》海淀一带 · MEC-1 清晚期绘本", backing: true },
      { slotId: "p3_ring_sw", kind: "tag", text: "勺园故址 · 方位示意", backing: true, delay: 30 },
      { slotId: "p3_ring_ne", kind: "tag", text: "和珅赐园 · 方位示意", backing: true, delay: 450 },
      { slotId: "p3_sw", text: "西南 · 勺园链\n勺園故址 → 弘雅園 → 集贤院", size: 24, color: INK, weight: 800, lh: 1.45, backing: true, delay: 30 },
      { slotId: "p3_sw_badge", kind: "tag", text: "官书考订 · 今其园不可考", backing: true, delay: 280 },
      { slotId: "p3_sw2", text: "1801 改圆明园值日公所 · 1860 毁于战火", size: 22, color: INK, weight: 700, lh: 1.3, backing: true, delay: 30 },
      { slotId: "p3_ne", text: "东北 · 和珅赐园链\n淑春园之名已见于档案", size: 24, color: INK, weight: 800, lh: 1.45, backing: true, delay: 370 },
      { slotId: "p3_ne_badge", kind: "tag", text: "学术争议 · 两说并存", backing: true, delay: 550 },
      { slotId: "p3_ne2", text: "1799 和珅倒台 · 园子抄没", size: 22, color: INK, weight: 700, lh: 1.3, backing: true, delay: 510 },
      { slotId: "p3_punch", text: "这片湖，从来不是勺园的湖", size: 26, color: "#a8452c", weight: 800, lh: 1.3, backing: true, delay: 650 },
      { slotId: "p3_note", text: "双色圈＝方位示意 · 非边界复原图（勺园边界早已不可考）", size: 18, color: SOFT, weight: 700, lh: 1.3, backing: true, delay: 700 },
    ],
  },
  // ── p04 抄家清单（MixedPage：档案三件套 + 二十罪 + 双链方位图）──
  4: {
    design: 4,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p4_title", text: "抄家清单 · 嘉庆四年（1799）", size: 34, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p4_dispute", text: "这座园子，有的书叫它十笏园；\n是不是也叫淑春园，至今有争论。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 15 },
      { slotId: "p4_dispute_badge", kind: "tag", text: "学术争议 · 名称两说并存", backing: true },
      { slotId: "p4_map", kind: "photo", text: "海淀双链方位示意图（Page04 提供 node PhotoSpec）" },
      { slotId: "p4_map_tag", kind: "tag", text: "和珅赐园在今未名湖一带 · 方位示意（MEC-4）", backing: true },
      { slotId: "p4_ledger1", text: "花園一座，樓臺四十二所（42）", size: 26, color: INK, weight: 800, lh: 1.35, backing: true, delay: 300 },
      { slotId: "p4_ledger1_badge", kind: "tag", text: "一手档案 · 转引《庸庵笔记》", backing: true },
      { slotId: "p4_ledger2", text: "欽賜花園一座，亭臺六十四所（64）", size: 26, color: INK, weight: 800, lh: 1.35, backing: true, delay: 355 },
      { slotId: "p4_ledger2_badge", kind: "tag", text: "一手档案 · 抄家清单分记", backing: true },
      { slotId: "p4_ledger3", text: "現查得和珅花園內房一千零三間（1003）", size: 26, color: INK, weight: 800, lh: 1.35, backing: true, delay: 485 },
      { slotId: "p4_ledger3_badge", kind: "tag", text: "一手档案 · 一史馆《和珅犯罪全案档》", backing: true },
      { slotId: "p4_crime", text: "二十大罪第十三款：\n「園寓點綴，竟與圓明園蓬島瑤臺無異」", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 535 },
      { slotId: "p4_crime_badge", kind: "tag", text: "一手谕旨 · 转引《仁宗实录》", backing: true },
      { slotId: "p4_shihu", text: "昭梿《啸亭杂录》：「以和相十笏園為最，\n近為成邸所居」", size: 22, color: INK, weight: 700, lh: 1.5, backing: true, delay: 25 },
      { slotId: "p4_shihu_badge", kind: "tag", text: "时人记述 · 转引", backing: true },
    ],
  },
  // ── p05 园毁了，物还在说话（MixedPage：物证点位图 + 石舫/石屏）──
  5: {
    design: 5,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p5_title", text: "园毁了，物还在说话", size: 34, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p5_flow", text: "抄没后，先赏成亲王永瑆；\n道光年间，辗转归了睿亲王。", size: 22, color: INK, weight: 700, lh: 1.5, backing: true },
      { slotId: "p5_flow_badge", kind: "tag", text: "官书 · 实录/清史稿 转引", backing: true },
      { slotId: "p5_ship", text: "今天未名湖畔的石船，只剩当年的底座。\n后人常说和珅因它逾制获罪——", size: 24, color: INK, weight: 800, lh: 1.5, backing: true, delay: 250 },
      { slotId: "p5_ship2", text: "但谕旨原文里，并没有「石舫」二字。", size: 26, color: "#a8452c", weight: 800, lh: 1.35, backing: true, delay: 445 },
      { slotId: "p5_ship_badge", kind: "tag", text: "谕旨原文无石舫 · 现代引申层", backing: true },
      { slotId: "p5_screen", text: "湖边四扇石屏，刻的是乾隆题在圆明园\n夹镜鸣琴的诗，后来才移入燕园。", size: 24, color: INK, weight: 800, lh: 1.5, backing: true, delay: 530 },
      { slotId: "p5_screen_quote", text: "「夾鏡光澄風四面，垂虹影界水中央」", size: 24, color: INK, weight: 700, lh: 1.4, backing: true, delay: 575 },
      { slotId: "p5_screen_badge", kind: "tag", text: "圆明园夹镜鸣琴移入 · 非和珅园旧物", backing: true },
      { slotId: "p5_dot_ship", kind: "tag", text: "石舫底座 · 原地遗存", backing: true, delay: 195 },
      { slotId: "p5_dot_screen", kind: "tag", text: "石屏四扇 · 后移入", backing: true, delay: 485 },
      { slotId: "p5_dot_rui", kind: "tag", text: "睿邸时期 · 山水犹在", backing: true },
      { slotId: "p5_map_tag", kind: "tag", text: "物证点位 · MEC-4 示意", backing: true },
      { slotId: "p5_1860", text: "1860 年战火焚掠，这里重创成废园。", size: 26, color: INK, weight: 800, lh: 1.35, backing: true, delay: 15 },
      { slotId: "p5_end", text: "一条石船，两段公案。", size: 30, color: INK, weight: 800, lh: 1.3, backing: true, delay: 705 },
    ],
  },
  // ── p06 1920s：废园变大学（MixedPage：1926 全景 + 1860 对照）────
  6: {
    design: 6,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p6_title", text: "1920s：废园变大学", size: 34, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p6_photo1", kind: "photo", text: "燕大校园全景镜框（Page06 提供 PhotoSpec）" },
      { slotId: "p6_buy", text: "1920 年，司徒雷登买下这一带；\n据他回忆，地价六万银元。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 55 },
      { slotId: "p6_buy_badge", kind: "tag", text: "回忆转述 · 卖主陈树藩", backing: true },
      { slotId: "p6_plan", kind: "photo", text: "校园格局示意图（Page06 提供 node PhotoSpec）" },
      { slotId: "p6_plan_tag", kind: "tag", text: "墨菲总体规划 · 校园格局示意（MEC-4）", backing: true },
      { slotId: "p6_plan_note", text: "原规划图纸未检得 · 本图为制作组示意，非测绘图", size: 17, color: SOFT, weight: 700, lh: 1.3, backing: true },
      { slotId: "p6_tower", text: "1924 动工、1925 落成的水塔，仿通州燃灯塔的形制——\n设计者手里没有古塔的图纸。", size: 22, color: INK, weight: 700, lh: 1.5, backing: true, delay: 315 },
      { slotId: "p6_tower_badge", kind: "tag", text: "现代官方口径 · 北大文物页", backing: true },
      { slotId: "p6_boya", text: "这就是博雅塔。1860 年比托拍下的\n燃灯塔照片，成了对照。", size: 24, color: INK, weight: 800, lh: 1.5, backing: true, delay: 560 },
      { slotId: "p6_photo2", kind: "photo", text: "1860 通州燃灯塔照片镜框（Page06 提供 PhotoSpec）" },
      { slotId: "p6_photo2_tag", kind: "tag", text: "形制参照 · 非图纸依据", backing: true },
    ],
  },
  // ── p07 一个湖怎样得到名字（MixedPage：微水体图 + 书证卡）──────
  7: {
    design: 7,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p7_title", text: "一个湖怎样得到名字", size: 34, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p7_1928", text: "一九二八年，一位学生的小说落款写着：\n「改舊作于海甸未名湖畔」——\n这是最早的书面记录。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 70 },
      { slotId: "p7_1928_badge", kind: "tag", text: "北大校史馆考订 · 《燕大月刊》", backing: true },
      { slotId: "p7_names", text: "無名湖 · 睿湖 · 未名湖，一度并存\n（诸名此消彼长，非一夜定名）", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 285 },
      { slotId: "p7_names_badge", kind: "tag", text: "校史考订 · 诸名并用时期", backing: true },
      { slotId: "p7_1931", text: "1931，临湖轩集会上，钱穆赞成叫未名湖，\n冰心等支持。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 370 },
      { slotId: "p7_1931_badge", kind: "tag", text: "校史考订 · 侯仁之《燕园史话》系统", backing: true },
      { slotId: "p7_qian", text: "但钱穆并不是最初命名的人——\n未名湖，是燕大师生慢慢形成的共识。", size: 24, color: "#a8452c", weight: 800, lh: 1.5, backing: true, delay: 510 },
      { slotId: "p7_dot_wu", kind: "tag", text: "無名湖", backing: true, delay: 215 },
      { slotId: "p7_dot_rui", kind: "tag", text: "睿湖", backing: true, delay: 200 },
      { slotId: "p7_dot_wm", kind: "tag", text: "未名湖", backing: true, delay: 200 },
      { slotId: "p7_photo", kind: "photo", text: "燕京大学时期老照片镜框（Page07 提供 PhotoSpec）" },
      { slotId: "p7_photo_tag", kind: "tag", text: "真图 · 角落小图（出处链待核）", backing: true },
    ],
  },
  // ── p08 四个时代，叠在同一片湖山里（CrossFade 四时代收官）──────
  8: {
    design: 8,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p8_title", text: "四个时代，叠在同一片湖山里", size: 34, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p8_map_note", kind: "tag", text: "四时代叠合 · 研究示意 · 非测绘拓扑", backing: true },
      { slotId: "p8_era1", kind: "tag", text: "明代 · 勺园", backing: true, delay: 305 },
      { slotId: "p8_era2", kind: "tag", text: "清代 · 赐园与水田", backing: true, delay: 325 },
      { slotId: "p8_era3", kind: "tag", text: "民国 · 燕京大学", backing: true, delay: 340 },
      { slotId: "p8_era4", kind: "tag", text: "今 · 北京大学燕园", backing: true, delay: 370 },
      { slotId: "p8_1982", text: "1982 · 五号楼北侧的湖岸下，\n挖出长条石铺砌的建筑遗址。", size: 24, color: INK, weight: 800, lh: 1.5, backing: true },
      { slotId: "p8_1982_badge", kind: "tag", text: "校史转述 · 勺园故址唯一实物线索", backing: true },
      { slotId: "p8_2001", text: "2001 · 未名湖燕园建筑\n列入全国重点文物保护单位。", size: 24, color: INK, weight: 800, lh: 1.5, backing: true, delay: 510 },
      { slotId: "p8_2001_badge", kind: "tag", text: "现行 · 官方口径", backing: true },
      { slotId: "p8_photo", kind: "photo", text: "市保碑镜框（Page08 提供 PhotoSpec）" },
      { slotId: "p8_end", text: "公案讲完，湖还亮着。", size: 28, color: INK, weight: 800, lh: 1.3, backing: true, delay: 645 },
    ],
  },
};
