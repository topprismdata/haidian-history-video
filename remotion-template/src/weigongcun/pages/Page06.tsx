// Page06 — 1915：实测地图的定格。1915 北洋陆军测地局《实测京师四郊图》
// 魏公村切片（MEC-2 一手实测档案，1920×1080 与画布 1:1）PanZoom 推至
// 图内竖排「魏公村」注记一带（scale 1.4 落幅）。
// 呼吸圈标 魏公村 / 大慧寺 两处图上注记；命名一律走 backing tag 槽。
import React from "react";
import { MapPage } from "../SlotPage";
import { MapMarker, PanZoomView } from "../viewport";
import { PAGE_DURATIONS_SEC, VIDEO } from "../data/pageMap";
import { PALETTE } from "../ui";

// 底图 1920×1080 与画布恒等：scale1 时图层坐标＝画布坐标＝图上像素。
export const Page06: React.FC = () => {
  const frames = Math.round(PAGE_DURATIONS_SEC[5] * VIDEO.fps);
  return (
    <MapPage
      page={6}
      background={
        <PanZoomView
          src="weigongcun/beijing_1915_weigongcun_roi.png"
          startView={{ x: 0, y: 0, scale: 1 }}
          endView={{ x: -85, y: -61, scale: 1.4 }}
          durationInFrames={frames}
        >
          <MapMarker x={1135} y={555} label="" color={PALETTE.ochre} radius={18} delay={260} />
          <MapMarker x={1420} y={780} label="" color={PALETTE.gold} radius={14} delay={330} />
        </PanZoomView>
      }
      overlay={
        <div
          style={{
            position: "absolute", left: 0, right: 0, bottom: 0, height: 480,
            background:
              "linear-gradient(to bottom, rgba(247,240,223,0) 0%, rgba(247,240,223,0.90) 24%, rgba(247,240,223,0.97) 100%)",
          }}
        />
      }
    />
  );
};
