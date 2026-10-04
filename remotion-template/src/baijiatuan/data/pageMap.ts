// pageMap.ts — E27《白家疃·纸上的疃，嘴里的滩》页长与帧数。
// 🔴 E8 纪律：PAGE_DURATIONS_SEC 含 1.6s/页尾垫；bounds/pageLen 必须同源且标明含留白。
// 数值来源：baijiatuan_video/build_remotion_data.py 实测 ffprobe（2026-10-04，p05 因
// TTS 全文触顶循环改为两段拼接后实测 35.17s）。
// PAGE_DURATIONS_SEC = durations.json 纯音频时长 + 1.6s 尾垫（round 2 位）。

export const VIDEO = { width: 1920, height: 1080, fps: 30 } as const;

export const PAGE_DURATIONS_SEC = [31.84, 41.44, 42.08, 42.25, 36.77, 57.93, 50.88, 38.64];

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
