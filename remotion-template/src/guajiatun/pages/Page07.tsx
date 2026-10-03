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
          endView={{ x: -70, y: -50, scale: 1.35 }}
          durationInFrames={frames}
        >
          <MapMarker x={955} y={390} label="" color={PALETTE.ochre} radius={24} delay={90} />
          <MapMarker x={340} y={400} label="" color={PALETTE.indigo} radius={18} delay={170} />
        </PanZoomView>
      }
      overlay={
        <div
          style={{
            position: "absolute", left: 0, right: 0, bottom: 0, height: 420,
            background:
              "linear-gradient(to bottom, rgba(247,240,223,0) 0%, rgba(247,240,223,0.90) 28%, rgba(247,240,223,0.97) 100%)",
          }}
        />
      }
    />
  );
};
