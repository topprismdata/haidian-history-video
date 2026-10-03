// Page08 — 四个时代，叠在同一片湖山里：CrossFadeViewport 四时代半透明叠合收官。
// 图层序（口播节拍）：明代勺园 → 清代赐园水田 → 民国燕京大学 → 今日燕园；
// 终态四层全保留（opacity 0.18/0.42/0.55/0.92）＝「叠合」而非替换。
// 1982 条石 / 2001 国保 / 市保碑真图；图层内零文字（命名走 tag 槽）。
import React from "react";
import { staticFile } from "remotion";
import { MapPage } from "../SlotPage";
import { CrossFadeViewport } from "../viewport";
import { PAGE_DURATIONS_SEC, VIDEO } from "../data/pageMap";

export const Page08: React.FC = () => {
  const frames = Math.round(PAGE_DURATIONS_SEC[7] * VIDEO.fps);
  return (
    <MapPage
      page={8}
      background={
        <AbsoluteFillWrap>
          <CrossFadeViewport
            layers={[
              { src: "shaoyuan/mec4/era_ming.png", startOpacity: 1, endOpacity: 0.18, label: "ming" },
              { src: "shaoyuan/mec4/era_qing.png", startOpacity: 0, endOpacity: 0.42, label: "qing" },
              { src: "shaoyuan/mec4/era_minguo.png", startOpacity: 0, endOpacity: 0.55, label: "minguo" },
              { src: "shaoyuan/mec4/era_today.png", startOpacity: 0, endOpacity: 0.92, label: "today" },
            ]}
            durationInFrames={frames}
            smooth
          />
        </AbsoluteFillWrap>
      }
      photos={{
        p8_photo: {
          mode: "frame",
          src: staticFile("shaoyuan/commons_1930s_yenching_campus1.jpg"),
          caption: "原燕京大学未名湖区 · 北京市文物保护单位碑 · Wikimedia Commons · CC BY-SA 4.0",
        },
      }}
    />
  );
};

// CrossFadeViewport 以百分比铺满；包一层全幅容器统一 objectFit 基准。
const AbsoluteFillWrap: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ position: "absolute", inset: 0 }}>{children}</div>
);
