// Page01 — 今天这一湖：era_today 索引图（MEC-4）打底 + 未名湖实拍镜框。
// 标记圈 = MapMarker SVG 叠加层（label 为空 —— 命名一律走 backing 文字槽/tag 槽，
// 保证「每个可见字符都在某个槽位矩形内」的 QA 负控制前提）。
import React from "react";
import { Img, staticFile } from "remotion";
import { MapPage } from "../SlotPage";
import { MapMarker } from "../viewport";
import { PALETTE } from "../ui";

export const Page01: React.FC = () => (
  <MapPage
    page={1}
    background={
      <Img
        src={staticFile("shaoyuan/mec4/era_today.png")}
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }}
      />
    }
    overlay={
      <>
        <MapMarker x={640} y={545} label="" color={PALETTE.indigo} radius={13} delay={10} />
        <MapMarker x={612} y={448} label="" color={PALETTE.ochre} radius={10} delay={40} />
        <MapMarker x={1010} y={660} label="" color={PALETTE.inkSoft} radius={9} delay={70} />
        <MapMarker x={255} y={872} label="" color={PALETTE.legend} radius={12} delay={100} />
      </>
    }
    photos={{
      p1_photo: {
        mode: "frame",
        src: staticFile("shaoyuan/commons_2008_weiming_lake.jpg"),
        caption: "未名湖与博雅塔 · 今貌（2008 摄影）· Wikimedia Commons · VEC-2",
      },
    }}
  />
);
