// subtitles.ts — 字幕：按口播稿分句，时长按字数比例分配。
// TODO: 由 narration/all.json 生成。参考 landianchang_video/build_remotion_data.py
//       的做法：按 [。！？；] 切句，每句 dur = len(句)/len(整段) × 该页音频时长。

export interface CaptionLine { text: string; from: number; dur: number }

export const SUBTITLES: Record<number, CaptionLine[]> = {
  // 1: [
  //   { text: "第一句。", from: 0.00, dur: 2.10 },
  //   { text: "第二句。", from: 2.10, dur: 1.80 },
  // ],
};
