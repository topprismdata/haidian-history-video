// pages.config.ts — E24《大觉寺·阳台山麓的千年清水院》逐页槽位文案与样式.
// 唯一规格书：docs/superpowers/specs/2026-10-03-e24-dajuesi-design.md（APPROVED）
// ＋ dajuesi_video/research.md v1.0.
// 板型：MapPage 1（P4 旸台山麓朝向拓扑 PanZoom）
//      ＋ MixedPage 7（P1 索引 / P2 辽碑 / P3 帝京景物略 / P5 改名史 / P6 三废三兴 / P7 国保现状 / P8 四时代叠合）。
// 槽位几何见 slots.json（plate 全部 1920×1080 设计空间 = 画布 1:1）。
// 红线：文字项一律 backing: true；photo 槽 kind:"photo"；
//      屏显纪年 ⊆ 当页口播；逐字引文槽（slot_id 含 quote）豁免数字子集判据。
// V-NC01 严禁「始建于金章宗」；V-NC03 白玉兰不列植栽年代。
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
  // ── p01 背对太阳的古刹（阳台山麓索引打底 + 大觉寺实拍）────────────
  1: {
    design: 1,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p1_title", text: "大觉寺 · 阳台山麓的千年清水院", size: 40, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p1_sub", text: "一块刻于公元一〇六八年的石碑 · 一次改写通说的考据", size: 23, color: INK, weight: 700, lh: 1.3, backing: true },
      { slotId: "p1_tag_index", kind: "tag", text: "现代路网索引 · 制作组示意", backing: true },
      { slotId: "p1_tag_yangtai", kind: "tag", text: "旸台山 / 阳台山", backing: true, delay: 60 },
      { slotId: "p1_tag_dajuesi", kind: "tag", text: "大觉寺", backing: true, delay: 120 },
      { slotId: "p1_tag_heilongtan", kind: "tag", text: "黑龙潭", backing: true, delay: 180 },
      { slotId: "p1_tag_beianhe", kind: "tag", text: "北安河村", backing: true, delay: 240 },
      { slotId: "p1_question", text: "在海淀西北的山麓上，为什么有一座\n朝着西边的佛寺？", size: 29, color: INK, weight: 800, lh: 1.45, backing: true, delay: 300 },
      { slotId: "p1_truth", text: "日出，在它背后。\n答案不在传说里，它藏在一块刻于\n公元一〇六八年的石碑上——那块碑，至今仍立在寺内。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 440 },
      { slotId: "p1_photo", kind: "photo", text: "大觉寺山门实拍（Page01 提供 PhotoSpec）" },
    ],
  },
  // ── p02 公元 1068：碑上的五个字（辽碑书影 + 逐字释文，核心证据页）───
  2: {
    design: 2,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p2_title", text: "公元 1068：碑上的五个字", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p2_tag_stele", kind: "tag", text: "一手金石实物 · 辽咸雍四年", backing: true },
      { slotId: "p2_quote_1", text: "「旸台山者蓟壤之名峰，清水院者幽都之勝概。\n山之名傳諸前古，院之興止於近代。」", size: 26, color: INK, weight: 800, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p2_key_phrase", text: "院之興止於近代\n＝ 立碑时清水院已存在，且兴于不久之前", size: 27, color: INK, weight: 800, lh: 1.5, backing: true, delay: 260 },
      { slotId: "p2_key_badge", kind: "tag", text: "本集最硬的一条书证", backing: true, delay: 340 },
      { slotId: "p2_verdict", text: "同一段碑文又记：施主南陽鄧公從貴舍钱三十万葺僧舍，\n又出五十万募印大藏经，共印五百七十九帙。\n公元一〇六八年时，这里已经是清水院。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 420 },
      { slotId: "p2_verdict_badge", kind: "tag", text: "辽代已名清水院", backing: true, delay: 500 },
      { slotId: "p2_photo", kind: "photo", text: "辽咸雍四年清水院碑文书影（Page02 提供 PhotoSpec）" },
      { slotId: "p2_photo_tag", kind: "tag", text: "僧志延撰 · 碑今存大觉寺", backing: true },
    ],
  },
  // ── p03 金章宗的八院，是明人写下的（帝京景物略书影 + 时序对照）─────
  3: {
    design: 3,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p3_title", text: "金章宗的「八院」，是明人写下的", size: 39, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p3_tag_mingren", kind: "tag", text: "明人著述 · 帝京景物略卷五", backing: true },
      { slotId: "p3_quote_1", text: "「金章宗西山八院，寺其清水院也。」\n—— 《帝京景物略》大觉寺条", size: 26, color: INK, weight: 800, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p3_quote_badge", kind: "tag", text: "十六世纪明人追述", backing: true, delay: 200 },
      { slotId: "p3_chronology", text: "通行说：大觉寺始建于金章宗年间\n\n金章宗在位  1189 — 1208\n辽碑立年    1068\n\n▸ 碑比金章宗本人早了一百二十一年", size: 24, color: INK, weight: 800, lh: 1.6, backing: true, delay: 320 },
      { slotId: "p3_chronology_badge", kind: "tag", text: "时序否证 · 本集核心", backing: true, delay: 400 },
      { slotId: "p3_layer_note", text: "八院说可作金章宗确有西山营建的文化背景，\n但它是明人对辽金旧事的追述与归纳，\n不是金朝的原始文献。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 480 },
      { slotId: "p3_photo", kind: "photo", text: "帝京景物略大觉寺条书影（Page03 提供 PhotoSpec）" },
      { slotId: "p3_photo_tag", kind: "tag", text: "明万历间成书 · 追述层", backing: true },
    ],
  },
  // ── p04 为什么朝着西边（旸台山麓朝向拓扑 PanZoom）─────────────────────
  4: {
    design: 4,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p4_title", text: "为什么朝着西边？", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p4_map_tag", kind: "tag", text: "清代官绘舆图 · 旸台山麓", backing: true },
      { slotId: "p4_tag_dajuesi", kind: "tag", text: "大觉寺 · 坐西朝东", backing: true, delay: 90 },
      { slotId: "p4_tag_yangtai", kind: "tag", text: "旸台山", backing: true, delay: 170 },
      { slotId: "p4_card_badge", kind: "tag", text: "辽人尊日 · 建筑化石", backing: true },
      { slotId: "p4_card", text: "辽人尊日。契丹人相信太阳是生命与皇权的来源，\n东为阳，西为阴，面西朝日，是把对太阳的敬畏\n砌进了建筑朝向里。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 280 },
      { slotId: "p4_note", text: "今日地面殿宇为清代重修格局：\n无量寿佛殿 · 大悲坛 · 四宜堂。\n那道朝向，是从辽代院子里沿下来的。\n京城里找不出第二座这样坐西朝东的古刹。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 400 },
    ],
  },
  // ── p05 灵泉寺到大觉寺（日下旧闻考书影 + 寺名演变链）───────────────
  5: {
    design: 5,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p5_title", text: "寺名跟着时代换了三回", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p5_tag_source", kind: "tag", text: "清官书按语 · 钦定日下旧闻考", backing: true },
      { slotId: "p5_quote_1", text: "「大覺寺者金清水院故址，\n明以靈泉寺更名。」\n—— 乾隆御制重修大觉寺碑", size: 26, color: INK, weight: 800, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p5_quote_badge", kind: "tag", text: "三代叠加于一句碑文", backing: true, delay: 200 },
      { slotId: "p5_desc", text: "明宣德三年（1428）重建成寺，始名灵泉寺；\n宣宗赐名，改称大觉寺，沿用至今。\n正统十一年（1446）明英宗命工部右侍郎王祐督工重修。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 320 },
      { slotId: "p5_desc_badge", kind: "tag", text: "宣德赐名 · 正统督修", backing: true, delay: 400 },
      { slotId: "p5_chain", text: "清水院（辽）\n　↓ 明宣德三年重建\n灵泉寺（明宣德）\n　↓ 宣宗赐名\n大觉寺（明宣宗至今）", size: 24, color: INK, weight: 800, lh: 1.6, backing: true, delay: 480 },
      { slotId: "p5_photo", kind: "photo", text: "日下旧闻考卷一百六书影（Page05 提供 PhotoSpec）" },
      { slotId: "p5_photo_tag", kind: "tag", text: "御书四额 · 辽碑所在", backing: true },
    ],
  },
  // ── p06 三废三兴 ───────────────────────────────────────────────────
  6: {
    design: 6,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p6_title", text: "「今圯矣」：三废三兴的真实寺史", size: 39, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p6_tag_source", kind: "tag", text: "明人帝京景物略 · 清官书按语", backing: true },
      { slotId: "p6_quote_1", text: "「今圯矣。」\n—— 明人《帝京景物略》大觉寺条", size: 27, color: INK, weight: 800, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p6_quote_badge", kind: "tag", text: "明万历末年已废", backing: true, delay: 200 },
      { slotId: "p6_rebuilds", text: "清康熙五十九年（1720）尚在潜邸的雍正帝特加修葺；\n乾隆十二年（1747）发帑重修。\n一座曾湮灭的辽代小院，靠两代皇帝的手重新立起。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 320 },
      { slotId: "p6_rebuilds_badge", kind: "tag", text: "日下旧闻考按语直载", backing: true, delay: 400 },
      { slotId: "p6_plaques", text: "乾隆御书四额\n圆证妙果 · 无去来处 · 动静等观 · 最上法门", size: 25, color: INK, weight: 800, lh: 1.6, backing: true, delay: 480 },
      { slotId: "p6_photo", kind: "photo", text: "无量寿佛殿实拍（Page06 提供 PhotoSpec）" },
      { slotId: "p6_photo_tag", kind: "tag", text: "额曰动静等观", backing: true },
    ],
  },
  // ── p07 今天的遗存与国保现状 ──────────────────────────────────────
  7: {
    design: 7,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p7_title", text: "国保第六批：今天仍在开放", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p7_tag_status", kind: "tag", text: "现代机构口径 · 现状单独核查", backing: true },
      { slotId: "p7_relics", text: "寺内龙王堂，存辽碑一通（僧志延撰，咸雍四年立）；\n寺旁有僧性音塔，是雍正年间那位住持的墓塔；\n四宜堂前白玉兰一株，为寺中最有名的景致。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 140 },
      { slotId: "p7_relics_badge", kind: "tag", text: "遗存三事", backing: true, delay: 220 },
      { slotId: "p7_uncertain", text: "存疑：白玉兰是辽植还是清植，各家说法不一，\n没有文献与树木档案可以作证——\n本片不作断语。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 340 },
      { slotId: "p7_uncertain_badge", kind: "tag", text: "存疑不列年代 · 证据纪律", backing: true, delay: 420 },
      { slotId: "p7_status", text: "二〇〇六年五月，列入第六批全国重点文物保护单位，\n今天对外开放。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 500 },
      { slotId: "p7_photo", kind: "photo", text: "大觉寺殿宇实拍（Page07 提供 PhotoSpec）" },
      { slotId: "p7_photo_tag", kind: "tag", text: "国保第六批 · 2006", backing: true },
    ],
  },
  // ── p08 一座寺，两个名字，三次重生（四时代叠合图）──────────────────
  8: {
    design: 8,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p8_title", text: "一座寺，两个名字，三次重生", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p8_layer_tag", kind: "tag", text: "时代叠合 · 制作组示意 · 非测绘拓扑", backing: true },
      { slotId: "p8_tag_liao", kind: "tag", text: "辽 · 清水院", backing: true, delay: 60 },
      { slotId: "p8_tag_ming", kind: "tag", text: "明 · 灵泉寺至大觉寺", backing: true, delay: 90 },
      { slotId: "p8_tag_qing", kind: "tag", text: "清 · 御笔重修", backing: true, delay: 120 },
      { slotId: "p8_tag_modern", kind: "tag", text: "今 · 国保古刹", backing: true, delay: 150 },
      { slotId: "p8_sum_left", text: "一块一〇六八年的石碑，\n比关于它的所有传说都早两百年。", size: 27, color: INK, weight: 800, lh: 1.55, backing: true, delay: 300 },
      { slotId: "p8_sum_right", text: "地名会改，碑会立，\n可总有些东西，留在了原地。", size: 26, color: INK, weight: 800, lh: 1.55, backing: true, delay: 460 },
    ],
  },
};
