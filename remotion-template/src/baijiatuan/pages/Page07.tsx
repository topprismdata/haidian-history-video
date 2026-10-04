// Page07 — E27《白家疃》P07 主图：1915 实测图（地震台时间轴图待补，DOM 卡兜底）。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page07: React.FC = () => (
  <MixedPage
    page={7}
    photos={{
      p7_photo_1915: {
        mode: "frame",
        src: staticFile("baijiatuan/beijing_1915_baijiatuan_roi.png"),
        caption: "民国四年《實測京師四郊地圖》切片（公有领域）",
      },
    }}
  />
);
