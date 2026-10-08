// segments.ts — 五段旁白槽(段位/文本 = 3d/film/narration_script.md v0);
// 帧边界一律 stageStart/stageEnd 查 pace 表, 禁秒↔帧换算。
import { stageEnd, stageStart } from "./pace";

export interface FilmSegment {
  id: string; // 音频槽文件约定: public/audio/<id>.mp3
  label: string;
  from: number; // pace 边界锚(含)
  to: number; // 字幕窗终点(不含); pace 层重算后自动跟手
  lines: string[]; // 旁白字幕行(行级 G0/标签挂账见 narration_script.md)
}

export const SEGMENTS: FilmSegment[] = [
  {
    // 片头题卡段: pace S000(序幕 5s, 无事件空场段)——本段字幕窗
    // from=0 to=stageStart("S001") 查表即得, pace 重算自动跟手。
    // 音频槽 seg-01.mp3 从 0 起播。
    id: "seg-01",
    label: "开场",
    from: 0,
    to: stageStart("S001"),
    lines: [
      "乾隆十五年, 昆明湖上多了一道长桥; 官册文书只叫它「长桥」, 十七孔桥是后世才叫开的名字。",
      "御制诗里记得具体: 趁冬闲动工, 雇工给值, 不到两个月收工——一场官办民作的冬季赶工。",
      "四千多道安砌事件, 三千九百多块石料; 本片按营造账本把它们逐一归位, 是数字推演, 不是史料重演。",
    ],
  },
  {
    // 段位 S001-S015: ARCH01 全工序(IMPOST→CENTER_ERECT→RING→CLOSE_RING→SHOULDER→HOLD)
    id: "seg-02",
    label: "首孔教学",
    from: stageStart("S001"),
    to: stageEnd("S015"),
    lines: [
      "头一孔从墩肩教起: 撞券石先行, 墩肩分层自下而上——构件的名目, 则例册上都在。",
      "石匠先立券胎; 官式计价里这叫「支拆券胎」, 但册子只记工价, 不记先后次序。",
      "合龙之前, 拱圈自己站不住: 拆除实证里, 撤去侧墙与石灰土, 五边折线应声坍落。",
      "所以券石两侧交替、镜像配对往上砌, 谁也不许抢先压弯这一跨; 券脸石、内券石、龙门石逐位合拢。",
      "缝里灌的是餬灰——唐人石桥铭写得明白, 缝不是干拼的。",
      "合龙之后不急着卸架: 持荷满三拍, 才准落架。",
    ],
  },
  {
    // 段位 S009 起每孔 CLOSE_RING 共 17 处, 至 S379
    id: "seg-03",
    label: "合龙",
    from: stageStart("S009"),
    to: stageEnd("S379"),
    lines: [
      "龙门石楔进缺口, 拱圈闭合成环——从这个位置起, 石头自己顶住了自己。",
      "裸环合龙即自承: 裸环 case 十七孔逐孔可行, 这是全片唯一一条硬结论。",
      "但别把它说满: 十七孔全过属于模型族结论, 押着「餬灰胶结协同+冠缝共享支点」两个假设, 假设之外另有失效边界。",
    ],
  },
  {
    // 段位 S386-S391: DECENTER.DSTART.WAVE→WEDGE.1-4→CLEAR.WAVE
    id: "seg-04",
    label: "落架高潮",
    from: stageStart("S386"),
    to: stageEnd("S391"),
    lines: [
      "卸架的次序, 册子上找不到: 则例记工价, 不记工序——这是官式营造留下的空白。",
      "片中的串行卸架序是本门图式下的临界定, 非不可行证明。",
      "对称同步卸架=安全族: 全桥同一波段逐档下沉, 一百九十二个组合零违例——画面给的是这一族。",
    ],
  },
  {
    // 段位 S392-S408: ARCH01-17.FILL 肩背胞填筑, 至 S408 终态
    id: "seg-05",
    label: "桥成",
    from: stageStart("S392"),
    to: stageEnd("S408"),
    lines: [
      "券上肩背胞一层层填筑压实, 十七个环连成一整条石脊, 栏杆与石狮次第就位。",
      "拆除实证早提醒过: 券体从来依赖周围砌体共同工作——桥是整条一起站着的。",
      "片尾落回实景: 官册里的长桥, 后世口中的十七孔桥。",
    ],
  },
];

// 音频槽锚 = 段边界(TTS 实测秒数经 3d/film/pace_writeback.py 以
// {stage_id: audio_sec} 写回 pad, 使画面窗长追平音频; 成品落
// public/audio/<id>.mp3 后此处即出声)。
export const audioAnchor = (seg: FilmSegment): number => seg.from;
