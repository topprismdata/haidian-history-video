// Page07 — 湮没·以及一条被冤枉的河：延祐书影 + 衰败链时间轴（本集主轴）。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page07: React.FC = () => (
  <MixedPage
    page={7}
    photos={{
      p7_photo_yanyou: {
        mode: "frame",
        src: staticFile("guoshoujing/yuanshi_yanyou_folio.png"),
        caption: "《元史·河渠志》延祐元年条 · 依公开文本排印 · 非原刊扫描",
      },
      p7_photo_chain: {
        mode: "frame",
        src: staticFile("guoshoujing/guoshoujing_decay_chain_mec4.png"),
        caption: "一条渠的衰败链 · 依《元史·河渠志》与乾隆御制文 · 制作组示意 · 非测绘拓扑",
      },
    }}
  />
);
