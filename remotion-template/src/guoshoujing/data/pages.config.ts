// pages.config.ts — E29《郭守敬·一泉入都》逐页槽位文案与样式.
// 唯一规格书：guoshoujing_video/research.md v1.0（§3 八页结构）.
// 板型：全片八页皆为 MixedPage。
// 槽位几何见 slots.json（plate 全部 1920×1080 设计空间 = 画布 1:1）。
// 🔴 屏显纪律：全字形汉字纪年（「一二三一年」可）；禁 U+3007；禁阿拉伯公历上屏；
//    屏显数字 ⊆ 当页口播数字（reign-year 并行剥离口径与 qa_v2.normalize 一致）。
// V-NC01 通惠河为郭守敬建言并主持（三证闭环），无原文的翻案说法不进正片；
// V-NC02 「长河是郭守敬所开」禁说——河道先在，他只是系统化利用；
// V-NC03 禁「泽被六百年/至今仍在供水」——延祐元年已源泉微细不能通流；
// V-NC04 回归年原文是「三百六十五日二十四刻二十五分」，禁「精确到小数点后四位」；
// V-NC05 四海测验为 27 所定点测影（穷举名单），今海淀无站，无西藏/云南站点；
// V-NC06 「以海平面比较地形高差的思想」可说，「发明海拔」禁说；
// V-NC07 古代地望与现代地名分层（瓮山泊≠1750 昆明湖）。
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
  // ── p01 片头·一泉入都 ──────────────────────────────────────────
  1: {
    design: 1,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p1_title", text: "郭守敬 · 一泉入都", size: 42, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p1_tag_series", kind: "tag", text: "一泉入都 · 收束集", backing: true },
      { slotId: "p1_hook", text: "昌平的泉眼早已干涸，\n大都的湖面曾挤满漕船。\n把这两件事连起来的，是一个人。", size: 28, color: INK, weight: 800, lh: 1.45, backing: true, delay: 300 },
      { slotId: "p1_nine", text: "九个石雕龙头，今天滴不出一滴水", size: 24, color: INK, weight: 700, lh: 1.4, backing: true, delay: 420 },
      { slotId: "p1_gap", text: "泉在昌平，湖在海淀，船在什刹海。\n七百年前，这三处被一条渠连成一气。", size: 26, color: INK, weight: 800, lh: 1.55, backing: true, delay: 520 },
      { slotId: "p1_tag_hook", kind: "tag", text: "海淀诸水的总设计师", backing: true, delay: 620 },
      { slotId: "p1_photo_gate", kind: "photo", text: "九龙池干涸龙首示意（Page01 提供 PhotoSpec）" },
    ],
  },
  // ── p02 邢台来的年轻人 ────────────────────────────────────────
  2: {
    design: 2,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p2_title", text: "邢台来的年轻人", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p2_tag_source", kind: "tag", text: "一手正史 · 《元史·郭守敬传》", backing: true },
      { slotId: "p2_birth", text: "郭守敬，字若思，生于一二三一年。\n祖父郭荣通五经、精算数水利；\n少年从刘秉忠学于紫金山。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p2_liushi", text: "中统三年，面陈水利六事。\n头一件：引玉泉水以通舟——\n玉泉山，就在今天的海淀。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 260 },
      { slotId: "p2_note", text: "「巧思绝人」是《元史》给他的考语。\n此议并无下文，\n不得说成「当年就通了」。", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 400 },
      { slotId: "p2_tag_yuquan", kind: "tag", text: "海淀锚点 · 玉泉首想", backing: true, delay: 520 },
      { slotId: "p2_photo_folio", kind: "photo", text: "元史·郭守敬传六事条书影（Page02 提供 PhotoSpec）" },
    ],
  },
  // ── p03 测天之前·先造仪器 ────────────────────────────────────
  3: {
    design: 3,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p3_title", text: "测天之前，先造仪器", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p3_quote", text: "「曆之本在於測驗，而測驗之器莫先儀表」", size: 27, color: INK, weight: 800, lh: 1.45, backing: true },
      { slotId: "p3_instruments", text: "简仪、高表、景符，成批创制。\n旧浑仪是皇祐年间汴京所造，\n比量大都天度，约差四度。", size: 25, color: INK, weight: 700, lh: 1.55, backing: true, delay: 200 },
      { slotId: "p3_mingcopy", text: "郭守敬原件没有留到今天。\n南京紫金山天文台那架简仪，\n是明正统年间依旧制仿制的。", size: 25, color: INK, weight: 700, lh: 1.55, backing: true, delay: 340 },
      { slotId: "p3_tag_verdict", kind: "tag", text: "先有仪表后有历法", backing: true, delay: 480 },
      { slotId: "p3_photo_jianyi", kind: "photo", text: "简仪结构示意（Page03 提供 PhotoSpec）" },
    ],
  },
  // ── p04 四海测验·二十七所 ────────────────────────────────────
  4: {
    design: 4,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p4_title", text: "四海测验 · 凡二十七所", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p4_quote", text: "「東至高麗，西極滇池，南踰朱崖，北盡鐵勒，四海測驗，凡二十七所。」", size: 26, color: INK, weight: 800, lh: 1.5, backing: true },
      { slotId: "p4_stat", text: "二十七个定点测影站，测晷影与北极出地；\n不测地理，未测长城，未进西藏。", size: 25, color: INK, weight: 700, lh: 1.55, backing: true, delay: 200 },
      { slotId: "p4_haidian", text: "名单无西藏站点，无云南站点；\n今海淀境内，无一站。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 320 },
      { slotId: "p4_dengfeng", text: "登封观星台，元代遗构，\n即二十七所之「河南府陽城」站。", size: 25, color: INK, weight: 700, lh: 1.55, backing: true, delay: 440 },
      { slotId: "p4_tag_city", kind: "tag", text: "观天在城内 · 引水才经过海淀", backing: true, delay: 560 },
      { slotId: "p4_photo_tai", kind: "photo", text: "登封观星台示意（Page04 提供 PhotoSpec）" },
      { slotId: "p4_photo_27", kind: "photo", text: "二十七所北极出地排布示意（Page04 提供 PhotoSpec）" },
    ],
  },
  // ── p05 一年的长度 ────────────────────────────────────────────
  5: {
    design: 5,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p5_title", text: "一年的长度", size: 42, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p5_quote", text: "「每歲合得三百六十五日二十四刻二十五分」", size: 27, color: INK, weight: 800, lh: 1.45, backing: true },
      { slotId: "p5_conv", text: "百刻制换算：二十四刻二十五分\n＝万分之二千四百二十五日\n＝三百六十五点二四二五日", size: 25, color: INK, weight: 700, lh: 1.55, backing: true, delay: 200 },
      { slotId: "p5_banxing", text: "至元十七年历成，赐名授时历；\n其年冬，颁行天下——不是次年。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 340 },
      { slotId: "p5_tag_calc", kind: "tag", text: "据现代学者换算 · 原文无小数", backing: true, delay: 480 },
      { slotId: "p5_gregory", text: "同一数值的行用，早于格里历约三百年", size: 24, color: INK, weight: 700, lh: 1.4, backing: true, delay: 580 },
      { slotId: "p5_photo_folio", kind: "photo", text: "元史·歲餘条书影（Page05 提供 PhotoSpec）" },
    ],
  },
  // ── p06 白浮泉引水·全线 ──────────────────────────────────────
  6: {
    design: 6,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p6_title", text: "白浮泉引水 · 全线", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p6_quote", text: "「別引北山白浮泉水，西折而南，經瓮山泊，自西水門入城，環匯於積水潭」", size: 26, color: INK, weight: 800, lh: 1.5, backing: true },
      { slotId: "p6_route", text: "上自昌平县白浮村引神山泉，\n东至通州高丽庄入白河；\n首事至元二十九年春，告成至元三十年秋，赐名通惠河。", size: 25, color: INK, weight: 700, lh: 1.55, backing: true, delay: 200 },
      { slotId: "p6_length", text: "总长一百六十四里一百四步；\n每十里置一牐，比至通州，凡为牐七。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 340 },
      { slotId: "p6_guangyuan", text: "广源闸为壩牐之首，元代建置，\n今在海淀紫竹院街道。", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 480 },
      { slotId: "p6_tag_schematic", kind: "tag", text: "制作组示意 · 非测绘拓扑", backing: true, delay: 600 },
      { slotId: "p6_photo_route", kind: "photo", text: "白浮泉引水线路示意（Page06 提供 PhotoSpec）" },
    ],
  },
  // ── p07 湮没·以及一条被冤枉的河 ──────────────────────────────
  7: {
    design: 7,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p7_title", text: "湮没 · 以及一条被冤枉的河", size: 38, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p7_chain", text: "大德七年，山水暴涨冲决水口；\n大德十一年，河堤崩三十余里；\n皇庆元年征工修治；延祐元年，上源淤塞。", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 140 },
      { slotId: "p7_quote", text: "「多淤澱淺塞，源泉微細，不能通流」\n——延祐元年，郭守敬卒前两年", size: 24, color: INK, weight: 800, lh: 1.5, backing: true, delay: 280 },
      { slotId: "p7_qianlong", text: "乾隆己巳考源，御制文自承：时皆湮没不可详", size: 23, color: INK, weight: 700, lh: 1.4, backing: true, delay: 400 },
      { slotId: "p7_changhe", text: "长河不是他开的：河道先在（高梁河故道），\n他做的，是把昌平泉水引进来；\n「长河」作为地名，清代才叫开。", size: 24, color: INK, weight: 800, lh: 1.55, backing: true, delay: 520 },
      { slotId: "p7_baifu", text: "白浮泉今在昌平龙山，不在海淀；\n九龙池九个龙头，无自然涌泉。", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 640 },
      { slotId: "p7_photo_yanyou", kind: "photo", text: "元史·延祐元年条书影（Page07 提供 PhotoSpec）" },
      { slotId: "p7_photo_chain", kind: "photo", text: "衰败链时间轴（Page07 提供 PhotoSpec）" },
    ],
  },
  // ── p08 收束·他把水留给海淀 ──────────────────────────────────
  8: {
    design: 8,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p8_title", text: "他把水留给海淀", size: 42, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p8_tag_summary", kind: "tag", text: "观天无海淀 · 喝水全靠海淀", backing: true },
      { slotId: "p8_three", text: "行状定评：不可及者有三——\n水利之学，历数之学，仪象制度之学。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 140 },
      { slotId: "p8_haiba", text: "行状又记：以海平面比较京师至汴梁地形高差。\n这是思想的萌芽——不是发明海拔。", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 280 },
      { slotId: "p8_legacy", text: "海淀境内的实物遗存：广源闸与一段故道；\n玉泉双线：御用金水河，济漕入瓮山泊；\n观天的台，一座也不在海淀。", size: 24, color: INK, weight: 700, lh: 1.55, backing: true, delay: 420 },
      { slotId: "p8_sum", text: "泉死得比人早。\n水，留给了海淀。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 560 },
      { slotId: "p8_photo_veins", kind: "photo", text: "水脉终图（Page08 提供 PhotoSpec）" },
    ],
  },
};
