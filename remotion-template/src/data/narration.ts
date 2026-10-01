// narration.ts — 每页一段配音的节拍。
//
// ⚠⚠ from / dur 的单位是**帧**，不是秒。
//   SlotPage 用它算槽位入场 anchor：
//     const audioFrames = beats.reduce((mx, b) => Math.max(mx, b.from + b.dur), 0);
//     const audio = audioFrames / fps;
//   若这里传秒，audio 会小 30 倍 → anchor 缩到几帧 →
//   文字在页首全部进完又早退场，**终态帧上表现为「所有槽位空白」**。
//   （E10 踩过：qa_page.py 报 8 页全缺，一度以为是渲染坏了。）
//
// TODO: 把 PAGE_AUDIO_SEC 换成实测值，见 pageMap.ts 注释里的 ffprobe 命令。

export interface Beat { name: string; from: number; dur: number }

const FPS = 30;

/** 各页**纯音频**时长（秒），实测值 */
const PAGE_AUDIO_SEC = [21.6, 22.4, 25.6, 25.6, 21.8, 22.4, 26.0, 28.8];

/** 第 n 页（1-based）的音频节拍，from/dur 单位帧 */
export const audioBeats = (pageNo: number): Beat[] =>
  PAGE_AUDIO_SEC[pageNo - 1] === undefined
    ? []
    : [{
        name: `p${pageNo}`,
        from: 0,
        dur: Math.round(PAGE_AUDIO_SEC[pageNo - 1] * FPS),
      }];

/** 各页纯音频时长（秒） */
export const AUDIO_SEC = PAGE_AUDIO_SEC;
