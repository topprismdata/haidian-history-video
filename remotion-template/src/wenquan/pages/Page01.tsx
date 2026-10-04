// Page01 — 地图上两个字的地名：1915 实测图主 + 三山五园图北界副（MEC-1：
// 温泉村不在画内，画面严禁加温泉标注——这张图证明「图到哪儿为止」）。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page01: React.FC = () => (
  <MixedPage
    page={1}
    photos={{
      p1_photo_1915: {
        mode: "frame",
        src: staticFile("wenquan/beijing_1915_shiwo_roi.png"),
        caption: "民国四年《實測京師四郊地圖》切片（公有领域）",
      },
      p1_photo_sanshan: {
        mode: "strip",
        src: staticFile("wenquan/sanshanyuan_xiangshan_roi.png"),
      },
    }}
  />
);
