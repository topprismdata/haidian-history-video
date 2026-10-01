// EpisodeCourse — 8 页 16:9 宣纸工笔淡彩风（E1–E10 同管线）。
//
// 新开一集：复制本目录 → 改下面 4 处
//   1. EPISODE           集目录名（= public/<EPISODE>/）
//   2. audio 目录名      同上
//   3. PAGE_DURATIONS_SEC 由实测音频时长生成（见 METHODOLOGY §7）
//   4. pages/Page0N.tsx  的 page={N}
import React from "react";
import { AbsoluteFill, Audio, Sequence, Series, staticFile } from "remotion";
import { PAGE_DURATIONS_SEC, VIDEO } from "./data/pageMap";
import { audioBeats } from "./data/narration";
import { Page01 } from "./pages/Page01";
import { Page02 } from "./pages/Page02";
import { Page03 } from "./pages/Page03";
import { Page04 } from "./pages/Page04";
import { Page05 } from "./pages/Page05";
import { Page06 } from "./pages/Page06";
import { Page07 } from "./pages/Page07";
import { Page08 } from "./pages/Page08";

const PAGES = [Page01, Page02, Page03, Page04, Page05, Page06, Page07, Page08];
const EPISODE = "landianchang";   // ← 改这里

/** 页起点：前序各页**纯音频**累加（不含 1.6s 留白） */
const pageOffsetFrames = (i: number): number =>
  PAGE_DURATIONS_SEC.slice(0, i).reduce(
    (sum, s) => sum + Math.round(s * VIDEO.fps),
    0,
  );

export const DURATION_IN_FRAMES = PAGE_DURATIONS_SEC.reduce(
  (sum, s) => sum + Math.round(s * VIDEO.fps),
  0,
);

export const EpisodeCourse: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#f5eeda" }}>
    {PAGES.map((_, i) =>
      audioBeats(i + 1).map((b) => (
        // ⚠ b.from 已是**帧**（见 data/narration.ts 的单位约定），不要再乘 fps
        <Sequence key={`a-${b.name}`} from={pageOffsetFrames(i) + b.from} name={b.name}>
          <Audio src={staticFile(`audio/${EPISODE}/${b.name}.wav`)} />
        </Sequence>
      )),
    )}
    <Series>
      {PAGES.map((Page, i) => (
        <Series.Sequence
          key={i}
          durationInFrames={Math.round(PAGE_DURATIONS_SEC[i] * VIDEO.fps)}
          name={`Page-0${i + 1}`}
        >
          <Page />
        </Series.Sequence>
      ))}
    </Series>
  </AbsoluteFill>
);
