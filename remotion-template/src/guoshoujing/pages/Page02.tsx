// Page02 — 邢台来的年轻人：中统三年六事条书影 + 玉泉首想。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page02: React.FC = () => (
  <MixedPage
    page={2}
    photos={{
      p2_photo_folio: {
        mode: "frame",
        src: staticFile("guoshoujing/yuanshi_liushi_folio.png"),
        caption: "《元史·郭守敬传》中统三年条 · 依公开文本排印 · 非原刊扫描",
      },
    }}
  />
);
