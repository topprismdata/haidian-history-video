// Page07 — 1951：历史的巧合与时代的相逢。中央民族学院建校初期档案影像
// （VEC-2 公共领域）+ 选址卡 + 七百年时空呼应卡。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page07: React.FC = () => (
  <MixedPage
    page={7}
    photos={{
      p7_photo: {
        mode: "frame",
        src: staticFile("weigongcun/minzu_univ_archival_1950s.png"),
        caption: "中央民族学院建校初期校园 · 1952 年前后 · Wikimedia Commons · 公共领域 · VEC-2",
      },
    }}
  />
);
