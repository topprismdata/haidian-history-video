// Root.tsx — 注册 E30Film Composition; 时长/fps 由 pace.ts 注入, 禁字面量。
import React from "react";
import { Composition } from "remotion";
import { E30Film, E30_DURATION, E30_FPS } from "./E30Film";

export const RemotionRoot: React.FC = () => (
  <Composition
    id="E30Film"
    component={E30Film}
    durationInFrames={E30_DURATION}
    fps={E30_FPS}
    width={1920}
    height={1080}
  />
);
