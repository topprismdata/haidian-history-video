// narration.ts — E26《十方普觉寺·五次易名的半部北京佛教史》配音节拍。实测 2026-10-04。

export interface Beat { name: string; from: number; dur: number }

const FPS = 30;

const PAGE_AUDIO_SEC = [32.96, 30.40, 34.48, 34.16, 26.72, 34.48, 33.44, 35.52];

export const audioBeats = (pageNo: number): Beat[] =>
  PAGE_AUDIO_SEC[pageNo - 1] === undefined
    ? []
    : [{
        name: `p${pageNo}`,
        from: 0,
        dur: Math.round(PAGE_AUDIO_SEC[pageNo - 1] * FPS),
      }];

export const AUDIO_SEC = PAGE_AUDIO_SEC;
