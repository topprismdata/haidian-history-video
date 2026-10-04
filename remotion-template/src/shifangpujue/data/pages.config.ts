// pages.config.ts — E26《十方普觉寺·六次易名的半部北京佛教史》逐页槽位文案与样式.
// 唯一规格书：docs/superpowers/specs/2026-10-04-e26-shifangpujue-design.md（APPROVED）
// ＋ shifangpujue_video/research.md v1.0.
// 板型：全片八页皆为 MixedPage。
// 槽位几何见 slots.json（plate 全部 1920×1080 设计空间 = 画布 1:1）。
// 🔴 E24/E25 教训：屏显纪年一律用全字形汉字（三位/四位不上小字号屏显，只留年号），
//    禁 U+3007 圆圈数字（宋体下不可见 → OCR 漏读）。
// V-NC01 六名与年号一一对应，严禁笼统「数次易名」；
// V-NC02 铜卧佛系元代所铸，严禁「唐代遗存」；
// V-NC03 国保第五批、编号 5-205，严禁「1-75」式编号（第一批口径）；
// V-NC04「Offer 寺」不入史；V-NC05 寿安山南麓，严禁混写为「香山卧佛寺」。
const INK = "#3a3226";

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
  // ── p01 一座寺，五个名字 ────────────────────────────────────────
  1: {
    design: 1,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p1_title", text: "十方普觉寺 · 六次易名的半部北京佛教史", size: 38, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p1_sub", text: "七个名号 · 一尊元代铜佛", size: 24, color: INK, weight: 700, lh: 1.3, backing: true },
      { slotId: "p1_tag_index", kind: "tag", text: "寿安山南麓索引 · 制作组示意", backing: true },
      { slotId: "p1_hook", text: "一座寺换过六个名字。\n名字是皇帝给的，佛是元朝铸的——\n谁才真正「拥有」它？", size: 28, color: INK, weight: 800, lh: 1.45, backing: true, delay: 300 },
      { slotId: "p1_six", text: "兜率寺 → 寿安山寺 → 昭孝寺 → 洪庆寺\n寿安禅林 → 永安寺 → 十方普觉寺", size: 22, color: INK, weight: 700, lh: 1.5, backing: true, delay: 420 },
      { slotId: "p1_gap", text: "寺创于唐，铜卧佛铸于元。\n六个名号横跨一千三百余年，\n而寺里那尊佛，至今还是元朝的佛。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 520 },
      { slotId: "p1_tag_hook", kind: "tag", text: "首例纵向层累 · 名号沿革即断代史", backing: true, delay: 620 },
      { slotId: "p1_photo_gate", kind: "photo", text: "卧佛寺山门实拍（Page01 提供 PhotoSpec）" },
    ],
  },
  // ── p02 唐太宗贞观年间：初名兜率寺 ────────────────────────────
  2: {
    design: 2,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p2_title", text: "唐太宗贞观年间：初名兜率寺", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p2_tag_source", kind: "tag", text: "古代方志与正史所记 · 寺之始建", backing: true },
      { slotId: "p2_founded", text: "始建于唐太宗贞观年间，\n即六二七年至六四九年之间，\n距今一千三百余年。", size: 26, color: INK, weight: 800, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p2_tag_doushuai", kind: "tag", text: "名相考订", backing: true, delay: 220 },
      { slotId: "p2_name", text: "「兜率」＝梵文音译，指弥勒内院。\n与今寺所供的释迦牟尼涅槃像，\n并非同一尊佛，亦非同一种供奉。", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 320 },
      { slotId: "p2_note", text: "名字在前，佛像后来才换。\n初建时的供奉，与今日殿中的铜卧佛，\n分属两个不同的时代。", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 440 },
      { slotId: "p2_tag_gap", kind: "tag", text: "初建名 ≠ 今日供奉", backing: true, delay: 540 },
      { slotId: "p2_photo_folio", kind: "photo", text: "古籍书影（Page02 提供 PhotoSpec）" },
    ],
  },
  // ── p03 元英宗至治元年：昭孝寺与一尊元代铜佛 ──────────────────
  3: {
    design: 3,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p3_title", text: "元英宗至治元年：昭孝寺，与一尊元代铜佛", size: 38, color: INK, weight: 800, lh: 1.28, backing: true },
      { slotId: "p3_tag_source", kind: "tag", text: "一手正史与金石所记", backing: true },
      { slotId: "p3_zhaoxiao", text: "元英宗延祐七年（一三二零年九月）\n下诏在旧址敕建，寺名寿安山寺。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 120 },
      { slotId: "p3_hongqing", text: "至治元年（一三二一年十二月）\n冶铜五十万斤，铸成铜卧佛。\n寺名后又见昭孝寺、洪庆寺，\n改称的确切年份诸说不一。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 240 },
      { slotId: "p3_wofoe", text: "就在这次扩建里，寺内铸成\n释迦牟尼涅槃铜佛：卧姿朝右，\n身长约五米，北京现存最大最古。", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 360 },
      { slotId: "p3_tag_fact", kind: "tag", text: "佛系元代所铸 · 非唐物", backing: true, delay: 480 },
      { slotId: "p3_photo_wofoe", kind: "photo", text: "元代铜卧佛全貌（Page03 提供 PhotoSpec）" },
    ],
  },
  // ── p04 寺是唐的，佛是元的（年代错位核心页）───────────────────
  4: {
    design: 4,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p4_title", text: "寺是唐的，佛是元的", size: 42, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p4_tag_source", kind: "tag", text: "器物年代 ≠ 建置年代", backing: true },
      { slotId: "p4_left", text: "寺\n唐太宗贞观年间始建\n时名兜率寺\n初建之名", size: 23, color: INK, weight: 800, lh: 1.62, backing: true, delay: 140 },
      { slotId: "p4_right", text: "佛\n元代至治元年所铸\n释迦牟尼涅槃铜卧佛\n长约五米", size: 23, color: INK, weight: 800, lh: 1.62, backing: true, delay: 280 },
      { slotId: "p4_axis_era_left", text: "寺 · 唐 · 贞观年间", size: 19, color: INK, weight: 800, lh: 1.2, align: "center", backing: true, delay: 380 },
      { slotId: "p4_axis_era_right", text: "佛 · 元 · 至治元年", size: 19, color: INK, weight: 800, lh: 1.2, align: "center", backing: true, delay: 420 },
      { slotId: "p4_axis_gap", text: "相隔六百余载", size: 22, color: "#8a5a2c", weight: 800, lh: 1.2, align: "center", backing: true, delay: 470 },
      { slotId: "p4_verdict", text: "佛不能反过来证明寺有多老，\n寺也不能反过来证明佛有多新。\n它们在同一院子里，却是两个年代的东西。", size: 24, color: INK, weight: 800, lh: 1.55, backing: true, delay: 560 },
      { slotId: "p4_tag_verdict", kind: "tag", text: "同址 ≠ 同期", backing: true, delay: 540 },
      { slotId: "p4_photo_face", kind: "photo", text: "铜卧佛面部特写（Page04 提供 PhotoSpec）" },
    ],
  },
  // ── p05 明正统与成化：寿安山寺、永安寺 ────────────────────────
  5: {
    design: 5,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p5_title", text: "明正统与成化：寿安禅林、永安寺", size: 38, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p5_tag_source", kind: "tag", text: "明代实录与志书所记 · 两次更名", backing: true },
      { slotId: "p5_zhengtong", text: "正统八年（一四四三年）重修，\n朝廷赐名寿安禅林，\n并颁赐《大藏经》。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 120 },
      { slotId: "p5_chenghua", text: "成化十八年（一四八二年）\n再改称永安寺。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 260 },
      { slotId: "p5_note", text: "两次改名间隔不到四十年。\n名字一次一次地换，寺还是同一座寺：\n位置没动，佛殿也还在原处，\n连那尊元代大佛也一直躺着。\n变的只是头顶那块匾。", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 400 },
      { slotId: "p5_tag_note", kind: "tag", text: "改的是匾，不改的是寺", backing: true, delay: 520 },
      { slotId: "p5_timeline", kind: "photo", text: "六名纵贯时间轴（Page05 提供 PhotoSpec）" },
    ],
  },
  // ── p06 清雍正十二年：赐名十方普觉寺 ────────────────────────
  6: {
    design: 6,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p6_title", text: "清雍正十二年：赐名十方普觉寺", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p6_tag_source", kind: "tag", text: "御赐名号 · 寺额至今悬于殿前", backing: true },
      { slotId: "p6_bestow", text: "雍正十二年（一七三四年）大规模重修，\n雍正帝赐名「十方普觉寺」，\n此名沿用至今。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 120 },
      { slotId: "p6_shi_fang", text: "「十方」：东西南北四方，\n加东南、西南、东北、西北四维，\n再加上和下——共十个方位。", size: 23, color: INK, weight: 700, lh: 1.5, backing: true, delay: 260 },
      { slotId: "p6_pu_jue", text: "「普觉」：普遍地令众生觉悟。\n雍正御碑释此名为「佛能普知十方，\n一佛独卧十方普觉」。", size: 23, color: INK, weight: 700, lh: 1.5, backing: true, delay: 380 },
      { slotId: "p6_note", text: "七个名号里，有两个是皇帝敕赐或御赐的。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 500 },
      { slotId: "p6_tag_bestow", kind: "tag", text: "两个御赐名号", backing: true, delay: 600 },
      { slotId: "p6_photo_banner", kind: "photo", text: "寺额拓影（Page06 提供 PhotoSpec）" },
    ],
  },
  // ── p07 第五批国保：寺在国家植物园里 ──────────────────────────
  7: {
    design: 7,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p7_title", text: "第五批国保：寺在国家植物园里", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p7_guobao", text: "第五批全国重点文物保护单位，\n二零零一年六月二十五日国务院公布，\n编号 5-205。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 120 },
      { slotId: "p7_location", text: "寺在寿安山南麓，\n今位于国家植物园内，\n为园中古建与展陈空间之一。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 260 },
      { slotId: "p7_caveat", text: "寿安山、香山、玉泉山是三个不同的山名，\n这座寺在寿安山，不在香山。\n网传的英文谐音戏称属现代玩笑，\n不是寺的名字，不进寺史。", size: 23, color: INK, weight: 700, lh: 1.55, backing: true, delay: 400 },
      { slotId: "p7_tag_caveat", kind: "tag", text: "本集为第五批国保", backing: true, delay: 520 },
      { slotId: "p7_photo_garden", kind: "photo", text: "卧佛寺与国家植物园共存实景（Page07 提供 PhotoSpec）" },
    ],
  },
  // ── p08 名字是皇帝给的，佛是元朝铸的 ──────────────────────────
  8: {
    design: 8,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p8_title", text: "名字是皇帝给的，佛是元朝铸的", size: 42, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p8_tag_summary", kind: "tag", text: "六道刻度 · 唐至清", backing: true },
      { slotId: "p8_chain", text: "兜率寺 · 寿安山寺 · 昭孝寺 · 洪庆寺 · 寿安禅林 · 永安寺 · 十方普觉寺", size: 26, color: INK, weight: 800, lh: 1.4, backing: true, delay: 140 },
      { slotId: "p8_eras", text: "唐·贞观（初建）　元·延祐/至治（敕建＋三称）　明·正统/成化（两次）　清·雍正（御赐）", size: 21, color: INK, weight: 700, lh: 1.4, backing: true, delay: 260 },
      { slotId: "p8_composite", kind: "photo", text: "四时代叠合图（Page08 提供 PhotoSpec）" },
      { slotId: "p8_sum_left", text: "七个名号，横跨唐元明清四个朝代，\n就是一部北京佛教史的刻度。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 420 },
      { slotId: "p8_sum_right", text: "寺里最老的那件东西不属于任何一个名字，\n它比最后那个名字还要早四百多年。\n名字会换，佛不会。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 520 },
    ],
  },
};
