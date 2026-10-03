// narration.ts — E22《太舟坞·唐代羁縻带州与元代船坞之谜》配音节拍。实测 2026-10-03。

export interface Beat { name: string; from: number; dur: number }

const FPS = 30;

const PAGE_AUDIO_SEC = [30.80, 30.83, 36.56, 30.96, 34.24, 33.68, 27.12, 33.84];

export const audioBeats = (pageNo: number): Beat[] =>
  PAGE_AUDIO_SEC[pageNo - 1] === undefined
    ? []
    : [{
        name: `p${pageNo}`,
        from: 0,
        dur: Math.round(PAGE_AUDIO_SEC[pageNo - 1] * FPS),
      }];

export const AUDIO_SEC = PAGE_AUDIO_SEC;
