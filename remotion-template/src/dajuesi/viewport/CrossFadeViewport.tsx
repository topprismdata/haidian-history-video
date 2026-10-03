import React from "react";
import {
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

/**
 * E24《大觉寺·阳台山麓的千年清水院》分层视口引擎 — 多时代图层透明度叠合 (Cross-Fade)。
 *
 * 复用 E20 黄金数学契约（与 tests/test_dajuesi_viewport.py 黄金模型同源）：
 * - 各图层 opacity = startOpacity + (endOpacity - startOpacity) * progress，
 *   progress clamp 到 [0, 1]，帧越界不外推，结果恒落在 [0, 1]；
 * - 默认线性过渡；smooth = true 时套用 cubic-bezier(0.25, 0.1, 0.25, 1.0)；
 * - durationInFrames 缺省取所在 Sequence/合成时长（Math.max(1, …) 防除零）；
 * - label 仅作 aria-label 辅助信息，绝不渲染为可见 DOM 文字槽。
 *
 * E21 特化：
 * - 面向 MEC-4 四时代叠合（元·畏吾村 → 明·魏村 → 1915 实测京西 → 现代街区）；
 * - blend 属性支持 mixBlendMode（默认 normal），供等深叠合与等高线提亮使用。
 */

export type CrossFadeLayer = {
  src: string;
  startOpacity: number;
  endOpacity: number;
  label?: string;
};

const SMOOTH_EASE = Easing.bezier(0.25, 0.1, 0.25, 1.0);

const clamp01 = (v: number): number => Math.max(0, Math.min(1, v));

export const CrossFadeViewport: React.FC<{
  layers: CrossFadeLayer[];
  width?: number | string;
  height?: number | string;
  durationInFrames?: number;
  smooth?: boolean;
  blend?: React.CSSProperties["mixBlendMode"];
  style?: React.CSSProperties;
}> = ({ layers, width = "100%", height = "100%", durationInFrames, smooth = false, blend = "normal", style }) => {
  const frame = useCurrentFrame();
  const { durationInFrames: sceneDuration } = useVideoConfig();
  const span = Math.max(1, Math.round(durationInFrames ?? sceneDuration));

  const progress = interpolate(frame, [0, span], [0, 1], {
    easing: smooth ? SMOOTH_EASE : undefined,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "relative",
        overflow: "hidden",
        width,
        height,
        ...style,
      }}
    >
      {layers.map((layer, i) => {
        const opacity = clamp01(
          layer.startOpacity + (layer.endOpacity - layer.startOpacity) * progress
        );
        return (
          <Img
            key={`${i}-${layer.src}`}
            src={staticFile(layer.src)}
            aria-label={layer.label}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              objectFit: "cover",
              mixBlendMode: blend,
              opacity,
            }}
          />
        );
      })}
    </div>
  );
};
