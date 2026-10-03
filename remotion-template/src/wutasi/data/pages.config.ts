// pages.config.ts — E25《五塔寺·把塔的落成年错当成寺的始建年》逐页槽位文案与样式.
// 唯一规格书：docs/superpowers/specs/2026-10-04-e25-wutasi-design.md（APPROVED）
// ＋ wutasi_video/research.md v1.0.
// 板型：MapPage 0（全片八页皆为 MixedPage；1915 切片在 P1 作索引底图内嵌）
//      ＋ MixedPage 8（P1 索引 / P2 石匾 / P3 实录 / P4 永乐创寺 / P5 成化成塔 / P6 形制 / P7 国保 / P8 叠合）。
// 槽位几何见 slots.json（plate 全部 1920×1080 设计空间 = 画布 1:1）。
// 🔴 E24 教训：屏显纪年一律用全字形汉字（三位/四位不上小字号屏显，只留相对量），
//    禁 U+3007 圆圈数字（宋体下不可见 → OCR 漏读）。
// V-NC01 严禁「五塔寺建于明成化九年」；V-NC02 石匾只证塔；V-NC05 国保第一批不引编号。
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
  // ── p01 塔上的匾，写的是塔的名字 ────────────────────────────────
  1: {
    design: 1,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p1_title", text: "五塔寺 · 把塔的落成年错当成寺的始建年", size: 38, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p1_sub", text: "一方石匾 · 三个被压成一个的时间", size: 24, color: INK, weight: 700, lh: 1.3, backing: true },
      { slotId: "p1_tag_index", kind: "tag", text: "长河北岸索引 · 制作组示意", backing: true },
      { slotId: "p1_tag_pagoda", kind: "tag", text: "真觉寺金刚宝座塔", backing: true, delay: 60 },
      { slotId: "p1_tag_changhe", kind: "tag", text: "长河北岸", backing: true, delay: 120 },
      { slotId: "p1_tag_baishiqiao", kind: "tag", text: "白石桥", backing: true, delay: 180 },
      { slotId: "p1_tag_village", kind: "tag", text: "五塔寺村", backing: true, delay: 240 },
      { slotId: "p1_question", text: "券门石匾明载「成化九年造」，\n为何读成「寺建于成化九年」？", size: 28, color: INK, weight: 800, lh: 1.45, backing: true, delay: 300 },
      { slotId: "p1_truth", text: "可匾上写的是「造金刚宝座」——\n金刚宝座是塔，不是寺。\n寺的来历，要早这块匾几十年。", size: 26, color: INK, weight: 800, lh: 1.55, backing: true, delay: 440 },
      { slotId: "p1_photo", kind: "photo", text: "券门石匾特写（Page01 提供 PhotoSpec）" },
    ],
  },
  // ── p02 一方石匾的逐字解读（核心证据页）──────────────────────────
  2: {
    design: 2,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p2_title", text: "石匾上写的是「金刚宝座」", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p2_tag_stele", kind: "tag", text: "一手金石实物 · 券门石匾至今嵌于原处", backing: true },
      { slotId: "p2_quote_1", text: "「敕建金刚宝座\n大明成化九年十一月初二造」", size: 30, color: INK, weight: 800, lh: 1.6, backing: true, delay: 120 },
      { slotId: "p2_quote_badge", kind: "tag", text: "逐字释读", backing: true, delay: 200 },
      { slotId: "p2_reading", text: "「敕建」＝官修工程，非民间营建。\n「金刚宝座」四字指塔的形制。\n匾的通篇，没有出现过一个「寺」字。\n最后那个「造」，造的是这尊塔。", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 320 },
      { slotId: "p2_verdict", text: "一方石匾，只记了它自己落成的那一年。\n它从不记录自己依傍的那座寺。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 440 },
      { slotId: "p2_verdict_badge", kind: "tag", text: "石匾只证塔，不证寺", backing: true, delay: 520 },
      { slotId: "p2_photo", kind: "photo", text: "券门石匾逐字放大图（Page02 提供 PhotoSpec）" },
      { slotId: "p2_photo_tag", kind: "tag", text: "一手实物 · 通篇无「寺」字", backing: true },
    ],
  },
  // ── p03 塔年 ≠ 寺年（《明宪宗实录》书影 + 时序分岔）────────────────
  3: {
    design: 3,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p3_title", text: "塔年 ≠ 寺年", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p3_tag_shilu", kind: "tag", text: "一手正史 · 明宪宗实录卷一百二十", backing: true },
      { slotId: "p3_quote_1", text: "「成化九年冬十一月，\n真觉寺金刚宝座**塔**成，\n赐名**大觉金刚宝座**。」", size: 27, color: INK, weight: 800, lh: 1.6, backing: true, delay: 120 },
      { slotId: "p3_quote_badge", kind: "tag", text: "实录与石匾互证到月", backing: true, delay: 200 },
      { slotId: "p3_landing", text: "请注意这句话的落点：\n「塔」成，不是寺成；\n所赐之名是「大觉金刚宝座」——\n那是塔的名号，不是寺名。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 320 },
      { slotId: "p3_fork", text: "寺：永乐初年敕建（西域僧人进献印度塔式）\n塔：成化九年落成（实录＋石匾双证）\n▸ 两者相隔数十年", size: 24, color: INK, weight: 800, lh: 1.6, backing: true, delay: 440 },
      { slotId: "p3_fork_badge", kind: "tag", text: "塔寺时序分岔 · 本集核心", backing: true, delay: 520 },
      { slotId: "p3_photo", kind: "photo", text: "明宪宗实录书影（Page03 提供 PhotoSpec）" },
      { slotId: "p3_photo_tag", kind: "tag", text: "原书卷一百二十", backing: true },
    ],
  },
  // ── p04 永乐初年：西域僧人与印度图样 ─────────────────────────────
  4: {
    design: 4,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p4_title", text: "永乐初年：西域僧人与一幅印度图样", size: 38, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p4_tag_source", kind: "tag", text: "御制碑记与景物略所记 · 寺的创基", backing: true },
      { slotId: "p4_buddha", text: "西域高僧班迪达大国师来到北京，\n进献金身佛像五尊，\n还进献一份图样——\n印度佛陀迦耶精舍（大菩提寺）的金刚宝座样式。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 140 },
      { slotId: "p4_buddha_badge", kind: "tag", text: "进献金佛与塔式", backing: true, delay: 220 },
      { slotId: "p4_grant", text: "明成祖封其为大国师，\n择址京城西关外敕建寺院，\n赐名「真觉寺」。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 340 },
      { slotId: "p4_grant_badge", kind: "tag", text: "敕建真觉寺", backing: true, delay: 420 },
      { slotId: "p4_legacy", text: "寺，是为了安奉这批金佛与图样而设的。\n它比塔早，不止一代人。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 500 },
      { slotId: "p4_legacy_badge", kind: "tag", text: "寺的创基：永乐初年", backing: true },
    ],
  },
  // ── p05 断续数十年的一处工程 ────────────────────────────────────
  5: {
    design: 5,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p5_title", text: "工程一度搁置，绵延数朝", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p5_tag_source", kind: "tag", text: "御制记略与实录互证", backing: true },
      { slotId: "p5_desc", text: "从永乐到成化，中间隔着明朝的鼎盛，\n也隔着它的动荡。\n土木之变之后，朝局几度翻覆，\n寺与塔的工程一度搁置，一停就是几十年。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 140 },
      { slotId: "p5_desc_badge", kind: "tag", text: "永乐至成化的空档", backing: true, delay: 220 },
      { slotId: "p5_build", text: "到成化九年，太监钱义等人奉敕主持，\n才真正动土，依着中印度样式，\n「累石为台五丈」，把这座金刚宝座塔建成了。", size: 25, color: INK, weight: 800, lh: 1.5, backing: true, delay: 340 },
      { slotId: "p5_build_badge", kind: "tag", text: "成化九年 · 塔成", backing: true, delay: 420 },
      { slotId: "p5_note", text: "塔用了这么久才落成——\n这不是一朝一夕的工程，而是几代人接力的事。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 500 },
    ],
  },
  // ── p06 五座密檐小塔，四种文字 ──────────────────────────────────
  6: {
    design: 6,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p6_title", text: "五座密檐小塔，四种文字", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p6_tag_form", kind: "tag", text: "形制解构", backing: true },
      { slotId: "p6_form", text: "仿印度佛陀迦耶精舍式样：\n方形须弥座上立五座密檐小塔，\n合称金刚宝座。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 140 },
      { slotId: "p6_form_badge", kind: "tag", text: "中国现存最早 · 雕刻最精美", backing: true, delay: 220 },
      { slotId: "p6_script", text: "塔座四壁遍刻\n梵文、藏文、蒙文、阿拉伯文，\n是我国现存最早的多语种石刻之一。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 340 },
      { slotId: "p6_script_badge", kind: "tag", text: "多语种石刻", backing: true, delay: 420 },
      { slotId: "p6_uncertain", text: "存疑：土人因见塔顶五座小塔而称「五塔寺」，\n但这个俗名具体是哪一年叫开的，\n没有书证——本片不给它系年。", size: 24, color: INK, weight: 800, lh: 1.5, backing: true, delay: 500 },
      { slotId: "p6_photo", kind: "photo", text: "塔座多语种石刻特写（Page06 提供 PhotoSpec）" },
      { slotId: "p6_photo_tag", kind: "tag", text: "梵 · 藏 · 蒙 · 阿", backing: true },
    ],
  },
  // ── p07 第一批国保：塔成了博物馆的院墙 ───────────────────────────
  7: {
    design: 7,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p7_title", text: "第一批国保：塔成了博物馆的院墙", size: 38, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p7_tag_status", kind: "tag", text: "现代机构口径 · 现状单独核查", backing: true },
      { slotId: "p7_status", text: "今天的真觉寺遗址，只剩这一座塔还在。\n一九六一年三月四日，国务院公布\n第一批全国重点文物保护单位，\n真觉寺金刚宝座塔列名。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 140 },
      { slotId: "p7_status_badge", kind: "tag", text: "第一批国保 · 一九六一年三月四日", backing: true, delay: 220 },
      { slotId: "p7_museum", text: "塔的周围，建起了北京石刻艺术博物馆，\n收藏着北京的碑碣、墓志、石雕。\n今天你去五塔寺村，看到的是\n一座塔、一座博物馆，和一座旧寺影。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 340 },
      { slotId: "p7_museum_badge", kind: "tag", text: "北京石刻艺术博物馆", backing: true, delay: 420 },
      { slotId: "p7_numbering", text: "附带说明：一九六一年第一批国保\n还没有后来的编号体系，\n所以本片不引用任何编号。", size: 24, color: INK, weight: 800, lh: 1.5, backing: true, delay: 500 },
      { slotId: "p7_photo", kind: "photo", text: "塔与博物馆共存实拍（Page07 提供 PhotoSpec）" },
      { slotId: "p7_photo_tag", kind: "tag", text: "首批国保 · 五塔寺村", backing: true },
    ],
  },
  // ── p08 三个时间，一方石匾（四时代叠合图）──────────────────────
  8: {
    design: 8,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p8_title", text: "三个时间，一方石匾", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p8_layer_tag", kind: "tag", text: "时代叠合 · 制作组示意 · 非测绘拓扑", backing: true },
      { slotId: "p8_tag_yongle", kind: "tag", text: "永乐 · 敕建真觉寺", backing: true, delay: 60 },
      { slotId: "p8_tag_chenghua", kind: "tag", text: "成化 · 金刚宝座塔成", backing: true, delay: 90 },
      { slotId: "p8_tag_qing", kind: "tag", text: "清 · 民间称五塔寺", backing: true, delay: 120 },
      { slotId: "p8_tag_modern", kind: "tag", text: "今 · 首批国保博物馆", backing: true, delay: 150 },
      { slotId: "p8_sum_left", text: "寺、塔、村、名，四个层次，\n最后被一方石匾压成了一年。", size: 27, color: INK, weight: 800, lh: 1.55, backing: true, delay: 300 },
      { slotId: "p8_sum_right", text: "石匾忠实地记下了它自己造完的那天，\n却从不记得它所依傍的那座寺。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 460 },
    ],
  },
};
