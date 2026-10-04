// pageMap.ts — E26《十方普觉寺·五次易名的半部北京佛教史》页长与帧数。
// 🔴 E8 纪律：PAGE_DURATIONS_SEC 含 1.6s/页尾垫；bounds/pageLen 必须同源且标明含留白。
import type { Theme } from "./theme";

export const VIDEO = { width: 1920, height: 1080, fps: 30 } as const;

export const PAGE_DURATIONS_SEC = [34.56, 32.0, 36.08, 35.76, 28.32, 36.08, 35.04, 37.12];

export const PAGES: Record<number, { title: string; startSec: number; durationSec: number }> = (() => {
  const pages: Record<number, { title: string; startSec: number; durationSec: number }> = {};
  let acc = 0;
  PAGE_DURATIONS_SEC.forEach((s, i) => {
    pages[i + 1] = { title: "P0" + (i + 1), startSec: acc, durationSec: s };
    acc += s;
  });
  return pages;
})();

export const TOTAL_SEC = PAGE_DURATIONS_SEC.reduce((a, b) => a + b, 0);
