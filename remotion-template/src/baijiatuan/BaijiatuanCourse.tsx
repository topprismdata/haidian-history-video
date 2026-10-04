// BaijiatuanCourse — E27《白家疃·纸上的疃，嘴里的滩》8 页，16:9。
// 页长与音频锚点同源：data/pageMap.ts（含 1.6s/页尾垫）＋ data/narration.ts 纯音频。
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

const pageOffsetFrames = (i: number): number =>
  PAGE_DURATIONS_SEC.slice(0, i).reduce(
    (sum, s) => sum + Math.round(s * VIDEO.fps), 0,
  );

export const BAIJIATUAN_DURATION_IN_FRAMES = PAGE_DURATIONS_SEC.reduce(
  (sum, s) => sum + Math.round(s * VIDEO.fps), 0,
);

export const BaijiatuanCourse: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#f5eeda" }}>
    {PAGES.map((_, i) =>
      audioBeats(i + 1).map((b) => (
        <Sequence key={`a-${b.name}`} from={pageOffsetFrames(i) + b.from} name={b.name}>
          <Audio src={staticFile(`audio/baijiatuan/${b.name.replace(/^p(\d)$/, "p0$1")}.wav`)} />
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
