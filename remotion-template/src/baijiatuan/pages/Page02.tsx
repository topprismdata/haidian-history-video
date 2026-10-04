// Page02 — E27《白家疃》P02 主图：《说文》书影（排印件）。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page02: React.FC = () => (
  <MixedPage
    page={2}
    photos={{
      p2_photo_folio: {
        mode: "frame",
        src: staticFile("baijiatuan/shuowen_tuan_folio.png"),
        caption: "依公开文本排印 · 非原刊扫描",
      },
    }}
  />
);
