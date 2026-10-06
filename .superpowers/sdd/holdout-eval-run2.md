# Holdout v1 首轮跑分（run1）

- 快照：`haidian_kg/evaluation/holdout_v1.jsonl`（33 段，text_sha1 全量校验通过）
- 引擎：ClosureExpander `v4` / 规则档 `rp-v4`
- 真值：calibration 8 模块 48 实体字形表（独立路径，评分代码零 expansion 依赖）；**代理金标**——mention precision 为下界（KB 未收录的真实地名计 FP），见「偏差」

## 五指标 vs 冻结闸门

| 指标 | 实测 | 阈值 | 判定 |
|---|---|---|---|
| mention precision | 0.1613 | >= 0.90 | ❌ 不过 |
| mention recall | 0.3226 | >= 0.85 | ❌ 不过 |
| high-conf precision | — | >= 0.95 | ❌ 不过 |
| duplication | 0.0000 | <= 0.05 | ✅ 过 |
| collision | 0.0175 | == 0.00 | ❌ 不过 |
| mention F1（辅助） | 0.2151 | — | — |

**闸门结论：未全过 ❌**（计数 TP=10 FP=52 FN=21；gold 实体 17，假说总数 57）

## 逐段明细

| 段 | 金标 | 预测 | TP | FP | FN | high-conf |
|---|---|---|---|---|---|---|
| `era4_liao_jin.md:L41-L41` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `era4_liao_jin.md:L42-L49` | 1 | 9 | 0 | 9 | 1 | 0/0 |
| `era4_liao_jin.md:L50-L50` | 0 | 2 | 0 | 2 | 0 | 0/0 |
| `era4_liao_jin.md:L51-L51` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `era4_liao_jin.md:L54-L54` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `era4_liao_jin.md:L55-L55` | 0 | 3 | 0 | 3 | 0 | 0/0 |
| `era4_liao_jin.md:L56-L56` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `era5_yuan.md:L41-L41` | 0 | 1 | 0 | 1 | 0 | 0/0 |
| `era5_yuan.md:L42-L42` | 0 | 3 | 0 | 3 | 0 | 0/0 |
| `era5_yuan.md:L43-L43` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `era6_ming.md:L28-L29` | 1 | 2 | 0 | 2 | 1 | 0/0 |
| `era6_ming.md:L30-L33` | 4 | 6 | 1 | 5 | 3 | 0/0 |
| `era6_ming.md:L34-L34` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `era7_qing.md:L10-L11` | 0 | 3 | 0 | 3 | 0 | 0/0 |
| `era7_qing.md:L12-L13` | 1 | 1 | 1 | 0 | 0 | 0/0 |
| `era7_qing.md:L14-L15` | 0 | 2 | 0 | 2 | 0 | 0/0 |
| `era7_qing.md:L16-L16` | 0 | 4 | 0 | 4 | 0 | 0/0 |
| `era7_qing.md:L17-L17` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `era7_qing.md:L20-L22` | 9 | 4 | 3 | 1 | 6 | 0/0 |
| `era7_qing.md:L23-L24` | 3 | 4 | 2 | 2 | 1 | 0/0 |
| `era7_qing.md:L25-L26` | 0 | 3 | 0 | 3 | 0 | 0/0 |
| `era7_qing.md:L27-L27` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `era7_qing.md:L30-L30` | 0 | 1 | 0 | 1 | 0 | 0/0 |
| `era7_qing.md:L31-L31` | 0 | 3 | 0 | 3 | 0 | 0/0 |
| `era7_qing.md:L32-L32` | 2 | 1 | 1 | 0 | 1 | 0/0 |
| `era7_qing.md:L33-L33` | 3 | 3 | 2 | 1 | 1 | 0/0 |
| `era7_qing.md:L34-L34` | 1 | 0 | 0 | 0 | 1 | 0/0 |
| `era7_qing.md:L35-L35` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `era7_qing.md:L38-L38` | 4 | 0 | 0 | 0 | 4 | 0/0 |
| `era7_qing.md:L39-L40` | 0 | 4 | 0 | 4 | 0 | 0/0 |
| `era7_qing.md:L41-L41` | 0 | 0 | 0 | 0 | 0 | 0/0 |
| `era7_qing.md:L47-L48` | 0 | 1 | 0 | 1 | 0 | 0/0 |
| `era7_qing.md:L49-L50` | 2 | 2 | 0 | 2 | 2 | 0/0 |

## 漏检归因（21 条，100% 逐条）

**cue-window-narrow（1 条）**

- `era7_qing.md:L38-L38`「穷八家」（KB 字形「穷八家」）：仅 cue 窗通道可达（「家」非收录后缀），窗内未收拢该字形
**reign-prefix-suppressed（1 条）**

- `era7_qing.md:L38-L38`「穷八家」（KB 字形「穷八家」）：回溯头落进纪年「乾隆」被纪年模式压制
**same-form-elsewhere（6 条）**

- `era6_ming.md:L30-L33`「娘娘府」（KB 字形「娘娘府」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `era7_qing.md:L20-L22`「圆明园」（KB 字形「圆明园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `era7_qing.md:L20-L22`「圆明园」（KB 字形「圆明园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `era7_qing.md:L20-L22`「树村」（KB 字形「树村」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `era7_qing.md:L23-L24`「外火器营」（KB 字形「外火器营」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
- `era7_qing.md:L32-L32`「一亩园」（KB 字形「一亩园」）：同形 occurrence 落在段内其他位置（挖掘器同 fact 同形只发一次）
**suffix-and-cue-missing（8 条）**

- `era4_liao_jin.md:L42-L49`「董四墓」（KB 字形「董四墓」）：通名后缀「墓」不在词表且短语无线索词（v4 双通道同时不可达）
- `era6_ming.md:L30-L33`「董四墓」（KB 字形「董四墓」）：通名后缀「墓」不在词表且短语无线索词（v4 双通道同时不可达）
- `era6_ming.md:L30-L33`「董四墓」（KB 字形「董四墓」）：通名后缀「墓」不在词表且短语无线索词（v4 双通道同时不可达）
- `era7_qing.md:L20-L22`「正黄旗营房」（KB 字形「正黄旗营房」）：通名后缀「房」不在词表且短语无线索词（v4 双通道同时不可达）
- `era7_qing.md:L20-L22`「镶黄旗营房」（KB 字形「镶黄旗营房」）：通名后缀「房」不在词表且短语无线索词（v4 双通道同时不可达）
- `era7_qing.md:L20-L22`「正白旗营房」（KB 字形「正白旗营房」）：通名后缀「房」不在词表且短语无线索词（v4 双通道同时不可达）
- `era7_qing.md:L34-L34`「苏州街」（KB 字形「苏州街」）：通名后缀「街」不在词表且短语无线索词（v4 双通道同时不可达）
- `era7_qing.md:L49-L50`「苏州街」（KB 字形「苏州街」）：通名后缀「街」不在词表且短语无线索词（v4 双通道同时不可达）
**walkback-overrun（3 条）**

- `era6_ming.md:L28-L29`「七十二府」（KB 字形「七十二府」）：回溯跨度 10 字 > 6 上限（「俗呼一溜…」），该命中作废
- `era7_qing.md:L33-L33`「西顶娘娘庙」（KB 字形「西顶娘娘庙」）：回溯跨度 8 字 > 6 上限（「蓝靛厂西…」），该命中作废
- `era7_qing.md:L49-L50`「苏州街」（KB 字形「苏州街」）：回溯跨度 9 字 > 6 上限（「将万寿山…」），该命中作废
**walkback-too-short（2 条）**

- `era7_qing.md:L38-L38`「大有庄」（KB 字形「大有庄」）：回溯在边界字「有」处截停，只剩「庄」不足 2 字专名下限，命中作废
- `era7_qing.md:L38-L38`「大有庄」（KB 字形「大有庄」）：回溯在边界字「有」处截停，只剩「庄」不足 2 字专名下限，命中作废

## 误报归因（52 条，100% 逐条）

**boundary-splice（4 条）**

- `era4_liao_jin.md:L42-L49`「北安河」（suffix_scan/mid）：头带方位/虚词「北」，回溯边界没收干净
- `era4_liao_jin.md:L42-L49`「西山法海寺」（suffix_scan/mid）：头带方位/虚词「西」，回溯边界没收干净
- `era4_liao_jin.md:L50-L50`「西山山麓泉」（suffix_scan/mid）：头带方位/虚词「西」，回溯边界没收干净
- `era4_liao_jin.md:L50-L50`「后世三山五园」（suffix_scan/mid）：头带方位/虚词「后」，回溯边界没收干净
**kb-coverage-gap（48 条）**

- `era4_liao_jin.md:L42-L49`「大觉寺」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era4_liao_jin.md:L42-L49`「香山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era4_liao_jin.md:L42-L49`「香山公园香山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era4_liao_jin.md:L42-L49`「海淀温泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era4_liao_jin.md:L42-L49`「海淀凤凰岭」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era4_liao_jin.md:L42-L49`「碧云寺」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era4_liao_jin.md:L42-L49`「石景山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era4_liao_jin.md:L55-L55`「海淀」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era4_liao_jin.md:L55-L55`「海淀区三里河」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era4_liao_jin.md:L55-L55`「的金代行宫园」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era5_yuan.md:L41-L41`「碧云寺」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era5_yuan.md:L42-L42`「香山万安山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era5_yuan.md:L42-L42`「碧云庵」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era5_yuan.md:L42-L42`「刹碧云寺」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era6_ming.md:L28-L29`「金山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era6_ming.md:L28-L29`「俗呼一溜边山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era6_ming.md:L30-L33`「天寿山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era6_ming.md:L30-L33`「金山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era6_ming.md:L30-L33`「翠微山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era6_ming.md:L30-L33`「妃嫔园」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era6_ming.md:L30-L33`「居民依墓成村」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L10-L11`「畅春园」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L10-L11`「恩佑寺」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L10-L11`「恩慕寺山」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L14-L15`「万寿山清漪园」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L14-L15`「昆明湖」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L16-L16`「静明园」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L16-L16`「静宜园」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L16-L16`「玉泉山静明园」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L16-L16`「香山静宜园」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L20-L22`「肖家河」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L23-L24`「建满蒙八旗」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L23-L24`「枪炮演武场」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L25-L26`「健锐营」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L25-L26`「按八旗」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L25-L26`「香山静宜园」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L30-L30`「玉泉山甘泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L31-L31`「万泉庄」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L31-L31`「泉宗庙」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L31-L31`「十处天然泉」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L33-L33`「京西第一大庙」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L39-L40`「牛栏庄」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L39-L40`「柳浪庄」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L39-L40`「万泉河」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L39-L40`「讹写作六郎庄」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L47-L48`「六郎庄」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L49-L50`「将万寿山后湖」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）
- `era7_qing.md:L49-L50`「皇家宫廷内湖」（suffix_scan/mid）：规则按专名+通名结构正常命中，但 KB 无此实体（真值覆盖缺口）

## 假说层覆盖（duplication / collision 证据）

- 被覆盖 gold 实体：9；其中被 ≥2 假说覆盖（duplication 分子）：0
  - `ent_changchunyuan` ← 假说 长春园
  - `ent_landianchang` ← 假说 蓝靛厂
  - `ent_niangniangfu` ← 假说 娘娘府
  - `ent_qinglongqiao` ← 假说 青龙桥
  - `ent_shucun` ← 假说 树村
  - `ent_waihuoqiying` ← 假说 外火器营
  - `ent_yimuyuan` ← 假说 一亩园
  - `ent_yuanmingyuan` ← 假说 圆明园
  - `ent_yuanmingyuan_parent` ← 假说 圆明园
- 覆盖 ≥2 gold 实体的假说（collision 分子）：1
  - 「一亩园」→ ent_yimuyuan
  - 「圆明园」→ ent_yuanmingyuan、ent_yuanmingyuan_parent ⚠️collision
  - 「外火器营」→ ent_waihuoqiying
  - 「娘娘府」→ ent_niangniangfu
  - 「树村」→ ent_shucun
  - 「蓝靛厂」→ ent_landianchang
  - 「长春园」→ ent_changchunyuan
  - 「青龙桥」→ ent_qinglongqiao

  **collision 案例归因**：「圆明园」覆盖 ent_yuanmingyuan（yuanmingyuan 模块） + ent_yuanmingyuan_parent（banners 模块） —— 同一字形挂多个 KB 实体：若为跨模块同指（无 identity 断言），属 KB 双建模缺陷，非引擎合并错误；若确为异指，属引擎真碰撞

## 结论与最小修复路径

**闸门不通过**，卡在：mention_precision、mention_recall、high_conf_precision、collision_rate。

敏感度（两个有机械依据的界，非口径放水）：

- **precision 严格下界 = 实测值**：KB 覆盖缺口 FP（48 条，真实地名但 8 模块未建词条）按冻结公式计错。若经人工判定为真地名，P 上界 = 0.714——仍低于 0.90。
- **recall 受设计性拒发拖累**：0 条 FN 是引擎按身份/噪声纪律（旗名子串、机构复合词）主动拒发。若视为命中，R 上界 = 0.323——仍低于 0.85。

两个上界都够不着阈值 ⇒ 缺口是结构性的，调参无解，需按下列路径修复后重跑（holdout 不变）。

### 修复路径（按影响面排序）

| 优先级 | 归因类 | 条数(FN/FP) | 最小修复 | 说明 |
|---|---|---|---|---|
| P0 | `boundary-splice` | 0 / 4 | 回溯边界字增补 | 「今大觉寺」「北安河」：今/北/西 等头部边界字——注意其中部分（北安河）实为真地名，修复时须防误伤 lexicalized 方位头（西三旗先例） |
| P0 | `walkback-overrun` | 3 / 0 | 句读/回溯边界表扩记号 | rp-v3 的 _PUNCT_CHARS/_STOP_CHARS 缺 Markdown 记号（*、-、空格）与书名号《》；一处表修复同时治理多条 |
| 数据层 | `kb-coverage-gap` | 0 / 48 | KB 收录缺口 | 清水院/大觉寺/金山/万泉河等是真实海淀地名但 8 个校准模块未建词条：属代理金标口径偏差的主要来源（见敏感度），不是挖掘器缺陷 |
| P1 | `walkback-too-short` | 2 / 0 | 提示词/专名内部字冲突 | 「有」既是 cue 又在专名内部（大有庄）：需 known 别名优先召回或词边界判断，属引擎行为变更（v5 候选） |
| P2 | `suffix-and-cue-missing` | 8 / 0 | 通名后缀表扩墓/街/院 | 扩表必须先过 spec §5.2 Hard FP/Mutation 独立负控制，不在本闸门内擅动 |
| P2 | `same-form-elsewhere` | 6 / 0 | 同 fact 同形只发一次 | 多次出现只记首现：跨 fact 互证是设计行为，可按 mention 密度重估 |
| P2 | `cue-window-narrow` | 1 / 0 | cue 窗策略 | 生僻通名（院）靠 12 字窗保不住：可在 v4 引入 known 表预匹配 |
| P2 | `reign-prefix-suppressed` | 1 / 0 | 纪年模式 | 回溯头落进纪年/帝号模式被压 |

### 决策项（超出本评估器权限，需主代理裁定）

v4 已落地（known-mention 通道 + rp-v4 记号/边界表，v4/rp-v4）
纯地名的已知名压制已消除。余下两类身份层张力：

1. **机构复合词内嵌已知实体**（0 条，noise-keyword）：「圆明园护军营」「圆明园副将」语境中的圆明园 mention 被职官关键词拦下——引擎按纪律拒发（这些复合词确实不是地点），冻结公式恒计 FN。出路：(a) gold 口径为「复合词内嵌」单列（冻结修正案，需你批准）；(b) v5 内嵌实体识别。
2. **旗营专名**（0 条，stopword-suppressed/旗名子串）：「正黄旗营房」类不是纯地名、是建置名，营/房后缀通道天然不可达——建议在 KB 建置层补专名通道，或 gold 口径豁免。
3. **KB 跨模块双建模（collision 硬闸新败因）**：「圆明园」同时挂 ent_yuanmingyuan 与 ent_yuanmingyuan_parent。两词条分属不同校准模块且无 identity 断言：若同指，需 KB 侧补 DiachronicIdentityAssertion 或合并词条（数据修复，不是引擎修复）；若异指，则引擎真碰撞。碰撞=0 硬闸在该数据修复前无法过闸。

## 偏差声明

1. v1 真值为**代理金标**（KB 已知实体字形；人工 holdout_gold.jsonl 尚未产出）：KB 未收录的真实地名按公式计 FP，故 mention precision 实测值是真值的下界；recall 不受影响（gold 即 KB 实体提及）。
2. 分母为 0 的指标记 None 并判不过（证据不足不放行），本轮：high_conf_precision
3. span 恢复：挖掘器不产 offset，评估器按「同 fact 同形只发一次」的引擎保证取首现位置（`occurrence.text_span` 是窗口不是 span，不可用）。
