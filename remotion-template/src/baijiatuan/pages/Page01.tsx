// Page01 — E27《白家疃》P01 主图：民国四年实测图切片。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page01: React.FC = () => (
  <MixedPage
    page={1}
    photos={{
      p1_photo_main: {
        mode: "frame",
        src: staticFile("baijiatuan/beijing_1915_baijiatuan_roi.png"),
        caption: "民国四年《實測京師四郊地圖》切片（公有领域）",
      },
    }}
  />
);
