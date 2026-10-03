// pages.config.ts — E23《挂甲屯·杨六郎传说与清初额驸城》逐页槽位文案与样式.
// 唯一规格书：docs/superpowers/specs/2026-10-03-e23-guajiatun-design.md（APPROVED）
// ＋ guajiatun_video/research.md v1.0。
// 板型：MapPage 3（P4 畅春园西侧 PanZoom / P6 万泉河水系 PanZoom / P7 1915 实测图 PanZoom）
//      ＋ MixedPage 5（P1 街区索引 / P2 宋史书影 / P3 联姻谱系 / P5 清实录书影 / P8 四时代叠合）。
// 槽位几何见 slots.json（plate 全部 1920×1080 设计空间 = 画布 1:1）。
// 红线：浮在地图/照片上方的文字项一律 backing: true；标记圈/点位纯 SVG 叠加不入槽表；
//      photo 槽一律 kind:"photo"；屏显数字 ⊆ 当页口播。
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
  // ── p01 杨家将还是清代史（万泉河水系索引打底 + 挂甲屯现貌实拍）──────
  1: {
    design: 1,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p1_title", text: "挂甲屯 · 杨六郎传说与清初额驸城", size: 40, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p1_sub", text: "从评话演义到清宫档案 · 一座西郊古村的双面镜像", size: 23, color: INK, weight: 700, lh: 1.3, backing: true },
      { slotId: "p1_tag_index", kind: "tag", text: "现代路网索引 · 制作组示意", backing: true },
      { slotId: "p1_tag_changchun", kind: "tag", text: "畅春园", backing: true, delay: 60 },
      { slotId: "p1_tag_yuanming", kind: "tag", text: "圆明园", backing: true, delay: 90 },
      { slotId: "p1_tag_wanquan", kind: "tag", text: "万泉河水系", backing: true, delay: 120 },
      { slotId: "p1_tag_efc", kind: "tag", text: "额驸城遗址方位", backing: true, delay: 150 },
      { slotId: "p1_question", text: "「挂甲屯」，究竟是杨六郎挂甲的地方，\n还是一座清代额驸的王府？", size: 28, color: INK, weight: 800, lh: 1.45, backing: true, delay: 260 },
      { slotId: "p1_truth", text: "一个是评话演义里的神话，\n一个是清廷档案里的实录。", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 420 },
      { slotId: "p1_photo", kind: "photo", text: "挂甲屯社区现貌实拍（Page01 提供 PhotoSpec）" },
    ],
  },
  // ── p02 宋辽烟云：宋史杨延昭传辨伪（宋史书影 + 地理辨伪卡）─────────
  2: {
    design: 2,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p2_title", text: "宋辽烟云：杨六郎真来过海淀吗？", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p2_tag_source", kind: "tag", text: "正史列传 · 宋史列传", backing: true },
      { slotId: "p2_quote", text: "「延昭本名延朗，莫州清苑人……\n在邊防二十餘年，繕治障塞，\n契丹憚之，目為楊六郎。」", size: 26, color: INK, weight: 800, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p2_quote_badge", kind: "tag", text: "宋史列传原书书证", backing: true, delay: 200 },
      { slotId: "p2_verdict", text: "正史确证：杨延昭知保州、定州、高阳关，\n终身镇守河北三关一线。\n宋辽分界远在白沟河以南；此时海淀深处\n辽国南京幽都府腹地——\n所谓「挂甲」，纯属后世说书评话附会。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 380 },
      { slotId: "p2_verdict_badge", kind: "tag", text: "民间传说与史实分层判据", backing: true, delay: 460 },
      { slotId: "p2_photo", kind: "photo", text: "宋史杨延昭传书影（Page02 提供 PhotoSpec）" },
      { slotId: "p2_photo_tag", kind: "tag", text: "百衲本宋史列传书影", backing: true },
    ],
  },
  // ── p03 清初风云：政治联姻（正史公主表 + 联姻谱系卡）───────────────
  3: {
    design: 3,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p3_title", text: "清初风云：一场决定王朝命运的政治联姻", size: 38, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p3_tag_marriage", kind: "tag", text: "正史公主表 · 清史稿", backing: true },
      { slotId: "p3_marriage_quote", text: "「太宗第十四女，和碩恪純長公主。\n順治十年，封和碩公主，\n下嫁吳應熊。」", size: 27, color: INK, weight: 800, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p3_marriage_badge", kind: "tag", text: "建宁公主的历史原型", backing: true, delay: 200 },
      { slotId: "p3_desc", text: "顺治十年（1653），清廷为羁縻镇守西南的\n平西王吴三桂，将皇太极第十四女下嫁其长子\n吴应熊。吴应熊留居京师，官至少保兼太子太保，\n成为清初显赫一时的和硕额驸。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 380 },
      { slotId: "p3_desc_badge", kind: "tag", text: "满汉政治联姻", backing: true, delay: 460 },
      { slotId: "p3_genealogy", text: "联姻谱系：\n\n清太宗 皇太极\n　└ 第十四女 和硕恪纯长公主\n　　　　↓ 下嫁（顺治十年）\n平西王 吴三桂\n　└ 长子 吴应熊（和硕额驸）\n\n→ 京都西郊赐第，世称「额驸城」", size: 23, color: INK, weight: 700, lh: 1.6, backing: true, delay: 560 },
    ],
  },
  // ── p04 西郊赐第：额驸城地望（《三山五园图》畅春园西侧漫游）───────
  4: {
    design: 4,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p4_title", text: "西郊赐第：揭开「额驸城」的真实地望", size: 38, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p4_map_tag", kind: "tag", text: "清代官绘舆图 · 畅春园西侧", backing: true },
      { slotId: "p4_tag_efc", kind: "tag", text: "额驸城遗址", backing: true, delay: 90 },
      { slotId: "p4_tag_changchun", kind: "tag", text: "畅春园", backing: true, delay: 160 },
      { slotId: "p4_banner_badge", kind: "tag", text: "官修政书 · 钦定日下旧闻考", backing: true },
      { slotId: "p4_banner", text: "「掛甲屯在海淀西北，世傳吳應熊額駙府第\n遺址在此，俗亦稱額駙城。」", size: 27, color: INK, weight: 800, lh: 1.55, backing: true, delay: 280 },
      { slotId: "p4_note", text: "乾隆朝官书按语补充：\n挂甲屯距畅春园不数里，\n相传吴应熊第遗址即其处；\n今但存聚落，额驸城之名沿俗称也。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 420 },
    ],
  },
  // ── p05 1674：三藩之乱（清圣祖实录书影 + 抄没转折卡）───────────────
  5: {
    design: 5,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p5_title", text: "三藩之乱与一座府第的烟灭", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p5_tag_source", kind: "tag", text: "正史实录 · 清圣祖实录", backing: true },
      { slotId: "p5_quote", text: "「康熙十三年夏四月庚辰，\n平西王吳三桂反……\n吳應熊、吳世霖，著即處絞。」", size: 27, color: INK, weight: 800, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p5_quote_badge", kind: "tag", text: "一手实录书证", backing: true, delay: 200 },
      { slotId: "p5_desc", text: "康熙十二年（1673）三藩乱起，次年四月吴应熊伏诛。\n府第抄没入官，昔日显赫的额驸城沦为废墟。\n岁月推移，废墟之上渐聚民居，挂甲屯就此成形。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 380 },
      { slotId: "p5_desc_badge", kind: "tag", text: "府第废而聚落存", backing: true, delay: 460 },
      { slotId: "p5_photo", kind: "photo", text: "清圣祖实录吴应熊案书影（Page05 提供 PhotoSpec）" },
      { slotId: "p5_photo_tag", kind: "tag", text: "清代实录原刊书影", backing: true },
    ],
  },
  // ── p06 万泉河畔：《三山五园图》水系漫游 ────────────────────────
  6: {
    design: 6,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p6_title", text: "万泉河畔：御园西侧的聚落生长", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p6_map_tag", kind: "tag", text: "清代官绘舆图 · 万泉河水系", backing: true },
      { slotId: "p6_tag_gjt", kind: "tag", text: "挂甲屯", backing: true, delay: 60 },
      { slotId: "p6_tag_changchun", kind: "tag", text: "畅春园", backing: true, delay: 120 },
      { slotId: "p6_tag_yuanming", kind: "tag", text: "圆明园大宫门", backing: true, delay: 180 },
      { slotId: "p6_tag_wanquan", kind: "tag", text: "万泉河", backing: true, delay: 240 },
      { slotId: "p6_note_badge", kind: "tag", text: "空间拓扑 · 御园外围聚落", backing: true },
      { slotId: "p6_note", text: "挂甲屯南依万泉河，东临畅春园，\n东北近圆明园大宫门。\n乾隆年间御园西侧卫署与民居相依，\n成为皇家园林外围重要的居住与服务聚落。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 320 },
    ],
  },
  // ── p07 1915：实测地形图上的村名定格（1915 图特写漫游）─────────────
  7: {
    design: 7,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p7_title", text: "1915：实测地图上的村名定格", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p7_map_tag", kind: "tag", text: "民国档案 · 北洋陆军测地局实测京师四郊图", backing: true },
      { slotId: "p7_tag_gjt", kind: "tag", text: "掛甲屯 · 1915 定名", backing: true, delay: 90 },
      { slotId: "p7_tag_wanquan", kind: "tag", text: "万泉河", backing: true, delay: 150 },
      { slotId: "p7_tag_liangjiadian", kind: "tag", text: "亮甲店 · 杨家将传说带", backing: true, delay: 210 },
      { slotId: "p7_summary", text: "民国四年（1915）五万分之一实测图上，\n万泉河北侧、畅春园以西工整标绘「掛甲屯」。\n近代朱自清先生清华任教期间曾寓居于此。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 340 },
      { slotId: "p7_summary_badge", kind: "tag", text: "一手实测档案 · 测绘定型", backing: true, delay: 440 },
    ],
  },
  // ── p08 岁月留痕：演义传奇与人间烟火的共生（四时代叠合图）──────────
  8: {
    design: 8,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p8_title", text: "岁月留痕：演义传奇与人间烟火的共生", size: 38, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p8_layer_tag", kind: "tag", text: "时代叠合 · 制作组示意 · 非测绘拓扑", backing: true },
      { slotId: "p8_tag_song", kind: "tag", text: "宋辽 · 演义想象", backing: true, delay: 60 },
      { slotId: "p8_tag_earlyqing", kind: "tag", text: "清初 · 额驸城", backing: true, delay: 90 },
      { slotId: "p8_tag_midqing", kind: "tag", text: "清中叶 · 御园村落", backing: true, delay: 120 },
      { slotId: "p8_tag_modern", kind: "tag", text: "今 · 高校居住街区", backing: true, delay: 150 },
      { slotId: "p8_sum_left", text: "杨六郎的铠甲挂在说书人的评话里，\n吴应熊的额驸城留在官书的档案里。", size: 26, color: INK, weight: 800, lh: 1.55, backing: true, delay: 280 },
      { slotId: "p8_sum_right", text: "一个地名，两面镜像。\n万泉河水流过的是未曾断流的京西记忆。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 440 },
    ],
  },
};
