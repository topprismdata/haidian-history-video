import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";

/**
 * E25《五塔寺·把塔的落成年错当成寺的始建年》分层视口引擎 — 长卷水平慢移 (Scroll-Pan)。
 *
 * 复用 E20 契约（设计规范 §2.1-3 同源）：
 * - 固定视口，内部内容按声明宽度 scrollWidth 铺开；
 * - translateX 从 0 线性（可选平滑）推至 -(scrollWidth - viewportWidth)，
 *   起幅见首、落幅见尾，帧越界 clamp 不外推；
 * - scrollWidth <= 视口宽时不平移（内容静置居左）；
 * - durationInFrames <= 0 视为已完成，Math.max(1, …) 防除零与 inputRange 非单调。
 *
 * E21 特化：面向《三山五园图》高梁河带 4000px 长卷的河道巡礼镜头。
 *
 * 红线：卷内只放图形与装裱元素，任何可 OCR 文字必须落在固定文字槽
 * （backing 卡 / tag 芯片，由 data/slots.json 承载），严禁随卷漂移、
 * 严禁由本组件导出任何文字槽——QA 槽位几何按画布恒定坐标检验。
 */

const SMOOTH_EASE = Easing.bezier(0.25, 0.1, 0.25, 1.0);

export const ScrollPanView: React.FC<{
  scrollWidth: number;
  viewportWidth: number;
  durationInFrames?: number;
  smooth?: boolean;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({ scrollWidth, viewportWidth, durationInFrames = 90, smooth = false, style, children }) => {
  const frame = useCurrentFrame();
  const safeDuration = Math.max(1, Math.round(durationInFrames));
  const progress = interpolate(frame, [0, safeDuration], [0, 1], {
    easing: smooth ? SMOOTH_EASE : undefined,
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const drift = Math.max(0, scrollWidth - viewportWidth);

  return (
    <div
      style={{
        position: "relative",
        overflow: "hidden",
        width: "100%",
        height: "100%",
        ...style,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: scrollWidth,
          height: "100%",
          transform: `translate3d(${-drift * progress}px, 0, 0)`,
          willChange: "transform",
        }}
      >
        {children}
      </div>
    </div>
  );
};
