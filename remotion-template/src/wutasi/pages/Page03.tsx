// Page03 — 塔年 ≠ 寺年：《明宪宗实录》书影 + 时序分岔。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page03: React.FC = () => (
  <MixedPage
    page={3}
    photos={{
      p3_photo: {
        mode: "frame",
        src: staticFile("wutasi/mingxianzong_shilu_folio.png"),
        caption: "《明宪宗实录》卷一百二十「真觉寺金刚宝座塔成」书影 · VEC-1",
      },
    }}
  />
);
