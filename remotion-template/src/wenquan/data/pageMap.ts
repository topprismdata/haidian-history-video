// pageMap.ts — E28《温泉·「温泉」之前叫「石窝」》页长与帧数。
// 🔴 E8 纪律：PAGE_DURATIONS_SEC 含 1.6s/页尾垫；bounds/pageLen 必须同源且标明含留白。
// 时长来源：wenquan_video/narration/durations.json（2026-10-04 TTS 实测）＋ 1.6s 尾垫。
export const VIDEO = { width: 1920, height: 1080, fps: 30 } as const;

export const PAGE_DURATIONS_SEC = [34.56, 41.28, 38.08, 43.92, 39.45, 43.6, 39.29, 40.56];

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
