// Page04 — 1292：郭守敬的白浮引水渠。
// PanZoomView 漫游《三山五园图》西山山麓 4000px 切片（MEC-1）：
// startView 俯瞰山麓 → endView 聚焦山麓等高线转折凹岸台地（scale 1.2）。
// 下部纸雾渐变确保文字槽可读性与负控制绝对干净。
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
          src="taizhouwu/sanshanyuan_xishan_roi_4000.png"
          startView={{ x: 0, y: 0, scale: 1 }}
          endView={{ x: 80, y: 140, scale: 1.2 }}
          durationInFrames={frames}
        >
          {/* 白浮引水渠山麓水线定位标 */}
          <MapMarker x={440} y={160} label="" color={PALETTE.indigo} radius={18} delay={40} />
          {/* 太舟坞凹岸台地定位标 */}
          <MapMarker x={1540} y={240} label="" color={PALETTE.ochre} radius={20} delay={180} />
        </PanZoomView>
      }
      overlay={
        <div
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: 0,
            height: 720,
            background:
              "linear-gradient(to bottom, rgba(247,240,223,0) 0%, rgba(247,240,223,0.95) 12%, rgba(247,240,223,0.98) 100%)",
          }}
        />
      }
    />
  );
};
