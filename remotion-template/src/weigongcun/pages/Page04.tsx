// Page04 — 明代的印记：大慧寺（国保 5-199）与首辅李东阳祖茔。
// 实拍为大悲宝殿明代殿宇外景（sources.csv 内容核实：非二十八诸天塑像本体，
// 题注如实标注）——V-NC03/VEC-3 红线：严禁以塑像名目冒配外景照。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page04: React.FC = () => (
  <MixedPage
    page={4}
    photos={{
      p4_photo: {
        mode: "frame",
        src: staticFile("weigongcun/dahuisi_twenty_eight_devas.png"),
        caption: "大慧寺大悲宝殿外景 · 明代殿宇（寺创于正德八年）· Wikimedia Commons · CC BY-SA 3.0 · VEC-3",
      },
    }}
  />
);
