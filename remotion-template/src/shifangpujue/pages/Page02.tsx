// Page02 — 唐太宗贞观年间，初名兜率寺：古籍书影。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page02: React.FC = () => (
  <MixedPage
    page={2}
    photos={{
      p2_photo_folio: {
        mode: "frame",
        src: staticFile("shifangpujue/yuanshi_folio.png"),
        caption: "元史·英宗本纪冶铜条 · 转引排印 · 非原刊扫描",
      },
    }}
  />
);
