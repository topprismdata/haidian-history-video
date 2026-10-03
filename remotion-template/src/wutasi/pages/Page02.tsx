// Page02 — 一方石匾的逐字解读（核心证据页）：石匾逐字放大图。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page02: React.FC = () => (
  <MixedPage
    page={2}
    photos={{
      p2_photo: {
        mode: "frame",
        src: staticFile("wutasi/quanmen_shibei_folio.png"),
        caption: "券门石匾逐字放大图 · 敕建金刚宝座 大明成化九年十一月初二造 · L1 一手实物",
      },
    }}
  />
);
