// pages.config.ts — E21《魏公村·高梁河畔的畏吾村》逐页槽位文案与样式。
// 唯一规格书：docs/superpowers/specs/2026-10-03-e21-weigongcun-design.md（APPROVED）
// ＋ weigongcun_video/research.md v1.0（考据修正：元史卷126 无「畏吾村」字样，
//    葬地书证以 元明善神道碑「葬于宛平之西原」＋查礼/乔松年考据 为准）。
// 板型：MapPage 3（P3 三山五园图 PanZoom / P6 1915 实测图 PanZoom / P8 四时代叠合）
//      ＋ MixedPage 5（P1 街区索引 / P2 元史书影 / P4 大慧寺 / P5 演变链 / P7 民院建校）。
// 槽位几何见 slots.json（plate 全部 1920×1080 设计空间 = 画布 1:1）。
// 红线：浮在地图/照片上方的文字项一律 backing: true（卡纸垫 rgba(247,240,223,0.95)）；
// 屏显数字 ⊆ 当页口播（1280/17/11/50/1513/2001/199/1915/1951/700/56）；标记圈/点位
// 纯 SVG 叠加不入槽表；全幅视口由页面打底不占槽位；photo 槽一律 kind:"photo"。
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
  // ── p01 今天的魏公村（街区索引示意打底 + 民大东门实拍镜框）──────
  1: {
    design: 1,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p1_title", text: "魏公村 · 高梁河畔的畏吾村", size: 42, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p1_sub", text: "七百年族源公案 · 一个村庄的民族记忆", size: 23, color: INK, weight: 700, lh: 1.3, backing: true },
      { slotId: "p1_index_tag", kind: "tag", text: "现代街区索引 · MEC-4 制作组示意", backing: true },
      { slotId: "p1_tag_lib", kind: "tag", text: "国家图书馆", backing: true, delay: 60 },
      { slotId: "p1_tag_minzu", kind: "tag", text: "中央民族大学", backing: true, delay: 90 },
      { slotId: "p1_tag_metro", kind: "tag", text: "魏公村地铁站", backing: true, delay: 120 },
      { slotId: "p1_tag_village", kind: "tag", text: "畏吾村故址 · 方位示意", backing: true, delay: 150 },
      { slotId: "p1_case", text: "「魏公村」，到底是不是\n一位姓魏的公公留下的村子？", size: 30, color: INK, weight: 800, lh: 1.45, backing: true, delay: 260 },
      { slotId: "p1_truth", text: "它原本的名字，叫「畏吾村」——\n与「魏」字无关，得从元朝说起。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 420 },
      { slotId: "p1_photo", kind: "photo", text: "民大东门今貌镜框（Page01 提供 PhotoSpec）" },
    ],
  },
  // ── p02 1280：廉孟子（《元史》书影 + 正史列传卡）────────────────
  2: {
    design: 2,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p2_title", text: "1280：忽必烈身边的「廉孟子」", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p2_bio", text: "廉希宪 · 字善甫 · 西域高昌畏兀儿人\n元世祖忽必烈的名相 · 官至中书平章政事", size: 25, color: INK, weight: 700, lh: 1.5, backing: true, delay: 120 },
      { slotId: "p2_bio_badge", kind: "tag", text: "正史列传 · 元史卷一百二十六", backing: true },
      { slotId: "p2_quote", text: "「帝尝以『廉孟子』称之。\n至元十七年十一月卒，年五十。」", size: 30, color: INK, weight: 800, lh: 1.55, backing: true, delay: 330 },
      { slotId: "p2_quote_badge", kind: "tag", text: "一手书证 · 《元史·廉希宪传》", backing: true },
      { slotId: "p2_end", text: "一位出身畏兀儿的名相，身后归葬大都城西——\n守墓的族人，将叫响一个村名。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 560 },
      { slotId: "p2_photo", kind: "photo", text: "元史廉希宪传书影镜框（Page02 提供 PhotoSpec）" },
      { slotId: "p2_photo_tag", kind: "tag", text: "正史刊本书影 · VEC-1", backing: true },
    ],
  },
  // ── p03 高梁河畔的归宿（三山五园图 PanZoom + 神道碑引文横幅）────
  3: {
    design: 3,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p3_title", text: "高梁河畔的归宿", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p3_map_tag", kind: "tag", text: "《三山五园图》高梁河一带 · MEC-1", backing: true },
      { slotId: "p3_tag_river", kind: "tag", text: "高梁河（今南长河）水道", backing: true, delay: 40 },
      { slotId: "p3_tag_site", kind: "tag", text: "畏吾村故址 · 方位示意", backing: true, delay: 200 },
      { slotId: "p3_banner", text: "「葬于宛平之西原」", size: 46, color: INK, weight: 800, lh: 1.35, backing: true, delay: 330 },
      { slotId: "p3_banner_badge", kind: "tag", text: "神道碑 · 元明善撰", backing: true },
      { slotId: "p3_note", text: "大都城西 · 高梁河畔的台地", size: 22, color: SOFT, weight: 700, lh: 1.3, backing: true },
      { slotId: "p3_chali", text: "乾隆学者查礼《畏吾村考》：\n「守冢者亦廉姓，疑即右丞后人。」", size: 24, color: INK, weight: 800, lh: 1.5, backing: true, delay: 480 },
      { slotId: "p3_chali_badge", kind: "tag", text: "文献记载 · 清人考据", backing: true },
      { slotId: "p3_qiao", text: "乔松年《萝藦亭札记》：\n畏吾村「本西域畏吾部落」", size: 24, color: INK, weight: 800, lh: 1.5, backing: true, delay: 620 },
      { slotId: "p3_qiao_badge", kind: "tag", text: "文献记载 · 清人札记", backing: true },
    ],
  },
  // ── p04 明代的印记（大慧寺实拍 + 张雄建寺 + 李东阳祖茔）────────
  4: {
    design: 4,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p4_title", text: "明代：宛平县香山乡畏吾村", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p4_card1", text: "正德八年（1513），司礼监太监张雄\n在村里建起大慧寺。", size: 28, color: INK, weight: 800, lh: 1.5, backing: true, delay: 150 },
      { slotId: "p4_card1_badge", kind: "tag", text: "官书考订 · 《日下旧闻考》卷九十八", backing: true },
      { slotId: "p4_card2", text: "内阁首辅李东阳《怀麓堂集》：\n「宛平县香山乡畏吾村，吾祖茔也。」\n曾祖考妣，即葬于此。", size: 27, color: INK, weight: 800, lh: 1.5, backing: true, delay: 420 },
      { slotId: "p4_card2_badge", kind: "tag", text: "文集书证 · 李东阳《怀麓堂集》", backing: true },
      { slotId: "p4_guobao", text: "2001 年，大慧寺以第五批第 199 号\n列入全国重点文物保护单位。", size: 26, color: INK, weight: 800, lh: 1.45, backing: true, delay: 640 },
      { slotId: "p4_guobao_badge", kind: "tag", text: "现行 · 官方口径", backing: true },
      { slotId: "p4_wei", text: "距魏忠贤当权尚有百余年——把村子记在他名下，实在冤枉。", size: 22, color: SOFT, weight: 700, lh: 1.35, backing: true, delay: 700 },
      { slotId: "p4_photo", kind: "photo", text: "大慧寺大悲宝殿镜框（Page04 提供 PhotoSpec）" },
      { slotId: "p4_photo_tag", kind: "tag", text: "全国重点文物保护单位 · 编号5-199", backing: true },
    ],
  },
  // ── p05 从「畏吾」到「魏公」（演变链 + 双轨道解构）──────────────
  5: {
    design: 5,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p5_title", text: "从「畏吾」到「魏公」：双重合流", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p5_chain_tag", kind: "tag", text: "演变脉络 · MEC-4 制作组示意", backing: true },
      { slotId: "p5_n1", text: "元明 · 畏吾村", size: 24, color: INK, weight: 800, lh: 1.3, backing: true, delay: 130 },
      { slotId: "p5_n2", text: "清 · 畏兀村（俗写）", size: 24, color: INK, weight: 800, lh: 1.3, backing: true, delay: 210 },
      { slotId: "p5_n3", text: "民国 · 魏公村", size: 24, color: INK, weight: 800, lh: 1.3, backing: true, delay: 290 },
      { slotId: "p5_trackA", text: "轨道一 · 音转\n「畏吾」二字的京腔口传，\n离「魏公」只有一步之遥。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 420 },
      { slotId: "p5_trackA_badge", kind: "tag", text: "音转 · 语言层", backing: true },
      { slotId: "p5_trackB", text: "轨道二 · 爵位\n廉希宪身后追封魏国公，\n爵号与转音在此重合。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 560 },
      { slotId: "p5_trackB_badge", kind: "tag", text: "爵位 · 史册层", backing: true },
      { slotId: "p5_merge", text: "市井的口耳相传，与史册里的显赫爵位，\n在这里完成了一次双重合流。", size: 28, color: INK, weight: 800, lh: 1.5, backing: true, delay: 640 },
    ],
  },
  // ── p06 1915：实测地图的定格（1915 实测京西图 PanZoom）─────────
  6: {
    design: 6,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p6_title", text: "1915：实测地图的定格", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p6_arch_tag", kind: "tag", text: "民国档案 · 北洋陆军测地局《实测京师四郊图》", backing: true },
      { slotId: "p6_tag_road", kind: "tag", text: "南北大道 · 今中关村南大街一带", backing: true, delay: 60 },
      { slotId: "p6_tag_vc", kind: "tag", text: "魏公村 · 1915 定名", backing: true, delay: 260 },
      { slotId: "p6_tag_dahui", kind: "tag", text: "大慧寺 · 明代古刹", backing: true, delay: 330 },
      { slotId: "p6_card", text: "京西图幅上，「魏公村」三个字\n端端正正印在高梁河旁；\n畏吾村、畏兀村的种种旧写，\n从此定格为官方测绘档案。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 470 },
      { slotId: "p6_card_badge", kind: "tag", text: "一手实测档案 · 测绘定型", backing: true },
    ],
  },
  // ── p07 1951：历史的巧合与时代的相逢（民院档案照 + 相逢卡）──────
  7: {
    design: 7,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p7_title", text: "1951：同一片土地上的时代重逢", size: 38, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p7_fact", text: "1951 年，中央民族学院\n选址白石桥以北、魏公村一带建校。", size: 27, color: INK, weight: 800, lh: 1.5, backing: true, delay: 150 },
      { slotId: "p7_fact_badge", kind: "tag", text: "建校档案 · 中央民族学院", backing: true },
      { slotId: "p7_echo", text: "七百年前，西域高昌的畏兀儿人\n在这片土地上聚族而居；\n七百年后，五十六个民族的学子同窗共读。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 380 },
      { slotId: "p7_echo_badge", kind: "tag", text: "空间相逢 · 从畏吾村到民族大学", backing: true },
      { slotId: "p7_concl", text: "这不是巧合——\n是历史在同一片泥土上的深情回响。", size: 28, color: INK, weight: 800, lh: 1.5, backing: true, delay: 620 },
      { slotId: "p7_photo", kind: "photo", text: "中央民族学院建校初期影像镜框（Page07 提供 PhotoSpec）" },
      { slotId: "p7_photo_tag", kind: "tag", text: "建校初期影像 · VEC-2", backing: true },
      { slotId: "p7_now", text: "昔日畏兀儿守冢者的坟茔台地，\n今日各民族学子的共同校园。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 560 },
    ],
  },
  // ── p08 七百年，一座活着的纪念碑（四时代叠合收官）──────────────
  8: {
    design: 8,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p8_title", text: "七百年，一座活着的纪念碑", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p8_map_tag", kind: "tag", text: "四时代叠合 · MEC-4 制作组示意 · 非测绘拓扑", backing: true },
      { slotId: "p8_era1", kind: "tag", text: "元 · 畏吾村墓原", backing: true, delay: 250 },
      { slotId: "p8_era2", kind: "tag", text: "明 · 佛刹与村落", backing: true, delay: 300 },
      { slotId: "p8_era3", kind: "tag", text: "清 · 长河水道", backing: true, delay: 350 },
      { slotId: "p8_era4", kind: "tag", text: "今 · 高校街区", backing: true, delay: 400 },
      { slotId: "p8_concl", text: "「魏」字背后，并没有姓魏的人，\n只有一支西域部族融入北京的足迹。", size: 30, color: INK, weight: 800, lh: 1.5, backing: true, delay: 560 },
      { slotId: "p8_end", text: "地名，是一座活着的纪念碑。", size: 30, color: INK, weight: 800, lh: 1.35, backing: true, delay: 620 },
    ],
  },
};
