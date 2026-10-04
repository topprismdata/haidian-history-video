// Page04 — 正德九年，一座堂改写了山与村：《宛署杂记》书影主 + 命名链拓扑副。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page04: React.FC = () => (
  <MixedPage
    page={4}
    photos={{
      p4_photo_wanshu: {
        mode: "frame",
        src: staticFile("wenquan/wanshu_zaji_folio.png"),
        caption: "《宛署杂记》「温泉堂」条 · 依公开文本排印 · 非原刊扫描",
      },
      p4_photo_chain: {
        mode: "frame",
        src: staticFile("wenquan/mec4_quanming_chain.png"),
        caption: "制作组示意 · 非测绘拓扑",
      },
    }}
  />
);
