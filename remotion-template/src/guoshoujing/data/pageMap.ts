// pageMap.ts — E29《郭守敬·一泉入都》页长与帧数。
// 🔴 E8 纪律：PAGE_DURATIONS_SEC 含 1.6s/页尾垫；bounds/pageLen 必须同源且标明含留白。
// 🔴 当前为按旁白字数的估算占位（约 5.1 字/秒 + 1.6s 尾垫）；
//    TTS 完成后由 build_remotion_data.py 实测时长驱动，Main 统一同步回写本文件。

export const VIDEO = { width: 1920, height: 1080, fps: 30 } as const;

export const PAGE_DURATIONS_SEC = [34.88, 39.36, 36.72, 37.6, 31.04, 38.56, 39.12, 39.44];

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
