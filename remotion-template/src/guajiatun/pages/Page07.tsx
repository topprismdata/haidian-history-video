// Page07 — 1915 实测地形图特写漫游（MEC-2）。底图 1920×1080 与画布恒等。
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
          src="guajiatun/beijing_1915_guajiatun_roi.png"
          startView={{ x: 0, y: 0, scale: 1 }}
          endView={{ x: -140, y: -70, scale: 1.22 }}
          durationInFrames={frames}
        >
          <MapMarker x={1560} y={500} label="" color={PALETTE.ochre} radius={24} delay={90} />
          <MapMarker x={1200} y={280} label="" color={PALETTE.indigo} radius={18} delay={170} />
        </PanZoomView>
      }
      overlay={
        <div
          style={{
            position: "absolute", left: 0, right: 0, bottom: 0, height: 700,
            // 12% 处即达 0.99 不透明：覆盖 p7_summary 平移候选 (y=400..630) 内的图内汉字
            // 「頤和園」的「頤」，避免负控制把底图字迹误判为槽位文字（E23 事故）
            background:
              "linear-gradient(to bottom, rgba(247,240,223,0) 0%, rgba(247,240,223,0.99) 12%, rgba(247,240,223,1) 100%)",
          }}
        />
      }
    />
  );
};
