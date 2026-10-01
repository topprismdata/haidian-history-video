// pages.config.ts — 逐页槽位文案与样式。
//
// ⚠ 本文件由 <集>_video/build_remotion_data.py 从 design.md 生成，不要手写。
//    本文件只是**最小示例**（仅 p01 四个槽位），用于说明格式。
//
// 生成方式见 METHODOLOGY.md §「工具化」：
//   python3 <集>_video/build_remotion_data.py
//
// 三条纪律：
//  1) 页长用含留白的 PAGE_DURATIONS_SEC；页起点用纯音频累加（见 pageMap.ts）
//  2) 除 kind:"tag" 外，所有压在插画上的文字一律 backing: true
//  3) ⚠ slots.json 里**必须带 id 字段** —— SlotPage 的 boxOf() 靠
//     find(x => x.id === slotId) 定位。缺 id 就静默返回 10×10 兜底框，
//     FitText 在 10px 宽的框里装不下字，终态帧上表现为「整页槽位空白」。
//     （E10 实测踩中，排查了三轮才定位：先疑 anchor、再疑检测器，最后是数据缺字段。）

const INK = "#3a3226";

export const PAGE_CONFIG: Record<number, any> = {
  1: {
    design: 1,
    bounds: [0, 0, 9999, 9999],
    items: [
      { slotId: "title", text: "示例标题", size: 26, color: INK, weight: 800, lh: 1.4, backing: true },
      { slotId: "evidence_tag", kind: "tag", text: "文献记载" },
      { slotId: "era_line", text: "一行说明", size: 20, color: INK, weight: 800, lh: 1.4, backing: true },
      { slotId: "data_bar", text: "底部数据带", size: 18, color: INK, weight: 800, lh: 1.4, backing: true },
    ],
  },
  // p02..p08 同理
};
