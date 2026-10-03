// Page02 — 1280：忽必烈身边的「廉孟子」：《元史·廉希宪传》卒谥书影（VEC-1）
// + 正史列传档案卡。引文逐字照录书影所据卷126（sources.csv 内容核实项）。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page02: React.FC = () => (
  <MixedPage
    page={2}
    photos={{
      p2_photo: {
        mode: "frame",
        src: staticFile("weigongcun/yuanshi_lianxixian_folio.png"),
        caption: "《欽定元史·卷一百二十六·廉希憲傳》卒謚書影 · 四庫本 · Internet Archive · VEC-1",
      },
    }}
  />
);
