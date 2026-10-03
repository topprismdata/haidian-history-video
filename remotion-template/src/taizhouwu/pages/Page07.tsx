// Page07 — 1915：实测地形图上的正式定名
// PanZoomView 聚焦 1915 北洋陆军测地局《实测京师四郊图》太舟坞、黑龙潭特写
import React from "react";
import { MapPage } from "../SlotPage";
import { MapMarker, PanZoomView } from "../viewport";
import { PAGE_DURATIONS_SEC, VIDEO } from "../data/pageMap";
import { PALETTE } from "../ui";

export const Page07: React.FC = () => {
  const frames = Math.round(PAGE_DURATIONS_SEC[6] * VIDEO.fps);
  return (
    <MapPage
      page={7}
      background={
        <PanZoomView
          src="taizhouwu/beijing_1915_taizhouwu_roi.png"
          startView={{ x: 0, y: 0, scale: 1 }}
          endView={{ x: 40, y: 60, scale: 1.25 }}
          durationInFrames={frames}
        >
          {/* 太舟坞工整注记位置 */}
          <MapMarker x={1390} y={540} label="" color={PALETTE.ochre} radius={24} delay={60} />
          {/* 黑龙潭泉眼与龙王庙位置 */}
          <MapMarker x={600} y={400} label="" color={PALETTE.indigo} radius={20} delay={120} />
        </PanZoomView>
      }
    />
  );
};
