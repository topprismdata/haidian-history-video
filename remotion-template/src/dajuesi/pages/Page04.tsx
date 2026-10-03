// Page04 — 为什么朝着西边：旸台山麓朝向拓扑 PanZoom（MEC-1）。
// 纸雾渐变 12% 内达 0.99 不透明（E23 事故教训：平移候选会落进地图「頤」字一类底图字迹）。
import React from "react";
import { MapPage } from "../SlotPage";
import { MapMarker, PanZoomView } from "../viewport";
import { PAGE_DURATIONS_SEC, VIDEO } from "../data/pageMap";
import { PALETTE } from "../ui";

export const Page04: React.FC = () => {
  const frames = Math.round(PAGE_DURATIONS_SEC[3] * VIDEO.fps);
  return (
    <MapPage
      page={4}
      background={
        <PanZoomView
          src="dajuesi/sanshanyuan_yangtai_roi_4000.png"
          startView={{ x: 0, y: 0, scale: 1 }}
          endView={{ x: 60, y: 110, scale: 1.15 }}
          durationInFrames={frames}
        >
          <MapMarker x={760} y={520} label="" color={PALETTE.ochre} radius={22} delay={80} />
          <MapMarker x={240} y={180} label="" color={PALETTE.gold} radius={18} delay={170} />
        </PanZoomView>
      }
      overlay={
        <div
          style={{
            position: "absolute", left: 0, right: 0, bottom: 0, height: 430,
            // 12% 处即达 0.99 不透明：负控制平移候选（y=740~980）须落在纯净纸雾区
            background:
              "linear-gradient(to bottom, rgba(247,240,223,0) 0%, rgba(247,240,223,0.99) 12%, rgba(247,240,223,1) 100%)",
          }}
        />
      }
    />
  );
};
