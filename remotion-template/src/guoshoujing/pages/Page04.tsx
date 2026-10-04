// Page04 — 四海测验·二十七所：观星台示意 + 北极出地排布示意（穷举名单）。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page04: React.FC = () => (
  <MixedPage
    page={4}
    photos={{
      p4_photo_tai: {
        mode: "frame",
        src: staticFile("guoshoujing/guansingtai_schematic.png"),
        caption: "登封观星台示意 · 元代遗构 · 制作组绘制示意 · 非实物照片",
      },
      p4_photo_27: {
        mode: "frame",
        src: staticFile("guoshoujing/sihai_27_stations_mec3.png"),
        caption: "二十七所按北极出地排布 · 依《元史·天文志》名单 · 制作组示意 · 非地图投影",
      },
    }}
  />
);
