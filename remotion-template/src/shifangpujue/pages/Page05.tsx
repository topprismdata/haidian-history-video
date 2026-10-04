// Page05 — 明正统与成化，寿安山寺、永安寺：六名纵贯时间轴。
import React from "react";
import { staticFile } from "remotion";
import { MixedPage } from "../SlotPage";

export const Page05: React.FC = () => (
  <MixedPage
    page={5}
    photos={{
      p5_timeline: {
        mode: "frame",
        src: staticFile("shifangpujue/mec3_six_names_timeline.png"),
        caption: "六名纵贯时间轴 · 制作组示意 · MEC-3",
      },
    }}
  />
);
