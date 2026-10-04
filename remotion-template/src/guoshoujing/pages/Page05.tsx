// Page05 — 一年的长度：歲餘条书影（刻分原文，无小数）。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page05: React.FC = () => (
  <MixedPage
    page={5}
    photos={{
      p5_photo_folio: {
        mode: "frame",
        src: staticFile("guoshoujing/yuanshi_suiyu_folio.png"),
        caption: "《元史·郭守敬传》歲餘条 · 依公开文本排印 · 非原刊扫描",
      },
    }}
  />
);
