// pages.config.ts — E22《太舟坞·唐代羁縻带州与元代船坞之谜》逐页槽位文案与样式.
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
  // ── p01 今天的太舟坞（山水街区索引打底 + 温泉村实景镜框）──────
  1: {
    design: 1,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p1_title", text: "太舟坞 · 山麓古村的千年谜题", size: 42, color: INK, weight: 800, lh: 1.25, backing: true },
      { slotId: "p1_sub", text: "从盛唐羁縻到元代船坞 · 一座山麓村庄的时空解谜", size: 23, color: INK, weight: 700, lh: 1.3, backing: true },
      { slotId: "p1_tag_index", kind: "tag", text: "现代街区索引 · 制作组示意", backing: true },
      { slotId: "p1_tag_wenquan", kind: "tag", text: "海淀温泉镇", backing: true, delay: 60 },
      { slotId: "p1_tag_canal", kind: "tag", text: "京密引水渠水网", backing: true, delay: 90 },
      { slotId: "p1_tag_village", kind: "tag", text: "太舟坞村故址", backing: true, delay: 120 },
      { slotId: "p1_tag_hlt", kind: "tag", text: "黑龙潭古迹", backing: true, delay: 150 },
      { slotId: "p1_question", text: "「太舟坞」，究竟是源自一千三百年前的盛唐，\n还是一座元代的船坞码头？", size: 28, color: INK, weight: 800, lh: 1.45, backing: true, delay: 260 },
      { slotId: "p1_intro", text: "同一个村名背后，为什么会藏着\n盛唐与大元两条截然不同的身世？", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 420 },
      { slotId: "p1_photo", kind: "photo", text: "现代太舟坞街区实景（Page01 提供 PhotoSpec）" },
    ],
  },
  // ── p02 公元 705：唐中宗的羁縻「带州」（《旧唐书》书影 + 羁縻政区卡）───
  2: {
    design: 2,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p2_title", text: "公元 705：唐中宗的羁縻「带州」", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p2_tag_source", kind: "tag", text: "正史官书 · 旧唐书地理志", backing: true },
      { slotId: "p2_quote", text: "「帶州，神龍元年置，\n寄治昌平縣清水店，領孤竹一縣。」", size: 28, color: INK, weight: 800, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p2_quote_badge", kind: "tag", text: "正史官书 · 新唐书地理志互证", backing: true, delay: 200 },
      { slotId: "p2_desc", text: "神龙元年（705），朝廷析营州置带州安置契丹降户，\n后寄治昌平清水店，领孤竹一县。\n方言里，「带州」二字读音与「太舟」极其相近。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 360 },
      { slotId: "p2_photo", kind: "photo", text: "旧唐书地理志原刊书影（Page02 提供 PhotoSpec）" },
      { slotId: "p2_photo_tag", kind: "tag", text: "文渊阁本旧唐书原刊书影", backing: true },
    ],
  },
  // ── p03 天宝九载：出土墓志的坐标裁判（金石拓片 + 裁判卡）──────────
  3: {
    design: 3,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p3_title", text: "天宝九载：出土墓志的坐标裁判", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p3_tag_ep", kind: "tag", text: "出土金石实物 · Level 1 硬证据", backing: true },
      { slotId: "p3_epitaph", text: "「授孤竹府帶州折衝……\n葬於幽州昌平縣清水店之原，禮也。」", size: 28, color: INK, weight: 800, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p3_ep_badge", kind: "tag", text: "天宝九载（750）焦金府墓志铭", backing: true, delay: 200 },
      { slotId: "p3_verdict", text: "出土硬实物确证：带州治所明确在昌平清水店（阳坊一带），\n距离海淀太舟坞十余公里。\n「太舟坞即带州」缺乏地望直核证据！", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 380 },
      { slotId: "p3_verdict_badge", kind: "tag", text: "历史地理学地望直核判据", backing: true, delay: 460 },
      { slotId: "p3_photo", kind: "photo", text: "焦金府墓志铭拓本书影（Page03 提供 PhotoSpec）" },
      { slotId: "p3_photo_tag", kind: "tag", text: "唐折冲都尉墓志刻石拓本 · VEC-1", backing: true },
    ],
  },
  // ── p04 1292：郭守敬的白浮引水渠（《三山五园图》西山漫游 + 工程卡）─────
  4: {
    design: 4,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p4_title", text: "1292：郭守敬的白浮引水渠", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p4_map_tag", kind: "tag", text: "清代官绘舆图西山山麓段", backing: true },
      { slotId: "p4_tag_canal", kind: "tag", text: "元代白浮堰绕山引水线", backing: true, delay: 90 },
      { slotId: "p4_tag_taizhouwu", kind: "tag", text: "太舟坞 · 山麓平缓凹岸", backing: true, delay: 150 },
      { slotId: "p4_banner_badge", kind: "tag", text: "正史工程实录 · 元史河渠志", backing: true },
      { slotId: "p4_banner", text: "「引白浮村神山泉，西折而南，\n傍西山，注甕山泊，由尋河入通惠河。」", size: 28, color: INK, weight: 800, lh: 1.55, backing: true, delay: 280 },
      { slotId: "p4_note", text: "至元二十九年（1292），郭守敬辟白浮堰，\n引水绕西山山麓六十里，过太舟坞山麓凹岸。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 420 },
    ],
  },
  // ── p05 何谓「太舟坞」？水文与船坞的真相（水利解构 + 双轨假说）──────
  5: {
    design: 5,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p5_title", text: "何谓「太舟坞」？水文与船坞的真相", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p5_etym_tag", kind: "tag", text: "古代水利地理学解构", backing: true },
      { slotId: "p5_etym", text: "太舟：大舟、大船\n坞：停泊修造船只、装卸货物的凹港码头", size: 26, color: INK, weight: 800, lh: 1.5, backing: true, delay: 120 },
      { slotId: "p5_wharf_tag", kind: "tag", text: "郭守敬引水运石工程实录", backing: true, delay: 240 },
      { slotId: "p5_wharf", text: "修筑大都宫城需要采运西山巨石。\n太舟坞避风水深，正是当年官船运石停泊的大官坞！\n地名，是古代水工地理的活化石。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 360 },
      { slotId: "p5_double_track", text: "双轨考订：\n• 唐带州音转：方言音近，但治所在昌平清水店（争议假说）\n• 元水利船坞：工程地理与水工台地高度契合（受证假说）", size: 24, color: INK, weight: 700, lh: 1.6, backing: true, delay: 520 },
      { slotId: "p5_double_badge", kind: "tag", text: "双轨竞争假说综合裁决", backing: true, delay: 600 },
    ],
  },
  // ── p06 清代印记：黑龙潭与皇家祈雨（政书书影 + 殿宇古建照）────────
  6: {
    design: 6,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p6_title", text: "清代：黑龙潭与皇家祈雨圣地", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p6_tag_source", kind: "tag", text: "官修政书 · 钦定日下旧闻考", backing: true },
      { slotId: "p6_rixia", text: "《日下旧闻考》卷一百四：\n「黑龍潭在太舟塢村西，平地出泉，匯為澄潭……\n康熙二十年建龍王廟，歲旱祈雨多有靈應。」", size: 25, color: INK, weight: 700, lh: 1.55, backing: true, delay: 120 },
      { slotId: "p6_rixia_badge", kind: "tag", text: "钦定日下旧闻考卷一百四", backing: true, delay: 200 },
      { slotId: "p6_ritual", text: "清康熙二十年（1681）敕建龙王庙并御制碑文。\n太舟坞百余户倚山面水，果木繁盛，\n正式成为清代皇帝西郊祈雨御道名村。", size: 24, color: INK, weight: 700, lh: 1.5, backing: true, delay: 380 },
      { slotId: "p6_ritual_badge", kind: "tag", text: "清代皇家祈雨御道名村", backing: true, delay: 460 },
      { slotId: "p6_photo", kind: "photo", text: "黑龙潭龙王庙殿宇外观（Page06 提供 PhotoSpec）" },
      { slotId: "p6_photo_tag", kind: "tag", text: "黑龙潭龙王庙大殿遗存照", backing: true },
    ],
  },
  // ── p07 1915：实测地形图上的正式定名（1915 五万分之一京西图特写）─────
  7: {
    design: 7,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p7_title", text: "1915：实测地图的定格", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p7_map_tag", kind: "tag", text: "民国档案 · 北洋陆军测地局《实测京师四郊图》", backing: true },
      { slotId: "p7_tag_tzw", kind: "tag", text: "太舟坞 · 1915 定名", backing: true, delay: 90 },
      { slotId: "p7_tag_hlt", kind: "tag", text: "黑龙潭 · 祈雨圣地", backing: true, delay: 150 },
      { slotId: "p7_tag_wq", kind: "tag", text: "温泉 · 西山古驿", backing: true, delay: 210 },
      { slotId: "p7_summary", text: "民国四年（1915）五万分之一实测图上，\n「太舟塢」三个字工整标绘在西山山麓。\n从羁縻记忆到漕运码头，官方测绘正式定格。", size: 26, color: INK, weight: 800, lh: 1.55, backing: true, delay: 340 },
      { slotId: "p7_summary_badge", kind: "tag", text: "一手实测档案 · 测绘定型", backing: true, delay: 440 },
    ],
  },
  // ── p08 水系与岁月：地名里的时空交响（四时代叠合图 + 终局总结）────────
  8: {
    design: 8,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "p8_title", text: "水系与岁月：地名里的时空交响", size: 40, color: INK, weight: 800, lh: 1.3, backing: true },
      { slotId: "p8_layer_tag", kind: "tag", text: "四时代叠合 · 制作组示意 · 非测绘拓扑", backing: true },
      { slotId: "p8_tag_tang", kind: "tag", text: "唐 · 羁縻带州孤竹府", backing: true, delay: 60 },
      { slotId: "p8_tag_yuan", kind: "tag", text: "元 · 白浮引水泊舟官坞", backing: true, delay: 90 },
      { slotId: "p8_tag_qing", kind: "tag", text: "清 · 黑龙潭祈雨御道", backing: true, delay: 120 },
      { slotId: "p8_tag_modern", kind: "tag", text: "今 · 京密引水渠水脉", backing: true, delay: 150 },
      { slotId: "p8_sum_left", text: "盛唐的关塞风云与元代的治水宏图，\n都在太舟坞的名字里相遇。", size: 27, color: INK, weight: 800, lh: 1.55, backing: true, delay: 280 },
      { slotId: "p8_sum_right", text: "水流不息，岁月成歌。\n地名，是一座在大地上活了一千三百年的时间坐标。", size: 25, color: INK, weight: 800, lh: 1.55, backing: true, delay: 440 },
    ],
  },
};
